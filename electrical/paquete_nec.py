# electrical/paquete_nec.py
"""
Paquete NEC (orquestador) — FV Engine

Reglas duras (cumplimiento):
- Este módulo NO calcula ampacidad/VD/calibre: delega a electrical/conductores/.
- Este módulo NO dimensiona OCPD: delega a electrical/protecciones/.
- Este módulo solo orquesta: corrientes DC/AC, armado del paquete, warnings y resumen.

Compatibilidad:
- Mantiene salida tipo dict con llaves principales:
  dc, ac, ocpd, conductores, canalizacion, warnings, resumen_pdf
- Integra spd y seccionamiento (si existen) sin romper consumidores legacy.

Entradas esperadas (flexibles):
- `entrada` puede ser dict-like. Se toleran claves faltantes.
- Se recomiendan estas claves (si existen en tu proyecto):
    * potencia_dc_w / potencia_dc_kw
    * potencia_ac_w / potencia_ac_kw
    * vdc_nom (V)
    * vac_ll (V) o vac_ln (V)
    * fases (1 o 3)
    * fp (factor de potencia)
    * eficiencia_inversor (0..1)
    * circuitos: lista de tramos/circuitos a calcular (DC/AC), opcional
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple
import math
import inspect
import warnings as _pywarnings

# Importes obligatorios por tu instrucción
from electrical.conductores.calculo_conductores import tramo_conductor
from electrical.protecciones.ocpd import armar_ocpd
from electrical.protecciones.spd import recomendar_spd
from electrical.protecciones.seccionamiento import recomendar_seccionamiento
from electrical.canalizacion.conduit import canalizacion_fv


# ---------------------------
# Utilidades de orquestación
# ---------------------------

def _get_num(m: Mapping[str, Any], *keys: str, default: Optional[float] = None) -> Optional[float]:
    for k in keys:
        if k in m and m[k] is not None:
            try:
                return float(m[k])
            except Exception:
                return default
    return default


def _get_int(m: Mapping[str, Any], *keys: str, default: Optional[int] = None) -> Optional[int]:
    for k in keys:
        if k in m and m[k] is not None:
            try:
                return int(m[k])
            except Exception:
                return default
    return default


def _get_str(m: Mapping[str, Any], *keys: str, default: Optional[str] = None) -> Optional[str]:
    for k in keys:
        if k in m and m[k] is not None:
            return str(m[k])
    return default


def _sqrt3() -> float:
    return 1.7320508075688772


def _call_with_supported_kwargs(func: Callable[..., Any], **kwargs: Any) -> Any:
    """
    Llama una función filtrando kwargs a solo los parámetros soportados.
    Esto evita romper por cambios de firmas durante el refactor.
    """
    try:
        sig = inspect.signature(func)
        allowed = set(sig.parameters.keys())
        filtered = {k: v for k, v in kwargs.items() if k in allowed}
        return func(**filtered)
    except Exception:
        # Si introspección falla (builtins / wrappers), intenta llamada directa
        return func(**kwargs)


def _merge_warnings(base: list[str], *more: Iterable[str]) -> list[str]:
    out = list(base or [])
    for it in more:
        if not it:
            continue
        for w in it:
            if w and w not in out:
                out.append(str(w))
    return out


# ---------------------------
# Cálculo de corrientes (solo magnitudes base)
# ---------------------------

@dataclass(frozen=True)
class CorrientesBase:
    idc_nom: Optional[float]
    iac_nom: Optional[float]
    meta: Dict[str, Any]


def _corrientes_dc_ac(entrada: Mapping[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], list[str]]:
    """
    Calcula corrientes NOMINALES base para alimentar módulos dominio.
    No dimensiona conductores ni protecciones.
    """
    warnings: list[str] = []

    pdc_w = _get_num(entrada, "potencia_dc_w", default=None)
    if pdc_w is None:
        pdc_kw = _get_num(entrada, "potencia_dc_kw", default=None)
        pdc_w = pdc_kw * 1000.0 if pdc_kw is not None else None

    pac_w = _get_num(entrada, "potencia_ac_w", default=None)
    if pac_w is None:
        pac_kw = _get_num(entrada, "potencia_ac_kw", default=None)
        pac_w = pac_kw * 1000.0 if pac_kw is not None else None

    vdc = _get_num(entrada, "vdc_nom", "vdc", default=None)
    vac_ll = _get_num(entrada, "vac_ll", "v_ll", default=None)
    vac_ln = _get_num(entrada, "vac_ln", "v_ln", default=None)

    fases = _get_int(entrada, "fases", default=None)
    if fases not in (1, 3, None):
        warnings.append(f"Valor de 'fases' inválido ({fases}). Se ignora.")
        fases = None

    fp = _get_num(entrada, "fp", "factor_potencia", default=1.0)
    if fp is not None and (fp <= 0 or fp > 1.0):
        warnings.append(f"FP fuera de rango ({fp}). Se fuerza a 1.0.")
        fp = 1.0

    eff = _get_num(entrada, "eficiencia_inversor", "eta_inversor", default=None)
    if eff is not None and (eff <= 0 or eff > 1.0):
        warnings.append(f"Eficiencia inversor fuera de rango ({eff}). Se ignora.")
        eff = None

    # DC nominal
    idc_nom = _get_num(entrada, "idc_nom", "corriente_dc", default=None)
    if idc_nom is None and pdc_w is not None and vdc is not None and vdc > 0:
        idc_nom = pdc_w / vdc
    if idc_nom is None:
        warnings.append("No se pudo inferir idc_nom (faltan potencia_dc y/o vdc_nom).")

    # AC nominal
    iac_nom = _get_num(entrada, "iac_nom", "corriente_ac", default=None)
    if iac_nom is None and pac_w is not None:
        # Si no dan fases, intenta inferir: si hay vac_ll => 3 fases, si hay vac_ln => 1 fase
        fases_eff = fases
        if fases_eff is None:
            if vac_ll is not None:
                fases_eff = 3
            elif vac_ln is not None:
                fases_eff = 1

        if fases_eff == 3 and vac_ll is not None and vac_ll > 0:
            iac_nom = pac_w / (_sqrt3() * vac_ll * (fp or 1.0))
        elif fases_eff == 1:
            v1 = vac_ln or vac_ll
            if v1 is not None and v1 > 0:
                iac_nom = pac_w / (v1 * (fp or 1.0))

    if iac_nom is None:
        # alternativa: si solo hay Pdc y eficiencia
        if pac_w is None and pdc_w is not None and eff is not None:
            pac_w = pdc_w * eff
            # reintenta con lo que haya
            v1 = vac_ln or vac_ll
            if v1 and v1 > 0:
                if (fases or 1) == 3 and vac_ll:
                    iac_nom = pac_w / (_sqrt3() * vac_ll * (fp or 1.0))
                else:
                    iac_nom = pac_w / (v1 * (fp or 1.0))

    if iac_nom is None:
        warnings.append("No se pudo inferir iac_nom (faltan potencia_ac y/o voltajes AC).")

    dc = {
        "potencia_dc_w": pdc_w,
        "vdc_nom": vdc,
        "idc_nom": idc_nom,
    }

    ac = {
        "potencia_ac_w": pac_w,
        "vac_ll": vac_ll,
        "vac_ln": vac_ln,
        "fases": fases,
        "fp": fp,
        "iac_nom": iac_nom,
    }

    return dc, ac, warnings


# ---------------------------
# API pública (orquestación)
# ---------------------------

def armar_paquete_nec(entrada: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Ensambla el paquete NEC (dict) consumido por adaptador_nec/core/UI/PDF.

    Salida:
      {
        "dc": {...},
        "ac": {...},
        "ocpd": {...} | None,
        "conductores": {...},
        "canalizacion": {...} | None,
        "spd": {...} | None,
        "seccionamiento": {...} | None,
        "warnings": [...],
        "resumen_pdf": {...}
      }
    """
    warnings_out: list[str] = []

    # 1) Entradas → Validación (mínima y defensiva)
    if not isinstance(entrada, Mapping):
        raise TypeError("armar_paquete_nec: 'entrada' debe ser Mapping (dict-like).")

    # 2) Cálculos (solo magnitudes base aquí)
    dc, ac, w_corr = _corrientes_dc_ac(entrada)
    warnings_out = _merge_warnings(warnings_out, w_corr)

    # 3) Dominio protecciones (OCPD / SPD / seccionamiento)
    ocpd: Optional[Dict[str, Any]] = None
    spd: Optional[Dict[str, Any]] = None
    seccionamiento: Optional[Dict[str, Any]] = None

    try:
        ocpd = _call_with_supported_kwargs(
            armar_ocpd,
            entrada=entrada,
            dc=dc,
            ac=ac,
            idc_nom=dc.get("idc_nom"),
            iac_nom=ac.get("iac_nom"),
        )
        if isinstance(ocpd, Mapping):
            warnings_out = _merge_warnings(warnings_out, ocpd.get("warnings", []) if isinstance(ocpd.get("warnings"), list) else [])
    except Exception as e:
        warnings_out.append(f"OCPD no disponible o falló armar_ocpd(): {e}")

    try:
        spd = _call_with_supported_kwargs(
            recomendar_spd,
            entrada=entrada,
            dc=dc,
            ac=ac,
            ocpd=ocpd,
        )
        if isinstance(spd, Mapping):
            warnings_out = _merge_warnings(warnings_out, spd.get("warnings", []) if isinstance(spd.get("warnings"), list) else [])
    except Exception as e:
        warnings_out.append(f"SPD no disponible o falló recomendar_spd(): {e}")

    try:
        seccionamiento = _call_with_supported_kwargs(
            recomendar_seccionamiento,
            entrada=entrada,
            dc=dc,
            ac=ac,
            ocpd=ocpd,
        )
        if isinstance(seccionamiento, Mapping):
            warnings_out = _merge_warnings(
                warnings_out,
                seccionamiento.get("warnings", []) if isinstance(seccionamiento.get("warnings"), list) else [],
            )
    except Exception as e:
        warnings_out.append(f"Seccionamiento no disponible o falló recomendar_seccionamiento(): {e}")

    # 4) Dominio conductores (motor único)
    # Soporta dos modos:
    #   - Si entrada trae 'circuitos': calcula lista.
    #   - Si no, intenta calcular un tramo DC y/o AC a partir de idc_nom/iac_nom.
    conductores: Dict[str, Any] = {"circuitos": [], "warnings": []}

    circuitos = entrada.get("circuitos", None)
    try:
        if isinstance(circuitos, list) and circuitos:
            for idx, c in enumerate(circuitos, start=1):
                if not isinstance(c, Mapping):
                    conductores["warnings"].append(f"Circuito #{idx} inválido (no dict). Se omite.")
                    continue
                # Enriquecemos con corrientes base si el circuito no trae
                c_idc = _get_num(c, "corriente", "i", "idc", default=None)
                if c_idc is None and str(c.get("tipo", "")).upper() == "DC":
                    c_idc = dc.get("idc_nom")
                if c_idc is None and str(c.get("tipo", "")).upper() == "AC":
                    c_idc = ac.get("iac_nom")

                res = _call_with_supported_kwargs(
                    tramo_conductor,
                    entrada=entrada,
                    circuito=c,
                    corriente=c_idc,
                    dc=dc,
                    ac=ac,
                    ocpd=ocpd,
                )
                conductores["circuitos"].append(res)
        else:
            # modo mínimo: un tramo DC y un tramo AC si hay corriente
            if dc.get("idc_nom") is not None:
                res_dc = _call_with_supported_kwargs(
                    tramo_conductor,
                    entrada=entrada,
                    tipo="DC",
                    corriente=dc.get("idc_nom"),
                    dc=dc,
                    ac=ac,
                    ocpd=ocpd,
                )
                conductores["circuitos"].append(res_dc)

            if ac.get("iac_nom") is not None:
                res_ac = _call_with_supported_kwargs(
                    tramo_conductor,
                    entrada=entrada,
                    tipo="AC",
                    corriente=ac.get("iac_nom"),
                    dc=dc,
                    ac=ac,
                    ocpd=ocpd,
                )
                conductores["circuitos"].append(res_ac)

            if not conductores["circuitos"]:
                conductores["warnings"].append("No se calcularon tramos (no hay corrientes base ni 'circuitos').")

        # levantar warnings de tramos si existen
        for item in conductores["circuitos"]:
            if isinstance(item, Mapping) and isinstance(item.get("warnings"), list):
                conductores["warnings"] = _merge_warnings(conductores["warnings"], item["warnings"])
    except Exception as e:
        conductores["warnings"] = _merge_warnings(conductores["warnings"], [f"Falló cálculo de conductores (tramo_conductor): {e}"])

    warnings_out = _merge_warnings(warnings_out, conductores.get("warnings", []))

    # 5) Dominio canalización (conduit)
    canalizacion: Optional[Dict[str, Any]] = None
    try:
        canalizacion = _call_with_supported_kwargs(
            canalizacion_fv,
            entrada=entrada,
            dc=dc,
            ac=ac,
            ocpd=ocpd,
            conductores=conductores,
        )
        if isinstance(canalizacion, Mapping):
            warnings_out = _merge_warnings(warnings_out, canalizacion.get("warnings", []) if isinstance(canalizacion.get("warnings"), list) else [])
    except Exception as e:
        warnings_out.append(f"Canalización no disponible o falló canalizacion_fv(): {e}")

    # 6) Consolidación → resumen para UI/PDF
    resumen_pdf = _armar_resumen_pdf(
        entrada=entrada,
        dc=dc,
        ac=ac,
        ocpd=ocpd,
        spd=spd,
        seccionamiento=seccionamiento,
        conductores=conductores,
        canalizacion=canalizacion,
        warnings=warnings_out,
    )

    paquete = {
        "dc": dc,
        "ac": ac,
        "ocpd": ocpd,
        "spd": spd,
        "seccionamiento": seccionamiento,
        "conductores": conductores,
        "canalizacion": canalizacion,
        "warnings": warnings_out,
        "resumen_pdf": resumen_pdf,
    }
    return paquete


def _armar_resumen_pdf(
    *,
    entrada: Mapping[str, Any],
    dc: Mapping[str, Any],
    ac: Mapping[str, Any],
    ocpd: Optional[Mapping[str, Any]],
    spd: Optional[Mapping[str, Any]],
    seccionamiento: Optional[Mapping[str, Any]],
    conductores: Mapping[str, Any],
    canalizacion: Optional[Mapping[str, Any]],
    warnings: list[str],
) -> Dict[str, Any]:
    """
    Resumen estable para UI/PDF. Mantén esto conservador:
    - valores directos (corrientes/voltajes/potencias)
    - referencias a selecciones (breaker/fuse/calibre/conduit) si existen
    """
    def pick(m: Optional[Mapping[str, Any]], *keys: str) -> Any:
        if not isinstance(m, Mapping):
            return None
        for k in keys:
            if k in m and m[k] is not None:
                return m[k]
        return None

    # heurística de "mejor" tramo por tipo
    mejor_dc = None
    mejor_ac = None
    for it in (conductores.get("circuitos") or []):
        if not isinstance(it, Mapping):
            continue
        tipo = str(it.get("tipo") or it.get("circuito_tipo") or "").upper()
        if tipo == "DC" and mejor_dc is None:
            mejor_dc = it
        if tipo == "AC" and mejor_ac is None:
            mejor_ac = it

    resumen = {
        # DC
        "potencia_dc_w": dc.get("potencia_dc_w"),
        "vdc_nom": dc.get("vdc_nom"),
        "idc_nom": dc.get("idc_nom"),

        # AC
        "potencia_ac_w": ac.get("potencia_ac_w"),
        "vac_ll": ac.get("vac_ll"),
        "vac_ln": ac.get("vac_ln"),
        "fases": ac.get("fases"),
        "fp": ac.get("fp"),
        "iac_nom": ac.get("iac_nom"),

        # Selecciones (si existen)
        "ocpd_principal": pick(ocpd, "principal", "ocpd_principal", "breaker_principal"),
        "spd": pick(spd, "seleccion", "spd", "recomendacion"),
        "seccionamiento": pick(seccionamiento, "seleccion", "seccionamiento", "recomendacion"),

        "conductor_dc": pick(mejor_dc, "calibre", "awg", "kcmil", "conductor"),
        "conductor_ac": pick(mejor_ac, "calibre", "awg", "kcmil", "conductor"),

        "canalizacion": pick(canalizacion, "conduit", "seleccion", "canalizacion"),

        # Warnings
        "warnings": list(warnings or []),
    }
    return resumen


# ---------------------------------
# Criterios de aceptación (checks)
# ---------------------------------
CRITERIOS_ACEPTACION_SPRINT_1 = [
    # Import graph no rompe
    "Importa sin error: from electrical.paquete_nec import armar_paquete_nec",
    "No hay imports a tablas_conductores/cables_conductores aquí; solo tramo_conductor del motor conductores.",
    # Orquestación NEC mantiene llaves
    "armar_paquete_nec(entrada) retorna dict con llaves: dc, ac, ocpd, conductores, warnings, resumen_pdf.",
    "resumen_pdf contiene al menos: idc_nom, iac_nom y warnings.",
    # Adaptador/core compat
    "adaptador_nec.py + core/orquestador.py siguen pudiendo consumir el paquete NEC (mismas llaves principales).",
    # UI/PDF compat
    "UI/PDF siguen leyendo resumen_pdf y llaves principales (dc, ac, ocpd, conductores, warnings).",
]

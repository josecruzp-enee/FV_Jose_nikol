# electrical/paquete_nec.py
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple
import inspect

# ============================
# Imports de dominio (duros)
# ============================
from electrical.conductores.calculo_conductores import tramo_conductor
from electrical.protecciones.protecciones import dimensionar_protecciones_fv

# ============================
# Imports opcionales (tolerantes)
# ============================
try:
    from electrical.protecciones.spd import recomendar_spd  # type: ignore
except Exception:  # pragma: no cover
    recomendar_spd = None  # type: ignore

try:
    from electrical.protecciones.seccionamiento import recomendar_seccionamiento  # type: ignore
except Exception:  # pragma: no cover
    recomendar_seccionamiento = None  # type: ignore

try:
    # canalizacion_fv vive en electrical/canalizacion/canalizacion.py
    from electrical.canalizacion.canalizacion import canalizacion_fv  # type: ignore
except Exception:  # pragma: no cover
    canalizacion_fv = None  # type: ignore


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


def _sqrt3() -> float:
    return 1.7320508075688772


def _call_with_supported_kwargs(func: Callable[..., Any], **kwargs: Any) -> Any:
    """
    Llama una función filtrando kwargs a solo los parámetros soportados.
    Evita romper por cambios de firmas durante el refactor.
    """
    sig = None
    try:
        sig = inspect.signature(func)
    except Exception:
        sig = None

    if sig is None:
        return func(**kwargs)

    allowed = set(sig.parameters.keys())
    filtered = {k: v for k, v in kwargs.items() if k in allowed}
    return func(**filtered)


def _merge_warnings(base: Iterable[str], *more: Iterable[str]) -> list[str]:
    out: list[str] = []
    for w in (base or []):
        if w:
            out.append(str(w))
    for it in more:
        if not it:
            continue
        for w in it:
            if w and str(w) not in out:
                out.append(str(w))
    return out


def _ensure_list(x: Any) -> list:
    return x if isinstance(x, list) else []


# ---------------------------
# Cálculo de corrientes (solo magnitudes base)
# ---------------------------

def _corrientes_dc_ac(entrada: Mapping[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], list[str]]:
    """
    Calcula corrientes NOMINALES base para alimentar módulos de dominio.
    No dimensiona conductores ni protecciones.
    """
    warns: list[str] = []

    # Potencias
    pdc_w = _get_num(entrada, "potencia_dc_w", default=None)
    if pdc_w is None:
        pdc_kw = _get_num(entrada, "potencia_dc_kw", default=None)
        pdc_w = pdc_kw * 1000.0 if pdc_kw is not None else None

    pac_w = _get_num(entrada, "potencia_ac_w", default=None)
    if pac_w is None:
        pac_kw = _get_num(entrada, "potencia_ac_kw", default=None)
        pac_w = pac_kw * 1000.0 if pac_kw is not None else None

    # Voltajes
    vdc = _get_num(entrada, "vdc_nom", "vdc", default=None)
    vac_ll = _get_num(entrada, "vac_ll", "v_ll", default=None)
    vac_ln = _get_num(entrada, "vac_ln", "v_ln", default=None)

    # Parámetros AC
    fases = _get_int(entrada, "fases", default=None)
    if fases not in (1, 3, None):
        warns.append(f"Valor de 'fases' inválido ({fases}). Se ignora.")
        fases = None

    fp = _get_num(entrada, "fp", "factor_potencia", default=1.0)
    if fp is not None and (fp <= 0 or fp > 1.0):
        warns.append(f"FP fuera de rango ({fp}). Se fuerza a 1.0.")
        fp = 1.0

    eff = _get_num(entrada, "eficiencia_inversor", "eta_inversor", default=None)
    if eff is not None and (eff <= 0 or eff > 1.0):
        warns.append(f"Eficiencia inversor fuera de rango ({eff}). Se ignora.")
        eff = None

    # DC nominal
    idc_nom = _get_num(entrada, "idc_nom", "corriente_dc", default=None)
    if idc_nom is None and pdc_w is not None and vdc is not None and vdc > 0:
        idc_nom = pdc_w / vdc
    if idc_nom is None:
        warns.append("No se pudo inferir idc_nom (faltan potencia_dc y/o vdc_nom).")

    # AC nominal
    iac_nom = _get_num(entrada, "iac_nom", "corriente_ac", default=None)
    if iac_nom is None and pac_w is not None:
        # Si no dan fases, intenta inferir: vac_ll => 3φ, vac_ln => 1φ
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
            v1 = vac_ln or vac_ll
            if v1 and v1 > 0:
                if (fases or 1) == 3 and vac_ll:
                    iac_nom = pac_w / (_sqrt3() * vac_ll * (fp or 1.0))
                else:
                    iac_nom = pac_w / (v1 * (fp or 1.0))

    if iac_nom is None:
        warns.append("No se pudo inferir iac_nom (faltan potencia_ac y/o voltajes AC).")

    dc = {"potencia_dc_w": pdc_w, "vdc_nom": vdc, "idc_nom": idc_nom}
    ac = {
        "potencia_ac_w": pac_w,
        "vac_ll": vac_ll,
        "vac_ln": vac_ln,
        "fases": fases,
        "fp": fp,
        "iac_nom": iac_nom,
    }
    return dc, ac, warns


# ---------------------------
# Helpers resumen y selección
# ---------------------------

def _pick(m: Optional[Mapping[str, Any]], *keys: str) -> Any:
    if not isinstance(m, Mapping):
        return None
    for k in keys:
        if k in m and m[k] is not None:
            return m[k]
    return None


def _tipo_de_tramo(tramo: Mapping[str, Any]) -> str:
    return str(tramo.get("tipo") or tramo.get("circuito_tipo") or tramo.get("clase") or "").strip().upper()


def _mejor_tramo_por_tipo(circuitos: Iterable[Any], tipo: str) -> Optional[Mapping[str, Any]]:
    tipo = tipo.strip().upper()
    for it in circuitos or []:
        if isinstance(it, Mapping) and _tipo_de_tramo(it) == tipo:
            return it
    # fallback: inferencia por claves comunes
    for it in circuitos or []:
        if not isinstance(it, Mapping):
            continue
        if tipo == "DC" and any(k in it for k in ("vdc", "vdc_nom", "idc", "mppt")):
            return it
        if tipo == "AC" and any(k in it for k in ("vac", "vac_ll", "iac", "fases")):
            return it
    return None


# ---------------------------
# API pública (orquestación)
# ---------------------------

def armar_paquete_nec(entrada: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Ensambla el paquete NEC (dict) consumido por core/UI/PDF.

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
    if not isinstance(entrada, Mapping):
        raise TypeError("armar_paquete_nec: 'entrada' debe ser Mapping (dict-like).")

    warnings_out: list[str] = []

    # 1) Entradas → Validación (mínima y defensiva)
    dc, ac, w_corr = _corrientes_dc_ac(entrada)
    warnings_out = _merge_warnings(warnings_out, w_corr)

    # 2) Protecciones (OCPD / SPD / Seccionamiento)
    ocpd: Optional[Dict[str, Any]] = None
    spd: Optional[Dict[str, Any]] = None
    seccionamiento: Optional[Dict[str, Any]] = None

    # OCPD (duro)
    try:
        ocpd = _call_with_supported_kwargs(
            dimensionar_protecciones_fv,
            entrada=entrada,
            dc=dc,
            ac=ac,
            idc_nom=dc.get("idc_nom"),
            iac_nom=ac.get("iac_nom"),
        )
        if isinstance(ocpd, Mapping):
            warnings_out = _merge_warnings(warnings_out, _ensure_list(ocpd.get("warnings")))
    except Exception as e:
        warnings_out.append(f"OCPD no disponible o falló dimensionar_protecciones_fv(): {e}")

    # SPD (opcional)
    if callable(recomendar_spd):
        try:
            spd = _call_with_supported_kwargs(
                recomendar_spd,  # type: ignore[misc]
                entrada=entrada,
                dc=dc,
                ac=ac,
                ocpd=ocpd,
            )
            if isinstance(spd, Mapping):
                warnings_out = _merge_warnings(warnings_out, _ensure_list(spd.get("warnings")))
        except Exception as e:
            warnings_out.append(f"SPD no disponible o falló recomendar_spd(): {e}")
    else:
        warnings_out.append("SPD no configurado (módulo electrical.protecciones.spd no disponible).")

    # Seccionamiento (opcional)
    if callable(recomendar_seccionamiento):
        try:
            seccionamiento = _call_with_supported_kwargs(
                recomendar_seccionamiento,  # type: ignore[misc]
                entrada=entrada,
                dc=dc,
                ac=ac,
                ocpd=ocpd,
            )
            if isinstance(seccionamiento, Mapping):
                warnings_out = _merge_warnings(warnings_out, _ensure_list(seccionamiento.get("warnings")))
        except Exception as e:
            warnings_out.append(f"Seccionamiento no disponible o falló recomendar_seccionamiento(): {e}")
    else:
        warnings_out.append("Seccionamiento no configurado (módulo electrical.protecciones.seccionamiento no disponible).")

    # 3) Conductores (motor único)
    conductores: Dict[str, Any] = {"circuitos": [], "warnings": []}

    circuitos = entrada.get("circuitos", None)
    try:
        if isinstance(circuitos, list) and circuitos:
            for idx, c in enumerate(circuitos, start=1):
                if not isinstance(c, Mapping):
                    conductores["warnings"].append(f"Circuito #{idx} inválido (no dict). Se omite.")
                    continue

                tipo = str(c.get("tipo", "")).strip().upper()
                c_i = _get_num(c, "corriente", "i", "idc", "iac", default=None)

                # Enriquecer con corrientes base si el circuito no trae
                if c_i is None and tipo == "DC":
                    c_i = dc.get("idc_nom")
                if c_i is None and tipo == "AC":
                    c_i = ac.get("iac_nom")

                res = _call_with_supported_kwargs(
                    tramo_conductor,
                    entrada=entrada,
                    circuito=c,
                    tipo=tipo or None,
                    corriente=c_i,
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
            if isinstance(item, Mapping):
                conductores["warnings"] = _merge_warnings(conductores["warnings"], _ensure_list(item.get("warnings")))
    except Exception as e:
        conductores["warnings"] = _merge_warnings(
            conductores.get("warnings", []),
            [f"Falló cálculo de conductores (tramo_conductor): {e}"],
        )

    warnings_out = _merge_warnings(warnings_out, _ensure_list(conductores.get("warnings")))

    # 4) Canalización (opcional)
    canalizacion: Optional[Dict[str, Any]] = None
    if callable(canalizacion_fv):
        try:
            canalizacion = _call_with_supported_kwargs(
                canalizacion_fv,  # type: ignore[misc]
                entrada=entrada,
                dc=dc,
                ac=ac,
                ocpd=ocpd,
                conductores=conductores,
            )
            if isinstance(canalizacion, Mapping):
                warnings_out = _merge_warnings(warnings_out, _ensure_list(canalizacion.get("warnings")))
        except Exception as e:
            warnings_out.append(f"Canalización no disponible o falló canalizacion_fv(): {e}")
    else:
        warnings_out.append("Canalización no configurada (módulo electrical.canalizacion.canalizacion no disponible).")

    # 5) Consolidación → resumen para UI/PDF
    resumen_pdf = _armar_resumen_pdf(
        dc=dc,
        ac=ac,
        ocpd=ocpd,
        spd=spd,
        seccionamiento=seccionamiento,
        conductores=conductores,
        canalizacion=canalizacion,
        warnings=warnings_out,
    )

    return {
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


def _armar_resumen_pdf(
    *,
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
    Resumen estable para UI/PDF (conservador).
    """
    circuitos = conductores.get("circuitos") or []
    mejor_dc = _mejor_tramo_por_tipo(circuitos, "DC")
    mejor_ac = _mejor_tramo_por_tipo(circuitos, "AC")

    return {
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
        "ocpd_principal": _pick(ocpd, "principal", "ocpd_principal", "breaker_principal"),
        "spd": _pick(spd, "seleccion", "spd", "recomendacion"),
        "seccionamiento": _pick(seccionamiento, "seleccion", "seccionamiento", "recomendacion"),
        "conductor_dc": _pick(mejor_dc, "calibre", "awg", "kcmil", "conductor") if mejor_dc else None,
        "conductor_ac": _pick(mejor_ac, "calibre", "awg", "kcmil", "conductor") if mejor_ac else None,
        "canalizacion": _pick(canalizacion, "conduit", "seleccion", "canalizacion"),
        # Warnings
        "warnings": list(warnings or []),
    }


CRITERIOS_ACEPTACION_SPRINT_1 = [
    "Importa sin error: from electrical.paquete_nec import armar_paquete_nec",
    "No hay lógica REF ni imports a electrical.ref aquí.",
    "armar_paquete_nec(entrada) retorna dict con llaves: dc, ac, ocpd, conductores, warnings, resumen_pdf.",
    "resumen_pdf contiene al menos: idc_nom, iac_nom y warnings.",
]

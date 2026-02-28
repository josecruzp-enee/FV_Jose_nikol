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
# Imports backend REF (tolerantes)
# ============================
try:
    from electrical.catalogos.modelos import ParametrosCableado  # type: ignore
except Exception:  # pragma: no cover
    ParametrosCableado = None  # type: ignore

try:
    from electrical.conductores.calculo_conductores import (
        tramo_dc_ref,  # type: ignore
        tramo_ac_1f_ref,  # type: ignore
        tramo_ac_3f_ref,  # type: ignore
    )
except Exception:  # pragma: no cover
    tramo_dc_ref = None  # type: ignore
    tramo_ac_1f_ref = None  # type: ignore
    tramo_ac_3f_ref = None  # type: ignore

try:
    from electrical.canalizacion import conduit_ac_heuristico  # type: ignore
except Exception:  # pragma: no cover
    conduit_ac_heuristico = None  # type: ignore

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
# Backend REF (legacy) — interno
# ---------------------------

def _ref_cfg(cfg: Optional[Dict[str, Any]], k: str, d: float) -> float:
    try:
        return float((cfg or {}).get(k, d))
    except Exception:
        return float(d)


def _ref_tierra_awg(awg_fase: str) -> str:
    return "10" if awg_fase in ["6", "4", "3", "2", "1", "1/0", "2/0", "3/0", "4/0"] else "12"


def _ref_calc_tramos(
    *,
    p: Any,
    vmp: float,
    imp: float,
    isc: Optional[float],
    iac: float,
    fases_ac: int,
    cfg: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if tramo_dc_ref is None or tramo_ac_1f_ref is None or tramo_ac_3f_ref is None:
        raise RuntimeError("Backend REF no disponible: faltan tramo_dc_ref/tramo_ac_*_ref.")

    fdc = _ref_cfg(cfg, "factor_seguridad_dc", 1.25)
    fac = _ref_cfg(cfg, "factor_seguridad_ac", 1.25)
    vdd = _ref_cfg(cfg, "vdrop_obj_dc_pct", float(getattr(p, "vdrop_obj_dc_pct", 2.0)))
    vda = _ref_cfg(cfg, "vdrop_obj_ac_pct", float(getattr(p, "vdrop_obj_ac_pct", 2.0)))

    dc = tramo_dc_ref(
        vmp_v=vmp,
        imp_a=imp,
        isc_a=isc,
        dist_m=float(getattr(p, "dist_dc_m", 0.0)),
        factor_seguridad=fdc,
        vd_obj_pct=vdd,
    )

    fn_ac = tramo_ac_3f_ref if int(fases_ac) == 3 else tramo_ac_1f_ref
    ac = fn_ac(
        vac_v=float(getattr(p, "vac", 0.0)),
        iac_a=iac,
        dist_m=float(getattr(p, "dist_ac_m", 0.0)),
        factor_seguridad=fac,
        vd_obj_pct=vda,
    )

    ac["tierra_awg"] = _ref_tierra_awg(str(ac.get("awg", "")))
    return {"dc": dc, "ac": ac}


def _ref_calc_protecciones(*, ac: Dict[str, Any], n_strings: int, isc_mod_a: float, has_combiner: bool) -> Dict[str, Any]:
    # OJO: tu dimensionar_protecciones_fv soporta firmas distintas (a veces iac_nom_a directo).
    # Aquí usamos _call_with_supported_kwargs para tolerancia.
    return _call_with_supported_kwargs(
        dimensionar_protecciones_fv,
        iac_nom_a=float(ac.get("i_nom_a", 0.0)),
        n_strings=int(n_strings),
        isc_mod_a=float(isc_mod_a),
        has_combiner=bool(has_combiner),
    )


def _ref_calc_canalizacion(*, p: Any, ac: Dict[str, Any], fases_ac: int) -> Dict[str, Any]:
    conduit = "N/A"
    if callable(conduit_ac_heuristico):
        try:
            conduit = str(
                conduit_ac_heuristico(
                    awg_ac=str(ac.get("awg", "")),
                    incluye_neutro=bool(getattr(p, "incluye_neutro_ac", False)),
                    extra_ccc=int(getattr(p, "otros_ccc", 0)),
                )
            )
        except Exception:
            conduit = "N/A"

    # Canalización “nuevo” si existe canalizacion_fv (tu import tolerante)
    can: Any = None
    if callable(canalizacion_fv):
        try:
            can = _call_with_supported_kwargs(
                canalizacion_fv,  # type: ignore[misc]
                tiene_trunk=False,
                fases_ac=int(fases_ac),
                incluye_neutro=bool(getattr(p, "incluye_neutro_ac", False)),
            )
        except Exception:
            can = None

    return {"conduit_ac": conduit, "canalizacion": can}


def _ref_disclaimer() -> str:
    return (
        "Cálculo referencial. Calibre final sujeto a: temperatura, agrupamiento (CCC), "
        "factores de ajuste/corrección, fill real de tubería, terminales 75°C y normativa aplicable."
    )


def _armar_paquete_ref(entrada: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Backend legacy: arma paquete con MISMAS llaves que NEC.
    Entrada esperada:
      - params o params_cableado: ParametrosCableado o dict compatible
      - vmp_string_v, imp_a, isc_a, iac_estimado_a
      - fases_ac (1/3)
      - cfg_tecnicos (opcional)
      - n_strings, isc_mod_a, has_combiner (opcional)
    """
    warnings_out: list[str] = []

    params = entrada.get("params") or entrada.get("params_cableado")
    if params is None:
        raise ValueError("modo='ref': falta 'params' o 'params_cableado'.")

    if isinstance(params, dict):
        if ParametrosCableado is None:
            raise RuntimeError("modo='ref': ParametrosCableado no disponible (import falló).")
        params = ParametrosCableado(**params)  # type: ignore[misc]

    cfg = entrada.get("cfg_tecnicos") or entrada.get("cfg") or None
    fases_ac = int(entrada.get("fases_ac", 1))

    vmp = float(entrada.get("vmp_string_v", 0.0))
    imp = float(entrada.get("imp_a", 0.0))
    isc = entrada.get("isc_a", None)
    isc = float(isc) if isc is not None else None
    iac = float(entrada.get("iac_estimado_a", 0.0))

    tr = _ref_calc_tramos(p=params, vmp=vmp, imp=imp, isc=isc, iac=iac, fases_ac=fases_ac, cfg=cfg)

    ocpd = _ref_calc_protecciones(
        ac=tr["ac"],
        n_strings=int(entrada.get("n_strings", 0)),
        isc_mod_a=float(entrada.get("isc_mod_a", 0.0)),
        has_combiner=bool(entrada.get("has_combiner", False)),
    )

    can = _ref_calc_canalizacion(p=params, ac=tr["ac"], fases_ac=fases_ac)

    # En ref, construimos un "conductores" compatible con tu resumen NEC (usa circuitos con tipo DC/AC)
    conductores: Dict[str, Any] = {
        "circuitos": [
            {**(tr["dc"] if isinstance(tr["dc"], dict) else {}), "tipo": "DC"},
            {**(tr["ac"] if isinstance(tr["ac"], dict) else {}), "tipo": "AC", "conduit": can.get("conduit_ac")},
        ],
        "warnings": [],
    }

    # Canalización: si canalizacion_fv devolvió dict, le agregamos conduit legacy para UI/PDF
    canalizacion_out: Optional[Dict[str, Any]] = None
    if isinstance(can.get("canalizacion"), Mapping):
        canalizacion_out = {**can["canalizacion"], "conduit": can.get("conduit_ac")}
    else:
        canalizacion_out = {"conduit": can.get("conduit_ac")}

    # DC/AC base para resumen_pdf
    dc_base = {
        "potencia_dc_w": None,
        "vdc_nom": None,
        "idc_nom": tr["dc"].get("i_nom_a") if isinstance(tr["dc"], Mapping) else None,
    }
    if dc_base["idc_nom"] is None and isinstance(tr["dc"], Mapping):
        dc_base["idc_nom"] = tr["dc"].get("i_a")

    ac_base = {
        "potencia_ac_w": None,
        "vac_ll": getattr(params, "vac", None),
        "vac_ln": getattr(params, "vac", None),
        "fases": fases_ac,
        "fp": 1.0,
        "iac_nom": tr["ac"].get("i_nom_a") if isinstance(tr["ac"], Mapping) else None,
    }
    if ac_base["iac_nom"] is None and isinstance(tr["ac"], Mapping):
        ac_base["iac_nom"] = tr["ac"].get("i_a")

    # Armar resumen_pdf con la misma función NEC, y adjuntar info legacy adicional (no rompe consumidores)
    resumen_pdf = _armar_resumen_pdf(
        dc=dc_base,
        ac=ac_base,
        ocpd=ocpd if isinstance(ocpd, Mapping) else None,
        spd=None,
        seccionamiento=None,
        conductores=conductores,
        canalizacion=canalizacion_out,
        warnings=warnings_out,
    )

    # Extras legacy (opcionales)
    resumen_pdf["_ref_lineas"] = [
        f"Conductores DC (string): {tr['dc'].get('awg') if isinstance(tr['dc'], Mapping) else None} AWG Cu PV Wire/USE-2. Dist {float(getattr(params, 'dist_dc_m', 0.0)):.1f} m.",
        f"Conductores AC: {tr['ac'].get('awg') if isinstance(tr['ac'], Mapping) else None} AWG Cu THHN/THWN-2. Dist {float(getattr(params, 'dist_ac_m', 0.0)):.1f} m. Conduit: {can.get('conduit_ac')}.",
    ]
    resumen_pdf["_ref_disclaimer"] = _ref_disclaimer()

    return {
        "meta": {"modo": "ref"},
        "dc": dc_base,
        "ac": ac_base,
        "ocpd": ocpd if isinstance(ocpd, dict) else None,
        "spd": None,
        "seccionamiento": None,
        "conductores": conductores,
        "canalizacion": canalizacion_out,
        "warnings": warnings_out,
        "resumen_pdf": resumen_pdf,
    }


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
    # fallback: si no hay 'tipo' bien puesto, intenta inferencia por claves comunes
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
    Ensambla el paquete NEC (dict) consumido por adaptador_nec/core/UI/PDF.

    Salida:
      {
        "meta": {"modo": "nec"|"ref"},
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

    # Router por modo (UN SOLO punto de salida)
    modo = str(entrada.get("modo", "nec")).strip().lower()
    if modo == "ref":
        return _armar_paquete_ref(entrada)

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
        warnings_out.append("Canalización no configurada (módulo electrical.canalizacion.conduit no disponible).")

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
        "meta": {"modo": "nec"},
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


# ---------------------------------
# Criterios de aceptación (checks)
# ---------------------------------
CRITERIOS_ACEPTACION_SPRINT_1 = [
    "Importa sin error: from electrical.paquete_nec import armar_paquete_nec",
    "No hay imports a tablas_conductores/cables_conductores aquí; solo tramo_conductor del motor conductores.",
    "armar_paquete_nec(entrada) retorna dict con llaves: meta, dc, ac, ocpd, conductores, warnings, resumen_pdf.",
    "resumen_pdf contiene al menos: idc_nom, iac_nom y warnings.",
    "adaptador_nec.py + core/orquestador.py siguen pudiendo consumir el paquete NEC (mismas llaves principales).",
    "UI/PDF siguen leyendo resumen_pdf y llaves principales (dc, ac, ocpd, conductores, warnings).",
]

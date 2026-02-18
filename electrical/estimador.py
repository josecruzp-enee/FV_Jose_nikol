from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .catalogos import get_panel, get_inversor
from .strings import calcular_strings_dc
from .cableado import calcular_cableado_referencial
from .modelos import ParametrosCableado


# ==========================================================
# Helpers de configuración
# ==========================================================

def _cfg_get(cfg_tecnicos: Optional[Dict[str, Any]], key: str, default: float) -> float:
    if not cfg_tecnicos:
        return float(default)
    try:
        return float(cfg_tecnicos.get(key, default))
    except Exception:
        return float(default)


# ==========================================================
# Validación / Catálogos
# ==========================================================

def _validar_entradas(*, res: Dict[str, Any], panel_nombre: str, inv_nombre: str) -> None:
    if "sizing" not in res or "n_paneles" not in res["sizing"]:
        raise KeyError("res debe incluir res['sizing']['n_paneles'].")
    if not panel_nombre:
        raise KeyError("panel_nombre vacío.")
    if not inv_nombre:
        raise KeyError("inv_nombre vacío.")


def _cargar_catalogos(panel_nombre: str, inv_nombre: str):
    panel = get_panel(panel_nombre)
    inv = get_inversor(inv_nombre)
    return panel, inv


def _n_paneles_desde_res(res: Dict[str, Any]) -> int:
    return int(res["sizing"]["n_paneles"])


# ==========================================================
# Strings
# ==========================================================

def _t_min_c_efectiva(cfg_tecnicos: Optional[Dict[str, Any]], params: ParametrosCableado) -> float:
    return _cfg_get(cfg_tecnicos, "t_min_c", float(getattr(params, "t_min_c", 10.0)))


def _calcular_strings(
    *,
    n_paneles: int,
    panel,
    inv,
    dos_aguas: bool,
    t_min_c: float,
) -> Dict[str, Any]:
    cfg = calcular_strings_dc(
        n_paneles=n_paneles,
        panel=panel,
        inversor=inv,
        dos_aguas=bool(dos_aguas),
        t_min_c=float(t_min_c),
    )
    if not cfg.get("strings"):
        raise ValueError("cfg_strings no contiene strings calculados.")
    return cfg


def _primer_string(cfg_strings: Dict[str, Any]) -> Dict[str, Any]:
    return cfg_strings["strings"][0]


# ==========================================================
# Cableado
# ==========================================================

def calcular_iac_estimado(inv_kw_ac: float, *, vac: float, fases: int = 1, fp: float = 1.0) -> float:
    p_w = float(inv_kw_ac) * 1000.0
    if int(fases) == 3:
        return p_w / (3 ** 0.5 * float(vac) * float(fp))
    return p_w / (float(vac) * float(fp))


def _vdrop_objetivos(
    cfg_tecnicos: Optional[Dict[str, Any]],
    params: ParametrosCableado,
) -> Tuple[float, float]:
    vdc = _cfg_get(cfg_tecnicos, "vdrop_obj_dc_pct", float(getattr(params, "vdrop_obj_dc_pct", 2.0)))
    vac = _cfg_get(cfg_tecnicos, "vdrop_obj_ac_pct", float(getattr(params, "vdrop_obj_ac_pct", 2.0)))
    return float(vdc), float(vac)


def _construir_params_compat(
    *,
    params: ParametrosCableado,
    vdrop_obj_dc_pct: float,
    vdrop_obj_ac_pct: float,
    t_min_c: float,
) -> ParametrosCableado:
    """
    Compat temporal: mientras ParametrosCableado tenga vdrop_obj_* y t_min_c,
    inyectamos aquí los valores efectivos para que cableado.py funcione.
    (Luego eliminaremos estos campos del dataclass.)
    """
    return ParametrosCableado(
        vac=float(params.vac),
        fases=int(params.fases),
        fp=float(params.fp),
        dist_dc_m=float(params.dist_dc_m),
        dist_ac_m=float(params.dist_ac_m),
        vdrop_obj_dc_pct=float(vdrop_obj_dc_pct),
        vdrop_obj_ac_pct=float(vdrop_obj_ac_pct),
        incluye_neutro_ac=bool(params.incluye_neutro_ac),
        otros_ccc=int(params.otros_ccc),
        t_min_c=float(t_min_c),
    )


def _calcular_cableado(
    *,
    inv,
    params: ParametrosCableado,
    params_eff: ParametrosCableado,
    s0: Dict[str, Any],
    cfg_tecnicos: Optional[Dict[str, Any]],
) -> Tuple[Dict[str, Any], float]:
    iac = calcular_iac_estimado(inv.kw_ac, vac=params.vac, fases=params.fases, fp=params.fp)

    elect = calcular_cableado_referencial(
        params=params_eff,
        vmp_string_v=float(s0["vmp_V"]),
        imp_a=float(s0["imp_A"]),
        isc_a=float(s0.get("isc_A")) if s0.get("isc_A") is not None else None,
        iac_estimado_a=float(iac),
        cfg_tecnicos=cfg_tecnicos,  # ✅ ya lo soporta cableado.py refactor
    )
    return elect, float(iac)


# ==========================================================
# Salida / Formateo
# ==========================================================

def _formatear_lineas_strings(cfg_strings: Dict[str, Any]) -> list[str]:
    out: list[str] = []
    for s in (cfg_strings.get("strings") or []):
        out.append(
            f"{s['etiqueta']} — {s['ns']}S: "
            f"Vmp≈{s['vmp_V']:.0f} V | Voc frío≈{s['voc_frio_V']:.0f} V | Imp≈{s['imp_A']:.1f} A."
        )
    return out


def _armar_salida(
    *,
    panel_nombre: str,
    inv_nombre: str,
    cfg_strings: Dict[str, Any],
    electrico_ref: Dict[str, Any],
    iac_estimado_a: float,
    t_min_c: float,
    vdrop_obj_dc_pct: float,
    vdrop_obj_ac_pct: float,
) -> Dict[str, Any]:
    return {
        "cfg_strings": cfg_strings,
        "electrico_ref": electrico_ref,
        "texto_ui": {
            "strings": _formatear_lineas_strings(cfg_strings),
            "cableado": list(electrico_ref.get("texto_pdf") or []),
            "disclaimer": electrico_ref.get("disclaimer", ""),
            "checks": cfg_strings.get("checks") or [],
        },
        "meta": {
            "panel": panel_nombre,
            "inversor": inv_nombre,
            "iac_estimado_a": float(iac_estimado_a),
            "t_min_c": float(t_min_c),
            "vdrop_obj_dc_pct": float(vdrop_obj_dc_pct),
            "vdrop_obj_ac_pct": float(vdrop_obj_ac_pct),
        },
    }


# ==========================================================
# API pública (orquestadores)
# ==========================================================

def calcular_paquete_electrico_desde_inputs(
    *,
    res: Dict[str, Any],
    panel_nombre: str,
    inv_nombre: str,
    dos_aguas: bool,
    params: ParametrosCableado,
    cfg_tecnicos: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Orquestador corto.
    """
    _validar_entradas(res=res, panel_nombre=panel_nombre, inv_nombre=inv_nombre)

    panel, inv = _cargar_catalogos(panel_nombre, inv_nombre)
    n_paneles = _n_paneles_desde_res(res)

    t_min_c = _t_min_c_efectiva(cfg_tecnicos, params)
    cfg_strings = _calcular_strings(n_paneles=n_paneles, panel=panel, inv=inv, dos_aguas=dos_aguas, t_min_c=t_min_c)
    s0 = _primer_string(cfg_strings)

    vdrop_obj_dc, vdrop_obj_ac = _vdrop_objetivos(cfg_tecnicos, params)
    params_eff = _construir_params_compat(
        params=params,
        vdrop_obj_dc_pct=vdrop_obj_dc,
        vdrop_obj_ac_pct=vdrop_obj_ac,
        t_min_c=t_min_c,
    )

    electrico_ref, iac = _calcular_cableado(
        inv=inv,
        params=params,
        params_eff=params_eff,
        s0=s0,
        cfg_tecnicos=cfg_tecnicos,
    )

    return _armar_salida(
        panel_nombre=panel_nombre,
        inv_nombre=inv_nombre,
        cfg_strings=cfg_strings,
        electrico_ref=electrico_ref,
        iac_estimado_a=iac,
        t_min_c=t_min_c,
        vdrop_obj_dc_pct=vdrop_obj_dc,
        vdrop_obj_ac_pct=vdrop_obj_ac,
    )


def calcular_paquete_electrico(
    *,
    res: Dict[str, Any],
    state: Dict[str, Any],
    cfg_tecnicos: Optional[Dict[str, Any]] = None,
    panel_sel_key: str = "panel_sel",
    inv_sel_key: str = "inv_sel",
    dos_aguas_key: str = "dos_aguas",
) -> Dict[str, Any]:
    """
    Wrapper legacy: extrae selección desde state y llama API pura.
    """
    panel_nombre = state.get(panel_sel_key)
    inv_nombre = state.get(inv_sel_key)

    if not panel_nombre:
        raise KeyError("panel_nombre vacío.")
    if not inv_nombre:
        raise KeyError("inv_nombre vacío.")

    params = construir_parametros_cableado_desde_state(state)
    dos_aguas = bool(state.get(dos_aguas_key, True))

    return calcular_paquete_electrico_desde_inputs(
        res=res,
        panel_nombre=str(panel_nombre),
        inv_nombre=str(inv_nombre),
        dos_aguas=dos_aguas,
        params=params,
        cfg_tecnicos=cfg_tecnicos,
    )

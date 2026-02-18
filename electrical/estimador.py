# electrical/estimador.py
from __future__ import annotations

from typing import Any, Dict, Optional

from .catalogos import get_panel, get_inversor
from .strings import calcular_strings_dc
from .cableado import calcular_cableado_referencial
from .modelos import ParametrosCableado


# ==========================================================
# Helpers de configuración (no streamlit, no archivos)
# ==========================================================

def _cfg_get(cfg_tecnicos: Optional[Dict[str, Any]], key: str, default: float) -> float:
    """
    Lee una clave numérica desde cfg_tecnicos. Si no existe, usa default.
    """
    if not cfg_tecnicos:
        return float(default)
    try:
        return float(cfg_tecnicos.get(key, default))
    except Exception:
        return float(default)


# ==========================================================
# API legacy (state -> ParametrosCableado)
# ==========================================================

def construir_parametros_cableado_desde_state(state: Dict[str, Any]) -> ParametrosCableado:
    """
    Construye ParametrosCableado desde un state (ej: st.session_state).
    API legacy (compatible con UI vieja).
    """
    return ParametrosCableado(
        vac=float(state.get("vac", 240.0)),
        fases=int(state.get("fases", 1)),
        fp=float(state.get("fp", 1.0)),

        dist_dc_m=float(state.get("dist_dc_m", 15.0)),
        dist_ac_m=float(state.get("dist_ac_m", 25.0)),

        vdrop_obj_dc_pct=float(state.get("vdrop_obj_dc_pct", 2.0)),
        vdrop_obj_ac_pct=float(state.get("vdrop_obj_ac_pct", 2.0)),

        incluye_neutro_ac=bool(state.get("incluye_neutro_ac", False)),
        otros_ccc=int(state.get("otros_ccc", 0)),

        t_min_c=float(state.get("t_min_c", 10.0)),
    )


def calcular_iac_estimado(inv_kw_ac: float, *, vac: float, fases: int = 1, fp: float = 1.0) -> float:
    """
    Corriente AC estimada desde potencia AC del inversor (kW).
    """
    p_w = float(inv_kw_ac) * 1000.0
    if int(fases) == 3:
        return p_w / (3 ** 0.5 * float(vac) * float(fp))
    return p_w / (float(vac) * float(fp))


# ==========================================================
# API pura (recomendada)
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
    API pura (sin Streamlit): orquesta strings + cableado.

    Entradas:
      - res: dict del motor FV (debe traer res["sizing"]["n_paneles"])
      - panel_nombre, inv_nombre: keys del catálogo electrical/catalogos.py
      - dos_aguas: bool para reparto de strings (si aplica)
      - params: ParametrosCableado explícitos (instalación + compat legacy)
      - cfg_tecnicos: dict de criterios de diseño (YAML base + overrides UI)

    Salida:
      dict con:
        - cfg_strings
        - electrico_ref
        - texto_ui: dict de listas de líneas (para UI / PDF)
        - meta
    """
    _validar_entradas(res=res, panel_nombre=panel_nombre, inv_nombre=inv_nombre)

    panel = get_panel(panel_nombre)
    inv = get_inversor(inv_nombre)
    n_paneles = int(res["sizing"]["n_paneles"])

    # 1) Strings DC (t_min_c viene desde cfg_tecnicos)
    t_min_c = _cfg_get(cfg_tecnicos, "t_min_c", float(getattr(params, "t_min_c", 10.0)))

    cfg = calcular_strings_dc(
        n_paneles=n_paneles,
        panel=panel,
        inversor=inv,
        dos_aguas=bool(dos_aguas),
        t_min_c=float(t_min_c),
    )

    if not cfg.get("strings"):
        raise ValueError("cfg_strings no contiene strings calculados.")

    # 2) Cableado referencial (usa el primer string)
    s0 = cfg["strings"][0]
    iac = calcular_iac_estimado(inv.kw_ac, vac=params.vac, fases=params.fases, fp=params.fp)

    # objetivos vdrop desde cfg_tecnicos (si existen); si no, usa params legacy
    vdrop_obj_dc = _cfg_get(cfg_tecnicos, "vdrop_obj_dc_pct", float(getattr(params, "vdrop_obj_dc_pct", 2.0)))
    vdrop_obj_ac = _cfg_get(cfg_tecnicos, "vdrop_obj_ac_pct", float(getattr(params, "vdrop_obj_ac_pct", 2.0)))

    # Compat: si tu cableado.py hoy toma objetivos desde params, los inyectamos aquí.
    params_eff = _construir_params_compat(
        params=params,
        vdrop_obj_dc_pct=vdrop_obj_dc,
        vdrop_obj_ac_pct=vdrop_obj_ac,
        t_min_c=t_min_c,
    )

    elect = calcular_cableado_referencial(
        params=params_eff,
        vmp_string_v=float(s0["vmp_V"]),
        imp_a=float(s0["imp_A"]),
        isc_a=float(s0.get("isc_A")) if s0.get("isc_A") is not None else None,
        iac_estimado_a=float(iac),
    )

    # 3) Texto listo para UI/PDF
    lineas_strings = _formatear_lineas_strings(cfg)
    lineas_cableado = list(elect.get("texto_pdf") or [])

    return {
        "cfg_strings": cfg,
        "electrico_ref": elect,
        "texto_ui": {
            "strings": lineas_strings,
            "cableado": lineas_cableado,
            "disclaimer": elect.get("disclaimer", ""),
            "checks": cfg.get("checks") or [],
        },
        "meta": {
            "panel": panel_nombre,
            "inversor": inv_nombre,
            "iac_estimado_a": float(iac),
            "t_min_c": float(t_min_c),
            "vdrop_obj_dc_pct": float(vdrop_obj_dc),
            "vdrop_obj_ac_pct": float(vdrop_obj_ac),
        },
    }


# ==========================================================
# API legacy (wrapper)
# ==========================================================

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
    API legacy (compatible con UI vieja basada en state).
    Wrapper sobre calcular_paquete_electrico_desde_inputs().

    Nota:
      - cfg_tecnicos es opcional; si no se pasa, usa valores de state/params.
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


# ==========================================================
# Internals (funciones pequeñas)
# ==========================================================

def _validar_entradas(*, res: Dict[str, Any], panel_nombre: str, inv_nombre: str) -> None:
    if "sizing" not in res or "n_paneles" not in res["sizing"]:
        raise KeyError("res debe incluir res['sizing']['n_paneles'].")
    if not panel_nombre:
        raise KeyError("panel_nombre vacío.")
    if not inv_nombre:
        raise KeyError("inv_nombre vacío.")


def _formatear_lineas_strings(cfg: Dict[str, Any]) -> list[str]:
    strings = cfg.get("strings") or []
    out: list[str] = []
    for s in strings:
        out.append(
            f"{s['etiqueta']} — {s['ns']}S: "
            f"Vmp≈{s['vmp_V']:.0f} V | Voc frío≈{s['voc_frio_V']:.0f} V | Imp≈{s['imp_A']:.1f} A."
        )
    return out


def _construir_params_compat(
    *,
    params: ParametrosCableado,
    vdrop_obj_dc_pct: float,
    vdrop_obj_ac_pct: float,
    t_min_c: float,
) -> ParametrosCableado:
    """
    Mientras ParametrosCableado siga teniendo vdrop_obj_* y t_min_c,
    construimos un params efectivo para que cableado.py siga funcionando.
    En el siguiente paso vamos a remover esos campos del dataclass.
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

# electrical/orquestador.py
from __future__ import annotations

from typing import Any, Dict, Optional

from electrical.catalogos import PANELES, INVERSORES
from electrical.strings import calcular_strings_dc
from electrical.cableado import calcular_cableado_referencial
from electrical.modelos import ParametrosCableado


def construir_parametros_cableado_desde_state(state: Dict[str, Any]) -> ParametrosCableado:
    """
    Construye ParametrosCableado desde un state (ej: st.session_state).
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


def calcular_paquete_electrico(
    *,
    res: Dict[str, Any],
    state: Dict[str, Any],
    panel_sel_key: str = "panel_sel",
    inv_sel_key: str = "inv_sel",
    dos_aguas_key: str = "dos_aguas",
) -> Dict[str, Any]:
    """
    Orquesta TODO lo eléctrico (DC strings + cableado AC/DC) y actualiza 'res'.

    Entradas:
      - res: dict del motor FV (debe traer res["sizing"]["n_paneles"])
      - state: selections (ej st.session_state)

    Salida:
      dict con:
        - cfg_strings
        - electrico_ref
        - texto_ui: dict de listas de líneas (para streamlit)
    """
    if "sizing" not in res or "n_paneles" not in res["sizing"]:
        raise KeyError("res debe incluir res['sizing']['n_paneles'].")

    panel_nombre = state.get(panel_sel_key)
    inv_nombre = state.get(inv_sel_key)
    if not panel_nombre or panel_nombre not in PANELES:
        raise KeyError(f"state['{panel_sel_key}'] inválido o no existe.")
    if not inv_nombre or inv_nombre not in INVERSORES:
        raise KeyError(f"state['{inv_sel_key}'] inválido o no existe.")

    panel = PANELES[panel_nombre]
    inv = INVERSORES[inv_nombre]

    n_paneles = int(res["sizing"]["n_paneles"])
    dos_aguas = bool(state.get(dos_aguas_key, True))

    # 1) Strings DC
    cfg = calcular_strings_dc(
        n_paneles=n_paneles,
        panel=panel,
        inversor=inv,
        dos_aguas=dos_aguas,
        t_min_c=float(state.get("t_min_c", 10.0)),
    )
    res["cfg_strings"] = cfg

    if not cfg.get("strings"):
        raise ValueError("cfg_strings no contiene strings calculados.")

    # 2) Cableado referencial (usa el primer string)
    s0 = cfg["strings"][0]
    params = construir_parametros_cableado_desde_state(state)

    iac = calcular_iac_estimado(inv.kw_ac, vac=params.vac, fases=params.fases, fp=params.fp)

    elect = calcular_cableado_referencial(
        params=params,
        vmp_string_v=float(s0["vmp_V"]),
        imp_a=float(s0["imp_A"]),
        isc_a=float(s0.get("isc_A")) if s0.get("isc_A") is not None else None,
        iac_estimado_a=float(iac),
    )
    res["electrico_ref"] = elect

    # 3) Texto listo para UI (sin depender de streamlit)
    lineas_strings = [
        f"{s['etiqueta']} — {s['ns']}S: Vmp≈{s['vmp_V']:.0f} V | Voc frío≈{s['voc_frio_V']:.0f} V | Imp≈{s['imp_A']:.1f} A."
        for s in cfg.get("strings", [])
    ]
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
        }
    }

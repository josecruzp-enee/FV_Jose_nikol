# ui/ingenieria_electrica.py
from __future__ import annotations

from typing import List, Tuple, Dict, Any
import streamlit as st
import pandas as pd

from electrical.validador_strings import PanelFV, InversorFV, validar_string
from core.orquestador import ejecutar_estudio
from core.modelo import Datosproyecto
from electrical.catalogos import get_panel, get_inversor
from ui.validaciones_ui import campos_faltantes_para_paso5
from ui.state_helpers import ensure_dict, merge_defaults, save_result_fingerprint


# ==========================================================
# Helpers UI
# ==========================================================
def _yn(ok: bool) -> str:
    return "✅ OK" if ok else "❌ NO CUMPLE"


def _fmt(v, unit: str = "") -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        s = f"{v:.3f}".rstrip("0").rstrip(".")
        return f"{s} {unit}".rstrip() if unit else s
    return str(v)


def _asegurar_dict(ctx, nombre: str) -> dict:
    return ensure_dict(ctx, nombre, dict)


# ==========================================================
# Equipos / defaults
# ==========================================================
def _get_equipos(ctx) -> dict:
    eq = _asegurar_dict(ctx, "equipos")
    eq.setdefault("panel_id", None)
    eq.setdefault("inversor_id", None)
    eq.setdefault("sobredimension_dc_ac", 1.20)
    eq.setdefault("tension_sistema", "2F+N_120/240")
    return eq


def _defaults_electrico(ctx) -> dict:
    e = _asegurar_dict(ctx, "electrico")

    merge_defaults(
        e,
        {
            "vac": 240.0,
            "fases": 1,
            "fp": 1.0,
            "dist_dc_m": 15.0,
            "dist_ac_m": 25.0,
            "vdrop_obj_dc_pct": 2.0,
            "vdrop_obj_ac_pct": 2.0,
            "t_min_c": 10.0,
            "incluye_neutro_ac": False,
            "otros_ccc": 0,
            "dos_aguas": True,
        },
    )
    return e


# ==========================================================
# ctx → Datosproyecto
# ==========================================================
def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _get_equipos(ctx)

    consumo_12m = c.get("kwh_12m", [0.0] * 12)

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),
        consumo_12m=[float(x) for x in consumo_12m],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0)),
        prod_base_kwh_kwp_mes=float(sf.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf.get("factores_fv_12m", [1] * 12)],
        cobertura_objetivo=float(sf.get("cobertura_objetivo", 0.8)),
        costo_usd_kwp=float(sf.get("costo_usd_kwp", 1200)),
        tcambio=float(sf.get("tcambio", 27)),
        tasa_anual=float(sf.get("tasa_anual", 0.08)),
        plazo_anios=int(sf.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf.get("porcentaje_financiado", 1)),
        om_anual_pct=float(sf.get("om_anual_pct", 0.01)),
    )

    setattr(p, "equipos", dict(eq))
    setattr(p, "sistema_fv", dict(sf))
    setattr(p, "electrico", dict(_asegurar_dict(ctx, "electrico")))

    return p


# ==========================================================
# CORE — EJECUCIÓN CENTRAL
# ==========================================================
def _ejecutar_core(ctx) -> Dict[str, Any]:

    datos = _datosproyecto_desde_ctx(ctx)
    ctx.datos_proyecto = datos

    # ✅ ÚNICA FUENTE DE VERDAD DEL SISTEMA
    resultado_proyecto = ejecutar_estudio(datos)

    ctx.resultado_proyecto = resultado_proyecto

    # ---- compatibilidad legacy ----
    ctx.resultado_core = resultado_proyecto.get("_compat", {}) or {}

    electrico_nec = (
        (resultado_proyecto.get("tecnico") or {})
        .get("electrico_nec") or {}
    )

    ctx.resultado_electrico = electrico_nec.get("paq")

    return resultado_proyecto


# ==========================================================
# Validación string catálogo
# ==========================================================
def _validar_string_catalogo(eq, e, n_paneles):

    p = get_panel(eq["panel_id"])
    inv = get_inversor(eq["inversor_id"])

    panel = PanelFV(p.voc, p.vmp, p.isc, p.imp, getattr(p, "coef_voc", -0.28))

    imppt_max = getattr(inv, "imppt_max", None) or 1e9

    inversor = InversorFV(
        inv.vdc_max,
        inv.vmppt_min,
        inv.vmppt_max,
        imppt_max,
        inv.n_mppt,
    )

    return validar_string(panel, inversor, n_paneles, temp_min=float(e["t_min_c"])) or {}


# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    e = _defaults_electrico(ctx)
    eq = _get_equipos(ctx)

    if not (eq.get("panel_id") and eq.get("inversor_id")):
        st.error("Complete Paso 4.")
        return

    st.markdown("### Ingeniería eléctrica automática")

    faltantes = campos_faltantes_para_paso5(ctx)
    if faltantes:
        st.warning(
            "Complete estos datos antes de generar ingeniería:\n- "
            + "\n- ".join(faltantes)
        )

    st.divider()

    if not st.button(
        "Generar ingeniería eléctrica",
        type="primary",
        disabled=bool(faltantes),
    ):
        return

    try:
        res = _ejecutar_core(ctx)

        tecnico = res.get("tecnico") or {}
        sizing = tecnico.get("sizing") or {}

        n_paneles = int(sizing.get("n_paneles") or 10)

        validacion = _validar_string_catalogo(eq, e, n_paneles)
        ctx.validacion_string = validacion

        electrico_nec = tecnico.get("electrico_nec") or {}
        pkg = electrico_nec.get("paq") or {}

        save_result_fingerprint(ctx)

        st.success("Ingeniería eléctrica generada.")
        st.json(pkg)

    except Exception as exc:

        ctx.resultado_proyecto = None
        ctx.resultado_core = None
        ctx.resultado_electrico = None
        setattr(ctx, "result_inputs_fingerprint", None)

        st.error(f"No se pudo generar ingeniería: {exc}")


# ==========================================================
# VALIDAR PASO
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []
    eq = getattr(ctx, "equipos", {}) or {}

    if not (eq.get("panel_id") and eq.get("inversor_id")):
        errores.append("Falta seleccionar equipos.")

    if getattr(ctx, "resultado_proyecto", None) is None:
        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores

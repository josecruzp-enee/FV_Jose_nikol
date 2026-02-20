from __future__ import annotations

from typing import List, Tuple, Dict, Any
import streamlit as st

from core.orquestador import ejecutar_evaluacion
from core.modelo import Datosproyecto
from electrical.validador_strings import PanelFV, InversorFV, validar_string
from electrical.catalogos import get_panel, get_inversor


# ==========================================================
# Helpers estado
# ==========================================================
def _asegurar_dict(ctx, nombre: str) -> dict:
    if nombre not in ctx.__dict__ or ctx.__dict__[nombre] is None:
        ctx.__dict__[nombre] = {}
    if not isinstance(ctx.__dict__[nombre], dict):
        ctx.__dict__[nombre] = {}
    return ctx.__dict__[nombre]


def _get_equipos(ctx) -> dict:
    eq = _asegurar_dict(ctx, "equipos")
    eq.setdefault("panel_id", None)
    eq.setdefault("inversor_id", None)
    eq.setdefault("tension_sistema", "2F+N_120/240")
    return eq


# ==========================================================
# Datosproyecto desde ctx
# ==========================================================
def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _get_equipos(ctx)

    consumo = c.get("kwh_12m", [0.0]*12)

    p = Datosproyecto(
        cliente=str(dc.get("cliente","")),
        ubicacion=str(dc.get("ubicacion","")),

        consumo_12m=[float(x) for x in consumo],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh",0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes",0)),

        prod_base_kwh_kwp_mes=float(sf.get("produccion_base_kwh_kwp_mes",145)),
        factores_fv_12m=[float(x) for x in sf.get("factores_fv_12m",[1]*12)],
        cobertura_objetivo=float(sf.get("cobertura_objetivo",0.8)),

        costo_usd_kwp=float(sf.get("costo_usd_kwp",1200)),
        tcambio=float(sf.get("tcambio",27)),
        tasa_anual=float(sf.get("tasa_anual",0.08)),
        plazo_anios=int(sf.get("plazo_anios",10)),
        porcentaje_financiado=float(sf.get("porcentaje_financiado",1.0)),
        om_anual_pct=float(sf.get("om_anual_pct",0.01)),
    )

    setattr(p, "equipos", dict(eq))
    setattr(p, "sistema_fv", dict(sf))
    return p


# ==========================================================
# Pipeline corto
# ==========================================================
def _ejecutar_core(ctx):
    datos = _datosproyecto_desde_ctx(ctx)
    res = ejecutar_evaluacion(datos)
    ctx.resultado_core = res
    return res


def _extraer_n_paneles_string(res):
    sz = res.get("sizing") or {}
    return int(sz.get("n_paneles_string", 10))


def _validar_string_ui(eq, n_paneles_string):
    p = get_panel(eq["panel_id"])
    inv = get_inversor(eq["inversor_id"])

    panel = PanelFV(p.voc, p.vmp, p.isc, p.imp, getattr(p,"coef_voc",-0.28))
    inversor = InversorFV(inv.vdc_max, inv.vmppt_min, inv.vmppt_max,
                          getattr(inv,"imppt_max",p.imp), inv.n_mppt)

    return validar_string(panel, inversor, n_paneles_string)


def _ejecutar_nec(ctx):
    datos = _datosproyecto_desde_ctx(ctx)
    res = ejecutar_evaluacion(datos)
    nec = res.get("electrico_nec") or {}
    return nec.get("paq", {})


# ==========================================================
# UI Mostrar
# ==========================================================
def _mostrar_nec(pkg: dict):
    st.divider()
    st.subheader("Ingeniería NEC 2023")

    dc = pkg.get("dc", {})
    ac = pkg.get("ac", {})
    ocpd = pkg.get("ocpd", {})
    cond = pkg.get("conductores", {})

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Corrientes DC**")
        st.write(f"I string máx: {dc.get('i_string_max_a')} A")
        st.write(f"I array diseño: {dc.get('i_array_design_a')} A")
        st.write(f"Vmp: {dc.get('vmp_string_v')} V")
        st.write(f"Voc frío: {dc.get('voc_frio_string_v')} V")

    with c2:
        st.markdown("**Corrientes AC**")
        st.write(f"I AC nominal: {ac.get('i_ac_nom_a')} A")
        st.write(f"I AC diseño: {ac.get('i_ac_design_a')} A")
        st.write(f"VAC: {ac.get('v_ll_v')} V | Fases: {ac.get('fases')}")

    st.markdown("**Protecciones**")
    st.write(ocpd)

    st.markdown("**Conductores**")
    st.write(cond)


# ==========================================================
# UI principal
# ==========================================================
def render(ctx):

    eq = _get_equipos(ctx)

    if not (eq.get("panel_id") and eq.get("inversor_id")):
        st.error("Seleccione equipos primero.")
        return

    st.markdown("### Ingeniería eléctrica automática")

    if not st.button("Generar ingeniería eléctrica", type="primary"):
        return

    # CORE
    res = _ejecutar_core(ctx)

    # STRING VALIDATION
    n_paneles = _extraer_n_paneles_string(res)
    validacion = _validar_string_ui(eq, n_paneles)

    if validacion.get("string_valido"):
        st.success("✔ String válido")
    else:
        st.error("String no válido")

    # NEC REAL
    pkg = _ejecutar_nec(ctx)
    ctx.resultado_electrico = pkg

    _mostrar_nec(pkg)


# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:
    if getattr(ctx, "resultado_electrico", None) is None:
        return False, ["Debe generar la ingeniería eléctrica."]
    return True, []

# ui/ingenieria_electrica.py
from __future__ import annotations

from typing import List, Tuple, Dict, Any
import streamlit as st

from electrical.validador_strings import PanelFV, InversorFV, validar_string
from core.orquestador import ejecutar_evaluacion
from core.modelo import Datosproyecto
from core.configuracion import cargar_configuracion, construir_config_efectiva
from electrical.catalogos import get_panel, get_inversor
from ui.validaciones_ui import campos_faltantes_para_paso5
from ui.state_helpers import ensure_dict, merge_defaults, save_result_fingerprint


# ==========================================================
# Helpers estado
# ==========================================================
def _asegurar_dict(ctx, nombre: str) -> dict:
    # compat wrapper
    return ensure_dict(ctx, nombre, dict)


def _get_equipos(ctx) -> dict:
    eq = _asegurar_dict(ctx, "equipos")
    eq.setdefault("panel_id", None)
    eq.setdefault("inversor_id", None)
    eq.setdefault("sobredimension_dc_ac", 1.20)
    eq.setdefault("tension_sistema", "2F+N_120/240")
    return eq


# ==========================================================
# Defaults UI
# ==========================================================
def _defaults_electrico(ctx) -> dict:
    e = _asegurar_dict(ctx, "electrico")
    merge_defaults(e, {
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
    })
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
    if len(consumo_12m) != 12:
        consumo_12m = [0.0] * 12

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),
        consumo_12m=[float(x) for x in consumo_12m],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0)),
        prod_base_kwh_kwp_mes=float(sf.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf.get("factores_fv_12m", [1]*12)],
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
# UI Inputs
# ==========================================================
def _ui_inputs_electricos(e: dict):
    c1, c2, c3 = st.columns(3)

    with c1:
        e["vac"] = st.number_input("VAC", 100.0, value=float(e["vac"]))
    with c2:
        e["fases"] = st.selectbox("Fases", [1,3], index=[1,3].index(int(e["fases"])))
    with c3:
        e["fp"] = st.number_input("FP", 0.8, 1.0, value=float(e["fp"]))

    d1, d2 = st.columns(2)

    with d1:
        e["dist_dc_m"] = st.number_input("Distancia DC (m)", 1.0, value=float(e["dist_dc_m"]))
        e["vdrop_obj_dc_pct"] = st.number_input("Vdrop objetivo DC (%)", 0.5, value=float(e["vdrop_obj_dc_pct"]))
    with d2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", 1.0, value=float(e["dist_ac_m"]))
        e["vdrop_obj_ac_pct"] = st.number_input("Vdrop objetivo AC (%)", 0.5, value=float(e["vdrop_obj_ac_pct"]))

    k1,k2,k3 = st.columns(3)

    with k1:
        e["incluye_neutro_ac"] = st.checkbox("Incluye neutro AC", value=bool(e["incluye_neutro_ac"]))
    with k2:
        e["otros_ccc"] = st.number_input("Otros CCC", 0, value=int(e["otros_ccc"]))
    with k3:
        e["t_min_c"] = st.number_input("T mínima (°C)", -10.0, value=float(e["t_min_c"]))

    e["dos_aguas"] = st.checkbox("Techo dos aguas", value=bool(e["dos_aguas"]))


# ==========================================================
# CORE + NEC
# ==========================================================
def _ejecutar_core(ctx):
    datos = _datosproyecto_desde_ctx(ctx)
    ctx.datos_proyecto = datos
    res = ejecutar_evaluacion(datos)
    ctx.resultado_core = res
    return res


def _obtener_pkg_nec(ctx):
    datos = _datosproyecto_desde_ctx(ctx)
    res = ejecutar_evaluacion(datos)
    return (res.get("electrico_nec") or {}).get("paq", {})


# ==========================================================
# Validación string
# ==========================================================
def _validar_string_catalogo(eq, e, n_paneles):
    p = get_panel(eq["panel_id"])
    inv = get_inversor(eq["inversor_id"])

    panel = PanelFV(p.voc, p.vmp, p.isc, p.imp, getattr(p,"coef_voc",-0.28))
    inversor = InversorFV(inv.vdc_max, inv.vmppt_min, inv.vmppt_max,
                          getattr(inv,"imppt_max",p.imp), inv.n_mppt)

    return validar_string(panel, inversor, n_paneles, temp_min=float(e["t_min_c"]))


# ==========================================================
# UI NEC display
# ==========================================================
def _mostrar_nec(pkg: dict):
    st.divider()
    st.subheader("Ingeniería NEC 2023")

    if not pkg:
        st.info("Sin resultados NEC.")
        return

    dc = pkg.get("dc",{})
    ac = pkg.get("ac",{})
    cond = pkg.get("conductores",{})
    ocpd = pkg.get("ocpd",{})

    c1,c2 = st.columns(2)

    with c1:
        st.markdown("**Corrientes DC**")
        st.write(dc)

    with c2:
        st.markdown("**Corrientes AC**")
        st.write(ac)

    st.markdown("**Protecciones**")
    st.write(ocpd)

    st.markdown("**Conductores**")
    st.write(cond)


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
    _ui_inputs_electricos(e)

    faltantes = campos_faltantes_para_paso5(ctx)
    if faltantes:
        st.warning("Complete estos datos antes de generar ingeniería:\n- " + "\n- ".join(faltantes))

    st.divider()
    if not st.button("Generar ingeniería eléctrica", type="primary", disabled=bool(faltantes)):
        return

    try:
        # CORE
        res = _ejecutar_core(ctx)

        # sizing
        n_paneles = int((res.get("sizing") or {}).get("n_paneles_string", 10))

        # validación
        validacion = _validar_string_catalogo(eq, e, n_paneles)
        ctx.validacion_string = validacion

        # NEC
        pkg = _obtener_pkg_nec(ctx)
        ctx.resultado_electrico = pkg
        save_result_fingerprint(ctx)

        # UI
        st.success("Ingeniería eléctrica generada.")
        st.write(validacion)
        _mostrar_nec(pkg)
    except Exception as exc:
        ctx.resultado_core = None
        ctx.resultado_electrico = None
        setattr(ctx, "result_inputs_fingerprint", None)
        st.error(f"No se pudo generar ingeniería: {exc}")


# ==========================================================
# VALIDAR PASO
# ==========================================================
def validar(ctx) -> Tuple[bool,List[str]]:
    errores=[]
    eq=getattr(ctx,"equipos",{}) or {}

    if not(eq.get("panel_id") and eq.get("inversor_id")):
        errores.append("Falta seleccionar equipos.")

    if getattr(ctx,"resultado_electrico",None) is None:
        errores.append("Debe generar ingeniería.")

    return len(errores)==0, errores

# ui/ingenieria_electrica.py
from __future__ import annotations

from typing import List, Tuple, Dict, Any
import streamlit as st

from electrical.modelos import ParametrosCableado
from electrical.estimador import calcular_paquete_electrico_desde_inputs
from electrical.validador_strings import PanelFV, InversorFV, validar_string
from core.orquestador import ejecutar_evaluacion
from core.modelo import Datosproyecto
from core.configuracion import cargar_configuracion, construir_config_efectiva
from electrical.catalogos import get_panel, get_inversor


# ==========================================================
# Helpers de estado (pequeños)
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
    eq.setdefault("sobredimension_dc_ac", 1.20)
    eq.setdefault("tension_sistema", "2F+N_120/240")
    return eq


# ==========================================================
# Defaults paso 5 (solo UI)
# ==========================================================
def _defaults_electrico(ctx) -> dict:
    e = _asegurar_dict(ctx, "electrico")

    e.setdefault("vac", 240.0)
    e.setdefault("fases", 1)
    e.setdefault("fp", 1.0)

    e.setdefault("dist_dc_m", 15.0)
    e.setdefault("dist_ac_m", 25.0)

    e.setdefault("vdrop_obj_dc_pct", 2.0)
    e.setdefault("vdrop_obj_ac_pct", 2.0)
    e.setdefault("t_min_c", 10.0)

    e.setdefault("incluye_neutro_ac", False)
    e.setdefault("otros_ccc", 0)

    e.setdefault("dos_aguas", True)
    return e


# ==========================================================
# Consolidación: ctx -> Datosproyecto (mínimo consistente)
# ==========================================================
def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _get_equipos(ctx)

    consumo_12m = c.get("kwh_12m", [0.0] * 12)
    if not isinstance(consumo_12m, list) or len(consumo_12m) != 12:
        consumo_12m = [0.0] * 12

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")).strip(),
        ubicacion=str(dc.get("ubicacion", "")).strip(),

        consumo_12m=[float(x) for x in consumo_12m],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0.0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0.0)),

        prod_base_kwh_kwp_mes=float(sf.get("produccion_base_kwh_kwp_mes", 145.0)),
        factores_fv_12m=[float(x) for x in sf.get("factores_fv_12m", [1.0] * 12)],

        cobertura_objetivo=float(sf.get("cobertura_objetivo", 0.80)),

        costo_usd_kwp=float(sf.get("costo_usd_kwp", 1200.0)),
        tcambio=float(sf.get("tcambio", 27.0)),
        tasa_anual=float(sf.get("tasa_anual", 0.08)),
        plazo_anios=int(sf.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf.get("porcentaje_financiado", 1.0)),
        om_anual_pct=float(sf.get("om_anual_pct", 0.01)),
    )

    setattr(p, "equipos", dict(eq))
    setattr(p, "sistema_fv", dict(sf))

    if "hsp_kwh_m2_d" in sf:
        setattr(p, "hsp", float(sf.get("hsp_kwh_m2_d", 4.5)))
    if "perdidas_sistema_pct" in sf:
        setattr(p, "perdidas_sistema_pct", float(sf.get("perdidas_sistema_pct", 15.0)))
    if "sombras_pct" in sf:
        setattr(p, "sombras_pct", float(sf.get("sombras_pct", 0.0)))

    if "azimut_deg" in sf:
        setattr(p, "azimut_deg", float(sf.get("azimut_deg", 180)))
    if "inclinacion_deg" in sf:
        setattr(p, "inclinacion_deg", float(sf.get("inclinacion_deg", 15)))

    if sf.get("tipo_superficie") == "Techo dos aguas":
        setattr(p, "azimut_a_deg", float(sf.get("azimut_a_deg", 90)))
        setattr(p, "azimut_b_deg", float(sf.get("azimut_b_deg", 270)))
        setattr(p, "reparto_pct_a", float(sf.get("reparto_pct_a", 50.0)))

    return p


# ==========================================================
# Parametrización cableado (UI) -> modelo eléctrico
# ==========================================================
def _params_cableado_desde_ui(e: dict) -> ParametrosCableado:
    return ParametrosCableado(
        vac=float(e["vac"]),
        fases=int(e["fases"]),
        fp=float(e["fp"]),
        dist_dc_m=float(e["dist_dc_m"]),
        dist_ac_m=float(e["dist_ac_m"]),
        vdrop_obj_dc_pct=float(e["vdrop_obj_dc_pct"]),
        vdrop_obj_ac_pct=float(e["vdrop_obj_ac_pct"]),
        incluye_neutro_ac=bool(e["incluye_neutro_ac"]),
        otros_ccc=int(e["otros_ccc"]),
        t_min_c=float(e["t_min_c"]),
    )


def _guardar_overrides_tecnicos_en_session(e: dict) -> None:
    st.session_state["cfg_overrides"] = {
        "tecnicos": {
            "t_min_c": float(e["t_min_c"]),
            "vdrop_obj_dc_pct": float(e["vdrop_obj_dc_pct"]),
            "vdrop_obj_ac_pct": float(e["vdrop_obj_ac_pct"]),
        }
    }


def _config_tecnica_efectiva() -> Dict[str, Any]:
    cfg_base = cargar_configuracion()
    cfg = construir_config_efectiva(cfg_base, st.session_state.get("cfg_overrides"))
    return cfg.tecnicos


# ==========================================================
# UI: Presentación
# ==========================================================
def _mostrar_resultados(pkg: dict) -> None:
    st.success("Ingeniería eléctrica generada.")

    st.subheader("Strings DC (referencial)")
    for line in (pkg.get("texto_ui", {}).get("strings") or []):
        st.write("• " + str(line))

    checks = pkg.get("texto_ui", {}).get("checks") or []
    if checks:
        st.warning("\n".join([str(x) for x in checks]))

    st.subheader("Cableado AC/DC (referencial)")
    for line in (pkg.get("texto_ui", {}).get("cableado") or []):
        st.write("• " + str(line))

    disclaimer = pkg.get("texto_ui", {}).get("disclaimer") or ""
    if disclaimer:
        st.caption(str(disclaimer))


def _mostrar_validacion_string(validacion: dict) -> None:
    st.divider()
    st.subheader("Validación eléctrica del string")

    if not validacion:
        st.info("Sin validación disponible.")
        return

    if bool(validacion.get("string_valido")):
        st.success(
            f"✔ String válido | Voc frío {validacion.get('voc_frio_total')} V | "
            f"MPPT OK | Corriente OK"
        )
    else:
        st.error("⚠ Configuración de string no válida")

    st.caption(
        f"Voc frío: {validacion.get('voc_frio_total')} V | "
        f"Vmp: {validacion.get('vmp_operativo')} V | "
        f"I MPPT: {validacion.get('corriente_mppt')} A"
    )

def _mostrar_nec(e_nec: dict) -> None:
    st.divider()
    st.subheader("Ingeniería NEC 2023 (corrientes, conductores, protecciones)")

    if not e_nec:
        st.info("Sin resultados NEC.")
        return

    if not bool(e_nec.get("ok", True)):
        st.error("NEC no pudo calcularse.")
        for err in (e_nec.get("errores") or e_nec.get("warnings") or []):
            st.write("• " + str(err))
        # útil para depurar mapeo
        if e_nec.get("input"):
            with st.expander("Input enviado a NEC"):
                st.json(e_nec["input"])
        return

    dc = e_nec.get("dc", {})
    ac = e_nec.get("ac", {})
    ocpd = e_nec.get("ocpd", {})
    cond = e_nec.get("conductores", {})

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Corrientes DC**")
        st.write(f"I string máx (1.25·Isc): {dc.get('i_string_max_a')} A")
        st.write(f"I array diseño (1.25·ΣIsc): {dc.get('i_array_design_a')} A")
        st.write(f"Vmp string: {dc.get('vmp_string_v')} V")
        st.write(f"Voc frío string: {dc.get('voc_frio_string_v')} V")
    with c2:
        st.markdown("**Corrientes AC**")
        st.write(f"I AC nominal: {ac.get('i_ac_nom_a')} A")
        st.write(f"I AC diseño (125%): {ac.get('i_ac_design_a')} A")
        st.write(f"VAC: {ac.get('v_ll_v')} V | Fases: {ac.get('fases')}")

    st.markdown("**Protecciones (OCPD)**")
    st.write(f"Fusible string: {ocpd.get('fusible_string')}")
    st.write(f"Breaker AC: {ocpd.get('breaker_ac')}")

    st.markdown("**Conductores + caída**")
    st.write(f"DC string: {cond.get('dc_string')}")
    if cond.get("dc_trunk"):
        st.write(f"DC trunk: {cond.get('dc_trunk')}")
    st.write(f"AC salida: {cond.get('ac_out')}")

    st.markdown("**SPD / Seccionamiento / Canalización**")
    st.write(e_nec.get("spd"))
    st.write(e_nec.get("seccionamiento"))
    st.write(e_nec.get("canalizacion"))

    resumen = e_nec.get("resumen_pdf") or []
    if resumen:
        st.markdown("**Resumen listo para PDF**")
        for line in resumen:
            st.write("• " + str(line))

# ==========================================================
# Validador string desde catálogo
# ==========================================================
def _validar_string_desde_catalogo(*, panel_id: str, inversor_id: str, t_min_c: float, n_paneles_string: int) -> dict:
    p = get_panel(panel_id)
    inv = get_inversor(inversor_id)

    panel = PanelFV(
        voc=float(p.voc),
        vmp=float(p.vmp),
        isc=float(p.isc),
        imp=float(p.imp),
        coef_voc=float(getattr(p, "coef_voc", -0.28)),
    )

    imppt_max = float(getattr(inv, "imppt_max", panel.imp))

    inversor = InversorFV(
        vdc_max=float(inv.vdc_max),
        mppt_min=float(inv.vmppt_min),
        mppt_max=float(inv.vmppt_max),
        imppt_max=imppt_max,
        n_mppt=int(inv.n_mppt),
    )

    return validar_string(
        panel,
        inversor,
        int(n_paneles_string),
        temp_min=float(t_min_c),
    )


# ==========================================================
# UI Inputs
# ==========================================================
def _ui_inputs_electricos(e: dict) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        e["vac"] = st.number_input("VAC", min_value=100.0, step=1.0, value=float(e["vac"]))
    with c2:
        fases_val = int(e["fases"])
        e["fases"] = st.selectbox("Fases", options=[1, 3], index=[1, 3].index(fases_val))
    with c3:
        e["fp"] = st.number_input("FP", min_value=0.8, max_value=1.0, step=0.01, value=float(e["fp"]))

    d1, d2 = st.columns(2)
    with d1:
        e["dist_dc_m"] = st.number_input("Distancia DC (m)", min_value=1.0, step=1.0, value=float(e["dist_dc_m"]))
        e["vdrop_obj_dc_pct"] = st.number_input("Vdrop objetivo DC (%)", min_value=0.5, step=0.1, value=float(e["vdrop_obj_dc_pct"]))
    with d2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", min_value=1.0, step=1.0, value=float(e["dist_ac_m"]))
        e["vdrop_obj_ac_pct"] = st.number_input("Vdrop objetivo AC (%)", min_value=0.5, step=0.1, value=float(e["vdrop_obj_ac_pct"]))

    k1, k2, k3 = st.columns(3)
    with k1:
        e["incluye_neutro_ac"] = st.checkbox("Incluye neutro AC", value=bool(e["incluye_neutro_ac"]))
    with k2:
        e["otros_ccc"] = st.number_input("Otros CCC (agrupamiento)", min_value=0, step=1, value=int(e["otros_ccc"]))
    with k3:
        e["t_min_c"] = st.number_input("T mínima (°C) para Voc frío", min_value=-10.0, step=1.0, value=float(e["t_min_c"]))

    e["dos_aguas"] = st.checkbox("Techo dos aguas (reparte strings)", value=bool(e["dos_aguas"]))


# ==========================================================
# Pipeline de cálculo (funciones pequeñas)
# ==========================================================
def _run_core(ctx, datos: Datosproyecto) -> dict:
    res = ejecutar_evaluacion(datos)
    ctx.resultado_core = res
    return res


def _run_paquete_electrico(ctx, eq: dict, e: dict, res: dict) -> dict:
    datos = _datosproyecto_desde_ctx(ctx)
    resultado = ejecutar_evaluacion(datos)
    return resultado.get("electrico_nec", {})
# ==========================================================
# UI Paso 5
# ==========================================================
def render(ctx) -> None:
    e = _defaults_electrico(ctx)
    eq = _get_equipos(ctx)

    if not (eq.get("panel_id") and eq.get("inversor_id")):
        st.error("Complete la selección de equipos (Paso 4).")
        return

    st.markdown("### Ingeniería eléctrica automática")
    _ui_inputs_electricos(e)
    _guardar_overrides_tecnicos_en_session(e)

    # --- FIX CRÍTICO: validar catálogo ANTES de correr core/sizing ---
    try:
        _ = get_panel(str(eq.get("panel_id") or ""))
    except Exception:
        st.error(f"Panel no existe en catálogo: {eq.get('panel_id')}")
        st.caption("Revise Paso 4: debe guardarse el ID (key) del panel, no el nombre/label.")
        return

    try:
        _ = get_inversor(str(eq.get("inversor_id") or ""))
    except Exception:
        st.error(f"Inversor no existe en catálogo: {eq.get('inversor_id')}")
        st.caption("Revise Paso 4: debe guardarse el ID (key) del inversor, no el nombre/label.")
        return
    # ---------------------------------------------------------------

    st.divider()
    if not st.button("Generar ingeniería eléctrica", type="primary"):
        return

    # 1) Consolidar Datosproyecto
    datos = _datosproyecto_desde_ctx(ctx)
    ctx.datos_proyecto = datos

    # 2) Core
    res = _run_core(ctx, datos)

    # 3) n_paneles_string real desde sizing (fallback seguro)
    sz = res.get("sizing", {}) or {}
    n_paneles_string = int(sz.get("n_paneles_string", 10))

    # 4) Validación string (desde catálogo)
    validacion = _validar_string_desde_catalogo(
        panel_id=str(eq["panel_id"]),
        inversor_id=str(eq["inversor_id"]),
        t_min_c=float(e["t_min_c"]),
        n_paneles_string=n_paneles_string,
    )
    ctx.validacion_string = validacion

    # 5) Paquete eléctrico referencial (tu flujo actual)
    pkg = _run_paquete_electrico(eq=eq, e=e, res=res)
    ctx.resultado_electrico = pkg

    # 6) Mostrar
    _mostrar_resultados(pkg)
    _mostrar_validacion_string(validacion)
    _mostrar_nec(res.get("electrico_nec") or {})


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    eq = getattr(ctx, "equipos", None) or {}

    if not (eq.get("panel_id") and eq.get("inversor_id")):
        errores.append("Falta seleccionar panel e inversor (Paso 4).")

    if getattr(ctx, "resultado_electrico", None) is None:
        errores.append("Debe generar la ingeniería eléctrica antes de continuar.")

    return (len(errores) == 0), errores

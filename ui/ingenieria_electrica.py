# ui/ingenieria_electrica.py
from __future__ import annotations

from typing import List, Tuple, Dict, Any

import pandas as pd
import streamlit as st

from electrical.catalogos.modelos import Panel as PanelFV, Inversor as InversorFV
from core.modelo import Datosproyecto
from electrical.catalogos.catalogos import get_panel, get_inversor
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


def _kv_df(d: dict, rename: dict | None = None, units: dict | None = None) -> pd.DataFrame:
    rename = rename or {}
    units = units or {}
    rows = []
    for k, v in (d or {}).items():
        if isinstance(v, (dict, list)):
            continue
        label = rename.get(k, k)
        unit = units.get(k, "")
        rows.append((label, _fmt(v, unit)))
    return pd.DataFrame(rows, columns=["Parámetro", "Valor"])


def _render_warnings(warnings: list):
    if not warnings:
        st.success("Sin warnings ✅")
        return
    st.warning("Warnings")
    for w in warnings:
        st.write(f"• {w}")


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
    if not isinstance(consumo_12m, list) or len(consumo_12m) != 12:
        consumo_12m = [0.0] * 12

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
# UI Inputs (volvieron los controles)
# ==========================================================
def _ui_inputs_electricos(e: dict):
    c1, c2, c3 = st.columns(3)

    with c1:
        e["vac"] = st.number_input(
            "VAC",
            min_value=100.0,
            max_value=600.0,
            value=float(e.get("vac", 240.0)),
            step=1.0,
        )

    with c2:
        opciones = [1, 3]
        try:
            valor = int(e.get("fases", 1) or 1)
        except Exception:
            valor = 1
        index = opciones.index(valor) if valor in opciones else 0
        e["fases"] = st.selectbox("Fases", opciones, index=index)

    with c3:
        e["fp"] = st.number_input(
            "FP",
            min_value=0.80,
            max_value=1.00,
            value=float(e.get("fp", 1.0)),
            step=0.01,
        )

    d1, d2 = st.columns(2)
    with d1:
        e["dist_dc_m"] = st.number_input(
            "Distancia DC (m)",
            min_value=1.0,
            max_value=2000.0,
            value=float(e.get("dist_dc_m", 15.0)),
            step=1.0,
        )
        e["vdrop_obj_dc_pct"] = st.number_input(
            "Vdrop objetivo DC (%)",
            min_value=0.5,
            max_value=10.0,
            value=float(e.get("vdrop_obj_dc_pct", 2.0)),
            step=0.1,
        )

    with d2:
        e["dist_ac_m"] = st.number_input(
            "Distancia AC (m)",
            min_value=1.0,
            max_value=2000.0,
            value=float(e.get("dist_ac_m", 25.0)),
            step=1.0,
        )
        e["vdrop_obj_ac_pct"] = st.number_input(
            "Vdrop objetivo AC (%)",
            min_value=0.5,
            max_value=10.0,
            value=float(e.get("vdrop_obj_ac_pct", 2.0)),
            step=0.1,
        )

    k1, k2, k3 = st.columns(3)
    with k1:
        e["incluye_neutro_ac"] = st.checkbox("Incluye neutro AC", value=bool(e.get("incluye_neutro_ac", False)))
    with k2:
        e["otros_ccc"] = st.number_input(
            "Otros CCC",
            min_value=0,
            max_value=999,
            value=int(e.get("otros_ccc", 0)),
            step=1,
        )
    with k3:
        e["t_min_c"] = st.number_input(
            "T mínima (°C)",
            min_value=-40.0,
            max_value=60.0,
            value=float(e.get("t_min_c", 10.0)),
            step=1.0,
        )

    e["dos_aguas"] = st.checkbox("Techo dos aguas", value=bool(e.get("dos_aguas", True)))


# ==========================================================
# CORE — EJECUCIÓN CENTRAL
# ==========================================================
def _ejecutar_core(ctx) -> Dict[str, Any]:
    import streamlit as st
    from core.orquestador import ejecutar_estudio

    datos = _datosproyecto_desde_ctx(ctx)
    ctx.datos_proyecto = datos

    resultado_proyecto = ejecutar_estudio(datos)

    # 🔹 Persistencia real en Streamlit
    st.session_state["resultado_proyecto"] = resultado_proyecto
    st.session_state["resultado_core"] = resultado_proyecto.get("_compat", {}) or {}
    st.session_state["resultado_electrico"] = resultado_proyecto.get("electrico_nec") or {}

    # 🔹 Mantén compatibilidad con ctx 
    ctx.resultado_proyecto = resultado_proyecto
    ctx.resultado_core = st.session_state["resultado_core"]
    ctx.resultado_electrico = st.session_state["resultado_electrico"]

    return resultado_proyecto
# ==========================================================
# Validación string catálogo
# ==========================================================
def _validar_string_catalogo(eq, e, n_paneles, resultado_proyecto):

    res = resultado_proyecto or {}
    strings_res = res.get("strings") or {}
    lista = strings_res.get("strings") or []

    if not lista:
        return {}

    inv = get_inversor(eq["inversor_id"])

    voc_frio_total = max(s.get("voc_frio_string_v", 0) for s in lista)
    vmp_operativo = lista[0].get("vmp_string_v")
    corriente_mppt = max(s.get("imax_pv_a", 0) for s in lista)

    imppt_max = getattr(inv, "imppt_max", None) or getattr(inv, "imppt_max_a", None)

    ok_vdc = voc_frio_total <= inv.vdc_max_v
    ok_mppt = inv.mppt_min_v <= vmp_operativo <= inv.mppt_max_v
    ok_corriente = corriente_mppt <= imppt_max

    return {
        "voc_frio_total": voc_frio_total,
        "vmp_operativo": vmp_operativo,
        "corriente_mppt": corriente_mppt,
        "ok_vdc": ok_vdc,
        "ok_mppt": ok_mppt,
        "ok_corriente": ok_corriente,
        "string_valido": ok_vdc and ok_mppt and ok_corriente,
    }

# ==========================================================
# UI NEC display (cuadros bonitos)
# ==========================================================
def _mostrar_nec(pkg: dict):
    st.divider()
    st.subheader("Ingeniería NEC 2023")

    if not pkg:
        st.info("Sin resultados NEC.")
        return

    dc = pkg.get("dc") or {}
    ac = pkg.get("ac") or {}
    conductores = (pkg.get("conductores") or {}).get("circuitos") or []
    warnings_global = pkg.get("warnings") or []

    tabs = st.tabs(["⚡ DC", "🔌 AC", "🧵 Conductores", "⚠ Warnings", "🔎 Datos crudos"])

    # ========================= DC =========================
    with tabs[0]:
        st.markdown("### Corrientes DC")

        c1, c2, c3 = st.columns(3)
        c1.metric("Vdc nominal", _fmt(dc.get("vdc_nom"), "V"))
        c2.metric("Idc nominal", _fmt(dc.get("idc_nom"), "A"))
        c3.metric("Potencia DC", _fmt(dc.get("potencia_dc_w"), "W"))

        df_dc = pd.DataFrame(
            [
                ("Vdc nominal", _fmt(dc.get("vdc_nom"), "V")),
                ("Idc nominal", _fmt(dc.get("idc_nom"), "A")),
                ("Potencia DC", _fmt(dc.get("potencia_dc_w"), "W")),
            ],
            columns=["Parámetro", "Valor"],
        )

        st.dataframe(df_dc, use_container_width=True, hide_index=True)

    # ========================= AC =========================
    with tabs[1]:
        st.markdown("### Corrientes AC")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Potencia AC", _fmt(ac.get("potencia_ac_w"), "W"))
        c2.metric("Voltaje", _fmt(ac.get("vac_ll") or ac.get("vac_ln"), "V"))
        c3.metric("I nominal", _fmt(ac.get("iac_nom"), "A"))
        c4.metric("FP", _fmt(ac.get("fp")))

        df_ac = pd.DataFrame(
            [
                ("Fases", _fmt(ac.get("fases"))),
                ("FP", _fmt(ac.get("fp"))),
                ("I nominal", _fmt(ac.get("iac_nom"), "A")),
                ("Potencia AC", _fmt(ac.get("potencia_ac_w"), "W")),
            ],
            columns=["Parámetro", "Valor"],
        )

        st.dataframe(df_ac, use_container_width=True, hide_index=True)

    # ====================== CONDUCTORES ======================
    with tabs[2]:
        st.markdown("### Conductores calculados")

        if not conductores:
            st.info("Sin datos de conductores.")
        else:
            rows = []

            for c in conductores:
                rows.append(
                    {
                        "Circuito": c.get("nombre"),
                        "I diseño (A)": c.get("i_diseno_a"),
                        "Longitud (m)": c.get("l_m"),
                        "V base (V)": c.get("v_base_v"),
                        "Calibre": c.get("calibre"),
                        "Ampacidad ajustada (A)": c.get("ampacidad_ajustada_a"),
                        "VD (%)": c.get("vd_pct"),
                        "VD objetivo (%)": c.get("vd_obj_pct"),
                        "Cumple": "✅" if c.get("cumple") else "❌",
                    }
                )

            df_cond = pd.DataFrame(rows)
            st.dataframe(df_cond, use_container_width=True, hide_index=True)

    # ========================= WARNINGS =========================
    with tabs[3]:
        st.markdown("### Advertencias")

        if not warnings_global:
            st.success("Sin advertencias.")
        else:
            for w in warnings_global:
                st.warning(w)

    # ========================= DEBUG =========================
    with tabs[4]:
        st.json(pkg)




def _mostrar_validacion_string(validacion: dict):
    v = validacion or {}

    st.subheader("Validación de string (catálogo)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Voc frío total", _fmt(v.get("voc_frio_total"), "V"))
    c2.metric("Vmp operativo", _fmt(v.get("vmp_operativo"), "V"))
    c3.metric("Corriente MPPT", _fmt(v.get("corriente_mppt"), "A"))

    with c4:
        st.write("**Estado**")
        st.write(f"- Vdc: {_yn(bool(v.get('ok_vdc')))}")
        st.write(f"- MPPT: {_yn(bool(v.get('ok_mppt')))}")
        st.write(f"- Corriente: {_yn(bool(v.get('ok_corriente')))}")
        st.write(f"- String: {_yn(bool(v.get('string_valido')))}")

    if v.get("_imppt_max_fallback"):
        st.warning("El inversor no trae `imppt_max` en el catálogo. Se usó un fallback (muy alto) para no falsear la validación de corriente.")

    with st.expander("Ver validación (crudo)"):
        st.json(v)


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
        res = _ejecutar_core(ctx)

        st.markdown("### DEBUG RESULTADO PROYECTO")
        st.json(res)

        # ======================================================
        # 🔹 CORE devuelve formato PLANO
        # ======================================================

        sizing = res.get("sizing") or {}

        # usa n_paneles_string si existe, si no n_paneles
        n_paneles = int(
            sizing.get("n_paneles_string")
            or sizing.get("n_paneles")
            or 10
        )

        validacion = _validar_string_catalogo(eq, e, n_paneles, res)
        ctx.validacion_string = validacion

        # 🔹 NEC viene directo en raíz
        wrapper = res.get("electrico_nec") or {}
        pkg = wrapper.get("paq") or {}

        # guardar fingerprint para “stale”
        save_result_fingerprint(ctx)

        st.success("Ingeniería eléctrica generada.")

        _mostrar_validacion_string(validacion)
        _mostrar_nec(pkg)

    except Exception as exc:
        ctx.resultado_proyecto = None
        ctx.resultado_core = None
        ctx.resultado_electrico = None
        setattr(ctx, "result_inputs_fingerprint", None)
        st.error(f"No se pudo generar ingeniería: {exc}")

def _mostrar_validacion_string(validacion: dict):
    v = validacion or {}

    st.subheader("Validación de string (catálogo)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Voc frío total", _fmt(v.get("voc_frio_total"), "V"))
    c2.metric("Vmp operativo", _fmt(v.get("vmp_operativo"), "V"))
    c3.metric("Corriente MPPT", _fmt(v.get("corriente_mppt"), "A"))

    with c4:
        st.write("**Estado**")
        st.write(f"- Vdc: {_yn(bool(v.get('ok_vdc')))}")
        st.write(f"- MPPT: {_yn(bool(v.get('ok_mppt')))}")
        st.write(f"- Corriente: {_yn(bool(v.get('ok_corriente')))}")
        st.write(f"- String: {_yn(bool(v.get('string_valido')))}")

    if v.get("_imppt_max_fallback"):
        st.warning("El inversor no trae `imppt_max` en el catálogo. Se usó un fallback (muy alto) para no falsear la validación de corriente.")

    with st.expander("Ver validación (crudo)"):
        st.json(v)


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
        res = _ejecutar_core(ctx)

        st.markdown("### DEBUG RESULTADO PROYECTO")
        st.json(res)

        # ======================================================
        # 🔹 CORE devuelve formato PLANO
        # ======================================================

        sizing = res.get("sizing") or {}

        # usa n_paneles_string si existe, si no n_paneles
        n_paneles = int(
            sizing.get("n_paneles_string")
            or sizing.get("n_paneles")
            or 10
        )

        validacion = _validar_string_catalogo(eq, e, n_paneles, res)
        ctx.validacion_string = validacion

        # 🔹 NEC viene directo en raíz
        wrapper = res.get("electrico_nec") or {}
        pkg = wrapper.get("paq") or {}

        # guardar fingerprint para “stale”
        save_result_fingerprint(ctx)

        st.success("Ingeniería eléctrica generada.")

        _mostrar_validacion_string(validacion)
        _mostrar_nec(pkg)

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
    import streamlit as st

    errores = []
    eq = getattr(ctx, "equipos", {}) or {}

    if not (eq.get("panel_id") and eq.get("inversor_id")):
        errores.append("Falta seleccionar equipos.")

    # 🔹 Validar contra estado persistente real
    if "resultado_proyecto" not in st.session_state:
        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores

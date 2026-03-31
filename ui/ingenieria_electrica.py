from __future__ import annotations

from typing import List, Tuple
import streamlit as st

from core.dominio.modelo import Datosproyecto, InstalacionElectrica, Equipos
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.dependencias import construir_dependencias

from ui.state_helpers import ensure_dict

# 🔥 TRACE
from core.debug.trace_streamlit import trace, get_trace, clear_trace


# ==========================================================
# UTIL
# ==========================================================
def _asegurar_dict(ctx, nombre: str) -> dict:
    return ensure_dict(ctx, nombre, dict)


# ==========================================================
# INPUTS
# ==========================================================
def _ui_inputs_electricos(e: dict):

    st.subheader("Parámetros eléctricos de instalación")

    c1, c2, c3 = st.columns(3)

    with c1:
        e["vac"] = st.number_input("Voltaje AC (V)", 100.0, 600.0, float(e.get("vac", 240.0)))

    with c2:
        e["fases"] = st.selectbox("Fases", [1, 3], index=0 if int(e.get("fases", 1)) == 1 else 1)

    with c3:
        e["fp"] = st.number_input("Factor de potencia", 0.80, 1.00, float(e.get("fp", 1.0)), step=0.01)

    st.markdown("### Distancias")

    d1, d2 = st.columns(2)

    with d1:
        e["dist_dc_m"] = st.number_input("Distancia DC (m)", 1.0, value=float(e.get("dist_dc_m", 15.0)))

    with d2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", 1.0, value=float(e.get("dist_ac_m", 25.0)))


# ==========================================================
# DATOS PROYECTO
# ==========================================================
def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf_raw = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")
    e = _asegurar_dict(ctx, "electrico")

    consumo = c.get("consumo_12m", [0]*12)

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),

        lat=float(sf_raw.get("latitud", 15.8250)),
        lon=float(sf_raw.get("longitud", -87.9500)),

        consumo_12m=[float(x) for x in consumo],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 5.50)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 400)),

        prod_base_kwh_kwp_mes=float(sf_raw.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf_raw.get("factores_fv_12m", [1]*12)],
        cobertura_objetivo=float(sf_raw.get("cobertura_objetivo", 0.8)),

        costo_usd_kwp=float(sf_raw.get("costo_usd_kwp", 1200)),
        tcambio=float(sf_raw.get("tcambio", 27)),

        tasa_anual=float(sf_raw.get("tasa_anual", 0.08)),
        plazo_anios=int(sf_raw.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf_raw.get("porcentaje_financiado", 1)),

        instalacion_electrica=InstalacionElectrica(
            vac=float(e.get("vac", 240)),
            fases=int(e.get("fases", 1)),
            fp=float(e.get("fp", 1.0)),
            dist_dc_m=float(e.get("dist_dc_m", 15)),
            dist_ac_m=float(e.get("dist_ac_m", 25)),
        )
    )

    p.equipos = Equipos(
        panel_id=eq.get("panel_id"),
        inversor_id=eq.get("inversor_id"),
    )

    if sf_raw.get("zonas"):

        zonas = []
        for z in sf_raw.get("zonas", []):
            zonas.append({"n_paneles": int(z.get("n_paneles") or 0)})

        p.sistema_fv = {
            "modo": "multizona",
            "zonas": zonas
        }

    else:
        sizing = sf_raw.get("sizing_input", {})

        p.sistema_fv = {
            "modo": sizing.get("modo"),
            "valor": float(sizing.get("valor", 0))
        }

    return p


# ==========================================================
# DETALLE
# ==========================================================
def _mostrar_detalle(strings, electrical, sizing):

    st.markdown("## ⚡ Ingeniería eléctrica")

    corr = electrical.corrientes
    cond = electrical.conductores
    prot = electrical.protecciones

    tr = getattr(cond, "tramos", None)
    mppt_detalle = getattr(corr, "mppt_detalle", [])

    inv = getattr(sizing, "inversor", None)

    st.markdown("### ⚙ Inversor seleccionado")

    if not inv:
        st.warning("⚠ Inversor no disponible")
    else:
        kw = getattr(inv, "kw_ac", None)
        mppt = getattr(inv, "n_mppt", None)
        vdc = getattr(inv, "vdc_max_v", None)

        st.markdown(f"""
- Potencia AC: {kw if kw is not None else "-"} kW  
- MPPT: {mppt if mppt is not None else "-"}  
- Vdc máx: {vdc if vdc is not None else "-"} V  
""")

    st.markdown("### 🔷 Configuración FV")

    for i, s in enumerate(strings, 1):
        st.markdown(f"""
**String {i}**

- Paneles: {s.n_series}  
- Vmp: {s.vmp_string_v:.1f} V  
- Voc: {s.voc_frio_string_v:.1f} V  
- Corriente: {s.imp_string_a:.2f} A  
""")

    st.markdown("### ⚡ Resultado eléctrico por MPPT")

    for i, m in enumerate(mppt_detalle):

        p = prot.mppt[i] if i < len(prot.mppt) else None
        t = tr.dc_mppt[i] if tr and i < len(tr.dc_mppt) else None

        st.markdown(f"""
**MPPT {i+1}**

- Corriente operación: {m.i_operacion_a:.2f} A  
- Corriente diseño: {m.i_diseno_a:.2f} A  
- Protección: {p.tamano_a if p else "-"} A  
- Conductor: {t.calibre if t else "-"} AWG  
""")

    st.markdown("### 🔌 Sistema AC")

    t_ac = getattr(tr, "ac", None)

    st.markdown(f"""
- Corriente AC: {corr.ac.i_diseno_a:.2f} A  
- Protección: {prot.ocpd_ac.tamano_a if prot.ocpd_ac else "-"} A  
- Conductor: {t_ac.calibre if t_ac else "-"} AWG  
""")


# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    debug_mode = st.toggle("🧪 Activar debug pipeline", value=True)

    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    if st.button("⚡ Generar ingeniería eléctrica", width="stretch"):

        p = _datosproyecto_desde_ctx(ctx)

        deps = construir_dependencias()

        # 🔥 INSTRUMENTAR PIPELINE
        deps.sizing.ejecutar = trace("sizing")(deps.sizing.ejecutar)
        deps.paneles.ejecutar = trace("paneles")(deps.paneles.ejecutar)
        deps.energia.ejecutar = trace("energia")(deps.energia.ejecutar)
        deps.nec.ejecutar = trace("nec")(deps.nec.ejecutar)
        deps.finanzas.ejecutar = trace("finanzas")(deps.finanzas.ejecutar)

        clear_trace()

        resultado = ejecutar_estudio(p, deps)

        ctx.resultado = resultado

        st.success("✅ Ingeniería generada")

    resultado = getattr(ctx, "resultado", None)

    if not resultado:
        return

    st.write("Estado:", resultado.ok)
    st.write("Errores:", resultado.errores)

    if resultado.strings and resultado.electrical:
        strings = resultado.strings.strings
        _mostrar_detalle(strings, resultado.electrical, resultado.sizing)

    # ==========================================================
    # DEBUG PIPELINE
    # ==========================================================
    if debug_mode:

        trace_data = get_trace()

        if trace_data:

            st.markdown("## 🧪 Debug Pipeline FV")

            for step in trace_data:

                nombre = step.get("funcion", "unknown")
                entrada = step.get("entrada")
                salida = step.get("salida")
                error = step.get("error")

                with st.expander(f"🔹 {nombre.upper()}", expanded=False):

                    st.markdown("**Entrada**")
                    st.code(str(entrada)[:800], language="python")

                    if error:
                        st.error(error)
                    else:
                        st.markdown("**Salida**")
                        st.code(str(salida)[:800], language="python")


# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx):

    resultado = getattr(ctx, "resultado", None)

    if not resultado:
        return False, ["Debe generar ingeniería eléctrica"]

    if not getattr(resultado, "ok", False):
        return False, resultado.errores or ["Error en ingeniería"]

    return True, []

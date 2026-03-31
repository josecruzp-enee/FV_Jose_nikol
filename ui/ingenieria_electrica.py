from __future__ import annotations

from typing import List, Tuple
import streamlit as st

from core.dominio.modelo import Datosproyecto, InstalacionElectrica, Equipos
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.dependencias import construir_dependencias

from ui.state_helpers import ensure_dict


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

    # EQUIPOS
    p.equipos = Equipos(
        panel_id=eq.get("panel_id"),
        inversor_id=eq.get("inversor_id"),
    )

    # MULTIZONA
    if sf_raw.get("usar_zonas"):

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
# ZONAS (FIX: usar INPUT, no strings)
# ==========================================================
def _mostrar_zonas(ctx):

    st.markdown("### 🔀 Zonas FV (diseño real)")

    sf = getattr(ctx, "sistema_fv", {})
    zonas = sf.get("zonas", [])

    if not zonas:
        st.info("Sistema sin zonas definidas")
        return

    for i, z in enumerate(zonas, start=1):

        c1, c2 = st.columns(2)

        c1.metric(f"Zona {i}", z.get("n_paneles", 0))
        c2.metric("Strings (resultado)", "—")


# ==========================================================
# DETALLE COMPLETO
# ==========================================================
def _mostrar_detalle(paneles, electrical):

    st.markdown("## ⚡ Ingeniería eléctrica")

    strings = paneles.strings
    corr = electrical.corrientes
    cond = electrical.conductores
    prot = electrical.protecciones

    # ======================================================
    # AGRUPAR POR ZONA
    # ======================================================
    zonas = {}
    for s in strings:
        zona = getattr(s, "zona", 1)
        zonas.setdefault(zona, []).append(s)

    mppt_detalle = getattr(corr, "mppt_detalle", [])

    # ======================================================
    # 🔀 CONFIGURACIÓN POR ARREGLO
    # ======================================================
    st.markdown("### 🔀 Configuración por arreglo")

    for i, (zona, strings_zona) in enumerate(zonas.items(), 1):

        st.markdown(f"#### 🔹 Arreglo {i} (Zona {zona})")

        data = []

        for j, s in enumerate(strings_zona, 1):
            data.append({
                "String": f"S{j}",
                "Paneles": s.n_series,
                "Vmp (V)": round(s.vmp_string_v, 1),
                "Voc (V)": round(s.voc_frio_string_v, 1),
                "I (A)": round(s.imp_string_a, 2),
            })

        st.dataframe(data, width="stretch")

        # MPPT asociado
        if i-1 < len(mppt_detalle):
            m = mppt_detalle[i-1]

            st.success(
                f"MPPT {i} → {m.i_operacion_a:.2f} A "
                f"(diseño {m.i_diseno_a:.2f} A)"
            )

        # Protección DC por arreglo (simple por ahora)
        try:
            if prot.ocpd_dc_array:
                st.info(f"Protección DC sugerida: {prot.ocpd_dc_array.tamano_a} A")
        except:
            pass

        st.divider()

    # ======================================================
    # ⚡ SISTEMA AC
    # ======================================================
    st.markdown("### ⚡ Sistema")

    try:
        st.metric("Corriente AC", f"{corr.ac.i_diseno_a:.2f} A")
    except:
        st.metric("Corriente AC", "—")

    # ======================================================
    # 🧵 CONDUCTORES Y PROTECCIONES
    # ======================================================
    st.markdown("### 🧵 Conductores y protecciones (sistema)")

    try:
        tr = cond.tramos

        fus = prot.fusible_string
        fus_val = fus.tamano_a if fus and fus.tamano_a else "—"

        st.table([{
            "DC cable": f"{tr.dc.calibre} AWG" if tr.dc else "-",
            "AC cable": f"{tr.ac.calibre} AWG" if tr.ac else "-",
            "Breaker AC": f"{prot.ocpd_ac.tamano_a} A" if prot.ocpd_ac else "-",
            "Fusible (string)": fus_val
        }])

    except:
        st.warning("No se pudo calcular conductores/protecciones")
# ==========================================================
# RENDER
# ==========================================================

def render(ctx):

    import streamlit as st

    # ======================================================
    # INPUTS
    # ======================================================
    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    # ======================================================
    # BOTÓN GENERAR
    # ======================================================
    if "resultado" not in st.session_state:
        st.session_state["resultado"] = None

    generar = st.button("⚡ Generar ingeniería eléctrica", use_container_width=True)

    if generar:

        try:
            p = _datosproyecto_desde_ctx(ctx)
            deps = construir_dependencias()

            resultado = ejecutar_estudio(p, deps)

            # Guardar
            ctx.resultado = resultado
            st.session_state["resultado"] = resultado

            st.success("✅ Ingeniería generada")

        except Exception:
            import traceback
            st.error("Error en motor FV")
            st.code(traceback.format_exc())
            return

    # ======================================================
    # OBTENER RESULTADO
    # ======================================================
    resultado = getattr(ctx, "resultado", None) or st.session_state.get("resultado")

    if not resultado:
        st.info("Presiona el botón para generar la ingeniería eléctrica")
        return

    # ======================================================
    # 🔥 DEBUG REAL (CLAVE)
    # ======================================================
    st.markdown("### 🧪 Estado del motor")
    st.write(resultado.trazas)

    st.write("DEBUG ELECTRICAL:", resultado.electrical)

    # ======================================================
    # OUTPUTS
    # ======================================================
    if resultado.strings:

        _mostrar_zonas(ctx)

        if resultado.electrical:

            _mostrar_detalle(resultado.strings, resultado.electrical)

        else:
            st.error("❌ Electrical NO se generó")
# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    resultado = getattr(ctx, "resultado", None) or st.session_state.get("resultado")

    if not resultado:
        return False, ["Debe generar ingeniería."]

    return True, []

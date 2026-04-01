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
# DEBUG COMPLETO (ROBUSTO)
# ==========================================================
def mostrar_debug_completo(resultado):

    st.markdown("## 🧪 INSPECCIÓN COMPLETA DEL SISTEMA")

    def safe(obj):
        try:
            if obj is None:
                return "None"
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            return str(obj)
        except Exception as e:
            return f"ERROR: {e}"

    data = {}

    try:
        data["sizing"] = safe(getattr(resultado, "sizing", None))
    except:
        data["sizing"] = "ERROR"

    try:
        data["paneles"] = safe(getattr(resultado, "strings", None))
    except:
        data["paneles"] = "ERROR"

    try:
        data["energia"] = safe(getattr(resultado, "energia", None))
    except:
        data["energia"] = "ERROR"

    try:
        data["electrical"] = safe(getattr(resultado, "electrical", None))
    except:
        data["electrical"] = "ERROR"

    st.json(data)


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

def _mostrar_detalle(strings, electrical):

    st.markdown("## ⚡ Ingeniería eléctrica")

    try:
        corr = getattr(electrical, "corrientes", None)
        cond = getattr(electrical, "conductores", None)
        prot = getattr(electrical, "protecciones", None)

        # ==================================================
        # STRINGS
        # ==================================================
        st.markdown("### 🔋 Strings")

        if not strings:
            st.warning("No hay strings disponibles")
        else:
            data = []
            for i, s in enumerate(strings, 1):
                data.append({
                    "String": i,
                    "Vmp (V)": getattr(s, "vmp_v", "-"),
                    "Voc (V)": getattr(s, "voc_v", "-"),
                    "Imp (A)": getattr(s, "imp_a", "-"),
                    "Isc (A)": getattr(s, "isc_a", "-"),
                })

            st.dataframe(data, width="stretch")

        # ==================================================
        # CORRIENTES
        # ==================================================
        st.markdown("### ⚡ Corrientes")

        if corr:
            st.write("DC diseño:", getattr(corr.dc, "i_diseno_a", "-"))
            st.write("AC diseño:", getattr(corr.ac, "i_diseno_a", "-"))
        else:
            st.warning("No hay corrientes calculadas")

        # ==================================================
        # CONDUCTORES
        # ==================================================
        st.markdown("### 🧵 Conductores")

        if cond and getattr(cond, "tramos", None):

            tr = cond.tramos

            # DC
            if getattr(tr, "dc_mppt", None):
                for i, t in enumerate(tr.dc_mppt, 1):
                    st.info(
                        f"MPPT {i}: {t.calibre} AWG | "
                        f"Ampacidad: {t.ampacidad_ajustada_a:.2f} A | "
                        f"VD: {t.vd_pct:.2f}%"
                    )
            else:
                st.warning("No hay conductores DC")

            # AC
            if getattr(tr, "ac", None):
                t = tr.ac
                st.info(
                    f"AC: {t.calibre} AWG | "
                    f"Ampacidad: {t.ampacidad_ajustada_a:.2f} A | "
                    f"VD: {t.vd_pct:.2f}%"
                )
            else:
                st.warning("No hay conductor AC")

        else:
            st.warning("No hay datos de conductores")

        # ==================================================
        # PROTECCIONES
        # ==================================================
        st.markdown("### ⚡ Protecciones")

        if prot:

            # Breaker AC
            breaker = getattr(getattr(prot, "ocpd_ac", None), "tamano_a", "-")
            st.write("Breaker AC:", breaker)

            # Fusible string
            fus = getattr(getattr(prot, "fusible_string", None), "tamano_a", None)
            if fus:
                st.write("Fusible string:", fus)
            else:
                st.write("Fusible string: No requerido")

        else:
            st.warning("No hay protecciones calculadas")

    except Exception as err:
        st.error(f"Error en detalle eléctrico: {err}")


# ==========================================================
# RENDER
# ==========================================================



def render(ctx):

    # ===============================
    # INPUTS
    # ===============================
    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    # ===============================
    # BOTÓN
    # ===============================
    if st.button("⚡ Generar ingeniería eléctrica"):

        try:
            p = _datosproyecto_desde_ctx(ctx)
            deps = construir_dependencias()

            resultado = ejecutar_estudio(p, deps)

            # ✅ CORRECTO (ctx es objeto)
            setattr(ctx, "resultado", resultado)

            st.success("✅ Ingeniería generada")

        except Exception as err:
            import traceback

            st.error("❌ Error generando ingeniería")
            st.code(traceback.format_exc())
            return

    # ===============================
    # RESULTADO
    # ===============================
    resultado = getattr(ctx, "resultado", None)

    if resultado is None:
        st.warning("⚠ No hay resultado aún")
        return

    # ===============================
    # ESTADO
    # ===============================
    estado_ok = getattr(resultado, "ok", False)
    errores = getattr(resultado, "errores", [])

    st.write("Estado:", estado_ok)
    st.write("Errores:", errores)

    # ===============================
    # VALIDACIÓN
    # ===============================
    if not estado_ok:
        st.error("❌ Resultado no OK")
        return

    if not getattr(resultado, "strings", None):
        st.error("❌ No hay strings")
        return

    if not getattr(resultado, "electrical", None):
        st.error("❌ No hay resultado electrical")
        return

    # ===============================
    # DETALLE
    # ===============================
    try:
        strings = resultado.strings.strings
        electrical = resultado.electrical

        _mostrar_detalle(strings, electrical)

    except Exception as err:
        st.error(f"❌ Error mostrando detalle: {err}")


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

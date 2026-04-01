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

            # 🔥 SIEMPRE GUARDAR
            setattr(ctx, "resultado", resultado)

            st.success("✅ Ingeniería generada")

        except Exception as err:
            st.error(f"❌ Error generando ingeniería: {err}")
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
    try:
        estado_ok = getattr(resultado, "ok", False)
        errores = getattr(resultado, "errores", [])
    except Exception as e:
        import traceback
        st.code(traceback.format_exc())
        raise e

    st.write("Estado:", estado_ok)
    st.write("Errores:", errores)

    if not estado_ok:
        st.error("❌ Resultado no OK")
        return

    # ===============================
    # DEBUG SIMPLE (NO ROMPE)
    # ===============================
    try:
        st.markdown("## 🧪 Datos internos")

        st.write("sizing:", getattr(resultado, "sizing", None))
        st.write("paneles:", getattr(resultado, "strings", None))
        st.write("energia:", getattr(resultado, "energia", None))
        st.write("electrical:", getattr(resultado, "electrical", None))

    except Exception as e:
        st.error(f"Error debug: {e}")

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

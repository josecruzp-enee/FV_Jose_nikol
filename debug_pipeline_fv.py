import streamlit as st
import inspect
import pprint

from core.aplicacion.dependencias import construir_dependencias
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.dominio.modelo import Datosproyecto


# ==========================================================
# TRACE GLOBAL
# ==========================================================
def init_trace():
    if "_trace" not in st.session_state:
        st.session_state["_trace"] = []


def add_trace(nombre, entrada, salida=None, error=None):
    init_trace()
    st.session_state["_trace"].append({
        "funcion": nombre,
        "entrada": entrada,
        "salida": salida,
        "error": error
    })


def get_trace():
    return st.session_state.get("_trace", [])


def clear_trace():
    st.session_state["_trace"] = []


# ==========================================================
# TRACE WRAPPER
# ==========================================================
def trace_function(fn, name):

    def wrapper(*args, **kwargs):

        try:
            result = fn(*args, **kwargs)

            add_trace(
                name,
                {"args": str(args), "kwargs": str(kwargs)},
                str(result),
                None
            )

            return result

        except Exception as e:

            add_trace(
                name,
                {"args": str(args), "kwargs": str(kwargs)},
                None,
                str(e)
            )

            raise

    return wrapper


# ==========================================================
# INSTRUMENTAR
# ==========================================================
def instrument_dependencies(deps):

    deps.sizing.ejecutar = trace_function(deps.sizing.ejecutar, "sizing")
    deps.paneles.ejecutar = trace_function(deps.paneles.ejecutar, "paneles")
    deps.energia.ejecutar = trace_function(deps.energia.ejecutar, "energia")
    deps.nec.ejecutar = trace_function(deps.nec.ejecutar, "nec")
    deps.finanzas.ejecutar = trace_function(deps.finanzas.ejecutar, "finanzas")

    return deps


# ==========================================================
# DATOS DEMO
# ==========================================================
def construir_datos_demo():

    return Datosproyecto(

        cliente="DEBUG",
        ubicacion="TEST",

        consumo_12m=[500]*12,

        prod_base_kwh_kwp_mes=[
            140,145,150,148,140,135,
            132,134,130,128,135,138
        ],

        factores_fv_12m=[1]*12,

        cobertura_objetivo=1.0,

        costo_usd_kwp=900,

        tcambio=24.5,
        tasa_anual=0.12,
        plazo_anios=10,
        porcentaje_financiado=0.7,

        sistema_fv={
            "modo": "multizona",
            "zonas": [
                {"n_paneles": 6},
                {"n_paneles": 8}
            ]
        },

        panel_id="JA_450W",
        inversor_id="INV_5KW",

        electrico={
            "vac": 240,
            "fases": 1,
            "fp": 1.0
        }
    )


# ==========================================================
# UI
# ==========================================================
st.title("🧪 Debug Pipeline FV Engine")

if st.button("Ejecutar pipeline"):

    clear_trace()

    deps = construir_dependencias()
    deps = instrument_dependencies(deps)

    datos = construir_datos_demo()

    try:
        resultado = ejecutar_estudio(datos, deps)
        st.success("Pipeline ejecutado")

        st.write("Resultado final:", resultado)

    except Exception as e:
        st.error(str(e))


# ==========================================================
# MOSTRAR TRACE
# ==========================================================
trace = get_trace()

if trace:

    st.markdown("## 🔍 Pipeline FV")

    for step in trace:

        with st.expander(f"🔹 {step['funcion']}", expanded=True):

            st.markdown("**Entrada**")
            st.json(step["entrada"])

            if step["error"]:
                st.error(step["error"])
            else:
                st.markdown("**Salida**")
                st.json(step["salida"])

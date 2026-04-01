import streamlit as st

from core.aplicacion.dependencias import construir_dependencias
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.dominio.modelo import Datosproyecto


# ==========================================================
# DATOS DEMO (SIN TRACE)
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
# UI SIMPLE
# ==========================================================
st.title("⚡ Test Pipeline FV (SIN TRACE)")

if st.button("Ejecutar"):

    deps = construir_dependencias()
    datos = construir_datos_demo()

    try:
        resultado = ejecutar_estudio(datos, deps)

        st.success("OK")

        st.write("Resultado:")
        st.write(resultado)

    except Exception as e:
        st.error(f"Error: {e}")

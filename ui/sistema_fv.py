from __future__ import annotations
from typing import List, Tuple
import streamlit as st

_MESES = ["Ene","Feb","Mar","Abr","May","Jun",
          "Jul","Ago","Sep","Oct","Nov","Dic"]


def _defaults(ctx):
    if not ctx.sistema_fv:
        ctx.sistema_fv = {
            "modo_sizing": "offset",
            "offset_pct": 80.0,
            "kwp_objetivo": None,
            "kwp_limite": 0.0,
            "produccion_base": 145.0,
            "perdidas_pct": 14.0,
            "factores_fv_12m": [1.0]*12,
            "orientacion": "sur",
            "inclinacion_deg": 15.0,
        }


def render(ctx):
    _defaults(ctx)
    s = ctx.sistema_fv

    st.markdown("### Sistema Fotovoltaico")


def validar(ctx) -> Tuple[bool, List[str]]:
    e=[]
    s = ctx.sistema_fv

    if s["modo_sizing"]=="offset" and s.get("offset_pct",0)<=0:
        e.append("Offset inválido.")

    if s["modo_sizing"]=="kwp_fijo" and not s.get("kwp_objetivo"):
        e.append("Ingrese potencia objetivo.")

    if s["produccion_base"]<=0:
        e.append("Producción base inválida.")

    return len(e)==0, e

    # ======================
    # MODO DE SIZING
    # ======================
    modo = st.radio(
        "Modo de dimensionamiento",
        options=["offset","kwp_fijo","limite"],
        format_func=lambda x: {
            "offset":"Autoconsumo (% consumo)",
            "kwp_fijo":"Potencia fija (kWp)",
            "limite":"Límite máximo del sitio"
        }[x]
    )

    s["modo_sizing"] = modo

    col1, col2 = st.columns(2)

    if modo == "offset":
        with col1:
            s["offset_pct"] = st.slider(
                "Cobertura del consumo (%)",
                10,120,
                int(s.get("offset_pct",80)),
                step=5
            )

    elif modo == "kwp_fijo":
        with col1:
            s["kwp_objetivo"] = st.number_input(
                "Potencia objetivo (kWp)",
                min_value=0.5,
                step=0.5,
                value=float(s.get("kwp_objetivo") or 5.0)
            )

    elif modo == "limite":
        with col1:
            s["kwp_limite"] = st.number_input(
                "Potencia máxima disponible (kWp)",
                min_value=0.5,
                step=0.5,
                value=float(s.get("kwp_limite",5.0))
            )

    # ======================
    # SUPUESTOS FV
    # ======================
    st.markdown("#### Supuestos energéticos")

    a,b,c = st.columns(3)

    with a:
        s["produccion_base"] = st.number_input(
            "Producción base (kWh/kWp·mes)",
            50.0,250.0,
            value=float(s.get("produccion_base",145.0))
        )

    with b:
        s["perdidas_pct"] = st.number_input(
            "Pérdidas (%)",
            0.0,30.0,
            value=float(s.get("perdidas_pct",14.0))
        )

    with c:
        pr = 1 - s["perdidas_pct"]/100
        st.metric("PR estimado", f"{pr:.2f}")

    # ======================
    # FACTORES MENSUALES
    # ======================
    st.markdown("#### Estacionalidad FV")

    f = s["factores_fv_12m"]

    for fila in range(3):
        cols = st.columns(4)
        for j in range(4):
            i = fila*4+j
            with cols[j]:
                f[i] = st.number_input(
                    _MESES[i],
                    0.6,1.4,
                    value=float(f[i]),
                    step=0.02,
                    key=f"fvf_{i}"
                )

    s["factores_fv_12m"] = f

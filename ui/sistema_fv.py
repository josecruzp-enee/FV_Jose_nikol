# ui/sistema_fv.py
from __future__ import annotations
from typing import List, Tuple, Optional

import streamlit as st

_MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]


def _asegurar_defaults(ctx) -> None:
    if not ctx.sistema_fv:
        ctx.sistema_fv = {
            "modalidad": "autoconsumo",
            "objetivo_offset_pct": 80.0,
            "kwp_objetivo": None,
            "limit_kwp": 0.0,
            "produccion_base_kwh_kwp_mes": 145.0,
            "factores_fv_12m": [1.0] * 12,
            "perdidas_pct": 14.0,
            "orientacion": "sur",
            "inclinacion_deg": 15.0,
        }


def render(ctx) -> None:
    _asegurar_defaults(ctx)

    st.markdown("### Sistema FV")

    s = ctx.sistema_fv

    col1, col2, col3 = st.columns(3)
    with col1:
        s["modalidad"] = st.selectbox(
            "Modalidad",
            options=["autoconsumo"],
            index=0,
            help="Por ahora: autoconsumo. Luego: total/mixto.",
        )
    with col2:
        s["objetivo_offset_pct"] = st.slider(
            "Objetivo de cobertura (%)",
            min_value=10,
            max_value=120,
            value=int(float(s.get("objetivo_offset_pct", 80.0))),
            step=5,
            help="Ej: 80% cubre la mayor parte del consumo sin sobredimensionar.",
        )
    with col3:
        s["limit_kwp"] = st.number_input(
            "Límite de potencia (kWp) (0 = sin límite)",
            min_value=0.0,
            step=0.5,
            value=float(s.get("limit_kwp", 0.0) or 0.0),
        )

    st.markdown("#### Supuestos de producción y pérdidas")

    a, b, c = st.columns(3)
    with a:
        s["produccion_base_kwh_kwp_mes"] = st.number_input(
            "Producción base (kWh/kWp·mes)",
            min_value=50.0,
            max_value=250.0,
            step=1.0,
            value=float(s.get("produccion_base_kwh_kwp_mes", 145.0)),
            help="Valor base por ubicación/irradiación. Luego lo refinamos por zona.",
        )
    with b:
        s["perdidas_pct"] = st.number_input(
            "Pérdidas globales (%)",
            min_value=0.0,
            max_value=30.0,
            step=0.5,
            value=float(s.get("perdidas_pct", 14.0)),
            help="Incluye temperatura, mismatch, inversor, cables, suciedad, etc.",
        )
    with c:
        pr = (1.0 - float(s["perdidas_pct"]) / 100.0)
        st.metric("PR estimado", f"{pr:.2f}")

    st.markdown("#### Estacionalidad (factor mensual)")
    factores = list(s.get("factores_fv_12m", [1.0] * 12))
    if len(factores) != 12:
        factores = [1.0] * 12

    # inputs 4x3
    for fila in range(3):
        cols = st.columns(4)
        for j in range(4):
            i = fila * 4 + j
            with cols[j]:
                factores[i] = st.number_input(
                    f"{_MESES[i]}",
                    min_value=0.60,
                    max_value=1.40,
                    step=0.02,
                    value=float(factores[i] or 1.0),
                    key=f"fv_factor_{i}",
                    help="1.00 = mes promedio. <1 menor producción, >1 mayor.",
                )

    s["factores_fv_12m"] = factores

    st.markdown("#### Referencia geométrica (no bloqueante)")
    g1, g2 = st.columns(2)
    with g1:
        s["orientacion"] = st.selectbox(
            "Orientación (referencial)",
            options=["sur", "sureste", "suroeste", "este", "oeste", "norte"],
            index=["sur","sureste","suroeste","este","oeste","norte"].index(str(s.get("orientacion","sur"))),
        )
    with g2:
        s["inclinacion_deg"] = st.number_input(
            "Inclinación (°) (referencial)",
            min_value=0.0,
            max_value=45.0,
            step=1.0,
            value=float(s.get("inclinacion_deg", 15.0)),
        )

    ctx.sistema_fv = s


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    s = ctx.sistema_fv or {}

    # objetivo
    try:
        offset = float(s.get("objetivo_offset_pct", 0.0))
    except Exception:
        offset = 0.0
    if offset <= 0:
        errores.append("Objetivo de cobertura inválido.")

    # producción base
    try:
        prod = float(s.get("produccion_base_kwh_kwp_mes", 0.0))
    except Exception:
        prod = 0.0
    if prod <= 0:
        errores.append("Producción base inválida (kWh/kWp·mes).")

    # pérdidas
    try:
        perd = float(s.get("perdidas_pct", -1.0))
    except Exception:
        perd = -1.0
    if perd < 0 or perd > 30:
        errores.append("Pérdidas globales deben estar entre 0% y 30%.")

    # factores 12m
    f = s.get("factores_fv_12m", [])
    if not isinstance(f, list) or len(f) != 12:
        errores.append("Factores FV: deben ser 12 valores (Ene–Dic).")
    else:
        try:
            fvals = [float(x) for x in f]
            if any(v <= 0 for v in fvals):
                errores.append("Factores FV inválidos: no se permiten ceros/negativos.")
        except Exception:
            errores.append("Factores FV inválidos: revise que sean numéricos.")

    return (len(errores) == 0), errores

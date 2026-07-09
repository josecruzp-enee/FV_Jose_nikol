from __future__ import annotations

"""
PASO 1 — DATOS DEL CLIENTE
FV Engine
"""

from typing import List, Tuple
import streamlit as st


# ==========================================================
# Render UI
# ==========================================================

def render(ctx) -> None:

    st.markdown("### Datos del cliente")

    sf = st.session_state

    # defaults
    sf.setdefault("cliente_nombre", "Cliente Demo")
    sf.setdefault("cliente_ubicacion", "Ciudad")
    sf.setdefault("cliente_email", "correo@demo.com")
    sf.setdefault("cliente_lat", 15.8)
    sf.setdefault("cliente_lon", -87.2)

    sf.setdefault("usa_financiamiento", True)
    sf.setdefault("costo_usd_kwp", 1200.0)
    sf.setdefault("tcambio", 26.75)
    sf.setdefault("prima_pct_ui", 10.0)
    sf.setdefault("tasa_anual_ui", 19.5)
    sf.setdefault("plazo_anios", 7)

    # asegurar diccionarios
    if not hasattr(ctx, "datos_cliente") or not isinstance(ctx.datos_cliente, dict):
        ctx.datos_cliente = {}

    if not hasattr(ctx, "sistema_fv") or not isinstance(ctx.sistema_fv, dict):
        ctx.sistema_fv = {}

    # inputs cliente
    cliente = st.text_input("Nombre del cliente", key="cliente_nombre")
    ubicacion = st.text_input("Ubicación", key="cliente_ubicacion")
    email = st.text_input("Email (opcional)", key="cliente_email")

    col1, col2 = st.columns(2)

    with col1:
        lat = st.number_input("Latitud", key="cliente_lat", format="%.6f")

    with col2:
        lon = st.number_input("Longitud", key="cliente_lon", format="%.6f")

    st.markdown("### Escenario económico")

    costo_usd_kwp = st.number_input(
        "Costo instalado (USD/kWp)",
        min_value=0.0,
        value=float(sf["costo_usd_kwp"]),
        step=50.0,
        key="costo_usd_kwp",
    )

    tcambio = st.number_input(
        "Tipo de cambio (L/USD)",
        min_value=0.0,
        value=float(sf["tcambio"]),
        step=0.01,
        key="tcambio",
    )

    usa_financiamiento = st.checkbox(
        "El cliente financiará el proyecto",
        value=bool(sf["usa_financiamiento"]),
        key="usa_financiamiento",
    )

    if usa_financiamiento:
        prima_pct_ui = st.number_input(
            "Prima (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(sf["prima_pct_ui"]),
            step=1.0,
            key="prima_pct_ui",
        )

        tasa_anual_ui = st.number_input(
            "Tasa anual (%)",
            min_value=0.0,
            value=float(sf["tasa_anual_ui"]),
            step=0.5,
            key="tasa_anual_ui",
        )

        plazo_anios = st.number_input(
            "Plazo (años)",
            min_value=1,
            value=int(sf["plazo_anios"]),
            step=1,
            key="plazo_anios",
        )

        prima_pct = float(prima_pct_ui) / 100.0
        tasa_anual = float(tasa_anual_ui) / 100.0
        porcentaje_financiado = 1.0 - prima_pct

    else:
        prima_pct = 1.0
        tasa_anual = 0.0
        plazo_anios = 1
        porcentaje_financiado = 0.0

    # guardar cliente
    ctx.datos_cliente.update({
        "cliente": cliente.strip(),
        "ubicacion": ubicacion.strip(),
        "email": email.strip(),
        "lat": float(lat),
        "lon": float(lon),
    })

    # guardar también global por compatibilidad
    ctx.lat = float(lat)
    ctx.lon = float(lon)

    # guardar económico
    ctx.sistema_fv["costo_usd_kwp"] = float(costo_usd_kwp)
    ctx.sistema_fv["tcambio"] = float(tcambio)
    ctx.sistema_fv["usa_financiamiento"] = bool(usa_financiamiento)
    ctx.sistema_fv["prima_pct"] = float(prima_pct)
    ctx.sistema_fv["tasa_anual"] = float(tasa_anual)
    ctx.sistema_fv["plazo_anios"] = int(plazo_anios)
    ctx.sistema_fv["porcentaje_financiado"] = float(porcentaje_financiado)

    # compatibilidad legacy
    ctx.costo_usd_kwp = float(costo_usd_kwp)
    ctx.tcambio = float(tcambio)
    ctx.prima_pct = float(prima_pct)
    ctx.tasa_anual = float(tasa_anual)
    ctx.plazo_anios = int(plazo_anios)
    ctx.porcentaje_financiado = float(porcentaje_financiado)

# ==========================================================
# Validación
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores: List[str] = []

    cliente = str(ctx.datos_cliente.get("cliente", "")).strip()
    ubicacion = str(ctx.datos_cliente.get("ubicacion", "")).strip()
    email = str(ctx.datos_cliente.get("email", "")).strip()

    lat = float(getattr(ctx, "lat", 0))
    lon = float(getattr(ctx, "lon", 0))

    if not cliente:
        errores.append("Ingrese el nombre del cliente.")

    if not ubicacion:
        errores.append("Ingrese la ubicación.")

    # validación simple de email
    if email:
        if "@" not in email or "." not in email.split("@")[-1]:
            errores.append("Email inválido (revise el formato).")

    # 🔥 VALIDACIÓN NUEVA (evitar PVGIS error)
    if lat == 0 and lon == 0:
        errores.append("Debe ingresar coordenadas válidas (lat/lon).")

    return (len(errores) == 0), errores

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

    # ------------------------------------------------------
    # VALORES POR DEFECTO (SOLO PRIMERA VEZ)
    # ------------------------------------------------------
    sf.setdefault("cliente_nombre", "Cliente Demo")
    sf.setdefault("cliente_ubicacion", "Ciudad")
    sf.setdefault("cliente_email", "correo@demo.com")
    st.markdown("### Escenario económico")

    sf.setdefault("usa_financiamiento", True)
    sf.setdefault("costo_usd_kwp", 1200.0)
    sf.setdefault("tcambio", 26.75)
    sf.setdefault("prima_pct_ui", 10.0)
    sf.setdefault("tasa_anual_ui", 19.5)
    sf.setdefault("plazo_anios", 7)

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

        ctx.modo_financiamiento = "credito_con_prima"
        ctx.prima_pct = float(prima_pct_ui) / 100.0
        ctx.porcentaje_financiado = 1.0 - ctx.prima_pct
        ctx.tasa_anual = float(tasa_anual_ui) / 100.0
        ctx.plazo_anios = int(plazo_anios)
        ctx.nombre_financiamiento = "Crédito bancario"
        ctx.entidad_financiera = "Banco"

    else:
        ctx.modo_financiamiento = "contado"
        ctx.prima_pct = 1.0
        ctx.porcentaje_financiado = 0.0
        ctx.tasa_anual = 0.0
        ctx.plazo_anios = 0
        ctx.nombre_financiamiento = "Pago de contado"
        ctx.entidad_financiera = "Cliente"

        ctx.costo_usd_kwp = float(costo_usd_kwp)
        ctx.tcambio = float(tcambio)
        # 🔥 NUEVO: coordenadas
        sf.setdefault("cliente_lat", 15.8)
        sf.setdefault("cliente_lon", -87.2)

        ctx.datos_cliente = {
        "cliente": cliente,
        "ubicacion": ubicacion,
        "email": email,
        "lat": float(sf["cliente_lat"]),
        "lon": float(sf["cliente_lon"]),
    }

    ctx.sistema_fv["costo_usd_kwp"] = float(costo_usd_kwp)
    ctx.sistema_fv["tcambio"] = float(tcambio)
    
    ctx.sistema_fv["usa_financiamiento"] = bool(sf["usa_financiamiento"])
    ctx.sistema_fv["prima_pct"] = float(sf["prima_pct_ui"])

    ctx.sistema_fv["tasa_anual"] = float(sf["tasa_anual_ui"]) / 100.0
    ctx.sistema_fv["plazo_anios"] = int(sf["plazo_anios"])

    if sf["usa_financiamiento"]:
        ctx.sistema_fv["porcentaje_financiado"] = (
            1.0 - float(sf["prima_pct_ui"]) / 100.0
        )
    else:
        ctx.sistema_fv["porcentaje_financiado"] = 0.0
    # ------------------------------------------------------
    # INPUTS
    # ------------------------------------------------------
    cliente = st.text_input(
        "Nombre del cliente",
        key="cliente_nombre",
    )

    ubicacion = st.text_input(
        "Ubicación",
        key="cliente_ubicacion",
    )

    email = st.text_input(
        "Email (opcional)",
        key="cliente_email",
    )

    # 🔥 NUEVO: coordenadas visibles (puedes ocultarlas luego)
    col1, col2 = st.columns(2)

    with col1:
        lat = st.number_input(
            "Latitud",
            key="cliente_lat",
            format="%.6f"
        )

    with col2:
        lon = st.number_input(
            "Longitud",
            key="cliente_lon",
            format="%.6f"
        )

    # ------------------------------------------------------
    # GUARDAR EN CONTEXTO
    # ------------------------------------------------------
    ctx.datos_cliente["cliente"] = cliente.strip()
    ctx.datos_cliente["ubicacion"] = ubicacion.strip()
    ctx.datos_cliente["email"] = email.strip()

    # 🔥 CLAVE: guardar coordenadas en ctx global
    ctx.lat = float(lat)
    ctx.lon = float(lon)


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

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

    # 🔥 NUEVO: coordenadas
    sf.setdefault("cliente_lat", 15.8)
    sf.setdefault("cliente_lon", -87.2)

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

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

    # ------------------------------------------------------
    # GUARDAR EN CONTEXTO
    # ------------------------------------------------------
    ctx.datos_cliente["cliente"] = cliente.strip()
    ctx.datos_cliente["ubicacion"] = ubicacion.strip()
    ctx.datos_cliente["email"] = email.strip()


# ==========================================================
# Validación
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores: List[str] = []

    cliente = str(ctx.datos_cliente.get("cliente", "")).strip()
    ubicacion = str(ctx.datos_cliente.get("ubicacion", "")).strip()
    email = str(ctx.datos_cliente.get("email", "")).strip()

    if not cliente:
        errores.append("Ingrese el nombre del cliente.")

    if not ubicacion:
        errores.append("Ingrese la ubicación.")

    # validación simple de email
    if email:
        if "@" not in email or "." not in email.split("@")[-1]:
            errores.append("Email inválido (revise el formato).")

    return (len(errores) == 0), errores

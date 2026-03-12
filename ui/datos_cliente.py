from __future__ import annotations

"""
PASO 1 — DATOS DEL CLIENTE
FV Engine

Este módulo representa el primer paso del wizard.

Responsabilidades
-----------------

- capturar datos básicos del cliente
- almacenarlos en ctx.datos_cliente
- validar los campos requeridos

Este módulo pertenece a la capa UI.
No contiene lógica de negocio.
"""

from typing import List, Tuple
import streamlit as st


# ==========================================================
# Render UI
# ==========================================================

def render(ctx) -> None:

    st.markdown("### Datos del cliente")

    cliente = st.text_input(
        "Nombre del cliente",
        value=str(ctx.datos_cliente.get("cliente", "")),
        key="cliente_nombre",
    )

    ubicacion = st.text_input(
        "Ubicación",
        value=str(ctx.datos_cliente.get("ubicacion", "")),
        key="cliente_ubicacion",
    )

    email = st.text_input(
        "Email (opcional)",
        value=str(ctx.datos_cliente.get("email", "")),
        key="cliente_email",
    )

    # guardar en contexto
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

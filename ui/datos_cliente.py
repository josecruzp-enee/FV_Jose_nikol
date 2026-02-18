# ui/datos_cliente.py
from __future__ import annotations
from typing import List, Tuple

import streamlit as st


def render(ctx) -> None:
    st.markdown("### Datos del cliente")

    cliente = st.text_input(
        "Nombre del cliente",
        value=str(ctx.datos_cliente.get("cliente", "")),
    )
    ubicacion = st.text_input(
        "Ubicación",
        value=str(ctx.datos_cliente.get("ubicacion", "")),
    )
    email = st.text_input(
        "Email (opcional)",
        value=str(ctx.datos_cliente.get("email", "")),
    )

    # persistencia en ctx
    ctx.datos_cliente["cliente"] = cliente
    ctx.datos_cliente["ubicacion"] = ubicacion
    ctx.datos_cliente["email"] = email


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []

    cliente = str(ctx.datos_cliente.get("cliente", "")).strip()
    ubicacion = str(ctx.datos_cliente.get("ubicacion", "")).strip()
    email = str(ctx.datos_cliente.get("email", "")).strip()

    if not cliente:
        errores.append("Ingrese el nombre del cliente.")
    if not ubicacion:
        errores.append("Ingrese la ubicación.")

    # email: solo si lo ingresan
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        errores.append("Email inválido (revise el formato).")

    return (len(errores) == 0), errores

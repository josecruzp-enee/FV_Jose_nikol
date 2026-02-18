# ui/datos_cliente.py
from __future__ import annotations
from typing import List, Tuple

import streamlit as st

def render(ctx) -> None:
    st.markdown("### Datos del cliente")
    ctx.datos_cliente["cliente"] = st.text_input("Nombre del cliente", value=ctx.datos_cliente.get("cliente",""))
    ctx.datos_cliente["ubicacion"] = st.text_input("Ubicación", value=ctx.datos_cliente.get("ubicacion",""))
    ctx.datos_cliente["email"] = st.text_input("Email (opcional)", value=ctx.datos_cliente.get("email",""))

def validar(ctx) -> Tuple[bool, List[str]]:
    errores = []
    if not ctx.datos_cliente.get("cliente"):
        errores.append("Ingrese el nombre del cliente.")
    if not ctx.datos_cliente.get("ubicacion"):
        errores.append("Ingrese la ubicación.")
    return (len(errores) == 0), errores

from __future__ import annotations

from typing import Any

import streamlit as st


def render(ctx: Any):
    """
    Render de ingeniería eléctrica (corregido)

    ✔ NO usa resultado.sistema_fv (no existe en ResultadoProyecto)
    ✔ Usa ctx como fuente de verdad
    ✔ Evita AttributeError
    """

    resultado = ctx.get("resultado")

    if resultado is None:
        st.error("No hay resultado disponible")
        return

    sistema_fv = ctx.get("sistema_fv")

    if resultado.sizing:
        _mostrar_sizing(resultado.sizing, sistema_fv)

    if resultado.paneles:
        _mostrar_paneles(resultado.paneles)

    if resultado.energia:
        _mostrar_energia(resultado.energia)

    if getattr(resultado, "electrical", None):
        _mostrar_electrical(resultado.electrical)

    if getattr(resultado, "financiero", None):
        _mostrar_finanzas(resultado.financiero)


# ==========================================================
# SECCIONES
# ==========================================================
def _mostrar_sizing(sizing: Any, sistema_fv: Any):

    st.markdown("### 📐 Sizing del sistema FV")

    if sizing is None:
        st.warning("Sizing no disponible")
        return

    col1, col2, col3 = st.columns(3)

    col1.metric("Paneles", getattr(sizing, "n_paneles", 0))
    col2.metric("Potencia DC (kWp)", round(getattr(sizing, "kw_dc", 0.0), 2))
    col3.metric("Potencia AC (kW)", round(getattr(sizing, "kw_ac", 0.0), 2))

    if sistema_fv:
        sf = _to_dict(sistema_fv)

        if sf.get("usar_zonas"):
            st.markdown("#### 🔀 Configuración multizona")

            for i, z in enumerate(sf.get("zonas", []), start=1):
                z = _to_dict(z)

                if "n_paneles" in z:
                    st.write(f"Zona {i}: {z.get('n_paneles')} paneles")
                else:
                    st.write(f"Zona {i}: {z.get('area')} m²")


def _mostrar_paneles(paneles: Any):
    st.markdown("### 🔋 Paneles")

    if paneles is None:
        st.warning("Paneles no disponibles")
        return

    st.json(paneles)


def _mostrar_energia(energia: Any):
    st.markdown("### ⚡ Energía")

    if energia is None:
        st.warning("Energía no disponible")
        return

    st.json(energia)


def _mostrar_electrical(electrical: Any):
    st.markdown("### ⚠ Ingeniería eléctrica")

    if electrical is None:
        st.warning("Electrical no disponible")
        return

    st.json(electrical)


def _mostrar_finanzas(finanzas: Any):
    st.markdown("### 💰 Finanzas")

    if finanzas is None:
        st.warning("Finanzas no disponibles")
        return

    st.json(finanzas)


# ==========================================================
# UTILIDAD
# ==========================================================
def _to_dict(obj: Any):

    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    if hasattr(obj, "__dict__"):
        return vars(obj)

    return {}

from __future__ import annotations

from typing import Any, Dict

import streamlit as st


# ==========================================================
# RENDER
# ==========================================================
def render(ctx: Any):
    """
    Render de ingeniería eléctrica

    ✔ Usa ctx como fuente de verdad
    ✔ Evita acceso a atributos inexistentes
    """

    resultado = ctx.get("resultado")

    if resultado is None:
        st.error("No hay resultado disponible")
        return

    sistema_fv = ctx.get("sistema_fv")

    if getattr(resultado, "sizing", None):
        _mostrar_sizing(resultado.sizing, sistema_fv)

    if getattr(resultado, "paneles", None):
        _mostrar_paneles(resultado.paneles)

    if getattr(resultado, "energia", None):
        _mostrar_energia(resultado.energia)

    if getattr(resultado, "electrical", None):
        _mostrar_electrical(resultado.electrical)

    if getattr(resultado, "financiero", None):
        _mostrar_finanzas(resultado.financiero)


# ==========================================================
# VALIDAR (REQUERIDO POR WIZARD)
# ==========================================================
def validar(ctx: Any) -> bool:
    """
    Validación del paso de ingeniería eléctrica

    ✔ Siempre existe (evita AttributeError)
    ✔ Solo valida existencia de resultado
    """

    if ctx is None:
        return False

    resultado = ctx.get("resultado")

    if resultado is None:
        return False

    if not getattr(resultado, "sizing", None):
        return False

    return True


# ==========================================================
# SECCIONES
# ==========================================================
def _mostrar_sizing(sizing: Any, sistema_fv: Any):

    st.markdown("### 📐 Sizing del sistema FV")

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
    st.json(paneles)


def _mostrar_energia(energia: Any):
    st.markdown("### ⚡ Energía")
    st.json(energia)


def _mostrar_electrical(electrical: Any):
    st.markdown("### ⚠ Ingeniería eléctrica")
    st.json(electrical)


def _mostrar_finanzas(finanzas: Any):
    st.markdown("### 💰 Finanzas")
    st.json(finanzas)


# ==========================================================
# UTILIDAD
# ==========================================================
def _to_dict(obj: Any) -> Dict[str, Any]:

    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    if hasattr(obj, "__dict__"):
        return vars(obj)

    return {}

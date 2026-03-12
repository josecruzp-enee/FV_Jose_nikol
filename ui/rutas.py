from __future__ import annotations

"""
UTILIDADES DE RUTAS Y FORMATO
FV Engine

CAPA
----
UI / Infraestructura ligera

FRONTERA
--------
Entrada:
    nombre_carpeta (str)

Variables:
    base_dir
    out_dir
    charts_dir

Salida:
    Diccionario con rutas de salida

Este módulo NO depende de Streamlit ni del motor FV.
Solo gestiona rutas de archivos y formato visual.
"""

import os
from pathlib import Path
from typing import Dict


# ==========================================================
# BASE DEL PROYECTO
# ==========================================================

def base_dir_seguro() -> Path:
    """
    Devuelve una base estable del proyecto.

    Funciona correctamente en:
        • Spyder
        • Streamlit
        • Windows
        • Linux
    """

    try:
        # .../FV_Jose_nikol/
        return Path(__file__).resolve().parents[1]

    except Exception:

        return Path(os.getcwd()).resolve()


# ==========================================================
# PREPARAR CARPETAS DE SALIDA
# ==========================================================

def preparar_salida(nombre_carpeta: str = "salidas") -> Dict[str, str]:

    base = base_dir_seguro()

    out_dir = base / nombre_carpeta
    out_dir.mkdir(parents=True, exist_ok=True)

    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    return {

        # directorios
        "out_dir": str(out_dir),
        "charts_dir": str(charts_dir),

        # charts
        "chart_energia": str(charts_dir / "fv_chart_energia.png"),
        "chart_neto": str(charts_dir / "fv_chart_neto.png"),
        "chart_generacion": str(charts_dir / "fv_chart_generacion.png"),

        # layout
        "layout_paneles": str(out_dir / "fv_layout_paneles.png"),

        # pdf final
        "pdf_path": str(out_dir / "reporte_evaluacion_fv.pdf"),
    }


# ==========================================================
# FORMATOS VISUALES
# ==========================================================

def money_L(x: float, dec: int = 2) -> str:

    try:
        v = float(x)

    except Exception:
        v = 0.0

    fmt = f"{{:,.{int(dec)}f}}"

    return f"L {fmt.format(v)}"


def num(x: float, nd: int = 2) -> str:

    try:
        v = float(x)
    except Exception:
        v = 0.0

    return f"{v:,.{nd}f}"

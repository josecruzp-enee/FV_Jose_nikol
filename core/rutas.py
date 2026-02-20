# nucleo/rutas.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


def base_dir_seguro() -> Path:
    """Devuelve una base estable en Spyder / Windows / Streamlit."""
    try:
        return Path(__file__).resolve().parents[1]  # .../FV_Jose_nikol/
    except Exception:
        return Path(os.getcwd()).resolve()


def preparar_salida(nombre_carpeta: str = "salidas") -> Dict[str, str]:

    base = base_dir_seguro()
    out_dir = base / nombre_carpeta
    out_dir.mkdir(parents=True, exist_ok=True)

    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    return {
        # carpetas
        "out_dir": str(out_dir),
        "charts_dir": str(charts_dir),

        # charts
        "chart_energia": str(charts_dir / "fv_chart_energia.png"),
        "chart_neto": str(charts_dir / "fv_chart_neto.png"),
        "chart_generacion": str(charts_dir / "fv_chart_generacion.png"),

        # layout
        "layout_paneles": str(out_dir / "fv_layout_paneles.png"),

        # pdf
        "pdf_path": str(out_dir / "reporte_evaluacion_fv.pdf"),
    }



def money_L(x: float, dec: int = 2) -> str:
    try:
        v = float(x)
    except Exception:
        v = 0.0
    fmt = f"{{:,.{int(dec)}f}}"
    return f"L {fmt.format(v)}"


def num(x: float, nd: int = 2) -> str:
    return f"{x:,.{nd}f}"

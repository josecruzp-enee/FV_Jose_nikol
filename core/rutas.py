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

    return {
        "out_dir": str(out_dir),
        "chart_energia": str(out_dir / "fv_chart_energia.png"),
        "chart_neto": str(out_dir / "fv_chart_neto.png"),
        "chart_generacion": str(out_dir / "fv_chart_generacion.png"),
        "layout_paneles": str(out_dir / "fv_layout_paneles.png"),
        "pdf": str(out_dir / "reporte_evaluacion_fv.pdf"),
    }


def money_L(x: float) -> str:
    return f"L {x:,.2f}"


def num(x: float, nd: int = 2) -> str:
    return f"{x:,.{nd}f}"

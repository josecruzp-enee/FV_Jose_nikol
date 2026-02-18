
# reportes/generar_pdf_profesional.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

def generar_pdf_profesional(resultado: Dict[str, Any], datos: Any, paths: Dict[str, Any]) -> str:
    """
    Stub temporal: genera un "PDF" placeholder (txt con extensión .pdf si no hay reportlab armado).
    Retorna la ruta del archivo creado para que Streamlit pueda ofrecer descarga.
    """
    # intenta deducir ruta salida
    out = paths.get("pdf") or paths.get("pdf_path") or paths.get("pdf_out") or "salidas/reporte_evaluacion_fv.pdf"
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # placeholder: crea un archivo simple (si reportlab no está implementado aún)
    contenido = [
        "REPORTE FV (placeholder)",
        "",
        f"Cliente: {getattr(datos, 'cliente', '')}",
        f"Ubicación: {getattr(datos, 'ubicacion', '')}",
        "",
        "Este archivo es un placeholder mientras se estabiliza el generador PDF.",
    ]
    out_path.write_text("\n".join(contenido), encoding="utf-8")

    return str(out_path)



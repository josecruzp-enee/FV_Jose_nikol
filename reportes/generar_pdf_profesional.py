# reportes/generar_pdf_profesional.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter

from .styles import pdf_palette, pdf_styles

# 🔥 BLOQUES MIGRADOS
from .bloques.resumen_ejecutivo import build_resumen_ejecutivo
from .bloques.analisis_energetico import build_analisis_energetico

# 🔴 TEMPORALES (AÚN NO MIGRADOS)
from .page_3 import build_page_3
from .page_4 import build_page_4
from .page_5 import build_page_5


# ==========================================================
# VALIDAR RUTA DE PDF
# ==========================================================

def _ensure_pdf_path(paths: Dict[str, Any]) -> str:
    """
    Garantiza que exista una ruta válida para generar el PDF.
    """

    if not isinstance(paths, dict):
        raise TypeError("`paths` debe ser dict.")

    pdf_path = paths.get("pdf_path")

    if not pdf_path:

        out_dir = (
            paths.get("out_dir")
            or paths.get("base_dir")
            or "salidas"
        )

        pdf_path = str(Path(out_dir) / "reporte_evaluacion_fv.pdf")

        paths["pdf_path"] = pdf_path

    p = Path(str(pdf_path))
    p.parent.mkdir(parents=True, exist_ok=True)

    return str(p)


# ==========================================================
# GENERADOR PRINCIPAL DE PDF
# ==========================================================

def generar_pdf_profesional(
    resultado_proyecto: Any,
    datos: Any,
    paths: Dict[str, Any],
) -> str:

    """
    Genera el reporte PDF profesional del estudio FV.
    """

    # ======================================================
    # CONFIGURACIÓN PDF
    # ======================================================

    pal = pdf_palette()
    styles = pdf_styles()

    pdf_path = _ensure_pdf_path(paths)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
    )

    story: List = []

    content_w = doc.width

    # ======================================================
    # DEBUG OPCIONAL
    # ======================================================

    try:
        nec_debug = getattr(resultado_proyecto, "nec", None)
    except Exception:
        nec_debug = None

    if nec_debug:
        print("\n========== DEBUG NEC ==========")
        print(nec_debug)
        print("================================\n")

    # ======================================================
    # BLOQUES DEL REPORTE
    # ======================================================

    bloques = [

        # 🔥 BLOQUES YA MIGRADOS
        build_resumen_ejecutivo,
        build_analisis_energetico,

        # 🔴 BLOQUES PENDIENTES
        build_page_3,
        build_page_4,
        build_page_5,
    ]

    for bloque in bloques:

        try:

            story += bloque(
                resultado_proyecto,
                datos,
                paths,
                pal,
                styles,
                content_w,
            )

        except Exception as e:

            print(f"❌ Error en bloque {bloque.__name__}: {e}")

    # ======================================================
    # CONSTRUIR PDF
    # ======================================================

    doc.build(story)

    return str(pdf_path)

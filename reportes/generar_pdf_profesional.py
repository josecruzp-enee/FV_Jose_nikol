# reportes/generar_pdf_profesional.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from reportlab.platypus import (
    SimpleDocTemplate,
    PageBreak,
)
from reportlab.lib.pagesizes import letter

from .styles import pdf_palette, pdf_styles
from .bloques import BLOQUES_REPORTE


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

        pdf_path = str(
            Path(out_dir)
            / "reporte_evaluacion_fv.pdf"
        )

        paths["pdf_path"] = pdf_path

    p = Path(str(pdf_path))

    p.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return str(p)


# ==========================================================
# NORMALIZAR BLOQUE DEL REPORTE
# ==========================================================

def _normalizar_elementos_bloque(elementos) -> List:
    """
    Elimina únicamente los saltos de página ubicados al
    principio o al final de un bloque.

    Los saltos internos se conservan porque pueden separar
    tablas, gráficos o imágenes grandes.
    """

    if not elementos:
        return []

    elementos = list(elementos)

    while (
        elementos
        and isinstance(elementos[0], PageBreak)
    ):
        elementos.pop(0)

    while (
        elementos
        and isinstance(elementos[-1], PageBreak)
    ):
        elementos.pop()

    return elementos


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

    Cada bloque principal comienza en una nueva página.
    Los saltos internos de cada bloque se conservan.
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
        nec_debug = getattr(
            resultado_proyecto,
            "nec",
            None,
        )
    except Exception:
        nec_debug = None

    if nec_debug:
        print("\n========== DEBUG NEC ==========")
        print(nec_debug)
        print("================================\n")

    # ======================================================
    # ENSAMBLAJE DEL REPORTE
    # ======================================================

    bloques_agregados = 0

    for bloque in BLOQUES_REPORTE:

        try:
            elementos = bloque(
                resultado_proyecto,
                datos,
                paths,
                pal,
                styles,
                content_w,
            )

            elementos = _normalizar_elementos_bloque(
                elementos
            )

            if not elementos:
                continue

            # Un único salto entre bloques principales.
            if bloques_agregados > 0:
                story.append(PageBreak())

            story.extend(elementos)
            bloques_agregados += 1

        except Exception as e:
            raise Exception(
                f"❌ Error en bloque "
                f"{bloque.__name__}: {e}"
            ) from e

    # ======================================================
    # CONSTRUIR PDF
    # ======================================================

    doc.build(story)

    return str(pdf_path)

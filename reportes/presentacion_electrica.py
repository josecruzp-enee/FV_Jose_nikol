# reportes/generar_pdf_profesional.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter

from .styles import pdf_palette, pdf_styles

from .page_1 import build_page_1
from .page_2 import build_page_2
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

    Parámetros
    ----------
    resultado_proyecto :
        Resultado completo del orquestador (ResultadoProyecto o dict).

    datos :
        Datos del proyecto / cliente.

    paths :
        Diccionario de rutas generadas por el pipeline:
        - pdf_path
        - charts
        - layout_paneles
        - string_fv
        - etc.

    Retorna
    -------
    str
        Ruta del PDF generado.
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

    nec_debug = None

    try:
        nec_debug = resultado_proyecto.get("nec")
    except Exception:
        pass

    if nec_debug:
        print("\n========== DEBUG NEC ==========")
        print(nec_debug)
        print("================================\n")

    # ======================================================
    # PÁGINAS DEL REPORTE
    # ======================================================

    paginas = [

        build_page_1,
        build_page_2,
        build_page_3,
        build_page_4,
        build_page_5,

    ]

    for pagina in paginas:

        try:

            story += pagina(
                resultado_proyecto,
                datos,
                paths,
                pal,
                styles,
                content_w,
            )

        except Exception as e:

            print(f"Error generando página {pagina.__name__}: {e}")

    # ======================================================
    # CONSTRUIR DOCUMENTO
    # ======================================================

    doc.build(story)

    return str(pdf_path)

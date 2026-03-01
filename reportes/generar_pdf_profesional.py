# reportes/generar_pdf_profesional.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter

from .styles import pdf_palette, pdf_styles
from .page_1 import build_page_1
from .page_2 import build_page_2
from .page_3 import build_page_3
from .page_4 import build_page_4
from .page_5 import build_page_5  # ✅ FIX: typo





def _ensure_pdf_path(paths: Dict[str, Any]) -> str:
    """
    Garantiza que exista paths["pdf_path"] y que su carpeta exista.
    """
    if not isinstance(paths, dict):
        raise TypeError("`paths` debe ser dict y contener 'pdf_path'.")

    pdf_path = paths.get("pdf_path")
    if not pdf_path:
        # fallback razonable si no viene definido
        out_dir = paths.get("out_dir") or paths.get("base_dir") or "salidas"
        pdf_path = str(Path(out_dir) / "reporte_evaluacion_fv.pdf")
        paths["pdf_path"] = pdf_path

    p = Path(str(pdf_path))
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


def generar_pdf_profesional(resultado_proyecto: dict, datos: Any, paths: Dict[str, Any]):
    """
    `resultado_proyecto` = objeto único del orquestador (ResultadoProyecto) o dict legacy.
    `datos` = Datosproyecto (o equivalente) para datos del cliente/inputs.
    `paths` = dict de rutas (pdf_path, charts_dir, layout_paneles, etc.)
    """
    pal = pdf_palette()
    styles = pdf_styles()

    pdf_path = _ensure_pdf_path(paths)

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)

    story = []
    content_w = doc.width  # ✅ se pasa a páginas (no deberían recalcularlo)

    # ✅ Compat: páginas actuales pueden seguir esperando dict plano
    resultado = resultado_proyecto

    story += build_page_1(resultado, datos, paths, pal, styles, content_w)
    story += build_page_2(resultado, datos, paths, pal, styles, content_w)
    story += build_page_3(resultado, datos, paths, pal, styles, content_w)
    story += build_page_4(resultado, datos, paths, pal, styles, content_w)
    story += build_page_5(resultado, datos, paths, pal, styles, content_w)

    doc.build(story)
    return str(pdf_path)

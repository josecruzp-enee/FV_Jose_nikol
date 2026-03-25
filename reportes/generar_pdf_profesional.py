# reportes/generar_pdf_profesional.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from reportlab.platypus import SimpleDocTemplate, Image
from reportlab.lib.pagesizes import letter

from .styles import pdf_palette, pdf_styles
from .page_1 import build_page_1
from .page_2 import build_page_2
from .page_3 import build_page_3
from .page_4 import build_page_4
from .page_5 import build_page_5

from dataclasses import asdict, is_dataclass

# 🔥 NUEVO: para escalar imágenes automáticamente
from PIL import Image as PILImage


# =========================
# 🛡️ FUNCIÓN ANTI-ERROR
# =========================
def safe_image(path, max_w=450, max_h=600):
    """
    Crea una imagen que SIEMPRE cabe en el PDF
    """
    try:
        pil = PILImage.open(path)
        w, h = pil.size

        ratio = min(max_w / w, max_h / h)

        img = Image(path)
        img.drawWidth = w * ratio
        img.drawHeight = h * ratio
        return img

    except Exception as e:
        print(f"⚠️ Error cargando imagen {path}: {e}")
        return None


def _ensure_pdf_path(paths: Dict[str, Any]) -> str:
    if not isinstance(paths, dict):
        raise TypeError("`paths` debe ser dict y contener 'pdf_path'.")

    pdf_path = paths.get("pdf_path")
    if not pdf_path:
        out_dir = paths.get("out_dir") or paths.get("base_dir") or "salidas"
        pdf_path = str(Path(out_dir) / "reporte_evaluacion_fv.pdf")
        paths["pdf_path"] = pdf_path

    p = Path(str(pdf_path))
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


def generar_pdf_profesional(resultado_proyecto: Any, datos: Any, paths: Dict[str, Any]):

    pal = pdf_palette()
    styles = pdf_styles()

    # =========================
    # CONVERTIR A DICT
    # =========================
    if is_dataclass(resultado_proyecto):
        resultado = asdict(resultado_proyecto)
    elif isinstance(resultado_proyecto, dict):
        resultado = resultado_proyecto
    else:
        resultado = dict(resultado_proyecto.__dict__)

    # =========================
    # DEBUG
    # =========================
    print("\n========== DEBUG PDF ==========")
    print(resultado.get("nec"))
    print("================================\n")

    pdf_path = _ensure_pdf_path(paths)

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)

    story = []
    content_w = doc.width

    # =========================
    # 🔥 PASAR safe_image A LAS PÁGINAS
    # =========================
    story += build_page_1(resultado, datos, paths, pal, styles, content_w, safe_image)
    story += build_page_2(resultado, datos, paths, pal, styles, content_w, safe_image)
    story += build_page_3(resultado, datos, paths, pal, styles, content_w, safe_image)
    story += build_page_4(resultado, datos, paths, pal, styles, content_w, safe_image)
    story += build_page_5(resultado, datos, paths, pal, styles, content_w, safe_image)

    doc.build(story)
    return str(pdf_path)

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter

from .styles import pdf_palette, pdf_styles
from .page_1 import build_page_1
from .page_2 import build_page_2
from .page_3 import build_page_3
from .page_4 import build_page_4
from .page_5 import build_page_5


def generar_pdf_profesional(resultado, datos, paths):

    pal = pdf_palette()
    styles = pdf_styles()

    doc = SimpleDocTemplate(
        str(paths["pdf_path"]),
        pagesize=letter
    )

    story = []

    content_w = doc.width
    story += build_page_1(resultado, datos, paths, pal, styles, content_w)
    story += build_page_2(resultado, datos, paths, pal, styles, content_w)
    story += build_page_3(resultado, datos, paths, pal, styles, content_w)
    story += build_page_4(resultado, datos, paths, pal, styles, content_w)
    story += build_page_5(resultado, datos, paths, pal, styles, content_w)


    doc.build(story)

    return paths["pdf_path"]

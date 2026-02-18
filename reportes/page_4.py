# reportes/pdf/page_4.py
from reportlab.platypus import Paragraph, Spacer, PageBreak


def build_page_4(resultado, datos, pal, styles):

    story = []

    story.append(Paragraph(
        "Impacto mensual estimado — Año 1",
        styles["Heading1"]
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(
        f"Ahorro anual estimado: {resultado.ahorro_anual_L:,.2f} L",
        styles["BodyText"]
    ))

    story.append(PageBreak())

    return story

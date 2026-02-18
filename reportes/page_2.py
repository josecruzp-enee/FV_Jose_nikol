# reportes/pdf/page_2.py
from reportlab.platypus import Paragraph, Spacer, PageBreak


def build_page_2(resultado, datos, pal, styles):

    story = []

    story.append(Paragraph(
        "Reporte de Demanda / Energía",
        styles["Heading1"]
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Comparación mensual consumo vs FV.",
        styles["BodyText"]
    ))

    story.append(PageBreak())

    return story

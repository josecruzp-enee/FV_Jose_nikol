# reportes/page_3.py
from reportlab.platypus import Paragraph, Spacer, PageBreak


def build_page_3(resultado, datos, pal, styles):

    story = []

    story.append(Paragraph(
        "Financiamiento — Evolución del préstamo",
        styles["Heading1"]
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(
        resultado['evaluacion']['tir']

        styles["BodyText"]
    ))

    story.append(PageBreak())

    return story

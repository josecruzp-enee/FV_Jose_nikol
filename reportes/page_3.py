# reportes/pdf/page_3.py
from reportlab.platypus import Paragraph, Spacer, PageBreak


def build_page_3(resultado, datos, pal, styles):

    story = []

    story.append(Paragraph(
        "Financiamiento — Evolución del préstamo",
        styles["Heading1"]
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(
        f"TIR estimada: {resultado.tir:.2f} %",
        styles["BodyText"]
    ))

    story.append(PageBreak())

    return story

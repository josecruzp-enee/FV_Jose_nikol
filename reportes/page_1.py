# reportes/pdf/page_1.py
from reportlab.platypus import Paragraph, Spacer, PageBreak


def build_page_1(resultado, datos, pal, styles):

    story = []

    story.append(Paragraph(
        "Reporte Ejecutivo — Evaluación Fotovoltaica",
        styles["Heading1"]
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(
        f"Cliente: {datos.cliente}",
        styles["BodyText"]
    ))

    story.append(Paragraph(
        f"Potencia propuesta: {resultado['sizing']['kwp_dc']:.2f} kWp",
        styles["BodyText"]
    ))

    story.append(PageBreak())

    return story

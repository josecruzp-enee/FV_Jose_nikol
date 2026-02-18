# reportes/pdf/page_5.py
from reportlab.platypus import Paragraph, Spacer


def build_page_5(resultado, datos, pal, styles):

    story = []

    story.append(Paragraph(
        "Propuesta Técnica",
        styles["Heading1"]
    ))

    story.append(Spacer(1, 12))

    story.append(Paragraph(
        f"Sistema FV estimado: {resultado.potencia_kwp:.2f} kWp",
        styles["BodyText"]
    ))

    return story

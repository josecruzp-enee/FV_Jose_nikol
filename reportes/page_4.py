# reportes/page_4.py
from reportlab.platypus import Paragraph, Spacer, PageBreak

def build_page_4(resultado, datos, paths, pal, styles):
    story = []

    story.append(Paragraph("Ahorros y comparación", styles["Title"]))
    story.append(Spacer(1, 10))

    tabla_12m = resultado.get("tabla_12m") or []
    ahorro_anual = sum(float(r.get("ahorro_L", 0.0)) for r in tabla_12m)

    story.append(Paragraph(f"Ahorro anual estimado: L {ahorro_anual:,.2f}", styles["BodyText"]))
    story.append(PageBreak())
    return story


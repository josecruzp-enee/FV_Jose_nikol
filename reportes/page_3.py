# reportes/page_3.py
from reportlab.platypus import Paragraph, Spacer, PageBreak


def build_page_3(resultado, datos, paths, pal, styles):
    story = []

    story.append(Paragraph("Finanzas (largo plazo)", styles["Title"]))
    story.append(Spacer(1, 10))

    fin = resultado.get("finanzas_lp") or {}

    irr = fin.get("irr", None)
    npv = fin.get("npv_L", None)
    pb = fin.get("payback_descontado_anios", None)

    # IRR (TIR)
    if irr is None:
        story.append(Paragraph("TIR (IRR) estimada: N/D", styles["BodyText"]))
    else:
        story.append(Paragraph(f"TIR (IRR) estimada: {float(irr)*100:.2f} %", styles["BodyText"]))

    # VAN (NPV)
    if npv is None:
        story.append(Paragraph("VAN (NPV) a tasa de descuento: N/D", styles["BodyText"]))
    else:
        story.append(Paragraph(f"VAN (NPV) a tasa de descuento: L {float(npv):,.0f}", styles["BodyText"]))

    # Payback descontado
    if pb is None:
        story.append(Paragraph("Payback descontado: N/D", styles["BodyText"]))
    else:
        story.append(Paragraph(f"Payback descontado: {float(pb):.1f} años", styles["BodyText"]))

    story.append(PageBreak())
    return story

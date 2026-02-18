# reportes/page_5.py
from reportlab.platypus import Paragraph, Spacer, PageBreak


def build_page_5(resultado, datos, pal, styles):
    """
    Página 5 — Resumen técnico (mínimo, robusto)
    No asume atributos en `resultado` (es dict).
    """

    story = []

    story.append(Paragraph("Resumen técnico", styles["Title"]))
    story.append(Spacer(1, 10))

    sizing = resultado.get("sizing", {}) or {}
    tabla_12m = resultado.get("tabla_12m", []) or []

    kwp_dc = float(sizing.get("kwp_dc", 0.0))
    n_paneles = int(sizing.get("n_paneles", 0) or 0)
    capex_L = float(sizing.get("capex_L", 0.0))

    ahorro_anual_L = sum(float(r.get("ahorro_L", 0.0)) for r in tabla_12m)
    fv_anual_kwh = sum(float(r.get("fv_kwh", 0.0)) for r in tabla_12m)
    consumo_anual_kwh = sum(float(r.get("consumo_kwh", 0.0)) for r in tabla_12m)

    story.append(Paragraph(f"Sistema FV estimado: {kwp_dc:.2f} kWp DC", styles["BodyText"]))
    story.append(Paragraph(f"Número de paneles: {n_paneles}", styles["BodyText"]))
    story.append(Paragraph(f"CAPEX estimado: L {capex_L:,.2f}", styles["BodyText"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Consumo anual (12m): {consumo_anual_kwh:,.0f} kWh", styles["BodyText"]))
    story.append(Paragraph(f"Generación FV útil (12m): {fv_anual_kwh:,.0f} kWh", styles["BodyText"]))
    story.append(Paragraph(f"Ahorro anual estimado (12m): L {ahorro_anual_L:,.2f}", styles["BodyText"]))

    story.append(PageBreak())
    return story

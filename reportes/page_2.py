# reportes/page_2.py
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Spacer, Paragraph, Image, Table, TableStyle, PageBreak

from .helpers_pdf import make_table, table_style_uniform, box_paragraph, get_field
from core.result_accessors import get_tabla_12m


def _append_layout_paneles(story, paths, styles, content_w):
    """
    Inserta el layout de paneles si existe.
    Mantenerlo como helper evita ensuciar build_page_2.
    """
    layout = paths.get("layout_paneles")
    if layout and Path(layout).exists():
        story.append(Spacer(1, 10))
        img = Image(str(layout), width=content_w, height=content_w * 0.55)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 8))
    else:
        story.append(Spacer(1, 6))
        story.append(Paragraph("Layout de paneles no disponible.", styles["BodyText"]))
        story.append(Spacer(1, 8))


def build_page_2(resultado, datos, paths, pal, styles, content_w):
    # content width estándar carta con márgenes típicos
    page_w, _ = letter
    left_margin = 36
    right_margin = 36
    content_w = page_w - left_margin - right_margin

    story = []
    story.append(Paragraph("Reporte de Demanda / Energía", styles["Title"]))
    story.append(Spacer(1, 8))

    

    story.append(Paragraph("Energía mensual (Consumo vs FV útil vs ENEE)", styles["H2b"]))
    story.append(Spacer(1, 6))

    header = ["Mes", "Consumo (kWh)", "FV útil (kWh)", "ENEE (kWh)"]
    tabla_12m = get_tabla_12m(resultado) or []
    rows = [
        [
            r.get("mes", ""),
            f"{float(r.get('consumo_kwh', 0.0)):,.0f}",
            f"{float(r.get('fv_kwh', 0.0)):,.0f}",
            f"{float(r.get('kwh_enee', 0.0)):,.0f}",
        ]
        for r in tabla_12m
    ]

    t = make_table([header] + rows, content_w, ratios=[0.65, 2.1, 2.1, 2.1], repeatRows=1)
    t.setStyle(table_style_uniform(pal, font_header=8, font_body=8))
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 8))

    # ===== CHARTS =====
    GAP = 10
    CH_W = (content_w - GAP) / 2.0
    CH_H = 2.15 * inch

    # ✅ tolerante: solo si existen
    chart_energia = paths.get("chart_energia")
    chart_generacion = paths.get("chart_generacion")

    if chart_energia and chart_generacion and Path(chart_energia).exists() and Path(chart_generacion).exists():
        img1 = Image(str(chart_energia), width=CH_W, height=CH_H)
        img2 = Image(str(chart_generacion), width=CH_W, height=CH_H)

        charts = Table([[img1, img2]], colWidths=[CH_W, CH_W])
        charts.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("COLSEP", (0, 0), (-1, -1), GAP),
                ]
            )
        )
        story.append(charts)
        story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Charts no disponibles.", styles["BodyText"]))
        story.append(Spacer(1, 8))

    interp = (
        "<b>Interpretación</b><br/>"
        "• Esta página muestra energía (kWh).<br/>"
        "• El dimensionamiento evita sobredimensionar en meses de baja demanda.<br/>"
        f"• Cobertura objetivo: <b>{float(get_field(datos,'cobertura_objetivo',0.0))*100:.0f}%</b>."
    )
    story.append(box_paragraph(interp, pal, content_w, font_size=9))

    story.append(PageBreak())
    return story

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import Spacer, Paragraph, Image, Table, TableStyle, PageBreak

from .helpers_pdf import make_table, table_style_uniform, box_paragraph, get_field


# =========================================================
# LECTURA SEGURA
# =========================================================

def leer(obj, campo, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# =========================================================
# LAYOUT DE PANELES
# =========================================================

def _append_layout_paneles(story, paths, styles, content_w, safe_image):

    layout = paths.get("layout_paneles")

    if layout and Path(str(layout)).exists():

        story.append(Spacer(1, 10))

        # 🔥 USO SEGURO
        img = safe_image(str(layout), max_w=content_w, max_h=400)

        if img:
            img.hAlign = "CENTER"
            story.append(img)
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("Error cargando layout de paneles.", styles["BodyText"]))
            story.append(Spacer(1, 8))

    else:

        story.append(Spacer(1, 6))
        story.append(Paragraph("Layout de paneles no disponible.", styles["BodyText"]))
        story.append(Spacer(1, 8))

# =========================================================
# PAGE 2
# =========================================================

def build_page_2(resultado: Any, datos, paths, pal, styles, content_w, safe_image):

    story = []

    # =========================
    # TÍTULO
    # =========================
    story.append(Paragraph("Reporte de Demanda / Energía", styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Energía mensual (Consumo Actual vs FV Proyectado)", styles["H2b"]))
    story.append(Spacer(1, 6))

    # =========================
    # TABLA
    # =========================
    financiero = leer(resultado, "financiero", {})
    tabla_12m = leer(financiero, "tabla_12m", [])

    header = ["Mes", "Consumo Actual (kWh)", "FV Proyectado (kWh)", "ENEE Residual (kWh)"]

    rows = [
        [
            r.get("mes", ""),
            f"{float(r.get('consumo_kwh', 0)):,.0f}",
            f"{float(r.get('fv_kwh', 0)):,.0f}",
            f"{float(r.get('kwh_enee', 0)):,.0f}",
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

    # =====================================================
    # CHARTS (SEGUROS)
    # =====================================================

    GAP = 10
    CH_W = (content_w - GAP) / 2.0
    CH_H = 2.15 * inch

    chart_energia = paths.get("chart_energia_mensual")
    chart_generacion = paths.get("chart_energia_diaria")

    if (
        chart_energia
        and chart_generacion
        and Path(str(chart_energia)).exists()
        and Path(str(chart_generacion)).exists()
    ):

        img1 = safe_image(str(chart_energia), max_w=CH_W, max_h=CH_H)
        img2 = safe_image(str(chart_generacion), max_w=CH_W, max_h=CH_H)

        if img1 and img2:

            img1.hAlign = "CENTER"
            img2.hAlign = "CENTER"

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
            story.append(Paragraph("Error cargando gráficos.", styles["BodyText"]))
            story.append(Spacer(1, 8))

    else:

        story.append(Paragraph("Charts no disponibles.", styles["BodyText"]))
        story.append(Spacer(1, 8))

    # =====================================================
    # INTERPRETACIÓN
    # =====================================================

    interp = (
        "<b>Interpretación</b><br/>"
        "• Esta página muestra energía mensual simulada.<br/>"
        "• La generación FV se limita al consumo (sin exportación).<br/>"
        f"• Cobertura objetivo: <b>{float(get_field(datos,'cobertura_objetivo',0))*100:.0f}%</b>."
    )

    story.append(box_paragraph(interp, pal, content_w, font_size=9))

    story.append(PageBreak())

    return story

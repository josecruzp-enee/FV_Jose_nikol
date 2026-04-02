from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle, PageBreak

from .helpers_pdf import make_table, table_style_uniform, box_paragraph, get_field


# =========================================================
# UTILIDAD
# =========================================================

def leer(obj, campo, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(campo, default)
    return getattr(obj, campo, default)


# =========================================================
# PAGE 2
# =========================================================

def build_page_2(resultado: Any, datos, paths, pal, styles, content_w, safe_image):

    story = []

    # =====================================================
    # TÍTULO
    # =====================================================
    story.append(Paragraph("Reporte de Demanda / Energía", styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Energía mensual (Consumo vs FV)", styles["H2b"]))
    story.append(Spacer(1, 6))

    # =====================================================
    # DATA
    # =====================================================
    financiero = leer(resultado, "financiero", {})
    tabla_12m = leer(financiero, "tabla_12m", [])

    header = ["Mes", "Consumo (kWh)", "FV (kWh)", "ENEE (kWh)"]

    rows = [
        [
            r.get("mes", ""),
            f"{float(r.get('consumo_kwh', 0)):,.0f}",
            f"{float(r.get('fv_kwh', 0)):,.0f}",
            f"{float(r.get('kwh_enee', 0)):,.0f}",
        ]
        for r in tabla_12m
    ]

    # =====================================================
    # 🔥 TOTAL ANUAL
    # =====================================================
    total_consumo = sum(float(r.get("consumo_kwh", 0)) for r in tabla_12m)
    total_fv = sum(float(r.get("fv_kwh", 0)) for r in tabla_12m)
    total_enee = sum(float(r.get("kwh_enee", 0)) for r in tabla_12m)

    rows.append([
        "TOTAL",
        f"{total_consumo:,.0f}",
        f"{total_fv:,.0f}",
        f"{total_enee:,.0f}",
    ])

    # =====================================================
    # TABLA
    # =====================================================
    t = make_table([header] + rows, content_w, ratios=[0.7, 2.1, 2.1, 2.1], repeatRows=1)

    t.setStyle(table_style_uniform(pal, font_header=8, font_body=8))

    t.setStyle(
        TableStyle([
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            # Mes centrado
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            # Encabezado centrado
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            # Números a la derecha (ya lo tienes)
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("BACKGROUND", (0, -1), (-1, -1), pal["HEADER"]),
            ("TEXTCOLOR", (0, -1), (-1, -1), "white"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ])
    )

    story.append(t)
    story.append(Spacer(1, 10))

    # =====================================================
    # GRÁFICAS
    # =====================================================

    GAP = 10
    CH_W = (content_w - GAP) / 2.0
    CH_H = 2.2 * inch

    chart_mes = paths.get("chart_energia_mensual")
    chart_dia = paths.get("chart_energia_diaria")

    if (
        chart_mes and chart_dia
        and Path(str(chart_mes)).exists()
        and Path(str(chart_dia)).exists()
    ):

        img1 = safe_image(str(chart_mes), max_w=CH_W, max_h=CH_H)
        img2 = safe_image(str(chart_dia), max_w=CH_W, max_h=CH_H)

        if img1 and img2:

            charts = Table([[img1, img2]], colWidths=[CH_W, CH_W])

            charts.setStyle(
                TableStyle([
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ])
            )

            story.append(charts)
            story.append(Spacer(1, 10))

    else:
        story.append(Paragraph("Gráficas no disponibles.", styles["BodyText"]))
        story.append(Spacer(1, 10))

    # =====================================================
    # INTERPRETACIÓN AUTOMÁTICA
    # =====================================================

    consumo_12m = get_field(datos, "consumo_12m", [])
    consumo_anual = sum(consumo_12m) if isinstance(consumo_12m, list) else 0

    cobertura_real = total_fv / consumo_anual if consumo_anual > 0 else 0

    interp = f"""
    <b>Interpretación técnica</b><br/><br/>
    • Generación FV anual: <b>{total_fv:,.0f} kWh</b><br/>
    • Consumo anual: <b>{consumo_anual:,.0f} kWh</b><br/>
    • Cobertura real del sistema: <b>{cobertura_real*100:.1f}%</b><br/><br/>
    • El sistema cubre parcialmente la demanda energética.<br/>
    • No se considera exportación a red.<br/>
    """

    story.append(box_paragraph(interp, pal, content_w, font_size=9))

    story.append(PageBreak())

    return story

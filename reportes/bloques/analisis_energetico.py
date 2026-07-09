# -*- coding: utf-8 -*-
# reportes/analisis_energetico.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import Spacer, Paragraph, Table, TableStyle, PageBreak, Image

from reportes.helpers_pdf import (
    make_table,
    table_style_uniform,
    box_paragraph,
    get_field,
)


# =========================================================
# CAPÍTULO 2
# ANÁLISIS ENERGÉTICO
# =========================================================
# Responsabilidad:
# - Presentar consumo mensual.
# - Presentar generación FV mensual.
# - Presentar energía tomada de ENEE.
# - Mostrar gráficas energéticas si existen.
# - Mostrar interpretación técnica básica.
#
# Reglas de mantenimiento:
# - No cambiar la firma de build_analisis_energetico().
# - No cambiar nombres de variables usadas por otros módulos.
# - No mover cálculos todavía.
# - No eliminar safe_image; es opcional y compatible.
# =========================================================


# =========================================================
# 1. ORQUESTADOR DEL CAPÍTULO
# =========================================================
# Esta función es llamada desde BLOQUES_REPORTE.
# Mantener firma por compatibilidad.
# =========================================================

def build_analisis_energetico(
    resultado: Any,
    datos,
    paths,
    pal,
    styles,
    content_w,
    safe_image=None,  # 🔥 OPCIONAL
):

    story = []

    # =====================================================
    # 1.1 TÍTULO DEL CAPÍTULO
    # =====================================================
    story.append(Paragraph("Análisis de Energía", styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Energía mensual (Consumo vs FV)", styles["H2b"]))
    story.append(Spacer(1, 6))

    # =====================================================
    # 1.2 DATA SEGURA
    # =====================================================
    financiero = getattr(resultado, "financiero", None)

    if not financiero or not isinstance(financiero, dict):
        story.append(Paragraph("No hay información energética disponible.", styles["BodyText"]))
        story.append(PageBreak())
        return story

    tabla_12m = financiero.get("tabla_12m", [])

    # =====================================================
    # 1.3 TABLA ENERGÉTICA MENSUAL
    # =====================================================
    header = ["Mes", "Consumo (kWh)", "FV (kWh)", "ENEE (kWh)"]
    rows = []

    for r in tabla_12m:
        if not isinstance(r, dict):
            continue

        rows.append([
            r.get("mes", ""),
            f"{float(r.get('consumo_kwh', 0)):,.0f}",
            f"{float(r.get('fv_kwh', 0)):,.0f}",
            f"{float(r.get('kwh_enee', 0)):,.0f}",
        ])

    total_consumo = sum(float(r.get("consumo_kwh", 0)) for r in tabla_12m if isinstance(r, dict))
    total_fv = sum(float(r.get("fv_kwh", 0)) for r in tabla_12m if isinstance(r, dict))
    total_enee = sum(float(r.get("kwh_enee", 0)) for r in tabla_12m if isinstance(r, dict))

    rows.append([
        "TOTAL",
        f"{total_consumo:,.0f}",
        f"{total_fv:,.0f}",
        f"{total_enee:,.0f}",
    ])

    tabla = make_table(
        [header] + rows,
        content_w,
        ratios=[0.7, 2.1, 2.1, 2.1],
        repeatRows=1
    )

    tabla.setStyle(table_style_uniform(pal, font_header=8, font_body=8))

    tabla.setStyle(TableStyle([
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), pal.get("PRIMARY")),
        ("TEXTCOLOR", (0, -1), (-1, -1), "white"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))

    story.append(tabla)
    story.append(Spacer(1, 10))

    # =====================================================
    # 1.4 GRÁFICAS ENERGÉTICAS
    # =====================================================
    GAP = 10
    CH_W = (content_w - GAP) / 2.0
    CH_H = 2.2 * inch

    chart_mes = paths.get("chart_energia_mensual") if isinstance(paths, dict) else None
    chart_dia = paths.get("chart_energia_diaria") if isinstance(paths, dict) else None

    if (
        chart_mes and chart_dia and
        Path(str(chart_mes)).exists() and
        Path(str(chart_dia)).exists()
    ):

        # 🔥 CONTROL SAFE_IMAGE
        if safe_image:
            img1 = safe_image(str(chart_mes), max_w=CH_W, max_h=CH_H)
            img2 = safe_image(str(chart_dia), max_w=CH_W, max_h=CH_H)
        else:
            img1 = Image(str(chart_mes))
            img2 = Image(str(chart_dia))

            img1.drawWidth = CH_W
            img1.drawHeight = CH_H

            img2.drawWidth = CH_W
            img2.drawHeight = CH_H

        if img1 and img2:
            charts = Table([[img1, img2]], colWidths=[CH_W, CH_W])

            charts.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            story.append(charts)
            story.append(Spacer(1, 10))

    else:
        story.append(Paragraph("Gráficas no disponibles.", styles["BodyText"]))
        story.append(Spacer(1, 10))

    # =====================================================
    # 1.5 INTERPRETACIÓN TÉCNICA
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
    """

    story.append(box_paragraph(interp, pal, content_w, font_size=9))

    story.append(PageBreak())

    return story

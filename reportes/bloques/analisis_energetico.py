# -*- coding: utf-8 -*-
# reportes/analisis_energetico.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib.units import inch
from reportlab.platypus import (
    Spacer,
    Paragraph,
    Table,
    TableStyle,
    PageBreak,
    Image,
)

from reportes.helpers_pdf import (
    make_table,
    table_style_uniform,
    box_paragraph,
)


# =========================================================
# CAPÍTULO 2
# ANÁLISIS ENERGÉTICO
# =========================================================
# Responsabilidad:
# - Presentar consumo mensual.
# - Presentar energía cubierta mensualmente por FV + batería.
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

def build_analisis_energetico(
    resultado: Any,
    datos,
    paths,
    pal,
    styles,
    content_w,
    safe_image=None,
):

    story = []

    # =====================================================
    # 1.1 TÍTULO DEL CAPÍTULO
    # =====================================================
    story.append(
        Paragraph(
            "Análisis de Energía",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Energía mensual",
            styles["H2b"],
        )
    )
    story.append(Spacer(1, 6))

    # =====================================================
    # 1.2 DATOS FINANCIEROS
    # =====================================================
    financiero = getattr(
        resultado,
        "financiero",
        None,
    )

    if not financiero or not isinstance(financiero, dict):
        story.append(
            Paragraph(
                "No hay información energética disponible.",
                styles["BodyText"],
            )
        )
        story.append(PageBreak())
        return story

    tabla_12m = financiero.get(
        "tabla_12m",
        [],
    )

    # =====================================================
    # 1.3 TABLA ENERGÉTICA MENSUAL
    # =====================================================
    header = [
        "Mes",
        "Consumo (kWh)",
        "Energía cubierta (kWh)",
        "ENEE (kWh)",
    ]

    rows = []

    for fila in tabla_12m:
        if not isinstance(fila, dict):
            continue

        rows.append([
            fila.get("mes", ""),
            f"{float(fila.get('consumo_kwh', 0)):,.0f}",
            f"{float(fila.get('fv_kwh', 0)):,.0f}",
            f"{float(fila.get('kwh_enee', 0)):,.0f}",
        ])

    total_consumo = sum(
        float(fila.get("consumo_kwh", 0))
        for fila in tabla_12m
        if isinstance(fila, dict)
    )

    total_fv = sum(
        float(fila.get("fv_kwh", 0))
        for fila in tabla_12m
        if isinstance(fila, dict)
    )

    total_enee = sum(
        float(fila.get("kwh_enee", 0))
        for fila in tabla_12m
        if isinstance(fila, dict)
    )

    rows.append([
        "TOTAL",
        f"{total_consumo:,.0f}",
        f"{total_fv:,.0f}",
        f"{total_enee:,.0f}",
    ])

    tabla = make_table(
        [header] + rows,
        content_w,
        ratios=[0.7, 2.0, 2.5, 2.0],
        repeatRows=1,
    )

    tabla.setStyle(
        table_style_uniform(
            pal,
            font_header=8,
            font_body=8,
        )
    )

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
    gap = 10
    chart_width = (content_w - gap) / 2.0
    chart_height = 2.2 * inch

    chart_mes = (
        paths.get("chart_energia_mensual")
        if isinstance(paths, dict)
        else None
    )

    chart_dia = (
        paths.get("chart_energia_diaria")
        if isinstance(paths, dict)
        else None
    )

    graficas_disponibles = (
        chart_mes
        and chart_dia
        and Path(str(chart_mes)).exists()
        and Path(str(chart_dia)).exists()
    )

    if graficas_disponibles:

        if safe_image:
            img_mes = safe_image(
                str(chart_mes),
                max_w=chart_width,
                max_h=chart_height,
            )

            img_dia = safe_image(
                str(chart_dia),
                max_w=chart_width,
                max_h=chart_height,
            )

        else:
            img_mes = Image(str(chart_mes))
            img_dia = Image(str(chart_dia))

            img_mes.drawWidth = chart_width
            img_mes.drawHeight = chart_height

            img_dia.drawWidth = chart_width
            img_dia.drawHeight = chart_height

        if img_mes and img_dia:
            charts = Table(
                [[img_mes, img_dia]],
                colWidths=[
                    chart_width,
                    chart_width,
                ],
            )

            charts.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            story.append(charts)
            story.append(Spacer(1, 10))

    else:
        story.append(
            Paragraph(
                "Gráficas no disponibles.",
                styles["BodyText"],
            )
        )
        story.append(Spacer(1, 10))

    # =====================================================
    # 1.5 INTERPRETACIÓN TÉCNICA
    # =====================================================
    cobertura_real = (
        total_fv / total_consumo
        if total_consumo > 0
        else 0.0
    )

    interp = f"""
    <b>Interpretación técnica</b><br/><br/>
    • Energía anual cubierta por el sistema FV y batería:
    <b>{total_fv:,.0f} kWh</b><br/>
    • Consumo anual:
    <b>{total_consumo:,.0f} kWh</b><br/>
    • Cobertura energética anual del sistema:
    <b>{cobertura_real * 100:.1f}%</b><br/><br/>
    • El sistema cubre parcialmente la demanda energética mediante
    generación fotovoltaica directa y energía desplazada por la batería.<br/>
    """

    story.append(
        box_paragraph(
            interp,
            pal,
            content_w,
            font_size=9,
        )
    )

    story.append(PageBreak())

    return story

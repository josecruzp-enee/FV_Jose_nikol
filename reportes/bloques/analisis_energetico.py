# -*- coding: utf-8 -*-
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


def _valor(fila, campo) -> float:
    return float(fila.get(campo, 0.0) or 0.0)


def build_analisis_energetico(
    resultado: Any,
    datos,
    paths,
    pal,
    styles,
    content_w,
    safe_image=None,
):
    story = [
        Paragraph("Análisis de Energía", styles["Title"]),
        Spacer(1, 8),
        Paragraph("Energía mensual", styles["H2b"]),
        Spacer(1, 6),
    ]

    financiero = getattr(resultado, "financiero", None)

    if not financiero or not isinstance(financiero, dict):
        story.append(
            Paragraph(
                "No hay información energética disponible.",
                styles["BodyText"],
            )
        )
        story.append(PageBreak())
        return story

    tabla_12m = financiero.get("tabla_12m", [])
    header = [
        "Mes",
        "Consumo",
        "Energía cubierta",
        "Compra ENEE",
        "Inyección",
    ]
    rows = []

    for fila in tabla_12m:
        if not isinstance(fila, dict):
            continue

        rows.append([
            fila.get("mes", ""),
            f"{_valor(fila, 'consumo_kwh'):,.0f}",
            f"{_valor(fila, 'fv_kwh'):,.0f}",
            f"{_valor(fila, 'kwh_enee'):,.0f}",
            f"{_valor(fila, 'inyeccion_kwh'):,.0f}",
        ])

    total_consumo = sum(
        _valor(fila, "consumo_kwh")
        for fila in tabla_12m
        if isinstance(fila, dict)
    )
    total_fv = sum(
        _valor(fila, "fv_kwh")
        for fila in tabla_12m
        if isinstance(fila, dict)
    )
    total_enee = sum(
        _valor(fila, "kwh_enee")
        for fila in tabla_12m
        if isinstance(fila, dict)
    )
    total_inyeccion = sum(
        _valor(fila, "inyeccion_kwh")
        for fila in tabla_12m
        if isinstance(fila, dict)
    )

    rows.append([
        "TOTAL",
        f"{total_consumo:,.0f}",
        f"{total_fv:,.0f}",
        f"{total_enee:,.0f}",
        f"{total_inyeccion:,.0f}",
    ])
    tabla = make_table(
        [header] + rows,
        content_w,
        ratios=[0.65, 1.4, 1.8, 1.5, 1.4],
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

    gap = 10
    chart_width = (content_w - gap) / 2.0
    chart_height = 2.2 * inch
    chart_mes = (
        paths.get("chart_energia_mensual")
        if isinstance(paths, dict) else None
    )
    chart_dia = (
        paths.get("chart_energia_diaria")
        if isinstance(paths, dict) else None
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
                colWidths=[chart_width, chart_width],
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
            Paragraph("Gráficas no disponibles.", styles["BodyText"])
        )
        story.append(Spacer(1, 10))

    cobertura = (
        total_fv / total_consumo
        if total_consumo > 0 else 0.0
    )
    capacidad_bateria = float(
        financiero.get("capacidad_bateria_kwh", 0.0) or 0.0
    )
    fuente = (
        "generación fotovoltaica directa y energía desplazada "
        "por la batería"
        if capacidad_bateria > 0
        else "generación fotovoltaica"
    )
    interp = f"""
    <b>Interpretación técnica</b><br/><br/>
    • Energía anual cubierta por el sistema:
    <b>{total_fv:,.0f} kWh</b><br/>
    • Consumo anual:
    <b>{total_consumo:,.0f} kWh</b><br/>
    • Compra anual a la red:
    <b>{total_enee:,.0f} kWh</b><br/>
    • Energía anual inyectada:
    <b>{total_inyeccion:,.0f} kWh</b><br/>
    • Cobertura energética anual:
    <b>{cobertura * 100:.1f}%</b><br/><br/>
    • El sistema cubre parcialmente la demanda mediante {fuente}.<br/>
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

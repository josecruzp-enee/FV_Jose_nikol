# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer, TableStyle, PageBreak

from reportes.helpers_pdf import (
    make_table,
    table_style_uniform,
    box_paragraph,
    money_L,
)


def leer(obj, campo, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(campo, default)
    return getattr(obj, campo, default)


def _valor(fila, campo) -> float:
    return float(fila.get(campo, 0.0) or 0.0)


def tabla_impacto_mensual_anio1(
    resultado: Any,
    pal: dict,
    content_w: float,
):
    financiero = leer(resultado, "financiero", {}) or {}
    tabla_12m = leer(financiero, "tabla_12m", []) or []
    cuota_m = float(
        leer(
            financiero,
            "cuota_mensual_L",
            leer(financiero, "cuota_mensual", 0.0),
        )
        or 0.0
    )
    es_contado = cuota_m <= 0.000001

    if es_contado:
        header = [
            "Mes",
            "Pago actual",
            "Compra ENEE",
            "Crédito inyección",
            "Pago neto ENEE",
            "Beneficio",
            "Acumulado",
        ]
        ratios = [0.55, 1.2, 1.2, 1.25, 1.25, 1.2, 1.25]
        col_beneficio = 5
    else:
        header = [
            "Mes",
            "Pago actual",
            "Compra ENEE",
            "Crédito iny.",
            "Pago neto",
            "Cuota",
            "Pago total",
            "Beneficio",
            "Acumulado",
        ]
        ratios = [0.45, 1.0, 1.0, 1.0, 1.0, 0.9, 1.0, 1.0, 1.05]
        col_beneficio = 7

    rows = []
    acumulado = 0.0
    totales = {
        "actual": 0.0,
        "compra": 0.0,
        "credito": 0.0,
        "neto": 0.0,
        "pago_total": 0.0,
        "beneficio": 0.0,
    }

    for fila in tabla_12m:
        if not isinstance(fila, dict):
            continue

        pago_actual = _valor(fila, "factura_base_L")
        credito = _valor(fila, "credito_inyeccion_aplicado_L")
        pago_neto = _valor(fila, "pago_enee_L")
        compra_enee = pago_neto + credito
        pago_total = pago_neto + cuota_m
        beneficio = pago_actual - pago_total
        acumulado += beneficio

        totales["actual"] += pago_actual
        totales["compra"] += compra_enee
        totales["credito"] += credito
        totales["neto"] += pago_neto
        totales["pago_total"] += pago_total
        totales["beneficio"] += beneficio

        base = [
            str(fila.get("mes", "")),
            money_L(pago_actual),
            money_L(compra_enee),
            money_L(credito),
            money_L(pago_neto),
        ]

        if es_contado:
            rows.append(base + [money_L(beneficio), money_L(acumulado)])
        else:
            rows.append(
                base
                + [money_L(cuota_m), money_L(pago_total)]
                + [money_L(beneficio), money_L(acumulado)]
            )

    if es_contado:
        rows.append([
            "TOTAL",
            money_L(totales["actual"]),
            money_L(totales["compra"]),
            money_L(totales["credito"]),
            money_L(totales["neto"]),
            money_L(totales["beneficio"]),
            money_L(totales["beneficio"]),
        ])
    else:
        rows.append([
            "TOTAL",
            money_L(totales["actual"]),
            money_L(totales["compra"]),
            money_L(totales["credito"]),
            money_L(totales["neto"]),
            money_L(cuota_m * 12),
            money_L(totales["pago_total"]),
            money_L(totales["beneficio"]),
            money_L(totales["beneficio"]),
        ])

    table_data = [header] + rows
    tabla = make_table(
        table_data,
        content_w,
        ratios=ratios,
        repeatRows=1,
    )
    tabla.setStyle(
        table_style_uniform(
            pal,
            font_header=7,
            font_body=7,
        )
    )
    last_row = len(table_data) - 1
    estilos = [
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (col_beneficio, 1), (col_beneficio, -2), "Helvetica-Bold"),
        ("BACKGROUND", (0, last_row), (-1, last_row), pal.get("SOFT", "#EAEAEA")),
        ("FONTNAME", (0, last_row), (-1, last_row), "Helvetica-Bold"),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.2, pal.get("PRIMARY")),
    ]

    for indice, fila in enumerate(tabla_12m, start=1):
        if isinstance(fila, dict) and (
            _valor(fila, "factura_base_L")
            - _valor(fila, "pago_enee_L")
            - cuota_m
        ) < 0:
            estilos.append((
                "TEXTCOLOR",
                (col_beneficio, indice),
                (col_beneficio, indice),
                pal.get("BAD", "red"),
            ))

    tabla.setStyle(TableStyle(estilos))
    return [tabla, Spacer(1, 10)]


def build_analisis_operativo(
    resultado: Any,
    datos: Any,
    paths: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):
    story = []
    financiero = leer(resultado, "financiero", {}) or {}
    tabla_12m = leer(financiero, "tabla_12m", []) or []
    cuota_m = float(
        leer(
            financiero,
            "cuota_mensual_L",
            leer(financiero, "cuota_mensual", 0.0),
        )
        or 0.0
    )
    es_contado = cuota_m <= 0.000001

    story.append(Paragraph("Impacto económico mensual", styles["Title"]))
    story.append(Spacer(1, 10))

    if es_contado:
        capex = float(
            leer(
                financiero,
                "capex_total_L",
                leer(financiero, "capex_L", 0.0),
            )
            or 0.0
        )
        beneficio_anual = sum(
            _valor(fila, "ahorro_L")
            for fila in tabla_12m
            if isinstance(fila, dict)
        )
        credito_anual = sum(
            _valor(fila, "credito_inyeccion_aplicado_L")
            for fila in tabla_12m
            if isinstance(fila, dict)
        )
        ahorro_autoconsumo = max(
            beneficio_anual - credito_anual,
            0.0,
        )
        beneficio_mensual = (
            beneficio_anual / len(tabla_12m)
            if tabla_12m else 0.0
        )
        retorno = (
            capex / beneficio_anual
            if capex > 0 and beneficio_anual > 0
            else 0.0
        )
        lectura = (
            "<b>Lectura ejecutiva</b><br/>"
            "• Modalidad evaluada: <b>Pago de contado</b><br/>"
            f"• CAPEX estimado: <b>{money_L(capex)}</b><br/>"
            f"• Ahorro anual por autoconsumo: <b>{money_L(ahorro_autoconsumo)}</b><br/>"
            f"• Crédito anual por inyección: <b>{money_L(credito_anual)}</b><br/>"
            f"• Beneficio energético mensual: <b>{money_L(beneficio_mensual)}</b><br/>"
            f"• Retorno simple estimado: <b>{retorno:.1f} años</b>"
        )
        story.append(
            box_paragraph(
                lectura,
                pal,
                content_w,
                font_size=9,
            )
        )
        story.append(Spacer(1, 10))

    story.append(Paragraph("Comparación mensual — Año 1", styles["H2b"]))
    story.append(Spacer(1, 6))
    story += tabla_impacto_mensual_anio1(
        resultado,
        pal,
        content_w,
    )
    story.append(PageBreak())
    return story

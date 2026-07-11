# -*- coding: utf-8 -*-
# reportes/analisis_operativo.py

from __future__ import annotations

from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer, TableStyle, PageBreak

# ✅ IMPORT CORRECTO (CAPA DE COMPATIBILIDAD)
from reportes.helpers_pdf import (
    make_table,
    table_style_uniform,
    box_paragraph,
    money_L,
)


# =========================================================
# CAPÍTULO 4
# ANÁLISIS OPERATIVO
# =========================================================
# Responsabilidad:
# - Presentar el impacto mensual del año 1.
# - Comparar pago actual, pago ENEE, cuota y ahorro.
# - Mostrar configuración DC resumida si existe.
# - Mostrar resumen eléctrico NEC si existe.
#
# Reglas de mantenimiento:
# - No cambiar la firma de build_analisis_operativo().
# - No cambiar nombres de variables usadas por otros módulos.
# - No mover cálculos todavía.
# - Mantener tabla_impacto_mensual_anio1() como función auxiliar.
# =========================================================


# =========================================================
# 1. UTILIDADES INTERNAS DEL CAPÍTULO
# =========================================================

def leer(obj, campo, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# =========================================================
# 2. SECCIÓN: TABLA DE IMPACTO MENSUAL AÑO 1
# =========================================================

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
        ) or 0.0
    )

    es_contado = cuota_m <= 0.000001

    if es_contado:
        header = [
            "Mes",
            "Pago actual",
            "Pago con FV",
            "Ahorro mes",
            "Ahorro acumulado",
        ]
        ratios = [0.7, 1.5, 1.5, 1.5, 1.7]
        col_ahorro = 3
    else:
        header = [
            "Mes",
            "Pago actual",
            "Pago ENEE",
            "Cuota",
            "Pago total",
            "Ahorro mes",
            "Ahorro acumulado",
        ]
        ratios = [0.7, 1.4, 1.4, 1.2, 1.4, 1.4, 1.5]
        col_ahorro = 5

    rows = []

    acumulado = 0.0
    total_pago_actual = 0.0
    total_enee = 0.0
    total_pago_fv = 0.0
    total_ahorro = 0.0

    for r in tabla_12m:

        if not isinstance(r, dict):
            continue

        pago_actual = float(r.get("factura_base_L", 0.0))
        pago_enee = float(r.get("pago_enee_L", 0.0))
        pago_fv = pago_enee + cuota_m
        ahorro_mes = pago_actual - pago_fv

        acumulado += ahorro_mes
        total_pago_actual += pago_actual
        total_enee += pago_enee
        total_pago_fv += pago_fv
        total_ahorro += ahorro_mes

        if es_contado:
            rows.append([
                str(r.get("mes", "")),
                money_L(pago_actual),
                money_L(pago_fv),
                money_L(ahorro_mes),
                money_L(acumulado),
            ])
        else:
            rows.append([
                str(r.get("mes", "")),
                money_L(pago_actual),
                money_L(pago_enee),
                money_L(cuota_m),
                money_L(pago_fv),
                money_L(ahorro_mes),
                money_L(acumulado),
            ])

    if es_contado:
        rows.append([
            "TOTAL",
            money_L(total_pago_actual),
            money_L(total_pago_fv),
            money_L(total_ahorro),
            money_L(total_ahorro),
        ])
    else:
        rows.append([
            "TOTAL",
            money_L(total_pago_actual),
            money_L(total_enee),
            money_L(cuota_m * 12),
            money_L(total_pago_fv),
            money_L(total_ahorro),
            money_L(total_ahorro),
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
            font_header=9,
            font_body=9,
        )
    )

    last_row = len(table_data) - 1

    estilos = [
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (col_ahorro, 1), (col_ahorro, -2), "Helvetica-Bold"),
        ("BACKGROUND", (0, last_row), (-1, last_row), pal.get("SOFT", "#EAEAEA")),
        ("FONTNAME", (0, last_row), (-1, last_row), "Helvetica-Bold"),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.2, pal.get("PRIMARY")),
    ]

    for i, r in enumerate(tabla_12m, start=1):

        if not isinstance(r, dict):
            continue

        ahorro = (
            float(r.get("factura_base_L", 0.0))
            - float(r.get("pago_enee_L", 0.0))
            - cuota_m
        )

        if ahorro < 0:
            estilos.append(
                (
                    "TEXTCOLOR",
                    (col_ahorro, i),
                    (col_ahorro, i),
                    pal.get("BAD", "red"),
                )
            )

    tabla.setStyle(TableStyle(estilos))

    return [tabla, Spacer(1, 10)]
# =========================================================
# 3. ORQUESTADOR DEL CAPÍTULO
# =========================================================
# Esta función es llamada desde BLOQUES_REPORTE.
# Mantener firma por compatibilidad.
# =========================================================

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
        ) or 0.0
    )

    es_contado = cuota_m <= 0.000001

    story.append(
        Paragraph(
            "Impacto económico mensual",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 10))

    if es_contado:

        capex = float(
            leer(
                financiero,
                "capex_total_L",
                leer(financiero, "capex_L", 0.0),
            ) or 0.0
        )

        ahorro_anual = sum(
            float(r.get("factura_base_L", 0.0))
            - float(r.get("pago_enee_L", 0.0))
            for r in tabla_12m
            if isinstance(r, dict)
        )

        ahorro_mensual = (
            ahorro_anual / len(tabla_12m)
            if tabla_12m
            else 0.0
        )

        retorno = (
            capex / ahorro_anual
            if capex > 0 and ahorro_anual > 0
            else 0.0
        )

        lectura = (
            "<b>Lectura ejecutiva</b><br/>"
            "• Modalidad evaluada: <b>Pago de contado</b><br/>"
            f"• CAPEX estimado: <b>{money_L(capex)}</b><br/>"
            f"• Reducción mensual promedio: "
            f"<b>{money_L(ahorro_mensual)}</b><br/>"
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

    story.append(
        Paragraph(
            "Comparación mensual — Año 1",
            styles["H2b"],
        )
    )
    story.append(Spacer(1, 6))

    story += tabla_impacto_mensual_anio1(
        resultado,
        pal,
        content_w,
    )

    story.append(PageBreak())

    return story

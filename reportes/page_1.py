from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.platypus import TableStyle

from .helpers_pdf import (
    section_bar,
    tabla_4cols,
    tabla_2cols,
    make_table,
    table_style_uniform,
    box_paragraph,
    get_field,
)

from ui.rutas import money_L, num


# ---------------------------
# Página 1
# ---------------------------

def p1_tabla_cliente(datos, sizing, fecha, pal, content_w):
    story = []
    story.append(section_bar("Datos del cliente y situación energética", pal, content_w))
    story.append(Spacer(1, 6))

    consumo_12m = get_field(datos, "consumo_12m", [])
    consumo_anual = sum(consumo_12m) if isinstance(consumo_12m, list) else 0.0

    tarifa_energia = float(get_field(datos, "tarifa_energia", 0.0))
    cargos_fijos = float(get_field(datos, "cargos_fijos", 0.0))

    rows = [
        ["Cliente", get_field(datos, "cliente", ""), "Ubicación", get_field(datos, "ubicacion", "")],
        ["Fecha", fecha, "Consumo anual", f"{consumo_anual:,.0f} kWh/año"],
        ["Tarifa energía", f"{tarifa_energia:.3f} L/kWh", "Cargos fijos", f"{money_L(cargos_fijos)}/mes"],
    ]

    t = tabla_4cols(
        header=["Dato", "Valor", "Dato", "Valor"],
        rows=rows,
        content_w=content_w,
        pal=pal,
        font_header=9,
        font_body=9,
    )

    story.append(t)
    story.append(Spacer(1, 12))
    return story


def p1_tabla_solucion_unica(datos, sizing, energia, financiero, pal, content_w):

    kwp = float(getattr(sizing, "kwp_dc", getattr(sizing, "pdc_kw", 0.0)))
    capex = float(financiero.get("capex_L", 0.0))

    energia_12m = energia.get("energia_util_12m", [])
    prod_anual = sum(energia_12m) if isinstance(energia_12m, list) else 0.0

    n_paneles = int(sizing.get("n_paneles", 0))

    panel_wp = 0
    if n_paneles > 0 and kwp > 0:
        panel_wp = int((kwp * 1000) / n_paneles)

    tasa_anual = float(get_field(datos, "tasa_anual", 0.0))
    plazo_anios = int(get_field(datos, "plazo_anios", 0))
    porcentaje_financiado = float(get_field(datos, "porcentaje_financiado", 0.0))
    cobertura_objetivo = float(get_field(datos, "cobertura_objetivo", 0.0))

    evaluacion = financiero.get("evaluacion", {})
    estado_txt = str(evaluacion.get("estado", "")).upper().strip()
    ds = float(evaluacion.get("dscr", 0.0))

    barra = section_bar("Solución propuesta e indicadores clave", pal, content_w)

    data = [
        ["Dato", "Valor", "Dato", "Valor"],
        [
            "Cobertura objetivo",
            f"{cobertura_objetivo*100:.0f}%",
            "Financiamiento",
            f"{tasa_anual*100:.2f}% | {plazo_anios} años | {porcentaje_financiado*100:.0f}%"
        ],
        ["Sistema", f"{num(kwp,2)} kWp", "CAPEX", money_L(capex)],
        ["Producción anual est.", f"{prod_anual:,.0f} kWh/año", "DSCR", num(ds,2)],
        ["Módulos FV", f"{n_paneles} × {panel_wp} Wp", "Estado", estado_txt],
    ]

    t = make_table(data, content_w, ratios=[1.25, 2.15, 1.25, 2.15], repeatRows=1)

    bg_estado = (
        pal["OK"] if "VIABLE" in estado_txt
        else pal["WARN"] if "MARGINAL" in estado_txt
        else pal["BAD"]
    )

    t.setStyle(table_style_uniform(pal, font_header=9, font_body=9))

    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                ("BACKGROUND", (3, 4), (3, 4), bg_estado),
                ("TEXTCOLOR", (3, 4), (3, 4), "white"),
                ("ALIGN", (3, 4), (3, 4), "CENTER"),
                ("FONTNAME", (3, 4), (3, 4), "Helvetica-Bold"),
            ]
        )
    )

    return [barra, Spacer(1, 6), t, Spacer(1, 12)]


def p1_tabla_decision(financiero, pal, content_w):

    story = []
    story.append(section_bar("Decisión del cliente (mensual)", pal, content_w))
    story.append(Spacer(1, 6))

    tabla = financiero.get("tabla_12m", [])

    if tabla:
        pago_actual = sum(x["factura_base_L"] for x in tabla) / 12
        pago_residual = sum(x["pago_enee_L"] for x in tabla) / 12
    else:
        pago_actual = 0.0
        pago_residual = 0.0

    cuota = float(financiero.get("cuota_mensual", 0.0))

    pago_total = pago_residual + cuota
    ahorro = pago_actual - pago_total

    plazo_anios = int(financiero.get("plazo_anios", 0))

    rows = [
        ["Pago actual ENEE (sin FV)", money_L(pago_actual)],
        ["Pago ENEE con FV (residual)", money_L(pago_residual)],
        ["Cuota de financiamiento", money_L(cuota)],
        ["Pago total con FV (ENEE + cuota)", money_L(pago_total)],
        ["Ahorro neto mensual estimado", money_L(ahorro)],
        [f"Pago después del año {plazo_anios} (solo ENEE residual)", money_L(pago_residual)],
    ]

    t = tabla_2cols(
        header=["Concepto", "Monto (L/mes)"],
        rows=rows,
        content_w=content_w,
        pal=pal,
        highlight_row=4,
        font_header=10,
        font_body=9,
    )

    story.append(t)
    story.append(Spacer(1, 12))
    return story

def p1_conclusion(financiero, sizing, datos, pal, content_w):

    evaluacion = financiero.get("evaluacion", {})

    impacto = float(financiero.get("ahorro_mensual", 0.0))
    ds = float(evaluacion.get("dscr", 0.0))
    peor = float(evaluacion.get("peor_mes", 0.0))
    estado = str(evaluacion.get("estado", "")).upper()

    kwp = float(sizing.get("kwp_dc", sizing.get("pdc_kw", 0.0)))
    cobertura_objetivo = float(get_field(datos, "cobertura_objetivo", 0.0))

    recomend = (
        "Se recomienda avanzar a visita técnica y propuesta final."
        if "VIABLE" in estado
        else "No se recomienda avanzar sin ajustar variables (CAPEX/plazo/cobertura)."
    )

    concl = (
        "<b>Conclusión ejecutiva</b><br/><br/>"
        f"• <b>Impacto financiero:</b> {money_L(impacto)}/mes (año 1).<br/>"
        f"• <b>Riesgo y capacidad de pago:</b> DSCR <b>{ds:.2f}</b>; peor mes neto <b>{money_L(peor)}</b>.<br/>"
        f"• <b>Propuesta técnica:</b> {num(kwp,2)} kWp para cobertura {cobertura_objetivo*100:.0f}% (sin exportación).<br/>"
        f"• <b>Recomendación:</b> {recomend}"
    )

    return [box_paragraph(concl, pal, content_w, font_size=10)]


def build_page_1(resultado: Dict[str, Any], datos, paths, pal, styles, content_w):

    story = []

    sizing = resultado.get("sizing", {})
    energia = resultado.get("energia", {})
    financiero = resultado.get("financiero", {})

    fecha = datetime.now().strftime("%Y-%m-%d")

    story.append(Paragraph("Reporte Ejecutivo — Evaluación Fotovoltaica", styles["Title"]))
    story.append(Spacer(1, 10))

    story += p1_tabla_cliente(datos, sizing, fecha, pal, content_w)
    story += p1_tabla_solucion_unica(datos, sizing, energia, financiero, pal, content_w)
    story += p1_tabla_decision(financiero, pal, content_w)
    story += p1_conclusion(financiero, sizing, datos, pal, content_w)

    story.append(PageBreak())

    return story

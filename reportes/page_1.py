# reportes/page_1.py
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict

from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Spacer, PageBreak

# OJO: estos helpers deben existir en tu repo en reportes/helpers_pdf.py
# Ajusta el import si tu archivo se llama distinto.
from core.result_accessors import get_sizing, get_kwp_dc, get_capex_L
from .helpers_pdf import (
    section_bar,
    tabla_4cols,
    tabla_2cols,
    make_table,
    table_style_uniform,
    box_paragraph,
)

# Si money_L / num están en core/rutas.py (como tu app.py), importalos así:
from core.rutas import money_L, num


def _getcampo(x, k, default=""):
    if isinstance(x, dict):
        return x.get(k, default)
    return getattr(x, k, default)


# ---------------------------
# Página 1 (tus bloques)
# ---------------------------
def p1_tabla_cliente(datos, sizing, fecha, pal, content_w):
    story = []
    story.append(section_bar("Datos del cliente y situación energética", pal, content_w))
    story.append(Spacer(1, 6))

    consumo_anual = float((sizing or {}).get("consumo_anual", 0.0) or 0.0)
    tarifa_energia = float(_getcampo(datos, "tarifa_energia", 0.0) or 0.0)
    cargos_fijos = float(_getcampo(datos, "cargos_fijos", 0.0) or 0.0)

    rows = [
        ["Cliente", _getcampo(datos, "cliente", ""), "Ubicación", _getcampo(datos, "ubicacion", "")],
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


def p1_tabla_solucion_unica(datos, kwp, capex, ds, estado, pal, content_w):
    from reportlab.platypus import TableStyle, Spacer

    prod_base_kwh_kwp_mes = float(_getcampo(datos, "prod_base_kwh_kwp_mes", 0.0) or 0.0)
    tasa_anual = float(_getcampo(datos, "tasa_anual", 0.0) or 0.0)
    plazo_anios = int(_getcampo(datos, "plazo_anios", 0) or 0)
    porcentaje_financiado = float(_getcampo(datos, "porcentaje_financiado", 0.0) or 0.0)
    cobertura_objetivo = float(_getcampo(datos, "cobertura_objetivo", 0.0) or 0.0)

    prod_anual = float(kwp) * prod_base_kwh_kwp_mes * 12.0
    n_paneles = int(math.ceil(float(kwp) * 1000.0 / 550.0)) if float(kwp) > 0 else 0
    panel_wp = 550

    estado_txt = (estado or "").replace("■", "").replace("✅", "").replace("⚠️", "").replace("❌", "").strip()

    barra = section_bar("Solución propuesta e indicadores clave", pal, content_w)

    data = [
        ["Dato", "Valor", "Dato", "Valor"],
        [
            "Cobertura objetivo",
            f"{cobertura_objetivo*100:.0f}%",
            "Financiamiento",
            f"{tasa_anual*100:.2f}% | {int(plazo_anios)} años | {porcentaje_financiado*100:.0f}%",
        ],
        ["Sistema", f"{num(kwp,2)} kWp", "CAPEX", money_L(capex)],
        ["Producción anual est.", f"{prod_anual:,.0f} kWh/año", "DSCR", num(ds,2)],
        ["Módulos FV", f"{n_paneles} × {int(panel_wp)} Wp", "Estado", estado_txt],
    ]

    t = make_table(data, content_w, ratios=[1.25, 2.15, 1.25, 2.15], repeatRows=1)

    u = estado_txt.upper()
    bg_estado = pal["OK"] if "VIABLE" in u else pal["WARN"] if "MARGINAL" in u else pal["BAD"]

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

def p1_tabla_decision(decision, cuota_mensual, plazo_anios, pal, content_w):
    story = []
    story.append(section_bar("Decisión del cliente (mensual)", pal, content_w))
    story.append(Spacer(1, 6))

    pago_actual = float((decision or {}).get("pago_actual", 0.0) or 0.0)
    pago_residual = float((decision or {}).get("pago_residual", 0.0) or 0.0)
    cuota = float((decision or {}).get("cuota_fv", cuota_mensual) or 0.0)
    pago_total = float((decision or {}).get("pago_total_fv", pago_residual + cuota) or 0.0)
    ahorro = float((decision or {}).get("ahorro_mensual", pago_actual - pago_total) or 0.0)

    rows = [
        ["Pago actual ENEE (sin FV)", money_L(pago_actual)],
        ["Pago ENEE con FV (residual)", money_L(pago_residual)],
        ["Cuota de financiamiento", money_L(cuota)],
        ["Pago total con FV (ENEE + cuota)", money_L(pago_total)],
        ["Ahorro neto mensual estimado", money_L(ahorro)],
        [f"Pago después del año {int(plazo_anios)} (solo ENEE residual)", money_L(pago_residual)],
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


def p1_conclusion(impacto, ds, peor, kwp, cobertura_objetivo, estado, pal, content_w):
    recomend = (
        "Se recomienda avanzar a visita técnica y propuesta final."
        if "VIABLE" in (estado or "").upper()
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
    """
    Page 1 versión GitHub = tu Page 1 local.
    No pedimos content_w desde builder; lo calculamos aquí.
    """
    # content width estándar carta con márgenes típicos
    page_w, _ = letter
    left_margin = 36
    right_margin = 36
    content_w = page_w - left_margin - right_margin

    story = []

    sizing = get_sizing(resultado)
    eval_ = (resultado or {}).get("evaluacion", {}) or {}
    decision = (resultado or {}).get("decision", {}) or {}

    fecha = datetime.now().strftime("%Y-%m-%d")

    kwp = get_kwp_dc(resultado)
    capex = get_capex_L(resultado)

    ds = float(eval_.get("dscr", 0.0) or 0.0)
    impacto = float(decision.get("ahorro_mensual", 0.0) or 0.0)
    peor = float(eval_.get("peor_mes", 0.0) or 0.0)
    estado = str(eval_.get("estado", "") or "")

    plazo_anios = int(_getcampo(datos, "plazo_anios", 0) or 0)
    cobertura_objetivo = float(_getcampo(datos, "cobertura_objetivo", 0.0) or 0.0)

    story.append(Paragraph("Reporte Ejecutivo — Evaluación Fotovoltaica", styles["Title"]))
    story.append(Spacer(1, 10))

    story += p1_tabla_cliente(datos, sizing, fecha, pal, content_w)
    story += p1_tabla_solucion_unica(datos, kwp, capex, ds, estado, pal, content_w)
    story += p1_tabla_decision(decision, (resultado or {}).get("cuota_mensual", 0.0), plazo_anios, pal, content_w)
    story += p1_conclusion(impacto, ds, peor, kwp, float(_getcampo(datos,"cobertura_objetivo",0.0)), estado, pal, content_w)

    story.append(PageBreak())
    return story

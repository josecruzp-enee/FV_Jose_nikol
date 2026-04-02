from __future__ import annotations

from datetime import datetime
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
# CLIENTE
# =========================================================

def p1_tabla_cliente(datos, sizing, fecha, pal, content_w):

    consumo_12m = get_field(datos, "consumo_12m", [])
    consumo_anual = sum(consumo_12m) if isinstance(consumo_12m, list) else 0.0

    tarifa = float(get_field(datos, "tarifa_energia", 0.0))
    cargos = float(get_field(datos, "cargos_fijos", 0.0))

    rows = [
        ["Cliente", get_field(datos, "cliente", ""), "Ubicación", get_field(datos, "ubicacion", "")],
        ["Fecha", fecha, "Consumo anual", f"{consumo_anual:,.0f} kWh/año"],
        ["Tarifa energía", f"{tarifa:.3f} L/kWh", "Cargos fijos", f"{money_L(cargos)}/mes"],
    ]

    t = tabla_4cols(
        header=["Dato", "Valor", "Dato", "Valor"],
        rows=rows,
        content_w=content_w,
        pal=pal,
        font_header=9,
        font_body=9,
    )

    return [section_bar("Datos del cliente y situación energética", pal, content_w),
            Spacer(1, 6), t, Spacer(1, 12)]


# =========================================================
# SOLUCIÓN
# =========================================================

def p1_tabla_solucion_unica(datos, sizing, energia, financiero, pal, content_w):

    kwp = float(leer(sizing, "kwp_dc", leer(sizing, "pdc_kw", 0.0)))
    capex = float(leer(financiero, "capex_L", 0.0))

    energia_12m = leer(energia, "energia_util_12m", [])
    if isinstance(energia_12m, list) and energia_12m:
        prod_anual = sum(energia_12m)
    else:
        prod_anual = 0.0
    

    n_paneles = int(leer(sizing, "n_paneles", 0))
    panel_wp = int((kwp * 1000) / n_paneles) if n_paneles > 0 else 0

    tasa = float(get_field(datos, "tasa_anual", 0.0))
    plazo = int(get_field(datos, "plazo_anios", 0))
    pct = float(get_field(datos, "porcentaje_financiado", 0.0))
    consumo_12m = get_field(datos, "consumo_12m", [])
    consumo_anual = sum(consumo_12m) if isinstance(consumo_12m, list) else 0

    cobertura_real = prod_anual / consumo_anual if consumo_anual > 0 else 0

    evaluacion = leer(financiero, "evaluacion", {}) or {}

    estado_txt = str(evaluacion.get("estado", "")).upper().strip()

    # ✅ DSCR CORRECTO
    ds_val = evaluacion.get("dscr", None)
    ds_txt = "—" if ds_val is None else f"{ds_val:.2f}"

    data = [
        ["Dato", "Valor", "Dato", "Valor"],
        ["Cobertura objetivo", f"{cobertura_real*80:.1f}%",
         "Financiamiento", f"{tasa*100:.2f}% | {plazo} años | {pct*100:.0f}%"],
        ["Sistema", f"{num(kwp,2)} kWp", "CAPEX", money_L(capex)],
        ["Producción anual", f"{prod_anual:,.0f} kWh/año", "DSCR", ds_txt],
        ["Módulos FV", f"{n_paneles} × {panel_wp} Wp", "Estado", estado_txt],
    ]

    t = make_table(data, content_w, ratios=[1.25, 2.15, 1.25, 2.15], repeatRows=1)
    t.setStyle(table_style_uniform(pal, font_header=9, font_body=9))

    return [section_bar("Solución propuesta e indicadores clave", pal, content_w),
            Spacer(1, 6), t, Spacer(1, 12)]


# =========================================================
# DECISIÓN
# =========================================================

def p1_tabla_decision(financiero, pal, content_w):

    tabla = leer(financiero, "tabla_12m", [])

    if tabla:
        pago_actual = sum(x["factura_base_L"] for x in tabla) / 12
        pago_residual = sum(x["pago_enee_L"] for x in tabla) / 12
    else:
        pago_actual = pago_residual = 0.0

    cuota = float(leer(financiero, "cuota_mensual", 0.0))

    pago_total = pago_residual + cuota
    ahorro = pago_actual - pago_total

    rows = [
        ["Pago actual ENEE (sin FV)", money_L(pago_actual)],
        ["Pago ENEE con FV (residual)", money_L(pago_residual)],
        ["Cuota de financiamiento", money_L(cuota)],
        ["Pago total con FV", money_L(pago_total)],
        ["Ahorro neto mensual", money_L(ahorro)],
    ]

    t = tabla_2cols(
        header=["Concepto", "Monto (L/mes)"],
        rows=rows,
        content_w=content_w,
        pal=pal,
        highlight_row=4,
    )

    return [section_bar("Decisión del cliente (mensual)", pal, content_w),
            Spacer(1, 6), t, Spacer(1, 12)]


# =========================================================
# CONCLUSIÓN
# =========================================================

def p1_conclusion(financiero, sizing, datos, pal, content_w):

    evaluacion = leer(financiero, "evaluacion", {}) or {}

    ds_val = evaluacion.get("dscr", None)
    ds_txt = "—" if ds_val is None else f"{ds_val:.2f}"

    estado = str(evaluacion.get("estado", "")).upper()

    impacto = float(leer(financiero, "ahorro_mensual", 0.0))
    peor = float(evaluacion.get("peor_mes", 0.0))

    kwp = float(leer(sizing, "kwp_dc", 0.0))
    cobertura = float(get_field(datos, "cobertura_objetivo", 0.0))

    concl = f"""
    <b>Conclusión ejecutiva</b><br/><br/>
    • Impacto financiero: {money_L(impacto)}/mes<br/>
    • DSCR: <b>{ds_txt}</b><br/>
    • Peor mes: <b>{money_L(peor)}</b><br/>
    • Sistema: {kwp:.2f} kWp<br/>
    • Cobertura objetivo: {cobertura_real*80:.1f}%<br/>
    """

    return [box_paragraph(concl, pal, content_w)]


# =========================================================
# ORQUESTADOR
# =========================================================

def build_page_1(resultado, datos, paths, pal, styles, content_w, safe_image):

    sizing = leer(resultado, "sizing", {})
    energia = leer(resultado, "energia", {})
    financiero = leer(resultado, "financiero", {})

    fecha = datetime.now().strftime("%Y-%m-%d")

    story = []

    story.append(Paragraph("Reporte Ejecutivo — Evaluación Fotovoltaica", styles["Title"]))
    story.append(Spacer(1, 10))

    story += p1_tabla_cliente(datos, sizing, fecha, pal, content_w)
    story += p1_tabla_solucion_unica(datos, sizing, energia, financiero, pal, content_w)
    story += p1_tabla_decision(financiero, pal, content_w)
    story += p1_conclusion(financiero, sizing, datos, pal, content_w)

    story.append(PageBreak())

    return story

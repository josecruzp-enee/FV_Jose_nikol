# -*- coding: utf-8 -*-
# reportes/analisis_financiero.py

from __future__ import annotations

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, PageBreak, TableStyle

from reportes.helpers_pdf import (
    make_table,
    table_style_uniform,
    box_paragraph,
    get_field,
    money_L,
)


# =========================================================
# CAPÍTULO 3
# ANÁLISIS FINANCIERO
# =========================================================
# Responsabilidad:
# - Presentar la evolución del préstamo.
# - Mostrar amortización anual.
# - Mostrar CAPEX, prima, monto financiado, tasa y plazo.
# - Mostrar lectura ejecutiva del financiamiento.
#
# Reglas de mantenimiento:
# - No cambiar la firma de build_analisis_financiero().
# - No cambiar nombres de variables usadas por otros módulos.
# - No mover cálculos todavía.
# - Mantener amortizacion_anual() como fallback compatible.
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
# 2. FALLBACK: AMORTIZACIÓN ANUAL
# =========================================================
# Compatible con plazo en años o meses.
# Se usa solo cuando financiero["tabla_amortizacion"] no existe.
# =========================================================

def amortizacion_anual(
    principal: float,
    tasa_anual: float,
    cuota_mensual: float,
    plazo_anios: int | None = None,
    plazo_meses: int | None = None,
) -> List[Dict[str, float]]:

    principal = float(principal)
    tasa_anual = float(tasa_anual)
    cuota_mensual = float(cuota_mensual)

    # =====================================================
    # Compatibilidad
    # =====================================================

    if plazo_meses is None:

        plazo_anios = int(plazo_anios or 0)

        if plazo_anios <= 0:
            raise ValueError("Plazo inválido.")

        plazo_meses = plazo_anios * 12

    else:

        plazo_meses = int(plazo_meses)

        if plazo_meses <= 0:
            raise ValueError("Plazo inválido.")

        plazo_anios = (plazo_meses + 11) // 12

    tasa_m = tasa_anual / 12.0
    saldo = principal

    out: List[Dict[str, float]] = []

    meses_transcurridos = 0

    for anio in range(1, plazo_anios + 1):

        interes_y = 0.0
        principal_y = 0.0
        pago_y = 0.0

        for _ in range(12):

            if saldo <= 0:
                break

            if meses_transcurridos >= plazo_meses:
                break

            interes_m = saldo * tasa_m
            principal_m = cuota_mensual - interes_m

            if principal_m > saldo:
                principal_m = saldo

            saldo -= principal_m

            interes_y += interes_m
            principal_y += principal_m
            pago_y += interes_m + principal_m

            meses_transcurridos += 1

        out.append(
            {
                "anio": anio,
                "meses_acumulados": meses_transcurridos,
                "pago_anual": float(pago_y),
                "interes_anual": float(interes_y),
                "principal_anual": float(principal_y),
                "saldo_fin": float(max(0.0, saldo)),
            }
        )

        if saldo <= 0:
            break

    return out


# =========================================================
# 3. ORQUESTADOR DEL CAPÍTULO
# =========================================================
# Esta función es llamada desde BLOQUES_REPORTE.
# Mantener firma por compatibilidad.
# =========================================================

def build_analisis_financiero(
    resultado: Dict[str, Any],
    datos: Any,
    paths: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):

    story: List[Any] = []

    financiero = leer(resultado, "financiero", {}) or {}
    sistema_fv = get_field(datos, "sistema_fv", {}) or {}

    capex = float(leer(financiero, "capex_L", 0.0))

    cuota = float(
        leer(
            financiero,
            "cuota_mensual_L",
            leer(financiero, "cuota_mensual", 0.0),
        )
    )

    pct_fin = float(
        leer(
            financiero,
            "porcentaje_financiado",
            sistema_fv.get(
                "porcentaje_financiado",
                get_field(datos, "porcentaje_financiado", 1.0),
            ),
        )
    )
    pct_fin = max(0.0, min(1.0, pct_fin))

    usa_financiamiento = bool(
        leer(
            financiero,
            "usa_financiamiento",
            sistema_fv.get("usa_financiamiento", pct_fin > 0),
        )
    )

    prima_pct = float(
        leer(
            financiero,
            "prima_pct",
            max(0.0, 1.0 - pct_fin),
        )
    )

    prima_L = float(
        leer(
            financiero,
            "prima_L",
            capex * prima_pct,
        )
    )

    principal = float(
        leer(
            financiero,
            "monto_financiado_L",
            capex * pct_fin,
        )
    )

    tasa_anual = float(
        leer(
            financiero,
            "tasa_anual",
            sistema_fv.get(
                "tasa_anual",
                get_field(datos, "tasa_anual", 0.0),
            ),
        )
    )

    cat = leer(financiero, "cat", None)

    plazo_anios = int(
        leer(
            financiero,
            "plazo_anios",
            sistema_fv.get(
                "plazo_anios",
                get_field(datos, "plazo_anios", 0),
            ),
        )
    )

    plazo_meses = int(
        leer(
            financiero,
            "plazo_meses",
            plazo_anios * 12,
        )
    )

    nombre_financiamiento = str(
        leer(
            financiero,
            "nombre_financiamiento",
            "Financiamiento seleccionado" if usa_financiamiento else "Pago de contado",
        )
    )

    entidad_financiera = str(
        leer(
            financiero,
            "entidad_financiera",
            "",
        ) or ""
    )

    nota_financiamiento = str(
        leer(
            financiero,
            "nota_financiamiento",
            "",
        ) or ""
    )

    # =====================================================
    # CASO 1: PAGO DE CONTADO
    # =====================================================

    if (not usa_financiamiento) or principal <= 0 or pct_fin <= 0:

        story.append(
            Paragraph("Análisis económico — Pago de contado", styles["Title"])
        )
        story.append(Spacer(1, 10))

        nota = (
            "<b>Lectura ejecutiva</b><br/>"
            f"• Modalidad de pago: <b>Contado</b><br/>"
            f"• CAPEX total estimado: <b>{money_L(capex)}</b><br/>"
            "• Monto financiado: <b>L 0.00</b><br/>"
            "• Este escenario no contempla préstamo bancario, "
            "por lo que no aplica prima financiera, cuota mensual, "
            "plazo, tasa de interés, amortización ni DSCR asociado a deuda."
        )

        if nota_financiamiento:
            nota += f"<br/><br/><i>{nota_financiamiento}</i>"

        story.append(box_paragraph(nota, pal, content_w, font_size=10))
        story.append(PageBreak())

        return story

    # =====================================================
    # CASO 2: FINANCIAMIENTO
    # =====================================================

    story.append(
        Paragraph("Financiamiento — Evolución del Préstamo", styles["Title"])
    )
    story.append(Spacer(1, 10))

    anual = leer(financiero, "tabla_amortizacion", [])

    if not anual:
        anual = amortizacion_anual(
            principal=principal,
            tasa_anual=tasa_anual,
            cuota_mensual=cuota,
            plazo_anios=plazo_anios,
            plazo_meses=plazo_meses,
        )

    header = [
        "Año",
        "Cuota (L/mes)",
        "Pago anual (L)",
        "Interés (L)",
        "Principal (L)",
        "Saldo fin (L)",
    ]

    rows: List[List[str]] = []

    for a in anual:

        rows.append(
            [
                str(int(a.get("anio", 0))),
                f"{cuota:,.2f}",
                f"{float(a.get('pago_anual', 0)):,.0f}",
                f"{float(a.get('interes_anual', 0)):,.0f}",
                f"{float(a.get('principal_anual', 0)):,.0f}",
                f"{float(a.get('saldo_fin', 0)):,.0f}",
            ]
        )

    if not rows:
        rows = [["—", "—", "—", "—", "—", "—"]]

    t = make_table(
        [header] + rows,
        content_w,
        ratios=[0.8, 1.4, 1.5, 1.3, 1.3, 1.4],
        repeatRows=1,
    )

    t.setStyle(table_style_uniform(pal, font_header=9, font_body=9))

    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(t)
    story.append(Spacer(1, 10))

    saldo_ultimo = principal

    if anual:
        saldo_ultimo = float(anual[-1].get("saldo_fin", principal))

    cat_txt = ""
    if cat is not None:
        try:
            cat_txt = f"• CAT referencial: <b>{float(cat) * 100:.2f}%</b><br/>"
        except Exception:
            cat_txt = ""

    entidad_txt = ""
    if entidad_financiera:
        entidad_txt = f"• Entidad financiera: <b>{entidad_financiera}</b><br/>"

    nota_extra = ""
    if nota_financiamiento:
        nota_extra = f"<br/><i>{nota_financiamiento}</i>"

    nota = (
        "<b>Lectura ejecutiva</b><br/>"
        f"• Producto financiero: <b>{nombre_financiamiento}</b><br/>"
        f"{entidad_txt}"
        f"• CAPEX total: <b>{money_L(capex)}</b><br/>"
        f"• Prima estimada: <b>{money_L(prima_L)}</b> ({prima_pct * 100:.2f}%).<br/>"
        f"• Monto financiado: <b>{money_L(principal)}</b> ({pct_fin * 100:.2f}% del CAPEX).<br/>"
        f"• Plazo: <b>{plazo_meses}</b> meses / <b>{plazo_anios}</b> años.<br/>"
        f"• Tasa anual referencial: <b>{tasa_anual * 100:.2f}%</b><br/>"
        f"{cat_txt}"
        f"• Cuota fija estimada: <b>{money_L(cuota)}/mes</b><br/>"
        f"• Saldo al cierre del plazo: <b>{money_L(saldo_ultimo)}</b>."
        f"{nota_extra}"
    )

    story.append(box_paragraph(nota, pal, content_w, font_size=10))

    story.append(PageBreak())

    return story

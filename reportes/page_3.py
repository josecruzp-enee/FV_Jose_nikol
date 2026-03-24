from __future__ import annotations

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, PageBreak, TableStyle

from .helpers_pdf import make_table, table_style_uniform, box_paragraph, get_field, money_L


# =========================================================
# LECTURA SEGURA
# =========================================================

def leer(obj, campo, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# =========================================================
# FALLBACK — amortización
# =========================================================

def amortizacion_anual(
    principal: float,
    tasa_anual: float,
    cuota_mensual: float,
    plazo_anios: int
) -> List[Dict[str, float]]:

    tasa_m = float(tasa_anual) / 12.0
    saldo = float(principal)

    out: List[Dict[str, float]] = []

    for anio in range(1, int(plazo_anios) + 1):

        interes_y = 0.0
        principal_y = 0.0
        pago_y = 0.0

        for _ in range(12):

            if saldo <= 0:
                break

            interes_m = saldo * tasa_m
            principal_m = float(cuota_mensual) - interes_m

            if principal_m > saldo:
                principal_m = saldo

            saldo -= principal_m

            interes_y += interes_m
            principal_y += principal_m
            pago_y += interes_m + principal_m

        out.append(
            {
                "anio": float(anio),
                "pago_anual": float(pago_y),
                "interes_anual": float(interes_y),
                "principal_anual": float(principal_y),
                "saldo_fin": float(max(0.0, saldo)),
            }
        )

    return out


# =========================================================
# PAGE 3
# =========================================================

def build_page_3(
    resultado: Dict[str, Any],
    datos: Any,
    paths: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):

    story: List[Any] = []

    story.append(
        Paragraph("Financiamiento — Evolución del Préstamo", styles["Title"])
    )

    story.append(Spacer(1, 10))

    # =====================================================
    # LECTURA SEGURA
    # =====================================================

    financiero = leer(resultado, "financiero", {}) or {}

    capex = float(leer(financiero, "capex_L", 0.0))
    cuota = float(leer(financiero, "cuota_mensual", 0.0))

    pct_fin = float(get_field(datos, "porcentaje_financiado", 1.0))
    pct_fin = max(0.0, min(1.0, pct_fin))

    principal = capex * pct_fin

    tasa_anual = float(get_field(datos, "tasa_anual", 0.0))
    plazo_anios = int(get_field(datos, "plazo_anios", 10))

    # =====================================================
    # TABLA DEL MOTOR
    # =====================================================

    anual = leer(financiero, "tabla_amortizacion", [])

    if not anual:
        anual = amortizacion_anual(
            principal,
            tasa_anual,
            cuota,
            plazo_anios
        )

    # =====================================================
    # TABLA PDF
    # =====================================================

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
                f"{float(a.get('pago_anual',0)):,.0f}",
                f"{float(a.get('interes_anual',0)):,.0f}",
                f"{float(a.get('principal_anual',0)):,.0f}",
                f"{float(a.get('saldo_fin',0)):,.0f}",
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

    # =====================================================
    # LECTURA EJECUTIVA
    # =====================================================

    saldo_ultimo = principal

    if anual:
        saldo_ultimo = float(anual[-1].get("saldo_fin", principal))

    nota = (

        "<b>Lectura ejecutiva</b><br/>"

        f"• Cuota fija estimada: <b>{money_L(cuota)}/mes</b> por <b>{plazo_anios}</b> años.<br/>"

        f"• Monto financiado: <b>{money_L(principal)}</b> (sobre CAPEX).<br/>"

        f"• Saldo al cierre del plazo: <b>{money_L(saldo_ultimo)}</b> (≈ 0 por redondeos)."

    )

    story.append(box_paragraph(nota, pal, content_w, font_size=10))

    story.append(PageBreak())

    return story

# reportes/page_3.py
from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer, PageBreak, TableStyle

# Ajusta este import a donde realmente estén tus helpers:
from .utils import make_table, table_style_uniform, box_paragraph



def amortizacion_anual(principal: float, tasa_anual: float, cuota_mensual: float, plazo_anios: int):
    tasa_m = float(tasa_anual) / 12.0
    saldo = float(principal)

    out = []
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
            pago_y += (interes_m + principal_m)

        out.append({
            "anio": anio,
            "pago_anual": pago_y,
            "interes_anual": interes_y,
            "principal_anual": principal_y,
            "saldo_fin": max(0.0, saldo),
        })

    return out


def build_page_3(resultado, datos, paths, pal, styles, content_w):
    story = []
    story.append(Paragraph("Financiamiento — Evolución del Préstamo", styles["Title"]))
    story.append(Spacer(1, 10))

    # ===== Entradas =====
    capex = float(resultado["sizing"]["capex_L"])
    pct_fin = float(getattr(datos, "porcentaje_financiado", 1.0))
    principal = capex * pct_fin

    tasa_anual = float(getattr(datos, "tasa_anual", 0.0))
    plazo_anios = int(getattr(datos, "plazo_anios", 10))
    cuota = float(resultado["cuota_mensual"])

    anual = amortizacion_anual(principal, tasa_anual, cuota, plazo_anios)

    # ===== Tabla =====
    header = ["Año", "Cuota (L/mes)", "Pago anual (L)", "Interés (L)", "Principal (L)", "Saldo fin (L)"]
    rows = []
    for a in anual:
        rows.append([
            str(a["anio"]),
            f"{cuota:,.0f}",
            f"{a['pago_anual']:,.0f}",
            f"{a['interes_anual']:,.0f}",
            f"{a['principal_anual']:,.0f}",
            f"{a['saldo_fin']:,.0f}",
        ])

    t = make_table(
        [header] + rows,
        content_w,
        ratios=[0.8, 1.4, 1.5, 1.3, 1.3, 1.4],
        repeatRows=1
    )
    t.setStyle(table_style_uniform(pal, font_header=9, font_body=9))
    t.setStyle(TableStyle([
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # ===== Lectura ejecutiva =====
    saldo_ultimo = anual[-1]["saldo_fin"] if anual else principal
    nota = (
        "<b>Lectura ejecutiva</b><br/>"
        f"• Cuota fija estimada: <b>{cuota:,.0f} L/mes</b> por <b>{plazo_anios}</b> años.<br/>"
        f"• Monto financiado: <b>{principal:,.0f} L</b> (sobre CAPEX).<br/>"
        f"• Saldo al cierre del plazo: <b>{saldo_ultimo:,.0f} L</b> (≈ 0 por redondeos)."
    )
    story.append(box_paragraph(nota, pal, content_w, font_size=10))

    story.append(PageBreak())
    return story

# reportes/page_5.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, Image


# ==========================================================
# Layout paneles
# ==========================================================

def _append_layout_paneles(story, paths, styles, content_w):
    layout = (paths or {}).get("layout_paneles")
    if layout and Path(str(layout)).exists():
        story.append(Spacer(1, 10))
        img = Image(str(layout), width=content_w, height=content_w * 0.45)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Layout de paneles no disponible.", styles["BodyText"]))
        story.append(Spacer(1, 8))


# ==========================================================
# Helpers básicos
# ==========================================================

def _sum_float(tabla: List[Dict[str, Any]], key: str) -> float:
    s = 0.0
    for r in tabla:
        s += float(r.get(key, 0.0))
    return float(s)


# ==========================================================
# Tabla Strings DC
# ==========================================================

def _tabla_strings(strings: List[Dict[str, Any]], pal, content_w):
    header = ["MPPT", "Serie (S)", "Paralelo (P)", "Vmp (V)", "Voc frío (V)", "Imp (A)", "Isc (A)"]

    rows = [header]

    for s in strings:
        rows.append([
            str(int(s["mppt"])),
            str(int(s["n_series"])),
            str(int(s["n_paralelo"])),
            f"{float(s['vmp_string_v']):.0f}",
            f"{float(s['voc_frio_string_v']):.0f}",
            f"{float(s['imp_a']):.1f}",
            f"{float(s['isc_a']):.1f}",
        ])

    colw = [
        content_w * 0.10,
        content_w * 0.12,
        content_w * 0.12,
        content_w * 0.16,
        content_w * 0.16,
        content_w * 0.17,
        content_w * 0.17,
    ]

    tbl = Table(rows, colWidths=colw, hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), pal.get("SOFT", colors.HexColor("#F5F7FA"))),
                ("TEXTCOLOR", (0, 0), (-1, 0), pal.get("PRIMARY", colors.HexColor("#0B2E4A"))),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.3, pal.get("BORDER", colors.HexColor("#D7DCE3"))),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return tbl


# ==========================================================
# Página 5
# ==========================================================

def build_page_5(resultado, datos, paths, pal, styles, content_w):
    """
    Página 5 — Resumen técnico + Strings DC + Layout
    Contrato fuerte:
        resultado["tecnico"]
        resultado["financiero"]
    """

    story: List[Any] = []

    tecnico = resultado["tecnico"]
    financiero = resultado["financiero"]

    sizing = tecnico["sizing"]
    strings = tecnico["strings"]["strings"]
    energia_12m = sizing["energia_12m"]

    kwp_dc = float(sizing["kwp_dc"])
    n_paneles = int(sizing["n_paneles"])
    capex_L = float(financiero["capex_L"])

    consumo_anual_kwh = _sum_float(energia_12m, "consumo_kwh")
    fv_anual_kwh = _sum_float(energia_12m, "generacion_kwh")
    ahorro_anual_L = float(financiero.get("ahorro_anual_L", 0.0))

    story.append(Paragraph("Resumen técnico", styles["Title"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"Sistema FV estimado: {kwp_dc:.2f} kWp DC", styles["BodyText"]))
    story.append(Paragraph(f"Número de paneles: {n_paneles}", styles["BodyText"]))
    story.append(Paragraph(f"CAPEX estimado: L {capex_L:,.2f}", styles["BodyText"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Consumo anual (12m): {consumo_anual_kwh:,.0f} kWh", styles["BodyText"]))
    story.append(Paragraph(f"Generación FV útil (12m): {fv_anual_kwh:,.0f} kWh", styles["BodyText"]))
    story.append(Paragraph(f"Ahorro anual estimado (12m): L {ahorro_anual_L:,.2f}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    # ===== Strings DC =====
    story.append(Paragraph("Configuración eléctrica (Strings DC)", styles["Heading2"]))
    story.append(Spacer(1, 6))

    if strings:
        story.append(_tabla_strings(strings, pal, content_w))
    else:
        story.append(Paragraph("<i>No hay configuración de strings disponible.</i>", styles["BodyText"]))

    story.append(Spacer(1, 10))

    # ===== Layout paneles =====
    _append_layout_paneles(story, paths, styles, content_w)

    story.append(PageBreak())

    return story

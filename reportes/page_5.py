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
# Helpers
# ==========================================================

def _sum_float(tabla: List[Dict[str, Any]], key: str) -> float:
    return sum(float(r.get(key, 0.0)) for r in tabla)


# ==========================================================
# Tabla Strings DC
# ==========================================================

def _tabla_strings(strings: List[Dict[str, Any]], n_inversores: int, pal, content_w):

    header = ["Inv", "MPPT", "Serie (S)", "Paralelo (P)", "Vmp (V)", "Voc frío (V)", "Imp (A)", "Isc (A)"]
    rows = [header]

    for inv in range(1, n_inversores + 1):
        for s in strings:
            rows.append([
                str(inv),
                str(int(s.get("mppt", 0))),
                str(int(s.get("n_series", 0))),
                str(int(s.get("n_paralelo", 0))),
                f"{float(s.get('vmp_string_v', 0.0)):.0f}",
                f"{float(s.get('voc_frio_string_v', 0.0)):.0f}",
                f"{float(s.get('imp_a', 0.0)):.1f}",
                f"{float(s.get('isc_a', 0.0)):.1f}",
            ])

    colw = [
        content_w * 0.08,
        content_w * 0.08,
        content_w * 0.10,
        content_w * 0.12,
        content_w * 0.15,
        content_w * 0.17,
        content_w * 0.15,
        content_w * 0.15,
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
# Tabla Resumen Técnico
# ==========================================================

def _tabla_resumen_tecnico(data, pal, content_w):

    colw = [content_w * 0.55, content_w * 0.45]

    tbl = Table(data, colWidths=colw, hAlign="LEFT")

    tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("BACKGROUND", (0,0), (-1,0), pal.get("SOFT", colors.HexColor("#F5F7FA"))),
                ("TEXTCOLOR", (0,0), (-1,0), pal.get("PRIMARY", colors.HexColor("#0B2E4A"))),

                ("ALIGN", (1,1), (-1,-1), "RIGHT"),

                ("GRID", (0,0), (-1,-1), 0.3, pal.get("BORDER", colors.HexColor("#D7DCE3"))),

                ("FONTSIZE", (0,0), (-1,-1), 10),

                ("TOPPADDING", (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]
        )
    )

    return tbl


# ==========================================================
# Página 5 — Resumen técnico
# ==========================================================

def build_page_5(resultado, datos, paths, pal, styles, content_w):

    story: List[Any] = []

    sizing = resultado.get("sizing", {})
    strings_block = resultado.get("strings", {})
    financiero = resultado.get("financiero", {})

    strings = strings_block.get("strings", [])
    tabla_12m = financiero.get("tabla_12m", [])

    # ======================================================
    # Datos técnicos
    # ======================================================

    kwp_dc = float(sizing.get("kwp_dc", sizing.get("pdc_kw", 0.0)))
    n_paneles = int(sizing.get("n_paneles", 0))

    panel_wp = (kwp_dc * 1000) / n_paneles if n_paneles > 0 else 0

    pac_kw = float(sizing.get("pac_kw", 0.0))
    n_inv = int(sizing.get("n_inversores", 1))
    inv_kw = pac_kw / n_inv if n_inv > 0 else 0

    capex_L = float(financiero.get("capex_L", 0.0))

    consumo_anual_kwh = _sum_float(tabla_12m, "consumo_kwh")
    fv_anual_kwh = _sum_float(tabla_12m, "fv_kwh")
    ahorro_anual_L = float(financiero.get("ahorro_anual_L", 0.0))

    # ======================================================
    # Tabla Resumen Técnico
    # ======================================================

    story.append(Paragraph("Resumen técnico", styles["Title"]))
    story.append(Spacer(1, 10))

    data = [
        ["Parámetro", "Valor"],
        ["Sistema FV estimado", f"{kwp_dc:.2f} kWp DC"],
        ["Número de paneles", f"{n_paneles} × {panel_wp:.0f} Wp"],
        ["Inversores", f"{n_inv} × {inv_kw:.1f} kW"],
        ["Potencia AC instalada", f"{pac_kw:.1f} kW"],
        ["CAPEX estimado", f"L {capex_L:,.2f}"],
        ["Consumo anual (12m)", f"{consumo_anual_kwh:,.0f} kWh"],
        ["Generación FV útil (12m)", f"{fv_anual_kwh:,.0f} kWh"],
        ["Ahorro anual estimado (12m)", f"L {ahorro_anual_L:,.2f}"],
    ]

    story.append(_tabla_resumen_tecnico(data, pal, content_w))
    story.append(Spacer(1, 12))

    # ======================================================
    # Strings DC
    # ======================================================

    story.append(Paragraph("Configuración eléctrica (Strings DC)", styles["Heading2"]))
    story.append(Spacer(1, 6))

    n_inversores = int(sizing.get("n_inversores", 1))

    if strings:
        story.append(_tabla_strings(strings, n_inversores, pal, content_w))
    else:
        story.append(Paragraph("<i>No hay configuración de strings disponible.</i>", styles["BodyText"]))

    story.append(Spacer(1, 10))

    # ======================================================
    # Layout paneles
    # ======================================================

    _append_layout_paneles(story, paths, styles, content_w)

    story.append(PageBreak())

    return story

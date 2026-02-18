# reportes/page_2.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from reportlab.platypus import Spacer, Paragraph, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import inch

from .helpers_pdf import make_table, table_style_uniform, box_paragraph


def _img_si_existe(path: str, *, width: float, height: float):
    """
    En Streamlit Cloud a veces el PNG no está generado.
    Esto evita que el PDF reviente por Image().
    """
    p = Path(str(path))
    if not p.exists() or p.stat().st_size < 1500:
        return None
    try:
        return Image(str(p), width=width, height=height)
    except Exception:
        return None


def build_page_2(resultado: Dict[str, Any], datos, paths, pal, styles):
    story = []
    # si no pasas content_w desde el generador, usamos uno estable:
    content_w = 540  # ~ letter - márgenes (suficiente para layout consistente)

    story.append(Paragraph("Reporte de Demanda / Energía", styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Energía mensual (Consumo vs FV útil vs ENEE)", styles["H2b"]))
    story.append(Spacer(1, 6))

    header = ["Mes", "Consumo (kWh)", "FV útil (kWh)", "ENEE (kWh)"]

    tabla_12m = resultado.get("tabla_12m", [])
    rows = [
        [
            r.get("mes", ""),
            f"{float(r.get('consumo_kwh', 0.0)):,.0f}",
            f"{float(r.get('fv_kwh', 0.0)):,.0f}",
            f"{float(r.get('kwh_enee', 0.0)):,.0f}",
        ]
        for r in tabla_12m
    ]

    t = make_table([header] + rows, content_w, ratios=[0.65, 2.1, 2.1, 2.1], repeatRows=1)
    t.setStyle(table_style_uniform(pal, font_header=8, font_body=8))
    t.setStyle(TableStyle([
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # ===== Charts (2 columnas) =====
    GAP = 10
    CH_W = (content_w - GAP) / 2.0
    CH_H = 2.15 * inch

    img1 = _img_si_existe(paths.get("chart_energia", ""), width=CH_W, height=CH_H)
    img2 = _img_si_existe(paths.get("chart_generacion", ""), width=CH_W, height=CH_H)

    # Si falta alguna imagen, colocamos un texto para NO romper
    c1 = img1 if img1 else Paragraph("<i>(Sin imagen: chart_energia)</i>", styles["BodyText"])
    c2 = img2 if img2 else Paragraph("<i>(Sin imagen: chart_generacion)</i>", styles["BodyText"])

    charts = Table([[c1, c2]], colWidths=[CH_W, CH_W])
    charts.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("COLSEP", (0, 0), (-1, -1), GAP),
    ]))
    story.append(charts)
    story.append(Spacer(1, 8))

    interp = (
        "<b>Interpretación</b><br/>"
        "• Esta página muestra energía (kWh).<br/>"
        "• El dimensionamiento evita sobredimensionar en meses de baja demanda.<br/>"
        f"• Cobertura objetivo: <b>{datos.cobertura_objetivo*100:.0f}%</b>."
    )
    story.append(box_paragraph(interp, pal, content_w, font_size=9))

    story.append(PageBreak())
    return story

# reportes/helpers_pdf.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle


def make_table(data: List[List[Any]], content_w: float, *, ratios=None, repeatRows: int = 0) -> Table:
    """
    Crea tabla con anchos proporcionales.
    """
    if ratios is None:
        ratios = [1] * len(data[0])

    total = float(sum(ratios)) if ratios else 1.0
    col_widths = [content_w * (float(r) / total) for r in ratios]

    t = Table(data, colWidths=col_widths, repeatRows=repeatRows)
    return t


def table_style_uniform(pal: Dict[str, Any], *, font_header: int = 9, font_body: int = 9) -> TableStyle:
    """
    Estilo uniforme tipo "ejecutivo".
    pal esperado: PRIMARY, BORDER, SOFT (y opcional OK/WARN/BAD).
    """
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), font_header),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), pal.get("PRIMARY", colors.HexColor("#0B2E4A"))),

        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), font_body),

        ("GRID", (0, 0), (-1, -1), 0.6, pal.get("BORDER", colors.HexColor("#D7DCE3"))),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 1), (-1, -1), pal.get("SOFT", colors.HexColor("#F5F7FA"))),
    ])


def box_paragraph(html: str, pal: Dict[str, Any], content_w: float, *, font_size: int = 9) -> Table:
    """
    Caja con borde + fondo suave (usa Paragraph con HTML).
    """
    style = ParagraphStyle(
        name="Box",
        fontName="Helvetica",
        fontSize=font_size,
        leading=font_size + 2,
        spaceAfter=0,
        spaceBefore=0,
    )
    p = Paragraph(html, style)

    t = Table([[p]], colWidths=[content_w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pal.get("SOFT", colors.HexColor("#F5F7FA"))),
        ("BOX", (0, 0), (-1, -1), 0.8, pal.get("BORDER", colors.HexColor("#D7DCE3"))),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


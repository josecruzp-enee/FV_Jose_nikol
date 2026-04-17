from __future__ import annotations

from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle


# ==========================================================
# GET FIELD
# ==========================================================

def get_field(x: Any, key: str, default: Any = "") -> Any:
    if isinstance(x, dict):
        return x.get(key, default)
    return getattr(x, key, default)


# ==========================================================
# SECTION BAR
# ==========================================================

def section_bar(texto: str, pal: Dict[str, Any], content_w: float):
    style = ParagraphStyle(
        name="section_bar",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.white,
        leftIndent=6,
    )

    p = Paragraph(texto, style)
    t = Table([[p]], colWidths=[content_w])

    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pal.get("PRIMARY")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    return t


# ==========================================================
# MAKE TABLE
# ==========================================================

def make_table(data, content_w, ratios=None, repeatRows=0):

    if ratios:
        s = float(sum(ratios))
        col_widths = [content_w * (r / s) for r in ratios]
    else:
        ncols = len(data[0]) if data else 1
        col_widths = [content_w / ncols] * ncols

    return Table(data, colWidths=col_widths, repeatRows=repeatRows)


# ==========================================================
# TABLE STYLE
# ==========================================================

def table_style_uniform(pal, font_header=9, font_body=9):

    return TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), pal.get("PRIMARY")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), font_header),

        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), font_body),

        ("GRID", (0, 0), (-1, -1), 0.6, pal.get("BORDER")),
        ("BACKGROUND", (0, 1), (-1, -1), pal.get("SOFT")),

    ])


# ==========================================================
# BOX PARAGRAPH
# ==========================================================

def box_paragraph(html_text, pal, content_w, font_size=10):

    style = ParagraphStyle(
        name="box",
        fontName="Helvetica",
        fontSize=font_size,
        leading=font_size + 2,
    )

    p = Paragraph(html_text, style)
    t = Table([[p]], colWidths=[content_w])

    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pal.get("SOFT")),
        ("BOX", (0, 0), (-1, -1), 0.8, pal.get("BORDER")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return t


# ==========================================================
# MONEY
# ==========================================================

def money_L(x: float, dec: int = 2) -> str:
    try:
        x = float(x)
    except Exception:
        x = 0.0

    return f"L {x:,.{dec}f}"

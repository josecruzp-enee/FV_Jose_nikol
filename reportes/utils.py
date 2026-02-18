from __future__ import annotations

from typing import List, Sequence, Optional
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle


def make_table(data, content_w, ratios=None, repeatRows=0):
    if ratios:
        s = float(sum(ratios))
        col_widths = [content_w * (r / s) for r in ratios]
    else:
        ncols = len(data[0])
        col_widths = [content_w / ncols] * ncols

    return Table(data, colWidths=col_widths, repeatRows=repeatRows)


def table_style_uniform(pal, font_header=9, font_body=9):
    primary = pal.get("PRIMARY", colors.HexColor("#0B2E4A"))
    border = pal.get("BORDER", colors.HexColor("#D7DCE3"))

    return TableStyle([
        ("BACKGROUND", (0,0), (-1,0), primary),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), font_header),

        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), font_body),

        ("GRID", (0,0), (-1,-1), 0.5, border),
    ])


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
        ("BACKGROUND", (0,0), (-1,-1), pal.get("SOFT")),
        ("BOX", (0,0), (-1,-1), 0.75, pal.get("BORDER")),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))

    return t

def money_L(x: float, dec: int = 0) -> str:
    """
    Formato monetario Lempiras consistente para tablas PDF.
    dec=0 por defecto para tablas ejecutivas.
    """
    try:
        v = float(x)
    except Exception:
        return "L 0"
    fmt = f"{{:,.{int(dec)}f}}"
    return f"L {fmt.format(v)}"


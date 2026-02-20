from __future__ import annotations

from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

from core.rutas import money_L as _money_L_core




def get_field(x: Any, key: str, default: Any = "") -> Any:
    if isinstance(x, dict):
        return x.get(key, default)
    return getattr(x, key, default)

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
        ("BACKGROUND", (0, 0), (-1, -1), pal["PRIMARY"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def make_table(data: List[List[Any]], content_w: float, *, ratios=None, repeatRows: int = 0):
    if ratios:
        s = float(sum(ratios))
        col_widths = [content_w * (r / s) for r in ratios]
    else:
        ncols = len(data[0]) if data else 1
        col_widths = [content_w / ncols] * ncols
    return Table(data, colWidths=col_widths, repeatRows=repeatRows)


def table_style_uniform(pal: Dict[str, Any], *, font_header=9, font_body=9):
    primary = pal.get("PRIMARY", colors.HexColor("#0B2E4A"))
    border = pal.get("BORDER", colors.HexColor("#D7DCE3"))
    soft = pal.get("SOFT", colors.HexColor("#F5F7FA"))

    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), font_header),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), font_body),
        ("GRID", (0, 0), (-1, -1), 0.6, border),
        ("BACKGROUND", (0, 1), (-1, -1), soft),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])


def tabla_4cols(header, rows, content_w, pal, font_header=9, font_body=9):
    data = [header] + rows
    t = make_table(data, content_w, ratios=[1.25, 2.15, 1.25, 2.15], repeatRows=1)
    t.setStyle(table_style_uniform(pal, font_header=font_header, font_body=font_body))
    t.setStyle(TableStyle([
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("ALIGN", (3, 1), (3, -1), "RIGHT"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
    ]))
    return t


def tabla_2cols(header, rows, content_w, pal, highlight_row=None, font_header=10, font_body=9):
    data = [header] + rows
    t = make_table(data, content_w, ratios=[2.8, 1.2], repeatRows=1)
    t.setStyle(table_style_uniform(pal, font_header=font_header, font_body=font_body))
    t.setStyle(TableStyle([("ALIGN", (1, 1), (1, -1), "RIGHT")]))
    if highlight_row is not None:
        r = highlight_row + 1
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, r), (-1, r), pal["OK"]),
            ("TEXTCOLOR", (0, r), (-1, r), colors.white),
            ("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
        ]))
    return t


def box_paragraph(html_text: str, pal: Dict[str, Any], content_w: float, *, font_size=10):
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


def money_L(x: float, dec: int = 2) -> str:
    return _money_L_core(x, dec=dec)

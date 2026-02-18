# reportes/helpers_pdf.py
from __future__ import annotations

from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle


# =========================================================
# BARRA DE SECCIÓN
# =========================================================
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
        ("BACKGROUND", (0,0), (-1,-1), pal["PRIMARY"]),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return t


# =========================================================
# TABLA BASE
# =========================================================
def make_table(data: List[List[Any]], content_w: float, *,
               ratios=None, repeatRows: int = 0):

    if ratios is None:
        ratios = [1]*len(data[0])

    total = float(sum(ratios))
    col_widths = [content_w*(r/total) for r in ratios]

    return Table(data, colWidths=col_widths, repeatRows=repeatRows)


# =========================================================
# ESTILO UNIFORME
# =========================================================
def table_style_uniform(pal: Dict[str, Any],
                        *,
                        font_header=9,
                        font_body=9):

    return TableStyle([
        ("BACKGROUND", (0,0), (-1,0), pal["PRIMARY"]),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), font_header),

        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), font_body),

        ("GRID", (0,0), (-1,-1), 0.6, pal["BORDER"]),
        ("BACKGROUND", (0,1), (-1,-1), pal["SOFT"]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ])


# =========================================================
# TABLA 4 COLUMNAS
# =========================================================
def tabla_4cols(header, rows, content_w, pal,
                font_header=9, font_body=9):

    data = [header] + rows

    t = make_table(
        data,
        content_w,
        ratios=[1.25, 2.15, 1.25, 2.15],
        repeatRows=1
    )

    t.setStyle(table_style_uniform(
        pal,
        font_header=font_header,
        font_body=font_body
    ))

    t.setStyle(TableStyle([
        ("ALIGN", (1,1), (1,-1), "RIGHT"),
        ("ALIGN", (3,1), (3,-1), "RIGHT"),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,1), (2,-1), "Helvetica-Bold"),
    ]))

    return t


# =========================================================
# TABLA 2 COLUMNAS
# =========================================================
def tabla_2cols(header, rows, content_w, pal,
                highlight_row=None,
                font_header=10,
                font_body=9):

    data = [header] + rows

    t = make_table(
        data,
        content_w,
        ratios=[2.8, 1.2],
        repeatRows=1
    )

    t.setStyle(table_style_uniform(
        pal,
        font_header=font_header,
        font_body=font_body
    ))

    t.setStyle(TableStyle([
        ("ALIGN", (1,1), (1,-1), "RIGHT"),
    ]))

    if highlight_row is not None:
        r = highlight_row + 1
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,r), (-1,r), pal["OK"]),
            ("TEXTCOLOR", (0,r), (-1,r), colors.white),
            ("FONTNAME", (0,r), (-1,r), "Helvetica-Bold"),
        ]))

    return t


# =========================================================
# CAJA TEXTO
# =========================================================
def box_paragraph(html: str, pal: Dict[str, Any],
                  content_w: float,
                  *,
                  font_size=9):

    style = ParagraphStyle(
        name="box",
        fontName="Helvetica",
        fontSize=font_size,
        leading=font_size+2,
    )

    p = Paragraph(html, style)

    t = Table([[p]], colWidths=[content_w])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), pal["SOFT"]),
        ("BOX", (0,0), (-1,-1), 0.8, pal["BORDER"]),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))

    return t

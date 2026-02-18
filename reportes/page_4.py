# reportes/page_4.py
from __future__ import annotations

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, TableStyle, PageBreak

from reportes.utils import make_table, table_style_uniform, box_paragraph, money_L


def tabla_impacto_mensual_anio1(resultado: Dict[str, Any], pal: dict, content_w: float) -> List:
    """
    Tabla comparativa año 1:
    - Pago actual
    - Con FV (ENEE)
    - FV + cuota
    - Ahorro mes
    - Ahorro acumulado
    """
    from reportlab.platypus import Spacer

    tabla = resultado.get("tabla_12m") or []
    cuota_m = float(resultado.get("cuota_mensual", 0.0))

    header = [
        "Mes",
        "Pago actual (L)",
        "Con FV (ENEE) (L)",
        "FV + cuota (L)",
        "Ahorro mes (L)",
        "Ahorro acumulado (L)",
    ]

    rows: List[List[str]] = []
    acum = 0.0

    total_pago_actual = 0.0
    total_con_fv_enee = 0.0
    total_fv_cuota = 0.0
    total_ahorro = 0.0

    for r in tabla:
        mes = int(r.get("mes", 0))
        pago_actual = float(r.get("factura_base_L", 0.0))
        con_fv_enee = float(r.get("pago_enee_L", 0.0))

        fv_cuota = con_fv_enee + cuota_m
        ahorro_mes = pago_actual - fv_cuota
        acum += ahorro_mes

        total_pago_actual += pago_actual
        total_con_fv_enee += con_fv_enee
        total_fv_cuota += fv_cuota
        total_ahorro += ahorro_mes

        rows.append([
            str(mes),
            money_L(pago_actual),
            money_L(con_fv_enee),
            money_L(fv_cuota),
            money_L(ahorro_mes),
            money_L(acum),
        ])

    # Fila total
    rows.append([
        "TOTAL",
        money_L(total_pago_actual),
        money_L(total_con_fv_enee),
        money_L(total_fv_cuota),
        money_L(total_ahorro),
        money_L(total_ahorro),
    ])

    t = make_table(
        [header] + rows,
        content_w,
        ratios=[0.8, 1.7, 1.7, 1.7, 1.45, 1.9],
        repeatRows=1,
    )
    t.setStyle(table_style_uniform(pal, font_header=9, font_body=9))

    last_row = len(rows)  # índice dentro de la tabla (header=0, rows empiezan en 1)
    t.setStyle(TableStyle([
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (5, 1), (5, -1), "Helvetica-Bold"),

        ("BACKGROUND", (0, last_row), (-1, last_row), pal.get("SOFT")),
        ("FONTNAME", (0, last_row), (-1, last_row), "Helvetica-Bold"),
        ("LINEABOVE", (0, last_row), (-1, last_row), 1.2, pal.get("PRIMARY")),

        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    return [t, Spacer(1, 10)]


def build_page_4(
    resultado: Dict[str, Any],
    datos: Any,
    paths: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):
    """
    Página 4: Tabla comparativa + bloques opcionales (config eléctrica y eléctrico referencial).
    """
    story: List = []

    story.append(Paragraph("Tabla Comparativa de Pagos", styles["Title"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Impacto mensual estimado — Año 1", styles["H2b"]))
    story.append(Spacer(1, 6))
    story += tabla_impacto_mensual_anio1(resultado, pal, content_w)

    # ===== Opcional: configuración eléctrica DC (strings) =====
    cfg_html = resultado.get("cfg_strings_html")
    if cfg_html:
        story.append(Paragraph("Configuración eléctrica (DC) — referencial", styles["H2b"]))
        story.append(Spacer(1, 6))
        story.append(box_paragraph(cfg_html, pal, content_w, font_size=9.5))
        story.append(Spacer(1, 8))

    # ===== Opcional: eléctrico referencial (AC/DC calibres y caída) =====
    elect = resultado.get("electrico_ref") or {}
    texto_pdf = elect.get("texto_pdf") or []
    disclaimer = elect.get("disclaimer")

    if texto_pdf:
        story.append(Paragraph("Conductores y canalización (referencial)", styles["H2b"]))
        story.append(Spacer(1, 6))
        bullets = "<br/>".join([f"• {line}" for line in texto_pdf])
        story.append(box_paragraph(bullets, pal, content_w, font_size=9.5))
        story.append(Spacer(1, 6))

    if disclaimer:
        story.append(Paragraph(disclaimer, styles["BodyText"]))
        story.append(Spacer(1, 8))

    # Cierre de página
    story.append(PageBreak())
    return story

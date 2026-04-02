from __future__ import annotations

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, TableStyle, PageBreak

from .helpers_pdf import make_table, table_style_uniform, box_paragraph, money_L


# =========================================================
# LECTURA SEGURA
# =========================================================

def leer(obj, campo, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# =========================================================
# TABLA IMPACTO AÑO 1
# =========================================================
def tabla_impacto_mensual_anio1(resultado: Any, pal: dict, content_w: float):

    financiero = leer(resultado, "financiero", {}) or {}

    tabla_12m = leer(financiero, "tabla_12m", [])
    cuota_m = float(leer(financiero, "cuota_mensual", 0.0))

    # 🔥 SOLO DINERO
    header = [
        "Mes",
        "Pago actual",
        "Pago ENEE",
        "Cuota ",
        "Total Pago",
        "Ahorro mes",
        "Ahorro acumulado",
    ]

    rows = []

    acum = 0.0

    total_pago_actual = 0.0
    total_enee = 0.0
    total_total_fv = 0.0
    total_ahorro = 0.0

    for r in tabla_12m:

        mes = r.get("mes", "")

        pago_actual = float(r.get("factura_base_L", 0.0))
        pago_enee = float(r.get("pago_enee_L", 0.0))

        total_fv = pago_enee + cuota_m
        ahorro_mes = pago_actual - total_fv

        acum += ahorro_mes

        total_pago_actual += pago_actual
        total_enee += pago_enee
        total_total_fv += total_fv
        total_ahorro += ahorro_mes

        rows.append([
            str(mes),
            money_L(pago_actual),
            money_L(pago_enee),
            money_L(cuota_m),
            money_L(total_fv),
            money_L(ahorro_mes),
            money_L(acum),
        ])

    # 🔥 TOTAL
    rows.append([
        "TOTAL",
        money_L(total_pago_actual),
        money_L(total_enee),
        money_L(cuota_m * 12),
        money_L(total_total_fv),
        money_L(total_ahorro),
        money_L(total_ahorro),
    ])

    table_data = [header] + rows

    t = make_table(
        table_data,
        content_w,
        ratios=[0.7,1.4,1.4,1.2,1.4,1.4,1.5],
        repeatRows=1,
    )

    t.setStyle(table_style_uniform(pal, font_header=9, font_body=9))

    last_row = len(table_data) - 1

    t.setStyle(TableStyle([

        # 🔹 Alineación
        ("ALIGN", (0,1), (0,-1), "CENTER"),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),

        # 🔹 Ahorro en negrita
        ("FONTNAME", (5,1), (5,-2), "Helvetica-Bold"),

        # 🔴 Negativos en rojo
        *[
            ("TEXTCOLOR", (5,i), (5,i), pal.get("BAD","red"))
            for i, r in enumerate(tabla_12m, start=1)
            if (float(r.get("factura_base_L",0)) - (float(r.get("pago_enee_L",0))+cuota_m)) < 0
        ],

        # 🔵 TOTAL
        ("BACKGROUND", (0,last_row), (-1,last_row), pal.get("SOFT","#EAEAEA")),
        ("FONTNAME", (0,last_row), (-1,last_row), "Helvetica-Bold"),
        ("LINEABOVE", (0,last_row), (-1,last_row), 1.2, pal.get("PRIMARY","#000000")),

    ]))

    return [t, Spacer(1, 10)]
# =========================================================
# PAGE 4
# =========================================================

def build_page_4(
    resultado: Any,
    datos: Any,
    paths: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):

    story = []

    story.append(Paragraph("Impacto energético y financiero", styles["Title"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Comparación mensual — Año 1", styles["H2b"]))
    story.append(Spacer(1, 6))

    story += tabla_impacto_mensual_anio1(resultado, pal, content_w)

    # =====================================================
    # CONFIGURACIÓN DC
    # =====================================================

    strings_block = leer(resultado, "strings", None)
    strings = leer(strings_block, "strings", []) if strings_block else []

    if strings:

        story.append(Paragraph("Configuración eléctrica (DC)", styles["H2b"]))
        story.append(Spacer(1, 6))

        lines = []

        for s in strings:

            lines.append(
                f"MPPT {leer(s,'mppt','')}: "
                f"{leer(s,'n_series','')} módulos en serie "
                f"(Vmp={leer(s,'vmp_string_v','')} V, "
                f"Voc frío={leer(s,'voc_frio_string_v','')} V)"
            )

        story.append(
            box_paragraph("<br/>".join(lines), pal, content_w, font_size=9.5)
        )

        story.append(Spacer(1, 8))

    # =====================================================
    # RESUMEN NEC
    # =====================================================

    nec_block = leer(resultado, "nec", {})
    nec_paq = leer(nec_block, "paquete_nec", {})

    resumen_pdf = nec_paq.get("resumen_pdf")

    if resumen_pdf:

        story.append(Paragraph("Resumen eléctrico (NEC 2023)", styles["H2b"]))
        story.append(Spacer(1, 6))

        lines = [

            f"I DC diseño: {resumen_pdf.get('i_dc_nom', '—')} A",

            f"I AC diseño: {resumen_pdf.get('i_ac_nom', '—')} A",

        ]

        story.append(
            box_paragraph("<br/>".join(lines), pal, content_w, font_size=9.5)
        )

        story.append(Spacer(1, 8))

    story.append(PageBreak())

    return story

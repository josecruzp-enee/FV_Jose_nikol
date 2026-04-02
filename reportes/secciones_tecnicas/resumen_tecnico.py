from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


# ==========================================================
# UTILIDAD LECTURA SEGURA
# ==========================================================

def leer(obj, campo, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# ==========================================================
# Tabla estilizada
# ==========================================================

def tabla(data, pal, content_w):

    tbl = Table(data, colWidths=[content_w*0.55, content_w*0.45])

    tbl.setStyle(TableStyle([

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),

        ("ALIGN",(1,1),(-1,-1),"RIGHT"),

        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),

        ("FONTSIZE",(0,0),(-1,-1),10),

        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),

    ]))

    return tbl


# ==========================================================
# Render resumen técnico
# ==========================================================

def build_resumen_tecnico(resultado, pal, styles, content_w):

    story = []

    sizing = leer(resultado, "sizing")
    strings_block = leer(resultado, "strings")  # 🔥 lista de StringFV
    nec = leer(resultado, "nec", {})

    # ======================================================
    # DATOS SIZING
    # ======================================================

    kwp_dc = float(leer(sizing, "kwp_dc", leer(sizing, "pdc_kw", 0)))
    kw_ac = float(leer(sizing, "kw_ac", 0))

    n_paneles = int(leer(sizing, "n_paneles", 0))
    n_inversores = int(leer(sizing, "n_inversores", 1))

    # ======================================================
    # STRINGS (🔥 FIX REAL)
    # ======================================================

    strings = strings_block if isinstance(strings_block, list) else []

    n_strings = len(strings)

    if strings:

        s = strings[0]

        n_series = int(leer(s, "n_series", 0))

        vmp = float(leer(s, "vmp_string_v", 0))

        voc = float(
            leer(s, "voc_frio_string_v",
            leer(s, "voc_string_v", 0))
        )

        imp = float(leer(s, "imp_string_a", 0))
        isc = float(leer(s, "isc_string_a", 0))

    else:

        n_series = 0
        vmp = 0
        voc = 0
        imp = 0
        isc = 0

    # ======================================================
    # NEC (si existe)
    # ======================================================

    paquete = leer(nec, "paquete_nec", {})
    corr = leer(paquete, "corrientes", {})

    panel_i = leer(leer(corr, "panel", {}), "i_operacion_a", imp)
    string_i = leer(leer(corr, "string", {}), "i_operacion_a", imp)

    # ======================================================
    # DERIVADOS
    # ======================================================

    potencia_inversor = kw_ac / n_inversores if n_inversores else 0
    relacion_dc_ac = kwp_dc / kw_ac if kw_ac else 0

    paneles_usados = n_paneles
    paneles_sobrantes = 0

    panel_wp = (kwp_dc * 1000) / n_paneles if n_paneles else 0

    # ======================================================
    # TABLA SISTEMA
    # ======================================================

    story.append(
        Paragraph("Resumen del sistema FV", styles["Heading1"])
    )

    story.append(Spacer(1, 10))

    data = [

        ["Parámetro", "Valor"],

        ["Potencia DC instalada", f"{kwp_dc:.2f} kWp"],
        ["Potencia AC instalada", f"{kw_ac:.2f} kW"],
        ["Relación DC/AC", f"{relacion_dc_ac:.2f}"],

        ["Número de módulos", f"{n_paneles} × {panel_wp:.0f} Wp"],

        ["Paneles utilizados", paneles_usados],
        ["Paneles sobrantes", paneles_sobrantes],

        ["Número de inversores",
         f"{n_inversores} × {potencia_inversor:.1f} kW"],
    ]

    story.append(tabla(data, pal, content_w))

    story.append(Spacer(1, 16))

    # ======================================================
    # TABLA GENERADOR
    # ======================================================

    story.append(
        Paragraph("Generador fotovoltaico", styles["Heading2"])
    )

    story.append(Spacer(1, 8))

    data = [

        ["Parámetro", "Valor"],

        ["Configuración strings", f"{n_series}S × {n_strings} strings"],

        ["Voltaje operativo string (Vmp)", f"{vmp:.0f} V"],
        ["Voltaje máximo en frío (Voc)", f"{voc:.0f} V"],

        ["Corriente por string (Imp)", f"{string_i:.2f} A"],
        ["Corriente de cortocircuito (Isc)", f"{isc:.2f} A"],

        ["Strings totales", n_strings],
    ]

    story.append(tabla(data, pal, content_w))

    story.append(Spacer(1, 16))

    return story

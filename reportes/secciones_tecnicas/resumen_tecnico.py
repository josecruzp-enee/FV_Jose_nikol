from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


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

    sizing = getattr(resultado, "sizing", None)
    strings_block = getattr(resultado, "strings", None)
    nec = getattr(resultado, "nec", {})

    # ------------------------------------------------------
    # Datos sizing
    # ------------------------------------------------------

    kwp_dc = float(getattr(sizing,"kwp_dc",getattr(sizing,"pdc_kw",0)))
    kw_ac = float(getattr(sizing,"kw_ac",0))

    n_paneles = int(getattr(sizing,"n_paneles",0))
    n_inversores = int(getattr(sizing,"n_inversores",1))

    # ------------------------------------------------------
    # Strings
    # ------------------------------------------------------

    strings = getattr(strings_block,"strings",[]) if strings_block else []

    if strings:

        s = strings[0]

        n_series = int(getattr(s,"n_series",0))
        vmp = float(getattr(s,"vmp_string_v",0))

        voc = float(
            getattr(s,"voc_frio_string_v",None)
            or getattr(s,"voc_string_v",0)
        )

        imp = float(getattr(s,"imp_string_a",0))
        isc = float(getattr(s,"isc_string_a",0))

    else:

        n_series=vmp=voc=imp=isc=0

    n_strings=len(strings)

    # ------------------------------------------------------
    # NEC
    # ------------------------------------------------------

    paquete = nec.get("paquete_nec",{})
    corr = paquete.get("corrientes",{})

    panel_i = corr.get("panel",{}).get("i_operacion_a",imp)
    string_i = corr.get("string",{}).get("i_operacion_a",imp)

    # ------------------------------------------------------
    # Parámetros derivados
    # ------------------------------------------------------

    panel_wp = (kwp_dc*1000)/n_paneles if n_paneles else 0

    potencia_inversor = kw_ac/n_inversores if n_inversores else 0

    relacion_dc_ac = kwp_dc/kw_ac if kw_ac else 0

    paneles_usados = n_series*n_strings

    paneles_sobrantes = max(0,n_paneles-paneles_usados)

    # ======================================================
    # TABLA SISTEMA
    # ======================================================

    story.append(Paragraph("Resumen del sistema FV", styles["Heading1"]))
    story.append(Spacer(1,10))

    data = [

        ["Parámetro","Valor"],

        ["Potencia DC instalada",f"{kwp_dc:.2f} kWp"],
        ["Potencia AC instalada",f"{kw_ac:.2f} kW"],
        ["Relación DC/AC",f"{relacion_dc_ac:.2f}"],

        ["Número de módulos",f"{n_paneles} × {panel_wp:.0f} Wp"],

        ["Paneles utilizados",paneles_usados],
        ["Paneles sobrantes",paneles_sobrantes],

        ["Número de inversores",f"{n_inversores} × {potencia_inversor:.1f} kW"],
    ]

    story.append(tabla(data,pal,content_w))

    story.append(Spacer(1,16))

    # ======================================================
    # TABLA GENERADOR
    # ======================================================

    story.append(Paragraph("Generador fotovoltaico", styles["Heading2"]))
    story.append(Spacer(1,8))

    data = [

        ["Parámetro","Valor"],

        ["Configuración strings",f"{n_series}S × {n_strings}P"],

        ["Voltaje operativo string (Vmp)",f"{vmp:.0f} V"],
        ["Voltaje máximo en frío (Voc)",f"{voc:.0f} V"],

        ["Corriente por string (Imp)",f"{string_i:.2f} A"],
        ["Corriente de cortocircuito (Isc)",f"{isc:.2f} A"],

        ["Strings totales",n_strings],
    ]

    story.append(tabla(data,pal,content_w))

    story.append(Spacer(1,16))

    return story

from __future__ import annotations
from typing import Any, Dict

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


# ==========================================================
# Tabla resumen técnico
# ==========================================================

def crear_tabla_resumen_tecnico(data, pal, content_w):

    colw = [content_w * 0.55, content_w * 0.45]

    tbl = Table(data, colWidths=colw)

    tbl.setStyle(
        TableStyle([
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

            ("BACKGROUND", (0,0), (-1,0), pal["SOFT"]),
            ("TEXTCOLOR", (0,0), (-1,0), pal["PRIMARY"]),

            ("ALIGN", (1,1), (-1,-1), "RIGHT"),

            ("GRID", (0,0), (-1,-1), 0.3, pal["BORDER"]),

            ("FONTSIZE", (0,0), (-1,-1), 10),

            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ])
    )

    return tbl


# ==========================================================
# Extraer datos del sistema
# ==========================================================

def extraer_datos_sistema(resultado):

    sizing = resultado.get("sizing", {})

    kwp_dc = float(sizing.get("kwp_dc", sizing.get("pdc_kw", 0)))
    kw_ac = float(sizing.get("kw_ac", 0))

    n_paneles = int(sizing.get("n_paneles", 0))
    n_inversores = int(sizing.get("n_inversores", 1))

    return kwp_dc, kw_ac, n_paneles, n_inversores


# ==========================================================
# Calcular parámetros del sistema
# ==========================================================

def calcular_parametros_generales(kwp_dc, kw_ac, n_paneles, n_inversores):

    panel_wp = (kwp_dc * 1000) / n_paneles if n_paneles else 0
    potencia_inversor = kw_ac / n_inversores if n_inversores else 0
    relacion_dc_ac = kwp_dc / kw_ac if kw_ac else 0

    return panel_wp, potencia_inversor, relacion_dc_ac


# ==========================================================
# Obtener configuración de strings
# ==========================================================

def obtener_configuracion_strings(resultado):

    strings = resultado.get("strings", {}).get("strings", [])

    if not strings:
        return 0, 0, 0, 0

    s = strings[0]

    n_series = int(s.get("n_series", 0))
    n_paralelo = int(s.get("n_paralelo", 0))

    vmp = float(s.get("vmp_string_v", 0))
    voc = float(s.get("voc_frio_string_v", 0))

    return n_series, n_paralelo, vmp, voc


# ==========================================================
# Obtener corrientes del sistema FV
# ==========================================================

# ==========================================================
# Obtener corrientes del sistema FV
# ==========================================================

def obtener_corrientes(resultado):

    nec = resultado.get("nec", {})
    paq = nec.get("paq", {})
    corr = paq.get("corrientes", {})
    corr_raw = paq.get("corrientes_raw", {})

    # panel viene de corrientes_raw
    panel = corr_raw.get("panel", {}).get("i_operacion_a", 0)

    # los demás vienen de corrientes
    string = corr.get("string", {}).get("i_nominal", 0)

    mppt = corr.get("mppt", {}).get("i_nominal", 0)

    dc_total = corr.get("dc_inversor", {}).get("i_nominal", 0)

    ac = corr.get("ac_salida", {}).get("i_nominal", 0)

    return panel, string, mppt, dc_total, ac
# ==========================================================
# Construir datos del resumen técnico
# ==========================================================

def construir_datos_resumen(
    kwp_dc,
    kw_ac,
    n_paneles,
    panel_wp,
    n_inversores,
    potencia_inversor,
    relacion_dc_ac,
    n_series,
    n_paralelo,
    vmp,
    voc,
    panel_i,
    string_i,
    mppt_i,
    dc_i,
    ac_i
):

    return [

        ["Parámetro", "Valor"],

        ["Potencia DC instalada", f"{kwp_dc:.2f} kWp"],
        ["Potencia AC instalada", f"{kw_ac:.2f} kW"],
        ["Relación DC/AC", f"{relacion_dc_ac:.2f}"],

        ["Número de módulos", f"{n_paneles} × {panel_wp:.0f} Wp"],
        ["Número de inversores", f"{n_inversores} × {potencia_inversor:.1f} kW"],

        ["Configuración strings", f"{n_series}S × {n_paralelo}P"],

        ["Voltaje operativo string (Vmp)", f"{vmp:.0f} V"],
        ["Voltaje máximo frío (Voc)", f"{voc:.0f} V"],

        ["Corriente panel", f"{panel_i:.2f} A"],
        ["Corriente string", f"{string_i:.2f} A"],
        ["Corriente MPPT", f"{mppt_i:.2f} A"],
        ["Corriente DC total", f"{dc_i:.2f} A"],
        ["Corriente AC total", f"{ac_i:.2f} A"],
    ]


# ==========================================================
# Renderizar resumen técnico
# ==========================================================

def build_resumen_tecnico(resultado, pal, styles, content_w):

    story = []

    kwp_dc, kw_ac, n_paneles, n_inversores = extraer_datos_sistema(resultado)

    panel_wp, potencia_inversor, relacion_dc_ac = calcular_parametros_generales(
        kwp_dc,
        kw_ac,
        n_paneles,
        n_inversores
    )

    n_series, n_paralelo, vmp, voc = obtener_configuracion_strings(resultado)

    panel_i, string_i, mppt_i, dc_i, ac_i = obtener_corrientes(resultado)

    data = construir_datos_resumen(
        kwp_dc,
        kw_ac,
        n_paneles,
        panel_wp,
        n_inversores,
        potencia_inversor,
        relacion_dc_ac,
        n_series,
        n_paralelo,
        vmp,
        voc,
        panel_i,
        string_i,
        mppt_i,
        dc_i,
        ac_i
    )

    story.append(Paragraph("Resumen técnico del sistema FV", styles["Heading1"]))
    story.append(Spacer(1, 10))

    story.append(crear_tabla_resumen_tecnico(data, pal, content_w))

    story.append(Spacer(1, 14))

    return story

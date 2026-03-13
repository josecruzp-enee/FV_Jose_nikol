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

    sizing = getattr(resultado, "sizing", None)

    if not sizing:
        return 0, 0, 0, 0

    kwp_dc = float(getattr(sizing, "kwp_dc", getattr(sizing, "pdc_kw", 0)))
    kw_ac = float(getattr(sizing, "kw_ac", 0))

    n_paneles = int(getattr(sizing, "n_paneles", 0))
    n_inversores = int(getattr(sizing, "n_inversores", 1))

    return kwp_dc, kw_ac, n_paneles, n_inversores


# ==========================================================
# Obtener configuración de strings
# ==========================================================

def obtener_configuracion_strings(resultado):

    strings_block = getattr(resultado, "strings", None)
    strings = getattr(strings_block, "strings", []) if strings_block else []

    if not strings:
        return 0, 0, 0, 0

    s = strings[0]

    n_series = int(getattr(s, "n_series", 0))
    n_strings = len(strings)

    vmp = float(getattr(s, "vmp_string_v", 0))

    voc = float(
        getattr(s, "voc_frio_string_v", None)
        or getattr(s, "voc_string_v", 0)
    )

    return n_series, n_strings, vmp, voc


# ==========================================================
# Obtener corrientes del sistema FV
# ==========================================================

def obtener_corrientes(resultado):

    strings_block = getattr(resultado, "strings", None)
    strings_data = getattr(strings_block, "strings", []) if strings_block else []

    imp_string = 0
    isc_string = 0

    if strings_data:

        s = strings_data[0]

        imp_string = float(getattr(s, "imp_string_a", 0))
        isc_string = float(getattr(s, "isc_string_a", 0))

    nec = getattr(resultado, "nec", {})
    paquete = nec.get("paquete_nec", {})

    corr = paquete.get("corrientes", {})

    panel = corr.get("panel", {}).get("i_operacion_a", imp_string)
    string = corr.get("string", {}).get("i_operacion_a", imp_string)
    mppt = corr.get("mppt", {}).get("i_operacion_a", imp_string)

    dc_total = corr.get("dc_total", {}).get("i_operacion_a", 0)
    ac = corr.get("ac", {}).get("i_operacion_a", 0)

    return panel, string, mppt, dc_total, ac, isc_string


# ==========================================================
# Calcular parámetros del sistema
# ==========================================================

def calcular_parametros_generales(
    kwp_dc,
    kw_ac,
    n_paneles,
    n_series,
    n_strings,
    n_inversores
):

    panel_wp = (kwp_dc * 1000) / n_paneles if n_paneles else 0

    potencia_inversor = kw_ac / n_inversores if n_inversores else 0

    relacion_dc_ac = kwp_dc / kw_ac if kw_ac else 0

    paneles_usados = n_series * n_strings

    paneles_sobrantes = max(0, n_paneles - paneles_usados)

    return (
        panel_wp,
        potencia_inversor,
        relacion_dc_ac,
        paneles_usados,
        paneles_sobrantes
    )


# ==========================================================
# Resumen sistema FV
# ==========================================================

def construir_resumen_sistema(
    kwp_dc,
    kw_ac,
    relacion_dc_ac,
    n_paneles,
    panel_wp,
    paneles_usados,
    paneles_sobrantes,
    n_inversores,
    potencia_inversor
):

    return [

        ["Parámetro", "Valor"],

        ["Potencia DC instalada", f"{kwp_dc:.2f} kWp"],
        ["Potencia AC instalada", f"{kw_ac:.2f} kW"],
        ["Relación DC/AC", f"{relacion_dc_ac:.2f}"],

        ["Número de módulos", f"{n_paneles} × {panel_wp:.0f} Wp"],

        ["Paneles utilizados", f"{paneles_usados}"],
        ["Paneles sobrantes", f"{paneles_sobrantes}"],

        ["Número de inversores", f"{n_inversores} × {potencia_inversor:.1f} kW"],
    ]


# ==========================================================
# Generador FV
# ==========================================================

def construir_resumen_generador(
    n_series,
    n_strings,
    vmp,
    voc,
    string_i,
    isc
):

    return [

        ["Parámetro", "Valor"],

        ["Configuración strings", f"{n_series}S × {n_strings}P"],

        ["Voltaje operativo string (Vmp)", f"{vmp:.0f} V"],
        ["Voltaje máximo en frío (Voc)", f"{voc:.0f} V"],

        ["Corriente por string (Imp)", f"{string_i:.2f} A"],
        ["Corriente de cortocircuito (Isc)", f"{isc:.2f} A"],

        ["Strings totales", f"{n_strings}"],
    ]


# ==========================================================
# Renderizar resumen técnico
# ==========================================================

def build_resumen_tecnico(resultado, pal, styles, content_w):

    story = []

    kwp_dc, kw_ac, n_paneles, n_inversores = extraer_datos_sistema(resultado)

    n_series, n_strings, vmp, voc = obtener_configuracion_strings(resultado)

    panel_i, string_i, mppt_i, dc_i, ac_i, isc = obtener_corrientes(resultado)

    panel_wp, potencia_inversor, relacion_dc_ac, paneles_usados, paneles_sobrantes = calcular_parametros_generales(
        kwp_dc,
        kw_ac,
        n_paneles,
        n_series,
        n_strings,
        n_inversores
    )

    story.append(Paragraph("Resumen del sistema FV", styles["Heading1"]))
    story.append(Spacer(1, 10))

    data_sistema = construir_resumen_sistema(
        kwp_dc,
        kw_ac,
        relacion_dc_ac,
        n_paneles,
        panel_wp,
        paneles_usados,
        paneles_sobrantes,
        n_inversores,
        potencia_inversor
    )

    story.append(crear_tabla_resumen_tecnico(data_sistema, pal, content_w))

    story.append(Spacer(1, 16))

    story.append(Paragraph("Generador fotovoltaico", styles["Heading2"]))
    story.append(Spacer(1, 8))

    data_generador = construir_resumen_generador(
        n_series,
        n_strings,
        vmp,
        voc,
        string_i,
        isc
    )

    story.append(crear_tabla_resumen_tecnico(data_generador, pal, content_w))

    story.append(Spacer(1, 16))

    return story

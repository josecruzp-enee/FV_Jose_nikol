# -*- coding: utf-8 -*-
from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


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
# TABLA ESTILIZADA GENERAL
# ==========================================================

def tabla(data, pal, content_w):

    tbl = Table(data, colWidths=[content_w * 0.55, content_w * 0.45])

    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), pal["SOFT"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), pal["PRIMARY"]),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, pal["BORDER"]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return tbl


# ==========================================================
# HELPERS DE FORMATO
# ==========================================================

def fmt_float(valor, decimales=2, default=0):
    try:
        return f"{float(valor):.{decimales}f}"
    except Exception:
        return f"{float(default):.{decimales}f}"


def agregar_tabla(story, titulo, data, pal, styles, content_w, nivel="Heading2"):

    story.append(Paragraph(titulo, styles[nivel]))
    story.append(Spacer(1, 8))
    story.append(tabla(data, pal, content_w))
    story.append(Spacer(1, 16))


# ==========================================================
# EXTRACCIÓN DE DATOS
# ==========================================================

def obtener_fuentes(resultado):

    sizing = leer(resultado, "sizing", {})
    paneles = leer(resultado, "paneles", None)
    corr = leer(resultado, "corrientes", {})

    return sizing, paneles, corr


def obtener_datos_sizing(sizing):

    kwp_dc = float(leer(sizing, "kwp_dc", leer(sizing, "pdc_kw", 0)))
    kw_ac_unitario = float(leer(sizing, "kw_ac", 0))
    kw_ac_total = float(leer(sizing, "kw_ac_total", kw_ac_unitario))

    n_paneles = int(leer(sizing, "n_paneles", 0))
    n_inversores = int(leer(sizing, "n_inversores", 1))

    return kwp_dc, kw_ac_unitario, kw_ac_total, n_paneles, n_inversores


def obtener_strings(paneles):

    if paneles and hasattr(paneles, "strings") and paneles.strings:
        return paneles.strings

    return []


def obtener_array(paneles):

    return leer(paneles, "array", {}) if paneles else {}


def obtener_datos_string(strings):

    if strings:

        s = strings[0]

        n_series = int(leer(s, "n_series", 0))

        vmp = float(leer(s, "vmp_string_v", 0))

        voc = float(
            leer(
                s,
                "voc_frio_string_v",
                leer(s, "voc_string_v", 0),
            )
        )

        imp = float(leer(s, "imp_string_a", 0))
        isc = float(leer(s, "isc_string_a", 0))

    else:
        n_series = 0
        vmp = 0
        voc = 0
        imp = 0
        isc = 0

    return n_series, vmp, voc, imp, isc


def obtener_derivados(
    kwp_dc,
    kw_ac_total,
    kw_ac_unitario,
    n_paneles,
    n_series=0,
    n_strings=0,
    panel_pmax_w=0,
):
    paneles_reales = int(n_series or 0) * int(n_strings or 0)

    if paneles_reales > 0 and panel_pmax_w > 0:
        n_paneles = paneles_reales
        kwp_dc = n_paneles * float(panel_pmax_w) / 1000.0

    potencia_inversor = kw_ac_unitario
    relacion_dc_ac = kwp_dc / kw_ac_total if kw_ac_total else 0

    panel_wp = float(panel_pmax_w or 0)

    if panel_wp <= 0 and n_paneles > 0:
        panel_wp = kwp_dc * 1000 / n_paneles

    return potencia_inversor, relacion_dc_ac, n_paneles, 0, panel_wp, kwp_dc


# ==========================================================
# DATA PARA TABLAS
# ==========================================================

def data_resumen_sistema(
    *,
    kwp_dc,
    kw_ac_total,
    relacion_dc_ac,
    n_paneles,
    panel_wp,
    paneles_usados,
    paneles_sobrantes,
    n_inversores,
    potencia_inversor,
):

    return [
        ["Parámetro", "Valor"],
        ["Potencia DC instalada", f"{kwp_dc:.2f} kWp"],
        ["Potencia AC instalada", f"{kw_ac_total:.2f} kW"],
        ["Relación DC/AC", f"{relacion_dc_ac:.2f}"],
        ["Número de módulos", f"{paneles_usados} × {panel_wp:.0f} Wp"],
        ["Número de inversores", f"{n_inversores} × {potencia_inversor:.1f} kW"],
    ]


def data_generador_fv(
    *,
    n_series,
    n_strings,
    vmp,
    voc,
    string_i,
    isc,
):

    return [
        ["Parámetro", "Valor"],
        ["Configuración strings", f"{n_series}S × {n_strings} strings"],
        ["Voltaje operativo string (Vmp)", f"{vmp:.0f} V"],
        ["Voltaje máximo en frío (Voc)", f"{voc:.0f} V"],
        ["Corriente por string (Imp)", f"{string_i:.2f} A"],
        ["Corriente de cortocircuito (Isc)", f"{isc:.2f} A"],
        ["Strings totales", n_strings],
    ]


def data_ficha_panel(panel, panel_wp):

    return [
        ["Parámetro", "Valor"],
        ["Marca", leer(panel, "marca", "—")],
        ["Modelo", leer(panel, "nombre", "—")],
        ["Código", leer(panel, "codigo", "—")],
        ["Potencia nominal", f'{float(leer(panel, "pmax_w", panel_wp)):.0f} Wp'],
        ["Voltaje máximo potencia (Vmp)", f'{float(leer(panel, "vmp_v", 0)):.2f} V'],
        ["Voltaje circuito abierto (Voc)", f'{float(leer(panel, "voc_v", 0)):.2f} V'],
        ["Corriente máxima potencia (Imp)", f'{float(leer(panel, "imp_a", 0)):.2f} A'],
        ["Corriente cortocircuito (Isc)", f'{float(leer(panel, "isc_a", 0)):.2f} A'],
        ["Coeficiente Voc", f'{float(leer(panel, "coef_voc_pct_c", 0)):.2f} %/°C'],
        ["Coeficiente Vmp", f'{float(leer(panel, "coef_vmp_pct_c", 0)):.2f} %/°C'],
        ["Coeficiente potencia", f'{float(leer(panel, "coef_potencia_pct_c", 0)):.2f} %/°C'],
        ["NOCT", f'{float(leer(panel, "noct_c", 0)):.1f} °C'],
    ]


def data_ficha_inversor(inversor, kw_ac_unitario, kw_ac_total, n_inversores):

    return [
        ["Parámetro", "Valor"],
        ["Marca", leer(inversor, "marca", "—")],
        ["Modelo", leer(inversor, "nombre", "—")],
        ["Código", leer(inversor, "codigo", "—")],
        ["Potencia AC nominal por inversor", f'{float(leer(inversor, "kw_ac", kw_ac_unitario)):.2f} kW'],
        ["Cantidad de inversores", n_inversores],
        ["Potencia AC total", f"{kw_ac_total:.2f} kW"],
        ["Número de MPPT por inversor", leer(inversor, "n_mppt", "—")],
        [
            "Ventana MPPT",
            f'{float(leer(inversor, "mppt_min_v", 0)):.0f} - '
            f'{float(leer(inversor, "mppt_max_v", 0)):.0f} V',
        ],
        ["Voltaje DC máximo", f'{float(leer(inversor, "vdc_max_v", 0)):.0f} V'],
        ["Corriente máxima MPPT", f'{float(leer(inversor, "imppt_max_a", 0) or 0):.2f} A'],
    ]


# ==========================================================
# TABLA COMPARATIVA DE INVERSORES
# ==========================================================

def construir_tabla_comparativa_inversores_pdf(
    comparativa_inversores,
    styles,
    content_w,
):
    """
    Construye la tabla PDF de comparación de inversores.

    Nota:
    - No calcula selección de inversores.
    - Solo presenta resultado["comparativa_inversores"].
    """

    elementos = []

    if not comparativa_inversores:
        return elementos

    elementos.append(Paragraph("Comparativa de inversores", styles["Heading2"]))
    elementos.append(Spacer(1, 8))

    normal = styles["Normal"]

    data = [[
        "Op.",
        "Configuración",
        "kW AC",
        "DC/AC",
        "Inv.",
        "Estado",
        "Motivo",
    ]]

    for fila in comparativa_inversores:
        data.append([
            str(fila.get("opcion", "")),
            Paragraph(str(fila.get("configuracion", "")), normal),
            f"{float(fila.get('kw_ac_total', 0) or 0):.2f}",
            f"{float(fila.get('dc_ac_real', fila.get('ratio_real', 0)) or 0):.2f}",
            str(fila.get("n_inversores", "")),
            Paragraph(str(fila.get("estado", "")), normal),
            Paragraph(str(fila.get("motivo", "")), normal),
        ])

    tabla_pdf = Table(
        data,
        colWidths=[
            content_w * 0.06,
            content_w * 0.25,
            content_w * 0.10,
            content_w * 0.09,
            content_w * 0.08,
            content_w * 0.12,
            content_w * 0.30,
        ],
        repeatRows=1,
    )

    tabla_pdf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("FONTSIZE", (0, 0), (-1, 0), 6),
        ("FONTSIZE", (0, 1), (-1, -1), 5.6),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (2, 1), (4, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),

        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),

        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))

    for i, fila in enumerate(comparativa_inversores, start=1):
        if str(fila.get("estado", "")).upper() == "ÓPTIMO":
            tabla_pdf.setStyle(TableStyle([
                ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#D9EAD3")),
                ("FONTNAME", (0, i), (-1, i), "Helvetica-Bold"),
            ]))

    elementos.append(tabla_pdf)
    elementos.append(Spacer(1, 16))

    return elementos


# ==========================================================
# CONSTRUCTOR PRINCIPAL DEL RESUMEN TÉCNICO
# ==========================================================

def build_resumen_tecnico(resultado, pal, styles, content_w):

    story = []

    # ======================================================
    # FUENTES
    # ======================================================

    sizing, paneles, corr = obtener_fuentes(resultado)

    # ======================================================
    # DATOS SIZING
    # ======================================================

    kwp_dc, kw_ac_unitario, kw_ac_total, n_paneles, n_inversores = (
        obtener_datos_sizing(sizing)
    )

    # ======================================================
    # STRINGS Y ARRAY
    # ======================================================

    strings = obtener_strings(paneles)

    array = obtener_array(paneles)
    n_strings = leer(array, "n_strings_total", len(strings))

    # ======================================================
    # VARIABLES DE STRING
    # ======================================================

    n_series, vmp, voc, imp, isc = obtener_datos_string(strings)

    # ======================================================
    # CORRIENTES
    # ======================================================

    string_i = leer(leer(corr, "string", {}), "i_operacion_a", imp)

    # ======================================================
    # DERIVADOS DE PRESENTACIÓN
    # ======================================================

    panel = leer(paneles, "panel", None) if paneles else None

    panel_pmax_w = (
        float(leer(panel, "pmax_w", 0))
        if panel
        else 0
    )

    (
        potencia_inversor,
        relacion_dc_ac,
        paneles_usados,
        paneles_sobrantes,
        panel_wp,
        kwp_dc,
    ) = obtener_derivados(
        kwp_dc,
        kw_ac_total,
        kw_ac_unitario,
        n_paneles,
        n_series=n_series,
        n_strings=n_strings,
        panel_pmax_w=panel_pmax_w,
    )

    # ======================================================
    # RESUMEN DEL SISTEMA FV
    # ======================================================

    story.append(Paragraph("Resumen del sistema FV", styles["Heading1"]))
    story.append(Spacer(1, 10))

    story.append(
        tabla(
            data_resumen_sistema(
                kwp_dc=kwp_dc,
                kw_ac_total=kw_ac_total,
                relacion_dc_ac=relacion_dc_ac,
                n_paneles=n_paneles,
                panel_wp=panel_wp,
                paneles_usados=paneles_usados,
                paneles_sobrantes=paneles_sobrantes,
                n_inversores=n_inversores,
                potencia_inversor=potencia_inversor,
            ),
            pal,
            content_w,
        )
    )

    story.append(Spacer(1, 16))

    # ======================================================
    # GENERADOR FOTOVOLTAICO
    # ======================================================

    agregar_tabla(
        story,
        "Generador fotovoltaico",
        data_generador_fv(
            n_series=n_series,
            n_strings=n_strings,
            vmp=vmp,
            voc=voc,
            string_i=string_i,
            isc=isc,
        ),
        pal,
        styles,
        content_w,
    )

    # ======================================================
    # FICHA TÉCNICA DEL MÓDULO FV
    # ======================================================

    panel = leer(paneles, "panel", None) if paneles else None

    agregar_tabla(
        story,
        "Ficha técnica del módulo FV",
        data_ficha_panel(
            panel=panel,
            panel_wp=panel_wp,
        ),
        pal,
        styles,
        content_w,
    )

    # ======================================================
    # FICHA TÉCNICA DEL INVERSOR
    # ======================================================

    inversor = leer(sizing, "inversor", None)

    agregar_tabla(
        story,
        "Ficha técnica del inversor",
        data_ficha_inversor(
            inversor=inversor,
            kw_ac_unitario=kw_ac_unitario,
            kw_ac_total=kw_ac_total,
            n_inversores=n_inversores,
        ),
        pal,
        styles,
        content_w,
    )

    # ======================================================
    # COMPARATIVA DE INVERSORES
    # ======================================================

    comparativa_inversores = leer(
        sizing,
        "comparativa_inversores",
        leer(resultado, "comparativa_inversores", []),
    )

    story.extend(
        construir_tabla_comparativa_inversores_pdf(
            comparativa_inversores,
            styles,
            content_w,
        )
    )

    return story


# ==========================================================
# RESUMEN DE MANTENIMIENTO
# ==========================================================
#
# Este módulo construye el resumen técnico del informe FV.
#
# Responsabilidad:
# - Leer datos consolidados desde resultado.sizing, resultado.paneles
#   y resultado.corrientes.
# - Construir tablas técnicas para ReportLab.
# - Mostrar resumen del sistema FV.
# - Mostrar configuración del generador FV.
# - Mostrar ficha técnica del módulo FV.
# - Mostrar ficha técnica del inversor.
# - Mostrar comparativa de inversores.
#
# Este módulo NO selecciona inversores.
# Este módulo NO calcula ingeniería eléctrica.
# Este módulo NO calcula corrientes, conductores ni protecciones.
# ==========================================================

# -*- coding: utf-8 -*-
from __future__ import annotations

from reportlab.platypus import Table, TableStyle


# ==========================================================
# TABLA 1 — PARÁMETROS ELÉCTRICOS
# ==========================================================
def crear_tabla_parametros_electricos(resultado, pal, content_w):

    electrical = getattr(resultado, "electrical", None)
    corr = getattr(electrical, "corrientes", None) if electrical else None

    if corr is None:
        return Table([["SIN DATOS ELÉCTRICOS"]])

    def leer(nivel):
        d = getattr(corr, nivel, None)
        if not d:
            return ("—", "—")

        return (
            f"{getattr(d, 'i_operacion_a', 0):.2f}",
            f"{getattr(d, 'i_diseno_a', 0):.2f}",
        )

    panel_nom, panel_dis = leer("panel")
    string_nom, string_dis = leer("string")
    mppt_nom, mppt_dis = leer("mppt")
    dc_nom, dc_dis = leer("dc_total")
    ac_nom, ac_dis = leer("ac")
    ac_inv_nom, ac_inv_dis = leer("ac_inversor")
    
    rows = [
        ["Nivel", "Corriente operación (A)", "Corriente diseño (A)"],
        ["Panel", panel_nom, panel_dis],
        ["String", string_nom, string_dis],
        ["MPPT crítico", mppt_nom, mppt_dis],
        ["DC total del Arreglo", dc_nom, dc_dis],
        ["AC por inversor", ac_inv_nom, ac_inv_dis],
        ["AC total del sistema", ac_nom, ac_dis],
    ]

    colw = [content_w * 0.4, content_w * 0.3, content_w * 0.3]

    tbl = Table(rows, colWidths=colw)

    tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),
        ("ALIGN",(1,1),(-1,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
        ("FONTSIZE",(0,0),(-1,-1),10),
    ]))

    return tbl


# ==========================================================
# TABLA 2 — DIMENSIONAMIENTO ELÉCTRICO
# ==========================================================
def crear_tabla_dimensionamiento_nec(resultado, pal, content_w):

    electrical = getattr(resultado, "electrical", None)

    corr = getattr(electrical, "corrientes", None) if electrical else None
    prot = getattr(electrical, "protecciones", None) if electrical else None
    conductores = getattr(electrical, "conductores", None) if electrical else None

    if corr is None:
        return Table([["SIN DATOS ELÉCTRICOS"]])

    # ======================================================
    # CONDUCTORES
    # ======================================================

    tramos = getattr(conductores, "tramos", None) if conductores else None
    dc_mppt = getattr(tramos, "dc_mppt", []) if tramos else []
    ac_tramo = getattr(tramos, "ac", None) if tramos else None

    cond_dc = "—"
    cond_ac = "—"

    for t in dc_mppt:
        cond_dc = f'{getattr(t,"calibre","—")} {getattr(t,"material","")}'

    if ac_tramo:
        cond_ac = f'{getattr(ac_tramo,"calibre","—")} {getattr(ac_tramo,"material","")}'

    # ======================================================
    # PROTECCIONES
    # ======================================================

    ocpd_ac = getattr(prot, "ocpd_ac", None) if prot else None
    ocpd_dc = getattr(prot, "ocpd_dc_array", None) if prot else None
    fusible = getattr(prot, "fusible_string", None) if prot else None

    rows = [
        ["Circuito", "I operación", "I diseño", "Protección", "Conductor"],
    ]

    niveles = [
        ("panel", "Panel", None, None),
        ("string", "String", fusible, cond_dc),
        ("mppt", "MPPT crítico", None, cond_dc),
        ("ac_inversor", "AC por inversor", None, "—"),
        ("ac", "AC total del sistema", ocpd_ac, cond_ac),
    ]

    for key, nombre, p, c in niveles:

        d = getattr(corr, key, None)

        if not d:
            rows.append([nombre, "—", "—", "—", "—"])
            continue

        i_op = f"{getattr(d, 'i_operacion_a', 0):.2f}"
        i_dis = f"{getattr(d, 'i_diseno_a', 0):.2f}"

        prot_txt = f'{getattr(p,"tamano_a","—")} A' if p else "—"
        cond_txt = c if c else "—"

        rows.append([
            nombre,
            i_op,
            i_dis,
            prot_txt,
            cond_txt
        ])

    colw = [
        content_w * 0.22,
        content_w * 0.18,
        content_w * 0.18,
        content_w * 0.20,
        content_w * 0.22,
    ]

    tbl = Table(rows, colWidths=colw)

    tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),
        ("ALIGN",(1,1),(2,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
        ("FONTSIZE",(0,0),(-1,-1),10),
    ]))

    return tbl


# ==========================================================
# TABLA 3 — INDICADORES TÉCNICOS
# ==========================================================
def crear_tabla_indicadores(resultado, pal, content_w):

    sizing = getattr(resultado, "sizing", None)
    paneles = getattr(resultado, "paneles", None)

    strings = getattr(paneles, "strings", []) if paneles else []

    n_paneles = getattr(sizing, "n_paneles", 0) if sizing else 0
    kw_ac_unitario = getattr(sizing, "kw_ac", 0) if sizing else 0
    kw_ac_total = getattr(sizing, "kw_ac_total", kw_ac_unitario) if sizing else 0
    kwp_dc = getattr(sizing, "kwp_dc", 0) if sizing else 0

    # ======================================================
    # PANEL UTILIZADOS
    # ======================================================

    paneles_en_strings = sum(getattr(s, "n_series", 0) for s in strings)

    utiliz_panel = (
        paneles_en_strings / n_paneles * 100
        if n_paneles else 0
    )

    # ======================================================
    # MPPT
    # ======================================================

    n_inv = getattr(sizing, "n_inversores", 1) if sizing else 1

    inversor = getattr(sizing, "inversor", None)
    mppt_por_inv = getattr(inversor, "n_mppt", 2) if inversor else 2

    n_mppt_total = n_inv * mppt_por_inv

    array = getattr(paneles, "array", None) if paneles else None

    strings_por_mppt = (
        getattr(array, "strings_por_mppt", 1)
        if array else 1
    )

    capacidad_total_strings = n_mppt_total * strings_por_mppt

    utiliz_mppt = (
        len(strings) / capacidad_total_strings * 100
        if capacidad_total_strings else 0
    )

    # ======================================================
    # DC / AC
    # ======================================================

    relacion = kwp_dc / kw_ac_total if kw_ac_total else 0
    carga_inv = kwp_dc / n_inv if n_inv else 0

    rows = [
        ["Indicador","Valor"],
        ["Utilización de paneles", f"{utiliz_panel:.1f} %"],
        ["Utilización de MPPT", f"{utiliz_mppt:.1f} %"],
        ["Relación DC/AC", f"{relacion:.2f}"],
        ["Carga promedio inversor", f"{carga_inv:.1f} kW DC"],
    ]

    colw = [
        content_w * 0.55,
        content_w * 0.45,
    ]

    tbl = Table(rows, colWidths=colw)

    tbl.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),
        ("ALIGN",(1,1),(1,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
        ("FONTSIZE",(0,0),(-1,-1),10),
    ]))

    return tbl

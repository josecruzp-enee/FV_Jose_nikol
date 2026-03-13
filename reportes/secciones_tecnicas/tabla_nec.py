from typing import Dict, Any
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


# ==========================================================
# TABLA 1 — PARÁMETROS ELÉCTRICOS
# ==========================================================

def crear_tabla_parametros_electricos(resultado, pal, content_w):

    # Leer corrientes directamente del paquete NEC
    corr = resultado.get("nec", {})

    def leer(nivel):
        d = corr.get(nivel, {})
        return (
            float(d.get("i_operacion_a", 0)),
            float(d.get("i_diseno_a", 0)),
        )

    panel_nom, panel_dis = leer("panel")
    string_nom, string_dis = leer("string")
    mppt_nom, mppt_dis = leer("mppt")
    dc_nom, dc_dis = leer("dc_total")
    ac_nom, ac_dis = leer("ac")

    rows = [
        ["Nivel", "Corriente nominal", "Corriente diseño"],

        ["Panel", f"{panel_nom:.2f} A", f"{panel_dis:.2f} A"],
        ["String", f"{string_nom:.2f} A", f"{string_dis:.2f} A"],
        ["MPPT", f"{mppt_nom:.2f} A", f"{mppt_dis:.2f} A"],
        ["Entrada inversor DC", f"{dc_nom:.2f} A", f"{dc_dis:.2f} A"],
        ["Salida inversor AC", f"{ac_nom:.2f} A", f"{ac_dis:.2f} A"],
    ]

    colw = [
        content_w * 0.40,
        content_w * 0.30,
        content_w * 0.30,
    ]

    tbl = Table(rows, colWidths=colw)

    tbl.setStyle(TableStyle([

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),

        ("ALIGN",(1,1),(1,-1),"RIGHT"),
        ("ALIGN",(2,1),(2,-1),"RIGHT"),

        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
        ("FONTSIZE",(0,0),(-1,-1),10),

    ]))

    return tbl


# ==========================================================
# TABLA 2 — DIMENSIONAMIENTO NEC
# ==========================================================

def crear_tabla_dimensionamiento_nec(resultado, pal, content_w):

    nec = resultado.get("nec", {}).get("protecciones")

    # Evitar tabla vacía
    if not nec:
        return None

    rows = [
        ["Circuito", "Corriente diseño", "Protección", "Conductor"],
    ]

    # Orden lógico de circuitos
    orden = [
        "string_dc",
        "mppt_dc",
        "entrada_inversor_dc",
        "salida_inversor_ac",
        "alimentador_ac"
    ]

    for circuito in orden:

        d = nec.get(circuito)

        if not d:
            continue

        rows.append([
            circuito.replace("_"," ").title(),
            f"{float(d.get('i_diseno_a',0)):.2f} A",
            d.get("proteccion","—"),
            d.get("conductor","—"),
        ])

    colw = [
        content_w * 0.30,
        content_w * 0.20,
        content_w * 0.25,
        content_w * 0.25,
    ]

    tbl = Table(rows, colWidths=colw)

    tbl.setStyle(TableStyle([

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),

        ("ALIGN",(1,1),(1,-1),"RIGHT"),
        ("ALIGN",(2,1),(-1,-1),"CENTER"),

        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
        ("FONTSIZE",(0,0),(-1,-1),10),

    ]))

    return tbl


# ==========================================================
# TABLA 3 — INDICADORES TÉCNICOS
# ==========================================================

def crear_tabla_indicadores(resultado, pal, content_w):

    sizing = resultado.get("sizing", {})
    strings = resultado.get("strings", {}).get("strings", [])

    n_paneles = sizing.get("n_paneles", 0)
    kw_ac = sizing.get("kw_ac", 0)

    paneles_usados = sum(s.get("n_series", 0) for s in strings)

    utiliz_panel = (paneles_usados / n_paneles) * 100 if n_paneles else 0

    n_mppt_total = (
        sizing.get("n_inversores", 1) *
        sizing.get("mppt_por_inversor", 2)
    )

    utiliz_mppt = (
        len(strings) / n_mppt_total * 100
        if n_mppt_total else 0
    )

    kwp_dc = sizing.get("pdc_kw", 0)

    relacion = kwp_dc / kw_ac if kw_ac else 0

    carga_inv = kwp_dc / sizing.get("n_inversores", 1)

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

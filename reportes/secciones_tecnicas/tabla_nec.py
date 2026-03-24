from typing import Dict, Any
from reportlab.platypus import Table, TableStyle


# ==========================================================
# UTILIDAD — lectura segura
# ==========================================================

def _leer(obj, campo, default=0):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


def _leer_dict(obj, campo, default=None):

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# ==========================================================
# TABLA 1 — PARÁMETROS ELÉCTRICOS (FIX)
# ==========================================================
def crear_tabla_parametros_electricos(resultado, pal, content_w):

    corr = getattr(resultado, "corrientes", None)

    # 🔥 SOLO valida existencia
    if corr is None:
        return Table([["SIN DATOS ELÉCTRICOS"]])

    def leer(nivel):
        d = getattr(corr, nivel, None)
        if not d:
            return ("—", "—")

        return (
            getattr(d, "i_operacion_a", "—"),
            getattr(d, "i_diseno_a", "—"),
        )

    panel_nom, panel_dis = leer("panel")
    string_nom, string_dis = leer("string")
    mppt_nom, mppt_dis = leer("mppt")
    dc_nom, dc_dis = leer("dc_total")
    ac_nom, ac_dis = leer("ac")

    rows = [
        ["Nivel", "Corriente nominal", "Corriente diseño"],
        ["Panel", f"{panel_nom}", f"{panel_dis}"],
        ["String", f"{string_nom}", f"{string_dis}"],
        ["MPPT", f"{mppt_nom}", f"{mppt_dis}"],
        ["Entrada inversor DC", f"{dc_nom}", f"{dc_dis}"],
        ["Salida inversor AC", f"{ac_nom}", f"{ac_dis}"],
    ]

    return Table(rows)

# ==========================================================
# TABLA 2 — DIMENSIONAMIENTO ELÉCTRICO (FIX)
# ==========================================================
def crear_tabla_dimensionamiento_nec(resultado, pal, content_w):

    corr = getattr(resultado, "corrientes", None)
    prot = getattr(resultado, "protecciones", None)
    conductores = getattr(resultado, "conductores", None)

    if corr is None:
        return Table([["SIN DATOS ELÉCTRICOS"]])

    # conductores (sin bloquear)
    cond = getattr(conductores, "tramos", []) if conductores else []

    cond_dc = "—"
    cond_ac = "—"

    for c in cond:
        nombre = getattr(c, "nombre", "")
        if "DC" in nombre:
            cond_dc = f'{getattr(c,"calibre","—")} {getattr(c,"material","")}'
        if "AC" in nombre:
            cond_ac = f'{getattr(c,"calibre","—")} {getattr(c,"material","")}'

    breaker_ac = getattr(prot, "ocpd_ac", None) if prot else None
    fusible_str = getattr(prot, "fusible_string", None) if prot else None

    rows = [
        ["Circuito", "I operación", "I diseño", "Protección", "Conductor"],
    ]

    niveles = [
        ("panel", "Panel", None, None),
        ("string", "String", fusible_str, cond_dc),
        ("mppt", "MPPT", None, cond_dc),
        ("dc_total", "DC Inversor", None, cond_dc),
        ("ac", "AC Inversor", breaker_ac, cond_ac),
    ]

    for key, nombre, p, c in niveles:
        d = getattr(corr, key, None)

        if not d:
            rows.append([nombre, "—", "—", "—", "—"])
            continue

        i_op = getattr(d, "i_operacion_a", "—")
        i_dis = getattr(d, "i_diseno_a", "—")

        prot_txt = f'{getattr(p,"tamano_a","—")} A' if p else "—"
        cond_txt = c if c else "—"

        rows.append([
            nombre,
            f"{i_op}",
            f"{i_dis}",
            prot_txt,
            cond_txt
        ])

    return Table(rows)

# ==========================================================
# TABLA 3 — INDICADORES TÉCNICOS
# ==========================================================
def crear_tabla_indicadores(resultado, pal, content_w):

    sizing = _leer(resultado, "sizing", None)
    strings_block = _leer(resultado, "strings", None)

    strings = _leer(strings_block, "strings", []) if strings_block else []

    n_paneles = _leer(sizing, "n_paneles", 0)
    kw_ac = _leer(sizing, "kw_ac", 0)
    kwp_dc = _leer(sizing, "pdc_kw", 0)

    # -------------------------------
    # PANEL UTILIZADOS
    # -------------------------------
    paneles_en_strings = sum(_leer(s, "n_series", 0) for s in strings)

    utiliz_panel = (
        paneles_en_strings / n_paneles * 100
        if n_paneles else 0
    )

    # -------------------------------
    # MPPT
    # -------------------------------
    n_inv = _leer(sizing, "n_inversores", 1)

    inversor = _leer(sizing, "inversor", None)
    mppt_por_inv = _leer(inversor, "n_mppt", 2)

    n_mppt_total = n_inv * mppt_por_inv

    strings_por_mppt = _leer(strings_block, "strings_por_mppt", 1)

    capacidad_total_strings = n_mppt_total * strings_por_mppt

    utiliz_mppt = (
        len(strings) / capacidad_total_strings * 100
        if capacidad_total_strings else 0
    )

    # -------------------------------
    # DC / AC
    # -------------------------------
    relacion = kwp_dc / kw_ac if kw_ac else 0
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

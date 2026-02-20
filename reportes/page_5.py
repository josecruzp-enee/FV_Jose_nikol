# reportes/page_5.py
from __future__ import annotations

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors

from core.result_accessors import (
    get_capex_L,
    get_kwp_dc,
    get_n_paneles,
    get_sizing,
    get_strings,
    get_tabla_12m,
)


def _sum_float(tabla: List[Dict[str, Any]], key: str) -> float:
    s = 0.0
    for r in tabla:
        try:
            s += float((r or {}).get(key, 0.0) or 0.0)
        except Exception:
            pass
    return float(s)


def _flt(x, d=0.0):
    try: return float(x)
    except Exception: return float(d)

def _int(x, d=0):
    try: return int(float(x))
    except Exception: return int(d)

def _get_dc(resultado: Dict[str, Any]) -> Dict[str, Any]:
    for k in ("electrico", "electrico_nec", "paquete_electrico", "ingenieria_electrica"):
        e = (resultado or {}).get(k)
        if isinstance(e, dict) and isinstance(e.get("dc"), dict):
            return e["dc"] or {}
    return (resultado or {}).get("dc") or {}

def _strings_desde_sizing(resultado: Dict[str, Any]):
    sizing = get_sizing(resultado)
    cfg = sizing.get("cfg_strings") or {}
    strings = get_strings(resultado)
    return cfg, strings

def _titulo_strings(styles):
    return [Spacer(1, 12),
            Paragraph("Configuración eléctrica referencial (Strings DC)", styles["Heading2"]),
            Spacer(1, 6)]

def _resumen_strings(resultado, styles):
    dc = _get_dc(resultado); c = (dc.get("config_strings") or {})
    if c.get("n_strings", 0) > 0:
        txt = f"{_int(c.get('n_strings'))} string(s) × {_int(c.get('modulos_por_string'))} módulos | {c.get('tipo','')}"
        return [Paragraph(txt, styles["BodyText"])]
    return [Paragraph("<i>No hay configuración de strings disponible.</i>", styles["BodyText"])]

def _fila_header_strings():
    return ["MPPT","Serie (S)","Paralelo (P)","Vmp (V)","Voc frío (V)","Imp (A)","Isc (A)"]

def _fila_string(s):
    return [str(_int(s.get("mppt", 0))), str(_int(s.get("n_series", 0))), str(_int(s.get("n_paralelo", 0))),
            f"{_flt(s.get('vmp_string_v', 0.0)):.0f}", f"{_flt(s.get('voc_string_frio_v', 0.0)):.0f}",
            f"{_flt(s.get('imp_a', 0.0)):.1f}", f"{_flt(s.get('isc_a', 0.0)):.1f}"]

def _colw_strings(content_w):
    return [content_w*0.10,content_w*0.12,content_w*0.12,content_w*0.16,content_w*0.16,content_w*0.17,content_w*0.17]

def _estilo_tabla_strings(pal):
    return TableStyle([
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),9),
        ("BACKGROUND",(0,0),(-1,0),pal.get("SOFT",colors.HexColor("#F5F7FA"))),
        ("TEXTCOLOR",(0,0),(-1,0),pal.get("PRIMARY",colors.HexColor("#0B2E4A"))),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.3,pal.get("BORDER",colors.HexColor("#D7DCE3"))),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ])

def _tabla_strings(strings, pal, content_w):
    rows = [_fila_header_strings()] + [_fila_string(s) for s in strings]
    tbl = Table(rows, colWidths=_colw_strings(content_w), hAlign="LEFT")
    tbl.setStyle(_estilo_tabla_strings(pal))
    return tbl

def _notas_strings(cfg, styles):
    checks = cfg.get("checks") or []
    if not checks: return []
    out = [Spacer(1, 8), Paragraph("<b>Notas de verificación</b>", styles["BodyText"])]
    return out + [Paragraph(f"• {str(c)}", styles["BodyText"]) for c in checks[:10]]

def _build_tabla_strings_dc(resultado: Dict[str, Any], pal, styles, content_w: float) -> List[Any]:
    cfg, strings = _strings_desde_sizing(resultado)
    story: List[Any] = []; story += _titulo_strings(styles)
    if not strings: return story + _resumen_strings(resultado, styles)
    story.append(_tabla_strings(strings, pal, content_w))
    return story + _notas_strings(cfg, styles)


def build_page_5(resultado, datos, paths, pal, styles, content_w):
    """
    Página 5 — Resumen técnico + Strings DC (VISIBLE)
    """
    story: List[Any] = []

    story.append(Paragraph("Resumen técnico", styles["Title"]))
    story.append(Spacer(1, 10))

    sizing = get_sizing(resultado)
    tabla_12m = get_tabla_12m(resultado)

    kwp_dc = get_kwp_dc(resultado)
    n_paneles = get_n_paneles(resultado)
    capex_L = get_capex_L(resultado)

    ahorro_anual_L = _sum_float(tabla_12m, "ahorro_L")
    fv_anual_kwh = _sum_float(tabla_12m, "fv_kwh")
    consumo_anual_kwh = _sum_float(tabla_12m, "consumo_kwh")

    story.append(Paragraph(f"Sistema FV estimado: {kwp_dc:.2f} kWp DC", styles["BodyText"]))
    story.append(Paragraph(f"Número de paneles: {n_paneles}", styles["BodyText"]))
    story.append(Paragraph(f"CAPEX estimado: L {capex_L:,.2f}", styles["BodyText"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Consumo anual (12m): {consumo_anual_kwh:,.0f} kWh", styles["BodyText"]))
    story.append(Paragraph(f"Generación FV útil (12m): {fv_anual_kwh:,.0f} kWh", styles["BodyText"]))
    story.append(Paragraph(f"Ahorro anual estimado (12m): L {ahorro_anual_L:,.2f}", styles["BodyText"]))

    # Strings DC
    story += _build_tabla_strings_dc(resultado, pal, styles, content_w)

    story.append(PageBreak())
    return story

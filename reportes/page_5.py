# reportes/page_5.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle, Image

from core.result_accessors import (
    get_capex_L,
    get_kwp_dc,
    get_n_paneles,
    get_sizing,
    get_strings,
    get_tabla_12m,
)


# ==========================================================
# Helpers: Layout paneles
# ==========================================================

def _append_layout_paneles(story, paths, styles, content_w):
    layout = (paths or {}).get("layout_paneles")
    if layout and Path(str(layout)).exists():
        story.append(Spacer(1, 10))
        img = Image(str(layout), width=content_w, height=content_w * 0.45)
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 8))
    else:
        story.append(Paragraph("Layout de paneles no disponible.", styles["BodyText"]))
        story.append(Spacer(1, 8))


# ==========================================================
# Helpers: básicos
# ==========================================================

def _sum_float(tabla: List[Dict[str, Any]], key: str) -> float:
    s = 0.0
    for r in tabla or []:
        try:
            s += float((r or {}).get(key, 0.0) or 0.0)
        except Exception:
            pass
    return float(s)


def _flt(x, d=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(d)


def _int(x, d=0) -> int:
    try:
        return int(float(x))
    except Exception:
        return int(d)


# ==========================================================
# Helpers: extraer DC/Strings desde NEC o desde sizing
# ==========================================================

def _get_dc(resultado: Dict[str, Any]) -> Dict[str, Any]:
    """
    Busca el bloque DC donde suele venir NEC:
    resultado["electrico"]["dc"]  o  resultado["electrico_nec"]["dc"] ...
    """
    for k in ("electrico", "electrico_nec", "paquete_electrico", "ingenieria_electrica"):
        e = (resultado or {}).get(k)
        if isinstance(e, dict) and isinstance(e.get("dc"), dict):
            return e.get("dc") or {}
    return (resultado or {}).get("dc") or {}


def _strings_desde_sizing_o_nec(resultado: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    1) Intenta strings "bonitos" del sizing/get_strings(resultado)
    2) Si no hay, arma un "string mínimo" desde NEC dc.config_strings
    """
    sizing = get_sizing(resultado) or {}
    cfg = sizing.get("cfg_strings") or {}

    strings = get_strings(resultado) or []
    if isinstance(strings, list) and len(strings) > 0:
        # ya vienen en el formato esperado (mppt, n_series, n_paralelo, vmp..., voc...)
        return cfg, strings

    # fallback NEC
    dc = _get_dc(resultado)
    c = dc.get("config_strings") or {}
    n_strings = _int(c.get("n_strings", 0))
    modulos_por_string = _int(c.get("modulos_por_string", 0))

    if n_strings > 0 and modulos_por_string > 0:
        # crear 1 fila mínima (o varias si quieres)
        s = {
            "mppt": 1,
            "n_series": modulos_por_string,
            "n_paralelo": n_strings,  # ojo: si NEC dice strings en paralelo; en tu caso 1.
            "vmp_string_v": _flt(dc.get("vmp_string_v", 0.0)),
            "voc_frio_string_v": _flt(dc.get("voc_frio_string_v", 0.0)),
            "imp_a": _flt(dc.get("i_string_oper_a", 0.0)),
            "isc_a": _flt(dc.get("i_array_isc_a", dc.get("i_string_max_a", 0.0))),
        }
        return cfg, [s]

    return cfg, []


# ==========================================================
# Tabla Strings
# ==========================================================

def _titulo_strings(styles):
    return [
        Spacer(1, 12),
        Paragraph("Configuración eléctrica referencial (Strings DC)", styles["Heading2"]),
        Spacer(1, 6),
    ]


def _fila_header_strings():
    return ["MPPT", "Serie (S)", "Paralelo (P)", "Vmp (V)", "Voc frío (V)", "Imp (A)", "Isc (A)"]


def _fila_string(s: Dict[str, Any]):
    # soporta ambos nombres de key para Voc
    voc = s.get("voc_frio_string_v", s.get("voc_string_frio_v", 0.0))
    return [
        str(_int(s.get("mppt", 0))),
        str(_int(s.get("n_series", 0))),
        str(_int(s.get("n_paralelo", 0))),
        f"{_flt(s.get('vmp_string_v', 0.0)):.0f}",
        f"{_flt(voc):.0f}",
        f"{_flt(s.get('imp_a', 0.0)):.1f}",
        f"{_flt(s.get('isc_a', 0.0)):.1f}",
    ]


def _colw_strings(content_w):
    return [
        content_w * 0.10,
        content_w * 0.12,
        content_w * 0.12,
        content_w * 0.16,
        content_w * 0.16,
        content_w * 0.17,
        content_w * 0.17,
    ]


def _estilo_tabla_strings(pal):
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), pal.get("SOFT", colors.HexColor("#F5F7FA"))),
            ("TEXTCOLOR", (0, 0), (-1, 0), pal.get("PRIMARY", colors.HexColor("#0B2E4A"))),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.3, pal.get("BORDER", colors.HexColor("#D7DCE3"))),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )


def _tabla_strings(strings, pal, content_w):
    rows = [_fila_header_strings()] + [_fila_string(s) for s in (strings or [])]
    tbl = Table(rows, colWidths=_colw_strings(content_w), hAlign="LEFT")
    tbl.setStyle(_estilo_tabla_strings(pal))
    return tbl


def _build_tabla_strings_dc(resultado: Dict[str, Any], pal, styles, content_w: float) -> List[Any]:
    cfg, strings = _strings_desde_sizing_o_nec(resultado)
    story: List[Any] = []
    story += _titulo_strings(styles)

    if not strings:
        story.append(Paragraph("<i>No hay configuración de strings disponible.</i>", styles["BodyText"]))
        return story

    story.append(_tabla_strings(strings, pal, content_w))

    # notas (si existen)
    checks = (cfg or {}).get("checks") or []
    if checks:
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Notas de verificación</b>", styles["BodyText"]))
        for c in checks[:10]:
            story.append(Paragraph(f"• {str(c)}", styles["BodyText"]))

    return story


# ==========================================================
# Página 5
# ==========================================================

def build_page_5(resultado, datos, paths, pal, styles, content_w):
    """
    Página 5 — Resumen técnico + Strings DC + Layout paneles
    """
    story: List[Any] = []

    story.append(Paragraph("Resumen técnico", styles["Title"]))
    story.append(Spacer(1, 10))

    tabla_12m = get_tabla_12m(resultado) or []

    kwp_dc = float(get_kwp_dc(resultado) or 0.0)
    n_paneles = int(get_n_paneles(resultado) or 0)
    capex_L = float(get_capex_L(resultado) or 0.0)

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

    # Layout paneles (al final, como pediste)
    _append_layout_paneles(story, paths, styles, content_w)

    story.append(PageBreak())
    return story

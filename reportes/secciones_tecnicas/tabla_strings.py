# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, List

from reportlab.platypus import Table, TableStyle


# ==========================================================
# TABLA DE STRINGS FV
# ==========================================================
# Responsabilidad:
# - Presentar la configuración eléctrica de strings.
# - Mostrar inversor, MPPT, serie, paralelo, voltajes y corrientes.
#
# Este módulo NO calcula strings.
# Este módulo NO asigna MPPT.
# Este módulo NO selecciona inversores.
# ==========================================================


# ==========================================================
# UTILIDADES INTERNAS
# ==========================================================

def leer(obj: Any, campo: str, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


def to_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default


def fmt_int(x):
    return str(to_int(x)) if x is not None else "—"


def fmt_float(x, dec=2):
    try:
        return f"{float(x):.{dec}f}"
    except Exception:
        return "—"


# ==========================================================
# CONSTRUCTOR DE TABLA
# ==========================================================

def crear_tabla_strings(strings: List[Any], pal, content_w):

    if not strings:
        return None

    # ======================================================
    # CONTEO DE STRINGS POR MPPT
    # ======================================================

    conteo_mppt = {}

    for s in strings:
        inv = to_int(leer(s, "inversor"))
        mppt = to_int(leer(s, "mppt"))

        key = (inv, mppt)
        conteo_mppt[key] = conteo_mppt.get(key, 0) + 1

    # ======================================================
    # ENCABEZADO
    # ======================================================

    rows = [[
        "String",
        "Inv",
        "MPPT",
        "Serie\n(S)",
        "Paralelo\n(P)",
        "Vmp\n(V)",
        "Voc frío\n(V)",
        "Imp\n(A)",
        "Isc\n(A)",
    ]]

    # ======================================================
    # ORDENAMIENTO SEGURO
    # ======================================================

    strings_ordenados = sorted(
        strings,
        key=lambda s: (
            to_int(leer(s, "inversor")),
            to_int(leer(s, "mppt")),
            to_int(leer(s, "id")),
        ),
    )

    # ======================================================
    # FILAS
    # ======================================================

    for s in strings_ordenados:

        inv = to_int(leer(s, "inversor"))
        mppt = to_int(leer(s, "mppt"))

        paralelos = conteo_mppt.get((inv, mppt), 1)

        voc = (
            leer(s, "voc_frio_string_v")
            or leer(s, "voc_string_v")
        )

        rows.append([
            fmt_int(leer(s, "id")),
            inv,
            mppt,
            fmt_int(leer(s, "n_series")),
            paralelos,
            fmt_float(leer(s, "vmp_string_v"), 0),
            fmt_float(voc, 0),
            fmt_float(leer(s, "imp_string_a"), 2),
            fmt_float(leer(s, "isc_string_a"), 2),
        ])

    # ======================================================
    # ANCHOS DE COLUMNA
    # ======================================================

    colw = [
        content_w * 0.08,
        content_w * 0.07,
        content_w * 0.08,
        content_w * 0.10,
        content_w * 0.11,
        content_w * 0.13,
        content_w * 0.15,
        content_w * 0.14,
        content_w * 0.14,
    ]

    tabla = Table(
        rows,
        colWidths=colw,
        repeatRows=1,
        splitByRow=1,
    )

    tabla.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), pal["SOFT"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), pal["PRIMARY"]),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("GRID", (0, 0), (-1, -1), 0.3, pal["BORDER"]),

        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),

        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))

    return tabla

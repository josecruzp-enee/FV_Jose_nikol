from typing import List, Any
from reportlab.platypus import Table, TableStyle


# ==========================================================
# TABLA — CONFIGURACIÓN DE STRINGS
# ==========================================================

def crear_tabla_strings(strings: List[Any], pal, content_w):

    if not strings:
        return None

    # ------------------------------------------------------
    # Lectura segura dict / dataclass
    # ------------------------------------------------------

    def leer(obj, campo, default=0):

        if obj is None:
            return default

        if isinstance(obj, dict):
            return obj.get(campo, default)

        return getattr(obj, campo, default)

    # ------------------------------------------------------
    # Calcular paralelos por MPPT
    # ------------------------------------------------------

    conteo_mppt = {}

    for s in strings:

        inv = int(leer(s, "inversor"))
        mppt = int(leer(s, "mppt"))

        key = (inv, mppt)

        conteo_mppt[key] = conteo_mppt.get(key, 0) + 1

    # ------------------------------------------------------
    # Encabezado
    # ------------------------------------------------------

    header = [
        "String",
        "Inv",
        "MPPT",
        "Serie (S)",
        "Paralelo (P)",
        "Vmp (V)",
        "Voc frío (V)",
        "Imp (A)",
        "Isc (A)",
    ]

    rows = [header]

    # ------------------------------------------------------
    # Ordenar strings
    # ------------------------------------------------------

    strings = sorted(
        strings,
        key=lambda s: (
            leer(s, "inversor"),
            leer(s, "mppt"),
            leer(s, "id"),
        )
    )

    # ------------------------------------------------------
    # Construir filas
    # ------------------------------------------------------

    for s in strings:

        inv = int(leer(s, "inversor"))
        mppt = int(leer(s, "mppt"))

        paralelos = conteo_mppt.get((inv, mppt), 1)

        voc = (
            leer(s, "voc_frio_string_v")
            or leer(s, "voc_string_v")
            or 0
        )

        rows.append([

            int(leer(s, "id")),
            inv,
            mppt,

            int(leer(s, "n_series")),

            paralelos,

            f"{float(leer(s,'vmp_string_v')):.0f}",
            f"{float(voc):.0f}",

            f"{float(leer(s,'imp_string_a')):.2f}",
            f"{float(leer(s,'isc_string_a')):.2f}",

        ])

    # ------------------------------------------------------
    # Anchos de columna
    # ------------------------------------------------------

    colw = [

        content_w * 0.08,
        content_w * 0.07,
        content_w * 0.07,

        content_w * 0.10,
        content_w * 0.10,

        content_w * 0.14,
        content_w * 0.14,

        content_w * 0.15,
        content_w * 0.15,

    ]

    tabla = Table(rows, colWidths=colw, repeatRows=1)

    tabla.setStyle(TableStyle([

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
        ("TEXTCOLOR",(0,0),(-1,0),pal["PRIMARY"]),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

        ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),

        ("FONTSIZE",(0,0),(-1,-1),9),

    ]))

    return tabla

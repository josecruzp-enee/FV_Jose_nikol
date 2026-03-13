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

        if isinstance(obj, dict):
            return obj.get(campo, default)

        return getattr(obj, campo, default)

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

    strings = sorted(strings, key=lambda s: leer(s, "id"))

    # ------------------------------------------------------
    # Construir filas
    # ------------------------------------------------------

    for s in strings:

        voc = (
            leer(s, "voc_frio_string_v")
            or leer(s, "voc_string_v")
            or 0
        )

        rows.append([

            int(leer(s, "id")),
            int(leer(s, "inversor")),
            int(leer(s, "mppt")),

            int(leer(s, "n_series")),

            1,  # strings en paralelo por MPPT

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

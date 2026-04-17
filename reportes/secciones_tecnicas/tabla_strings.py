from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_strings(strings: List[Any], pal, content_w):

    if not strings:
        return None

    # ======================================================
    # LECTURA SEGURA
    # ======================================================

    def leer(obj, campo, default=None):

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

    def to_float(x, default=0.0):
        try:
            return float(x)
        except Exception:
            return default

    def fmt_int(x):
        return str(to_int(x)) if x is not None else "—"

    def fmt_float(x, dec=2):
        try:
            return f"{float(x):.{dec}f}"
        except Exception:
            return "—"

    # ======================================================
    # CONTEO POR MPPT
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

    # ======================================================
    # ORDENAMIENTO SEGURO
    # ======================================================

    strings = sorted(
        strings,
        key=lambda s: (
            to_int(leer(s, "inversor")),
            to_int(leer(s, "mppt")),
            to_int(leer(s, "id")),
        )
    )

    # ======================================================
    # FILAS
    # ======================================================

    for s in strings:

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
    # ANCHOS
    # ======================================================

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

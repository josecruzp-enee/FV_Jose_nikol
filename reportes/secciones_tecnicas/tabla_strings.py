from typing import List, Dict, Any
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


# ==========================================================
# TABLA 1 — Distribución de strings por inversor
# ==========================================================

def crear_tabla_distribucion_inversores(strings: List[Dict[str, Any]], pal, content_w):

    if not strings:
        return None

    # ----------------------------------------
    # detectar número de inversores y MPPT
    # ----------------------------------------

    n_inversores = max(int(s.get("inversor", 0)) for s in strings)
    n_mppt = max(int(s.get("mppt", 0)) for s in strings)

    # ----------------------------------------
    # contar strings por inversor / mppt
    # ----------------------------------------

    matriz = {
        (inv, mppt): 0
        for inv in range(1, n_inversores + 1)
        for mppt in range(1, n_mppt + 1)
    }

    for s in strings:

        inv = int(s.get("inversor", 0))
        mppt = int(s.get("mppt", 0))

        matriz[(inv, mppt)] += 1

    # ----------------------------------------
    # header
    # ----------------------------------------

    header = ["Inversor"]

    for mppt in range(1, n_mppt + 1):
        header.append(f"MPPT {mppt}")

    rows = [header]

    # ----------------------------------------
    # filas
    # ----------------------------------------

    for inv in range(1, n_inversores + 1):

        row = [f"INV {inv}"]

        for mppt in range(1, n_mppt + 1):

            n = matriz[(inv, mppt)]

            if n == 0:
                row.append("—")
            elif n == 1:
                row.append("1 string")
            else:
                row.append(f"{n} strings")

        rows.append(row)

    # ----------------------------------------
    # tabla
    # ----------------------------------------

    colw = [content_w * 0.30] + [content_w * 0.35 / n_mppt] * n_mppt

    tabla = Table(rows, colWidths=colw)

    tabla.setStyle(TableStyle([

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        ("BACKGROUND", (0,0), (-1,0), pal["SOFT"]),
        ("TEXTCOLOR", (0,0), (-1,0), pal["PRIMARY"]),

        ("ALIGN", (1,1), (-1,-1), "CENTER"),

        ("GRID", (0,0), (-1,-1), 0.3, pal["BORDER"]),

        ("FONTSIZE", (0,0), (-1,-1), 10),

    ]))

    return tabla


# ==========================================================
# TABLA 2 — Configuración eléctrica de strings
# ==========================================================

def crear_tabla_strings(strings: List[Dict[str, Any]], pal, content_w):

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

    # ordenar strings
    strings = sorted(
        strings,
        key=lambda s: (
            s.get("inversor", 0),
            s.get("mppt", 0),
            s.get("id", 0),
        )
    )

    for s in strings:

        rows.append([

            int(s.get("id", 0)),
            int(s.get("inversor", 0)),
            int(s.get("mppt", 0)),
            int(s.get("n_series", 0)),

            1,

            f"{float(s.get('vmp_string_v', 0)):.0f}",

            f"{float(
                s.get('voc_frio_string_v')
                or s.get('voc_string_v')
                or 0
            ):.0f}",

            f"{float(s.get('imp_string_a', 0)):.2f}",

            f"{float(s.get('isc_string_a', 0)):.2f}",
        ])

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

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        ("BACKGROUND", (0,0), (-1,0), pal["SOFT"]),
        ("TEXTCOLOR", (0,0), (-1,0), pal["PRIMARY"]),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("GRID", (0,0), (-1,-1), 0.3, pal["BORDER"]),

        ("FONTSIZE", (0,0), (-1,-1), 9),

    ]))

    return tabla

from typing import List, Dict, Any
from reportlab.platypus import Table, TableStyle


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

    # ordenar strings por inversor y MPPT
    strings = sorted(strings, key=lambda s: (
        s.get("inversor", 0),
        s.get("mppt", 0),
        s.get("id", 0)
    ))

    for s in strings:

        rows.append([
            str(int(s.get("id", 0))),
            str(int(s.get("inversor", 0))),
            str(int(s.get("mppt", 0))),
            str(int(s.get("n_series", 0))),
            "1",
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

    tabla = Table(rows, colWidths=colw)

    tabla.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,0), (-1,0), pal["SOFT"]),
        ("TEXTCOLOR", (0,0), (-1,0), pal["PRIMARY"]),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.3, pal["BORDER"]),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))

    return tabla

from typing import List, Dict, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_strings(strings: List[Dict[str, Any]], n_inversores: int, pal, content_w):

    header = [
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

    for inv in range(1, n_inversores + 1):

        for s in strings:

            rows.append([
                str(inv),

                str(int(s.get("mppt", 0))),

                str(int(s.get("n_series", 0))),

                # ahora cada fila es un string
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
        content_w * 0.08,
        content_w * 0.10,
        content_w * 0.12,
        content_w * 0.15,
        content_w * 0.17,
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

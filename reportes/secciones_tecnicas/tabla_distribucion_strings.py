from typing import List, Dict, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings: List[Dict[str, Any]], pal, content_w):

    if not strings:
        return None

    n_inversores = max(int(s.get("inversor", 0)) for s in strings)
    n_mppt = max(int(s.get("mppt", 0)) for s in strings)

    matriz = {
        (inv, mppt): 0
        for inv in range(1, n_inversores + 1)
        for mppt in range(1, n_mppt + 1)
    }

    for s in strings:

        inv = int(s.get("inversor", 0))
        mppt = int(s.get("mppt", 0))

        matriz[(inv, mppt)] += 1

    header = ["Inversor"]

    for mppt in range(1, n_mppt + 1):
        header.append(f"MPPT {mppt}")

    rows = [header]

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

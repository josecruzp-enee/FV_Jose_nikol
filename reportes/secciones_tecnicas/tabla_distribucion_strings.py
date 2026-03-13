from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings: List[Any], pal, content_w):

    if not strings:
        return None

    def leer(obj, campo, default=0):
        if isinstance(obj, dict):
            return obj.get(campo, default)
        return getattr(obj, campo, default)

    n_inversores = max(int(leer(s, "inversor")) for s in strings)
    n_mppt = max(int(leer(s, "mppt")) for s in strings)

    matriz = {
        (inv, mppt): 0
        for inv in range(1, n_inversores + 1)
        for mppt in range(1, n_mppt + 1)
    }

    for s in strings:

        inv = int(leer(s, "inversor"))
        mppt = int(leer(s, "mppt"))

        matriz[(inv, mppt)] += 1

    header = ["Inversor"] + [f"MPPT {m}" for m in range(1, n_mppt + 1)]
    rows = [header]

    for inv in range(1, n_inversores + 1):

        row = [f"INV {inv}"]

        for mppt in range(1, n_mppt + 1):

            n = matriz[(inv, mppt)]

            row.append(
                "—" if n == 0
                else "1 string" if n == 1
                else f"{n} strings"
            )

        rows.append(row)

    colw = [content_w * 0.30] + [content_w * 0.70 / n_mppt] * n_mppt

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

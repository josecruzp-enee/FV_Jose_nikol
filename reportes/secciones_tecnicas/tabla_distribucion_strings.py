from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings, pal, content_w):

    def leer(obj, campo, default=0):
        if isinstance(obj, dict):
            return obj.get(campo, default)
        return getattr(obj, campo, default)

    # ======================================================
    # VALIDACIÓN FLEXIBLE
    # ======================================================

    strings_validos = []

    for s in strings:
        mppt = int(leer(s, "mppt", 0))
        inversor = int(leer(s, "inversor", 1))  # fallback a 1

        if mppt > 0:
            strings_validos.append({
                "inversor": inversor,
                "mppt": mppt
            })

    if not strings_validos:
        return Table([["Sin datos"]], colWidths=[content_w])

    # ======================================================
    # DETECCIÓN DINÁMICA
    # ======================================================

    inversores = sorted({s["inversor"] for s in strings_validos})
    mppts = sorted({s["mppt"] for s in strings_validos})

    # ======================================================
    # MATRIZ
    # ======================================================

    matriz = {(inv, mppt): 0 for inv in inversores for mppt in mppts}

    for s in strings_validos:
        matriz[(s["inversor"], s["mppt"])] += 1

    # ======================================================
    # TABLA
    # ======================================================

    header = ["Inversor"] + [f"MPPT {m}" for m in mppts]
    rows = [header]

    for inv in inversores:
        row = [f"INV {inv}"]
        for mppt in mppts:
            val = matriz.get((inv, mppt), 0)
            row.append(str(val) if val else "—")
        rows.append(row)

    # ======================================================
    # ESTILO
    # ======================================================

    colw = [content_w / len(header)] * len(header)

    tabla = Table(rows, colWidths=colw)
    tabla.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,0), (-1,0), pal.get("SOFT")),
        ("TEXTCOLOR", (0,0), (-1,0), pal.get("PRIMARY")),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.3, pal.get("BORDER")),
    ]))

    return tabla

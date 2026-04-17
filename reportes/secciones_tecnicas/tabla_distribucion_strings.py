from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings: List[Any], pal, content_w):

    # ======================================================
    # LECTURA SEGURA
    # ======================================================
    def leer(obj, campo, default=0):
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(campo, default)
        return getattr(obj, campo, default)

    # ======================================================
    # VALIDACIÓN
    # ======================================================
    if not strings:
        return Table([["Sin datos"]], colWidths=[content_w])

    # ======================================================
    # NORMALIZACIÓN
    # ======================================================
    strings_validos = []

    for s in strings:

        mppt = int(leer(s, "mppt", 1))
        inversor = int(leer(s, "inversor", 1))

        strings_validos.append({
            "inversor": inversor if inversor > 0 else 1,
            "mppt": mppt if mppt > 0 else 1
        })

    # ======================================================
    # DETECTAR DIMENSIONES
    # ======================================================
    inversores = sorted({s["inversor"] for s in strings_validos})
    mppts = sorted({s["mppt"] for s in strings_validos})

    # ======================================================
    # MATRIZ DE CONTEO
    # ======================================================
    matriz = {
        (inv, mppt): 0
        for inv in inversores
        for mppt in mppts
    }

    for s in strings_validos:
        matriz[(s["inversor"], s["mppt"])] += 1

    # ======================================================
    # CONSTRUIR TABLA
    # ======================================================
    header = ["Inversor"] + [f"MPPT {m}" for m in mppts]
    rows = [header]

    for inv in inversores:

        row = [f"INV {inv}"]

        for mppt in mppts:

            val = matriz.get((inv, mppt), 0)
            row.append(str(val) if val > 0 else "—")

        rows.append(row)

    # ======================================================
    # ANCHOS
    # ======================================================
    colw = [content_w / len(header)] * len(header)

    # ======================================================
    # ESTILO
    # ======================================================
    tabla = Table(rows, colWidths=colw)

    tabla.setStyle(TableStyle([

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), pal["SOFT"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), pal["PRIMARY"]),

        ("ALIGN", (1, 1), (-1, -1), "CENTER"),

        ("GRID", (0, 0), (-1, -1), 0.3, pal["BORDER"]),

        ("FONTSIZE", (0, 0), (-1, -1), 10),

        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

    ]))

    return tabla

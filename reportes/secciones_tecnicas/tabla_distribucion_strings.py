from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings: List[Any], pal, content_w):

    if not strings:
        return None

    # ======================================================
    # Lectura segura
    # ======================================================

    def leer(obj, campo, default=0):
        if isinstance(obj, dict):
            return obj.get(campo, default)
        return getattr(obj, campo, default)

    # ======================================================
    # Detectar inversores y MPPT (robusto)
    # ======================================================

    inversores = sorted({
        int(leer(s, "inversor", 0))
        for s in strings
        if int(leer(s, "inversor", 0)) > 0
    })

    mppts = sorted({
        int(leer(s, "mppt", 0))
        for s in strings
        if int(leer(s, "mppt", 0)) > 0
    })

    if not inversores or not mppts:
        return None

    # ======================================================
    # Crear matriz dinámica (sin asumir continuidad)
    # ======================================================

    matriz = {
        (inv, mppt): 0
        for inv in inversores
        for mppt in mppts
    }

    # ======================================================
    # Contar strings
    # ======================================================

    for s in strings:

        inv = int(leer(s, "inversor", 0))
        mppt = int(leer(s, "mppt", 0))

        if (inv, mppt) in matriz:
            matriz[(inv, mppt)] += 1

    # ======================================================
    # Encabezado
    # ======================================================

    header = ["Inversor"] + [f"MPPT {m}" for m in mppts]
    rows = [header]

    # ======================================================
    # Filas
    # ======================================================

    for inv in inversores:

        row = [f"INV {inv}"]

        for mppt in mppts:

            n = matriz.get((inv, mppt), 0)
            row.append(str(n) if n > 0 else "—")

        rows.append(row)

    # ======================================================
    # Ancho columnas dinámico
    # ======================================================

    n_cols = len(header)
    colw = [content_w / n_cols] * n_cols

    # ======================================================
    # Crear tabla
    # ======================================================

    tabla = Table(rows, colWidths=colw)

    tabla.setStyle(TableStyle([

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,0), (-1,0), pal["SOFT"]),
        ("TEXTCOLOR", (0,0), (-1,0), pal["PRIMARY"]),

        ("ALIGN", (1,1), (-1,-1), "CENTER"),

        ("GRID", (0,0), (-1,-1), 0.3, pal["BORDER"]),

        ("FONTSIZE", (0,0), (-1,-1), 10),

        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),

    ]))

    return tabla

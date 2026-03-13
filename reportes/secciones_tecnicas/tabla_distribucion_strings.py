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
    # Detectar inversores y MPPT
    # ======================================================

    inversores = set()
    mppts = set()

    for s in strings:

        inv = int(leer(s, "inversor", 0))
        mppt = int(leer(s, "mppt", 0))

        if inv > 0:
            inversores.add(inv)

        if mppt > 0:
            mppts.add(mppt)

    if not inversores or not mppts:
        return None

    n_inversores = max(inversores)
    n_mppt = max(mppts)

    # ======================================================
    # Crear matriz
    # ======================================================

    matriz = {
        (inv, mppt): 0
        for inv in range(1, n_inversores + 1)
        for mppt in range(1, n_mppt + 1)
    }

    # ======================================================
    # Contar strings
    # ======================================================

    for s in strings:

        inv = int(leer(s, "inversor", 0))
        mppt = int(leer(s, "mppt", 0))

        if inv > 0 and mppt > 0:

            if (inv, mppt) in matriz:
                matriz[(inv, mppt)] += 1

    # ======================================================
    # Encabezado
    # ======================================================

    header = ["Inversor"] + [f"MPPT {m}" for m in range(1, n_mppt + 1)]

    rows = [header]

    # ======================================================
    # Filas
    # ======================================================

    for inv in range(1, n_inversores + 1):

        row = [f"INV {inv}"]

        for mppt in range(1, n_mppt + 1):

            n = matriz.get((inv, mppt), 0)

            if n == 0:
                cell = "—"
            else:
                cell = str(n)

            row.append(cell)

        rows.append(row)

    # ======================================================
    # Ancho columnas
    # ======================================================

    colw = [content_w * 0.30] + [content_w * 0.70 / n_mppt] * n_mppt

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

    ]))

    return tabla

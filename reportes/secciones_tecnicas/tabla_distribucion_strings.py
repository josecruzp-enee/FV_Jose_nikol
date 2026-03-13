from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings: List[Any], pal, content_w):

    if not strings:
        return None

    # ======================================================
    # Función segura para leer campos
    # ======================================================

    def leer(obj, campo, default=0):
        if isinstance(obj, dict):
            return obj.get(campo, default)
        return getattr(obj, campo, default)

    # ======================================================
    # Detectar número de inversores y MPPT
    # ======================================================

    n_inversores = max((int(leer(s, "inversor")) for s in strings), default=0)
    n_mppt = max((int(leer(s, "mppt")) for s in strings), default=0)

    if n_inversores == 0 or n_mppt == 0:
        return None

    # ======================================================
    # Crear matriz de conteo
    # ======================================================

    matriz = {
        (inv, mppt): 0
        for inv in range(1, n_inversores + 1)
        for mppt in range(1, n_mppt + 1)
    }

    # ======================================================
    # Contar strings por inversor y MPPT
    # ======================================================

    for s in strings:

        inv = int(leer(s, "inversor"))
        mppt = int(leer(s, "mppt"))

        if inv > 0 and mppt > 0:
            matriz[(inv, mppt)] += 1

    # ======================================================
    # Construir encabezado
    # ======================================================

    header = ["Inversor"] + [f"MPPT {m}" for m in range(1, n_mppt + 1)]
    rows = [header]

    # ======================================================
    # Construir filas
    # ======================================================

    for inv in range(1, n_inversores + 1):

        row = [f"INV {inv}"]

        for mppt in range(1, n_mppt + 1):

            n = matriz[(inv, mppt)]

            if n == 0:
                cell = "—"
            elif n == 1:
                cell = "1 string"
            else:
                cell = f"{n} strings"

            row.append(cell)

        rows.append(row)

    # ======================================================
    # Ancho de columnas
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

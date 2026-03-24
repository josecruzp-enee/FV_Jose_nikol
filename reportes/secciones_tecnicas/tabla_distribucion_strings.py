from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings: List[Any], pal, content_w):
    """
    Genera una tabla de distribución de strings por inversor y MPPT para PDF.
    
    strings: lista de dicts o objetos con atributos 'inversor' y 'mppt'
    pal: diccionario de colores
    content_w: ancho total disponible para la tabla
    """

    # ======================================================
    # Lectura segura
    # ======================================================
    def leer(obj, campo, default=0):
        if isinstance(obj, dict):
            return obj.get(campo, default)
        return getattr(obj, campo, default)

    # ======================================================
    # Filtrar strings válidos (inversor > 0 y mppt > 0)
    # ======================================================
    strings_validos = [
        {"inversor": int(leer(s, "inversor", 0)), "mppt": int(leer(s, "mppt", 0))}
        for s in strings
        if int(leer(s, "inversor", 0)) > 0 and int(leer(s, "mppt", 0)) > 0
    ]

    if not strings_validos:
        # Si no hay datos válidos, devolver tabla con mensaje vacío
        rows = [["No hay datos de inversores válidos"]]
        tabla = Table(rows, colWidths=[content_w])
        tabla.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (-1, -1), pal.get("PRIMARY", "black"))
        ]))
        return tabla

    # ======================================================
    # Detectar inversores y MPPT únicos
    # ======================================================
    inversores = sorted({s["inversor"] for s in strings_validos})
    mppts = sorted({s["mppt"] for s in strings_validos})

    # ======================================================
    # Crear matriz dinámica
    # ======================================================
    matriz = {(inv, mppt): 0 for inv in inversores for mppt in mppts}

    for s in strings_validos:
        matriz[(s["inversor"], s["mppt"])] += 1

    # ======================================================
    # Crear encabezado y filas
    # ======================================================
    header = ["Inversor"] + [f"MPPT {m}" for m in mppts]
    rows = [header]

    for inv in inversores:
        row = [f"INV {inv}"]
        for mppt in mppts:
            count = matriz.get((inv, mppt), 0)
            row.append(str(count) if count > 0 else "—")
        rows.append(row)

    # ======================================================
    # Columnas de ancho dinámico
    # ======================================================
    n_cols = len(header)
    colw = [content_w / n_cols] * n_cols

    # ======================================================
    # Crear tabla con estilo
    # ======================================================
    tabla = Table(rows, colWidths=colw)
    tabla.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,0), (-1,0), pal.get("SOFT", "#DDDDDD")),
        ("TEXTCOLOR", (0,0), (-1,0), pal.get("PRIMARY", "black")),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.3, pal.get("BORDER", "#000000")),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))

    return tabla

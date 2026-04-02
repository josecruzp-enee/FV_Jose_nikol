from typing import List, Any
from reportlab.platypus import Table, TableStyle

from typing import List, Any
from reportlab.platypus import Table, TableStyle


def crear_tabla_distribucion_inversores(strings: List[Any], pal, content_w):

    # -------------------------------
    # Lectura segura
    # -------------------------------
    def leer(obj, campo, default=0):
        if isinstance(obj, dict):
            return obj.get(campo, default)
        return getattr(obj, campo, default)

    # -------------------------------
    # Validación / normalización
    # -------------------------------
    if not strings:
        return Table([["Sin datos"]], colWidths=[content_w])

    strings_validos = []
    for s in strings:
        mppt = int(leer(s, "mppt", 0))
        inversor = int(leer(s, "inversor", 1))  # fallback a 1

        # 🔥 No descartamos: si mppt viene 0, lo llevamos a 1
        strings_validos.append({
            "inversor": inversor if inversor > 0 else 1,
            "mppt": mppt if mppt > 0 else 1
        })

    if not strings_validos:
        return Table([["Sin datos"]], colWidths=[content_w])

    # -------------------------------
    # Detectar inversores / MPPT
    # -------------------------------
    inversores = sorted({s["inversor"] for s in strings_validos})
    mppts = sorted({s["mppt"] for s in strings_validos})

    # -------------------------------
    # Matriz de conteo
    # -------------------------------
    matriz = {(inv, mppt): 0 for inv in inversores for mppt in mppts}
    for s in strings_validos:
        matriz[(s["inversor"], s["mppt"])] += 1

    # -------------------------------
    # Construcción de tabla
    # -------------------------------
    header = ["Inversor"] + [f"MPPT {m}" for m in mppts]
    rows = [header]

    for inv in inversores:
        row = [f"INV {inv}"]
        for mppt in mppts:
            val = matriz.get((inv, mppt), 0)
            row.append(str(val) if val > 0 else "—")  # 🔥 UNA sola vez
        rows.append(row)

    # -------------------------------
    # Anchos
    # -------------------------------
    colw = [content_w / len(header)] * len(header)

    # -------------------------------
    # Estilo
    # -------------------------------
    tabla = Table(rows, colWidths=colw)
    tabla.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), pal.get("SOFT", "#DDDDDD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), pal.get("PRIMARY", "black")),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, pal.get("BORDER", "#000000")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    return tabla

def build_resumen_tecnico(resultado, pal, styles, content_w):

    from reportlab.platypus import Paragraph, Spacer

    story = []

    sizing = leer(resultado, "sizing")
    nec = leer(resultado, "nec", {})

    # ======================================================
    # 🔥 STRINGS (ROBUSTO)
    # ======================================================

    strings_block = leer(resultado, "strings")

    if not isinstance(strings_block, list) or not strings_block:
        paneles = leer(resultado, "paneles")
        strings_block = getattr(paneles, "strings", []) if paneles else []

    strings = strings_block if isinstance(strings_block, list) else []

    n_strings = len(strings)

    if strings:
        s = strings[0]

        n_series = int(leer(s, "n_series", 0))
        vmp = float(leer(s, "vmp_string_v", 0))
        voc = float(leer(s, "voc_frio_string_v", leer(s, "voc_string_v", 0)))
        imp = float(leer(s, "imp_string_a", 0))
        isc = float(leer(s, "isc_string_a", 0))
    else:
        n_series = vmp = voc = imp = isc = 0

    # ======================================================
    # SIZING
    # ======================================================

    kwp_dc = float(leer(sizing, "kwp_dc", leer(sizing, "pdc_kw", 0)))
    kw_ac = float(leer(sizing, "kw_ac", 0))

    n_paneles = int(leer(sizing, "n_paneles", 0))
    n_inversores = int(leer(sizing, "n_inversores", 1))

    panel_wp = (kwp_dc * 1000) / n_paneles if n_paneles else 0

    potencia_inversor = kw_ac / n_inversores if n_inversores else 0
    relacion_dc_ac = kwp_dc / kw_ac if kw_ac else 0

    # ======================================================
    # NEC
    # ======================================================

    paquete = leer(nec, "paquete_nec", {})
    corr = leer(paquete, "corrientes", {})

    string_i = leer(leer(corr, "string", {}), "i_operacion_a", imp)

    # ======================================================
    # TABLA SISTEMA
    # ======================================================

    story.append(Paragraph("Resumen del sistema FV", styles["Heading1"]))
    story.append(Spacer(1, 10))

    data = [
        ["Parámetro", "Valor"],
        ["Potencia DC instalada", f"{kwp_dc:.2f} kWp"],
        ["Potencia AC instalada", f"{kw_ac:.2f} kW"],
        ["Relación DC/AC", f"{relacion_dc_ac:.2f}"],
        ["Número de módulos", f"{n_paneles} × {panel_wp:.0f} Wp"],
        ["Número de inversores", f"{n_inversores} × {potencia_inversor:.1f} kW"],
    ]

    story.append(tabla(data, pal, content_w))
    story.append(Spacer(1, 16))

    # ======================================================
    # TABLA GENERADOR
    # ======================================================

    story.append(Paragraph("Generador fotovoltaico", styles["Heading2"]))
    story.append(Spacer(1, 8))

    data = [
        ["Parámetro", "Valor"],
        ["Configuración strings", f"{n_series}S × {n_strings}P"],
        ["Voltaje operativo string (Vmp)", f"{vmp:.0f} V"],
        ["Voltaje máximo en frío (Voc)", f"{voc:.0f} V"],
        ["Corriente por string (Imp)", f"{string_i:.2f} A"],
        ["Corriente de cortocircuito (Isc)", f"{isc:.2f} A"],
        ["Strings totales", n_strings],
    ]

    story.append(tabla(data, pal, content_w))
    story.append(Spacer(1, 16))

    # ======================================================
    # 🔥 NUEVA TABLA: DISTRIBUCIÓN POR INVERSOR / MPPT
    # ======================================================

    story.append(Paragraph("Distribución de strings por inversor", styles["Heading2"]))
    story.append(Spacer(1, 8))

    tabla_inv = crear_tabla_distribucion_inversores(
        strings,
        pal,
        content_w
    )

    story.append(tabla_inv)
    story.append(Spacer(1, 16))

    return story

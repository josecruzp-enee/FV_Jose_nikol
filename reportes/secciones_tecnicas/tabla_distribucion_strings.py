from typing import List, Any
from reportlab.platypus import Table, TableStyle


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

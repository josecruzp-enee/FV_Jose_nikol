def build_bloque_ingenieria(resultado, pal, styles, content_w):

    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    story = []

    paneles = getattr(resultado, "paneles", None)
    electrical = getattr(resultado, "electrical", None)

    # ======================================================
    # STRINGS (COPIA EXACTA DE UI)
    # ======================================================

    story.append(Paragraph("Strings FV", styles["Heading2"]))
    story.append(Spacer(1, 8))

    strings = paneles.strings if paneles else []

    if strings:
        data = [["#", "MPPT", "Series", "Vmp (V)", "Voc (V)", "Imp (A)", "Isc (A)"]]

        for i, s in enumerate(strings, 1):
            data.append([
                i,
                s.mppt,
                s.n_series,
                f"{s.vmp_string_v:.2f}",
                f"{s.voc_frio_string_v:.2f}",
                f"{s.imp_string_a:.2f}",
                f"{s.isc_string_a:.2f}",
            ])

        tabla = Table(data, colWidths=[content_w/7]*7)
        tabla.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
            ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ALIGN",(1,1),(-1,-1),"CENTER"),
        ]))

        story.append(tabla)

    else:
        story.append(Paragraph("Sin strings", styles["Normal"]))

    story.append(Spacer(1, 16))

    # ======================================================
    # CORRIENTES
    # ======================================================

    if electrical and hasattr(electrical, "corrientes"):

        story.append(Paragraph("Corrientes", styles["Heading2"]))
        story.append(Spacer(1, 8))

        c = electrical.corrientes

        data = [
            ["Nivel", "I operación (A)", "I diseño (A)"],
            ["Panel", f"{c.panel.i_operacion_a:.2f}", f"{c.panel.i_diseno_a:.2f}"],
            ["String", f"{c.string.i_operacion_a:.2f}", f"{c.string.i_diseno_a:.2f}"],
        ]

        for i, m in enumerate(c.mppt_detalle):
            data.append([
                f"MPPT {i+1}",
                f"{m.i_operacion_a:.2f}",
                f"{m.i_diseno_a:.2f}"
            ])

        data.extend([
            ["DC Total", f"{c.dc_total.i_operacion_a:.2f}", f"{c.dc_total.i_diseno_a:.2f}"],
            ["AC", f"{c.ac.i_operacion_a:.2f}", f"{c.ac.i_diseno_a:.2f}"],
        ])

        tabla = Table(data, colWidths=[content_w/3]*3)
        tabla.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
            ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ]))

        story.append(tabla)
        story.append(Spacer(1, 16))

    # ======================================================
    # PROTECCIONES
    # ======================================================

    if electrical and hasattr(electrical, "protecciones"):

        story.append(Paragraph("Protecciones", styles["Heading2"]))
        story.append(Spacer(1, 8))

        p = electrical.protecciones

        data = [
            ["Elemento", "Valor", "Norma"],
            ["Breaker AC", p.ocpd_ac.tamano_a, p.ocpd_ac.norma],
            ["OCPD DC", p.ocpd_dc_array.tamano_a, p.ocpd_dc_array.norma],
            ["Fusible", "Sí" if p.fusible_string.requerido else "No", p.fusible_string.nota],
        ]

        tabla = Table(data, colWidths=[content_w/3]*3)
        tabla.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
            ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ]))

        story.append(tabla)
        story.append(Spacer(1, 16))

    # ======================================================
    # CONDUCTORES
    # ======================================================

    if electrical and hasattr(electrical, "conductores"):

        story.append(Paragraph("Conductores", styles["Heading2"]))
        story.append(Spacer(1, 8))

        data = [["Tramo", "Calibre", "Material", "I diseño", "VD (%)", "Cumple"]]

        for t in electrical.conductores.tramos.dc_mppt:
            data.append([
                t.nombre,
                t.calibre,
                t.material,
                f"{t.i_diseno_a:.2f}",
                f"{t.vd_pct:.2f}",
                "✔" if t.cumple else "❌"
            ])

        tabla = Table(data, colWidths=[content_w/6]*6)
        tabla.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.3,pal["BORDER"]),
            ("BACKGROUND",(0,0),(-1,0),pal["SOFT"]),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ]))

        story.append(tabla)
        story.append(Spacer(1, 16))

    return story

def build_bloque_ingenieria(resultado, pal, styles, content_w):

    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    story = []

    paneles = getattr(resultado, "paneles", None)
    electrical = getattr(resultado, "electrical", None)

    # ======================================================
    # STRINGS
    # ======================================================

    story.append(Paragraph("Strings FV", styles["Heading2"]))
    story.append(Spacer(1, 8))

    strings = getattr(paneles, "strings", []) if paneles else []

    if strings:
        data = [["#", "MPPT", "Series", "Vmp (V)", "Voc (V)", "Imp (A)", "Isc (A)"]]

        for i, s in enumerate(strings, 1):
            data.append([
                i,
                getattr(s, "mppt", "-"),
                getattr(s, "n_series", "-"),
                f"{getattr(s, 'vmp_string_v', 0):.2f}",
                f"{getattr(s, 'voc_frio_string_v', 0):.2f}",
                f"{getattr(s, 'imp_string_a', 0):.2f}",
                f"{getattr(s, 'isc_string_a', 0):.2f}",
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

    corr = getattr(electrical, "corrientes", None) if electrical else None

    if corr:

        story.append(Paragraph("Corrientes", styles["Heading2"]))
        story.append(Spacer(1, 8))

        data = [
            ["Nivel", "I operación (A)", "I diseño (A)"],
            [
                "Panel",
                f"{getattr(getattr(corr, 'panel', None), 'i_operacion_a', 0):.2f}",
                f"{getattr(getattr(corr, 'panel', None), 'i_diseno_a', 0):.2f}",
            ],
            [
                "String",
                f"{getattr(getattr(corr, 'string', None), 'i_operacion_a', 0):.2f}",
                f"{getattr(getattr(corr, 'string', None), 'i_diseno_a', 0):.2f}",
            ],
        ]

        for i, m in enumerate(getattr(corr, "mppt_detalle", [])):
            data.append([
                f"MPPT {i+1}",
                f"{getattr(m, 'i_operacion_a', 0):.2f}",
                f"{getattr(m, 'i_diseno_a', 0):.2f}"
            ])

        data.extend([
            [
                "DC Total",
                f"{getattr(getattr(corr, 'dc_total', None), 'i_operacion_a', 0):.2f}",
                f"{getattr(getattr(corr, 'dc_total', None), 'i_diseno_a', 0):.2f}",
            ],
            [
                "AC",
                f"{getattr(getattr(corr, 'ac', None), 'i_operacion_a', 0):.2f}",
                f"{getattr(getattr(corr, 'ac', None), 'i_diseno_a', 0):.2f}",
            ],
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

    protec = getattr(electrical, "protecciones", None) if electrical else None

    if protec:

        story.append(Paragraph("Protecciones", styles["Heading2"]))
        story.append(Spacer(1, 8))

        ocpd_ac = getattr(protec, "ocpd_ac", None)
        ocpd_dc = getattr(protec, "ocpd_dc_array", None)
        fusible = getattr(protec, "fusible_string", None)

        data = [
            ["Elemento", "Valor", "Norma"],
            [
                "Breaker AC",
                getattr(ocpd_ac, "tamano_a", "-"),
                getattr(ocpd_ac, "norma", "-"),
            ],
            [
                "OCPD DC",
                getattr(ocpd_dc, "tamano_a", "-"),
                getattr(ocpd_dc, "norma", "-"),
            ],
            [
                "Fusible",
                "Sí" if getattr(fusible, "requerido", False) else "No",
                getattr(fusible, "nota", "-"),
            ],
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

    conductores = getattr(electrical, "conductores", None) if electrical else None
    tramos = getattr(conductores, "tramos", None) if conductores else None
    dc_mppt = getattr(tramos, "dc_mppt", []) if tramos else []

    if dc_mppt:

        story.append(Paragraph("Conductores", styles["Heading2"]))
        story.append(Spacer(1, 8))

        data = [["Tramo", "Calibre", "Material", "I diseño", "VD (%)", "Cumple"]]

        for t in dc_mppt:
            data.append([
                getattr(t, "nombre", "-"),
                getattr(t, "calibre", "-"),
                getattr(t, "material", "-"),
                f"{getattr(t, 'i_diseno_a', 0):.2f}",
                f"{getattr(t, 'vd_pct', 0):.2f}",
                "✔ Cumple" if getattr(t, "cumple", False) else "❌ No cumple"
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

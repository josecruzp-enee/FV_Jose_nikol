# reportes/page_5_tecnico.py

from reportlab.platypus import Paragraph, Spacer, PageBreak

from .secciones_tecnicas.resumen_tecnico import build_resumen_tecnico
from .secciones_tecnicas.tabla_strings import crear_tabla_strings
from .secciones_tecnicas.tabla_corrientes import crear_tabla_corrientes
from .secciones_tecnicas.tabla_nec import crear_tabla_diseno_nec
from .secciones_tecnicas.layout_paneles import insertar_layout_paneles



def build_page_5(resultado, datos, paths, pal, styles, content_w):

    story = []

    # ======================================================
    # Bloques del resultado
    # ======================================================

    sizing = resultado.get("sizing", {})
    strings_block = resultado.get("strings", {})

    strings = strings_block.get("strings", [])

    import streamlit as st
    st.write("DEBUG — número de strings:", len(strings))
    st.json(strings)

    paq = resultado.get("nec", {})
    corr = paq.get("corrientes", {})

    n_inv = int(sizing.get("n_inversores", 1))

    # ======================================================
    # 1. Resumen técnico
    # ======================================================

    story += build_resumen_tecnico(resultado, pal, styles, content_w)

    # ======================================================
    # 2. Configuración eléctrica (strings)
    # ======================================================

    story.append(Paragraph("Configuración eléctrica (Strings DC)", styles["Heading2"]))
    story.append(Spacer(1, 6))

    if strings:
        story.append(
            crear_tabla_strings(strings, pal, content_w)
        )
    else:
        story.append(
            Paragraph("No hay configuración de strings.", styles["BodyText"])
        )

    story.append(Spacer(1, 12))

    # ======================================================
    # 3. Corrientes del sistema FV
    # ======================================================

    story.append(Paragraph("Corrientes del sistema FV", styles["Heading2"]))
    story.append(Spacer(1, 6))

    story.append(
        crear_tabla_corrientes(corr, pal, content_w)
    )

    story.append(Spacer(1, 12))

    # ======================================================
    # 4. Diseño eléctrico NEC
    # ======================================================

    story.append(Paragraph("Parámetros de diseño eléctrico (NEC)", styles["Heading2"]))
    story.append(Spacer(1, 6))

    story.append(
        crear_tabla_diseno_nec(paq, pal, content_w)
    )

    story.append(Spacer(1, 12))

    # ======================================================
    # 5. Layout de paneles
    # ======================================================

    insertar_layout_paneles(story, paths, styles, content_w)

    story.append(PageBreak())

    return story

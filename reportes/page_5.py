# reportes/page_5.py

from reportlab.platypus import Paragraph, Spacer, PageBreak

from .secciones_tecnicas.resumen_tecnico import build_resumen_tecnico
from .secciones_tecnicas.tabla_strings import crear_tabla_strings
from .secciones_tecnicas.tabla_distribucion_strings import crear_tabla_distribucion_inversores
from .secciones_tecnicas.tabla_nec import (
    crear_tabla_parametros_electricos,
    crear_tabla_dimensionamiento_nec,
    crear_tabla_indicadores
)
from .secciones_tecnicas.layout_paneles import insertar_layout_paneles
from reportlab.platypus import Image

from reportlab.platypus import Paragraph, Spacer, PageBreak

from .secciones_tecnicas.resumen_tecnico import build_resumen_tecnico
from .secciones_tecnicas.tabla_strings import crear_tabla_strings
from .secciones_tecnicas.tabla_distribucion_strings import crear_tabla_distribucion_inversores
from .secciones_tecnicas.tabla_nec import (
    crear_tabla_parametros_electricos,
    crear_tabla_dimensionamiento_nec,
    crear_tabla_indicadores
)
from .secciones_tecnicas.layout_paneles import insertar_layout_paneles


# ======================================================
# SECCIONES
# ======================================================

def _section_resumen(story, resultado, pal, styles, content_w):

    story += build_resumen_tecnico(resultado, pal, styles, content_w)
    story.append(Spacer(1, 12))


def _section_distribucion_strings(story, strings, pal, styles, content_w):

    story.append(
        Paragraph("Distribución de strings por inversor", styles["Heading2"])
    )
    story.append(Spacer(1, 6))

    if strings:
        story.append(
            crear_tabla_distribucion_inversores(strings, pal, content_w)
        )
    else:
        story.append(
            Paragraph("No hay distribución de strings.", styles["BodyText"])
        )

    story.append(Spacer(1, 12))


def _section_config_strings(story, strings, pal, styles, content_w):

    story.append(
        Paragraph("Configuración eléctrica (Strings DC)", styles["Heading2"])
    )
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


def _section_parametros_electricos(story, resultado, pal, styles, content_w):

    story.append(
        Paragraph("Parámetros eléctricos del sistema", styles["Heading2"])
    )
    story.append(Spacer(1, 6))

    tabla = crear_tabla_parametros_electricos(resultado, pal, content_w)

    if tabla:
        story.append(tabla)
    else:
        story.append(
            Paragraph("No hay datos eléctricos disponibles.", styles["BodyText"])
        )

    story.append(Spacer(1, 12))


def _section_nec(story, resultado, pal, styles, content_w):

    story.append(
        Paragraph("Dimensionamiento eléctrico (NEC)", styles["Heading2"])
    )
    story.append(Spacer(1, 6))

    tabla = crear_tabla_dimensionamiento_nec(resultado, pal, content_w)

    if tabla:
        story.append(tabla)
    else:
        story.append(
            Paragraph("No hay dimensionamiento NEC disponible.", styles["BodyText"])
        )

    story.append(Spacer(1, 12))


def _section_indicadores(story, resultado, pal, styles, content_w):

    story.append(
        Paragraph("Indicadores técnicos del sistema", styles["Heading2"])
    )
    story.append(Spacer(1, 6))

    tabla = crear_tabla_indicadores(resultado, pal, content_w)

    if tabla:
        story.append(tabla)
    else:
        story.append(
            Paragraph("No hay indicadores disponibles.", styles["BodyText"])
        )

    story.append(Spacer(1, 12))

def _section_generacion_diaria(story, paths, styles, content_w):

    story.append(
        Paragraph("Perfil horario de generación fotovoltaica", styles["Heading2"])
    )

    story.append(Spacer(1, 6))

    chart = paths.get("chart_generacion_horaria")

    if chart:

        img = Image(chart)

        img.drawWidth = content_w
        img.drawHeight = content_w * 0.45

        story.append(img)

    else:

        story.append(
            Paragraph(
                "No se pudo generar la gráfica de generación horaria.",
                styles["BodyText"],
            )
        )

    story.append(Spacer(1, 12))

def _section_layout_paneles(story, paths, styles, content_w):

    insertar_layout_paneles(story, paths, styles, content_w)


# ======================================================
# ORQUESTADOR DE LA PÁGINA
# ======================================================

def build_page_5(resultado, datos, paths, pal, styles, content_w):

    story = []

    strings_block = resultado.get("strings", {})
    strings = strings_block.get("strings", [])

    _section_resumen(
        story, resultado, pal, styles, content_w
    )

    _section_distribucion_strings(
        story, strings, pal, styles, content_w
    )

    _section_config_strings(
        story, strings, pal, styles, content_w
    )

    _section_parametros_electricos(
        story, resultado, pal, styles, content_w
    )

    _section_nec(
        story, resultado, pal, styles, content_w
    )

    _section_indicadores(
        story, resultado, pal, styles, content_w
    )

    _section_generacion_diaria(
        story, paths, styles, content_w
    )
    
    _section_layout_paneles(
        story, paths, styles, content_w
    )

    story.append(PageBreak())

    return story

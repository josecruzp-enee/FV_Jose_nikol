from reportlab.platypus import Paragraph, Spacer, PageBreak, Image
from pathlib import Path

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

    story.append(Paragraph("Distribución de strings por inversor", styles["Heading2"]))
    story.append(Spacer(1, 6))

    if strings:
        story.append(crear_tabla_distribucion_inversores(strings, pal, content_w))
    else:
        story.append(Paragraph("No hay distribución de strings.", styles["BodyText"]))

    story.append(Spacer(1, 12))


def _section_config_strings(story, strings, pal, styles, content_w):

    story.append(Paragraph("Configuración eléctrica (Strings DC)", styles["Heading2"]))
    story.append(Spacer(1, 6))

    if strings:
        story.append(crear_tabla_strings(strings, pal, content_w))
    else:
        story.append(Paragraph("No hay configuración de strings.", styles["BodyText"]))

    story.append(Spacer(1, 12))


def _section_parametros_electricos(story, resultado, pal, styles, content_w):

    story.append(Paragraph("Parámetros eléctricos del sistema", styles["Heading2"]))
    story.append(Spacer(1, 6))

    tabla = crear_tabla_parametros_electricos(resultado, pal, content_w)

    if tabla:
        story.append(tabla)
    else:
        story.append(Paragraph("No hay datos eléctricos disponibles.", styles["BodyText"]))

    story.append(Spacer(1, 12))


def _section_nec(story, resultado, pal, styles, content_w):

    story.append(Paragraph("Dimensionamiento eléctrico (NEC)", styles["Heading2"]))
    story.append(Spacer(1, 6))

    tabla = crear_tabla_dimensionamiento_nec(resultado, pal, content_w)

    if tabla:
        story.append(tabla)
    else:
        story.append(Paragraph("No hay dimensionamiento NEC disponible.", styles["BodyText"]))

    story.append(Spacer(1, 12))


def _section_indicadores(story, resultado, pal, styles, content_w):

    story.append(Paragraph("Indicadores técnicos del sistema", styles["Heading2"]))
    story.append(Spacer(1, 6))

    tabla = crear_tabla_indicadores(resultado, pal, content_w)

    if tabla:
        story.append(tabla)
    else:
        story.append(Paragraph("No hay indicadores disponibles.", styles["BodyText"]))

    story.append(Spacer(1, 12))


# ======================================================
# UTILIDAD PARA INSERTAR GRÁFICOS
# ======================================================

def _insert_chart(story, path, styles, content_w, error_msg):

    if path and Path(path).exists():

        img = Image(path)
        img.drawWidth = content_w
        img.drawHeight = content_w * 0.45

        story.append(img)

    else:

        story.append(Paragraph(error_msg, styles["BodyText"]))

    story.append(Spacer(1, 12))


# ======================================================
# GRÁFICOS FV
# ======================================================

def _section_potencia_horaria(story, paths, styles, content_w):

    story.append(Paragraph("Perfil horario de potencia fotovoltaica", styles["Heading2"]))
    story.append(Spacer(1, 6))

    chart = None

    if isinstance(paths, dict):
        chart = paths.get("chart_potencia_horaria") or paths.get("chart_horaria")

    _insert_chart(
        story,
        chart,
        styles,
        content_w,
        "No se pudo generar la gráfica de potencia horaria."
    )


def _section_energia_horaria(story, paths, styles, content_w):

    story.append(Paragraph("Energía generada por hora", styles["Heading2"]))
    story.append(Spacer(1, 6))

    chart = None

    if isinstance(paths, dict):
        chart = paths.get("chart_energia_horaria") or paths.get("chart_diaria")

    _insert_chart(
        story,
        chart,
        styles,
        content_w,
        "No se pudo generar la gráfica de energía horaria."
    )


def _section_energia_mensual(story, paths, styles, content_w):

    story.append(Paragraph("Generación fotovoltaica mensual", styles["Heading2"]))
    story.append(Spacer(1, 6))

    chart = None

    if isinstance(paths, dict):
        chart = paths.get("chart_energia_mensual") or paths.get("chart_mensual")

    _insert_chart(
        story,
        chart,
        styles,
        content_w,
        "No se pudo generar la gráfica de generación mensual."
    )


# ======================================================
# LAYOUT DE PANELES
# ======================================================

def _section_layout_paneles(story, paths, styles, content_w):

    insertar_layout_paneles(story, paths, styles, content_w)


# ======================================================
# ORQUESTADOR DE LA PÁGINA
# ======================================================

def build_page_5(resultado, datos, paths, pal, styles, content_w):

    story = []

    strings_block = getattr(resultado, "strings", None)
    strings = getattr(strings_block, "strings", []) if strings_block else []


    # ======================================================
    # RESUMEN TÉCNICO
    # ======================================================

    _section_resumen(story, resultado, pal, styles, content_w)

    # ======================================================
    # DISTRIBUCIÓN DE STRINGS
    # ======================================================

    _section_distribucion_strings(story, strings, pal, styles, content_w)

    # ======================================================
    # CONFIGURACIÓN ELÉCTRICA STRINGS
    # ======================================================

    _section_config_strings(story, strings, pal, styles, content_w)

    # ======================================================
    # PARÁMETROS ELÉCTRICOS
    # ======================================================

    _section_parametros_electricos(story, resultado, pal, styles, content_w)

    # ======================================================
    # DIMENSIONAMIENTO NEC
    # ======================================================

    _section_nec(story, resultado, pal, styles, content_w)

    # ======================================================
    # INDICADORES TÉCNICOS
    # ======================================================

    _section_indicadores(story, resultado, pal, styles, content_w)

    # ======================================================
    # GRÁFICOS FV
    # ======================================================

    _section_potencia_horaria(story, paths, styles, content_w)

    _section_energia_horaria(story, paths, styles, content_w)

    _section_energia_mensual(story, paths, styles, content_w)

    # ======================================================
    # LAYOUT DE PANELES
    # ======================================================

    _section_layout_paneles(story, paths, styles, content_w)

    story.append(PageBreak())

    # ======================================================
    # DIAGRAMA STRING FV REPRESENTATIVO
    # ======================================================

    if isinstance(paths, dict) and paths.get("string_fv") and Path(paths["string_fv"]).exists():

        story.append(Paragraph("Configuración del String Fotovoltaico", styles["Heading2"]))
        story.append(Spacer(1, 6))

        img = Image(paths["string_fv"], width=420, height=120)
        img.hAlign = "CENTER"

        story.append(img)
        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                "String representativo del generador fotovoltaico. "
                "Todos los strings del sistema tienen la misma configuración "
                "y se conectan en paralelo al inversor.",
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 12))

    else:

        story.append(
            Paragraph(
                "No se pudo generar el diagrama del string fotovoltaico.",
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 12))

    return story

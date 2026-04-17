from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.platypus import Paragraph, Spacer, PageBreak, Image

from .secciones_tecnicas.resumen_tecnico import build_resumen_tecnico
from .secciones_tecnicas.tabla_strings import crear_tabla_strings
#from .secciones_tecnicas.tabla_distribucion_strings import crear_tabla_distribucion_inversores
from .secciones_tecnicas.tabla_nec import (
    crear_tabla_parametros_electricos,
    crear_tabla_dimensionamiento_nec,
    crear_tabla_indicadores
)
from .secciones_tecnicas.layout_paneles import insertar_layout_paneles


# =========================================================
# LECTURA SEGURA
# =========================================================

def leer(obj, campo, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# =========================================================
# UTILIDAD GRÁFICOS
# =========================================================

def _insert_chart(story, path, styles, content_w, error_msg):

    if path and Path(str(path)).exists():

        img = Image(str(path))
        img.drawWidth = content_w
        img.drawHeight = content_w * 0.45

        story.append(img)

    else:

        story.append(Paragraph(error_msg, styles["BodyText"]))

    story.append(Spacer(1, 12))


# =========================================================
# SECCIONES
# =========================================================

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


# =========================================================
# GRÁFICOS FV
# =========================================================

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


# =========================================================
# PAGE 5
# =========================================================

def build_ingenieria_electrica(resultado, datos, paths, pal, styles, content_w, safe_image=None):

    from pathlib import Path
    from reportlab.platypus import Paragraph, Spacer, PageBreak, Image

    story = []

    resultado = resultado or {}
    paths = paths or {}

    # =========================================================
    # OBTENER STRINGS (CORRECTO SEGÚN TU UI)
    # =========================================================
    paneles = leer(resultado, "paneles", None)

    if paneles and hasattr(paneles, "strings") and paneles.strings:
        strings = paneles.strings
    else:
        strings = []

    # =========================================================
    # SECCIONES
    # =========================================================
    _section_resumen(story, resultado, pal, styles, content_w)
    _section_distribucion_strings(story, strings, pal, styles, content_w)
    _section_config_strings(story, strings, pal, styles, content_w)
    _section_parametros_electricos(story, resultado, pal, styles, content_w)
    _section_nec(story, resultado, pal, styles, content_w)
    _section_indicadores(story, resultado, pal, styles, content_w)

    _section_potencia_horaria(story, paths, styles, content_w)
    _section_energia_horaria(story, paths, styles, content_w)
    _section_energia_mensual(story, paths, styles, content_w)

    insertar_layout_paneles(story, paths, styles, content_w, safe_image)

    story.append(PageBreak())

    # =========================================================
    # GENERAR STRING FV (AUTOMÁTICO)
    # =========================================================
    string_fv_path = None

    try:
        if paneles and paneles.strings:

            n_series = paneles.strings[0].n_series
            n_strings = (
                paneles.array.n_strings_total
                if hasattr(paneles, "array") and paneles.array
                else len(paneles.strings)
            )

            if n_series > 0 and n_strings > 0:

                from pathlib import Path
                ruta = Path("outputs/string_fv.png")
                ruta.parent.mkdir(parents=True, exist_ok=True)

                # 🔥 IMPORTANTE: importar tu función
                from reportes.generar_string_fv import generar_string_fv

                generar_string_fv(
                    n_series=n_series,
                    out_path=ruta,
                    n_strings=n_strings
                )

                string_fv_path = str(ruta)
                paths["string_fv"] = string_fv_path

    except Exception as e:
        string_fv_path = None

    # =========================================================
    # MOSTRAR STRING FV
    # =========================================================
    existe_imagen = string_fv_path and Path(str(string_fv_path)).exists()

    if existe_imagen:

        story.append(Paragraph("Configuración del String Fotovoltaico", styles["Heading2"]))
        story.append(Spacer(1, 6))

        if safe_image:
            img = safe_image(str(string_fv_path), max_w=content_w, max_h=300)
        else:
            img = Image(str(string_fv_path))
            img.drawWidth = content_w
            img.drawHeight = 300

        if img:
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

        msg = "No se pudo generar el diagrama del string fotovoltaico."

        if not paneles or not strings:
            msg += " (Sin datos de strings en resultado.paneles)"
        else:
            msg += " (Error al generar imagen o archivo no encontrado)"

        story.append(Paragraph(msg, styles["BodyText"]))
        story.append(Spacer(1, 6))

        # DEBUG mínimo útil
        story.append(
            Paragraph(
                f"DEBUG → n_series={locals().get('n_series', None)}, "
                f"n_strings={locals().get('n_strings', None)}",
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 12))

    return story

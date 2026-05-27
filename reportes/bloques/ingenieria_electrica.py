from ..secciones_tecnicas.resumen_tecnico import build_resumen_tecnico
from ..secciones_tecnicas.tabla_strings import crear_tabla_strings
from ..secciones_tecnicas.tabla_nec import (
    crear_tabla_parametros_electricos,
    crear_tabla_dimensionamiento_nec,
    crear_tabla_indicadores,
    crear_tabla_caida_voltaje,
)
from ..secciones_tecnicas.layout_paneles import insertar_layout_paneles
from ..secciones_tecnicas.tabla_distribucion_strings import crear_tabla_distribucion_inversores
from pathlib import Path
from reportlab.platypus import (
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Table,
    TableStyle,
)

from reportlab.lib import colors
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

def _section_caida_voltaje(story, resultado, pal, styles, content_w):

    story.append(
        Paragraph(
            "Análisis de caída de voltaje",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 6))

    tabla = crear_tabla_caida_voltaje(
        resultado,
        pal,
        content_w,
    )

    if tabla:
        story.append(tabla)
    else:
        story.append(
            Paragraph(
                "No hay análisis de caída de voltaje disponible.",
                styles["BodyText"]
            )
        )

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

def _section_optimizacion_economica(
    story,
    resultado,
    pal,
    styles,
    content_w
):

    # ======================================================
    # Leer optimización económica
    # Nuevo contrato: resultado.optimizacion_economica
    # Fallback: resultado.energia.optimizacion_economica
    # ======================================================
    opt = leer(
        resultado,
        "optimizacion_economica",
        None
    )

    if not opt:

        energia = leer(
            resultado,
            "energia",
            None
        )

        if energia is not None:
            opt = leer(
                energia,
                "optimizacion_economica",
                None
            )

    if not opt:
        return

    tabla = opt.get(
        "tabla_evaluacion",
        []
    )

    if not tabla:
        return

    pdc_optimo = float(
        opt.get("pdc_kw", 0.0) or 0.0
    )

    filas_filtradas = []

    for r in tabla:

        pdc = float(
            r.get("pdc_kw", 0.0) or 0.0
        )

        incluir = False

        if abs(pdc - pdc_optimo) <= 25:
            incluir = True

        if int(round(pdc)) % 10 == 0:
            incluir = True

        if abs(pdc - pdc_optimo) < 0.5:
            incluir = True

        if incluir:
            filas_filtradas.append(r)

    if not filas_filtradas:
        return

    story.append(
        Paragraph(
            "Optimización económica del sistema FV",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 6))

    data = [[
        "kWp",
        "Gen. anual",
        "Autocons.",
        "Exced.",
        "Cobertura",
        "Benef. bruto",
        "CAPEX",
        "Benef. neto",
    ]]

    for r in filas_filtradas:

        pdc = float(
            r.get("pdc_kw", 0.0) or 0.0
        )

        marca = (
            "★ "
            if abs(pdc - pdc_optimo) < 0.5
            else ""
        )

        data.append([
            f"{marca}{pdc:,.1f}",
            f"{float(r.get('generacion_kwh_anual', 0.0)):,.0f}",
            f"{float(r.get('autoconsumo_kwh_anual', 0.0)):,.0f}",
            f"{float(r.get('excedente_kwh_anual', 0.0)):,.0f}",
            f"{float(r.get('cobertura_directa_pct', 0.0)):,.1f}%",
            f"L {float(r.get('beneficio_bruto_l_anual', 0.0)):,.0f}",
            f"L {float(r.get('capex_estimado_l', 0.0)):,.0f}",
            f"L {float(r.get('beneficio_neto_l_anual', 0.0)):,.0f}",
        ])

    tabla_pdf = Table(
        data,
        colWidths=[
            content_w * 0.08,
            content_w * 0.12,
            content_w * 0.12,
            content_w * 0.11,
            content_w * 0.10,
            content_w * 0.14,
            content_w * 0.14,
            content_w * 0.14,
        ],
        repeatRows=1,
    )

    tabla_pdf.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3551")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),

    ]))

    story.append(tabla_pdf)
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "La fila marcada con ★ corresponde "
            "al tamaño seleccionado por el "
            "optimizador económico.",
            styles["BodyText"]
        )
    )

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

def _section_demanda_vs_fv_horaria(story, paths, styles, content_w):

    story.append(Paragraph("Demanda del cliente vs generación fotovoltaica", styles["Heading2"]))
    story.append(Spacer(1, 6))

    chart = None

    if isinstance(paths, dict):
        chart = paths.get("chart_demanda_vs_fv_horaria")

    _insert_chart(
        story,
        chart,
        styles,
        content_w,
        "No se pudo generar la gráfica de demanda del cliente vs generación FV."
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

def _section_layout_preliminar(story, resultado, pal, styles, content_w):

    layout = leer(resultado, "layout_preliminar", None)

    if layout is None:
        return

    story.append(Paragraph("Layout preliminar del sistema FV", styles["Heading2"]))
    story.append(Spacer(1, 6))

    data = [
        ["Concepto", "Valor"],
        ["Cantidad de paneles", f"{layout.n_paneles:,}"],
        ["Área por panel", f"{layout.area_panel_m2:,.2f} m²"],
        ["Área bruta de paneles", f"{layout.area_bruta_m2:,.2f} m²"],
        ["Factor de ocupación", f"{layout.factor_ocupacion:,.2f}"],
        ["Área necesaria estimada", f"{layout.area_necesaria_m2:,.2f} m²"],
        ["Distribución preliminar", f"{layout.filas} filas × {layout.columnas} columnas"],
        ["Paneles colocados", f"{layout.paneles_colocados:,}"],
        ["Espacios sobrantes en cuadrícula", f"{layout.paneles_sobrantes:,}"],
        ["Ancho total estimado", f"{layout.ancho_total_m:,.2f} m"],
        ["Largo total estimado", f"{layout.largo_total_m:,.2f} m"],
        ["Área rectangular estimada", f"{layout.area_rectangular_m2:,.2f} m²"],
    ]

    tabla = Table(
        data,
        colWidths=[
            content_w * 0.45,
            content_w * 0.55,
        ],
        repeatRows=1,
    )

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3551")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(tabla)
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            layout.nota,
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 12))
# =========================================================
# PAGE 5
# =========================================================

def build_ingenieria_electrica(resultado, datos, paths, pal, styles, content_w, safe_image=None):

    story = []

    resultado = resultado or {}
    paths = paths or {}

    # =========================================================
    # OBTENER STRINGS (CORRECTO)
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
    _section_caida_voltaje(story, resultado, pal, styles, content_w)

    _section_potencia_horaria(story, paths, styles, content_w)
    _section_energia_horaria(story, paths, styles, content_w)
    _section_demanda_vs_fv_horaria(story, paths, styles, content_w)
    _section_energia_mensual(story, paths, styles, content_w)
    _section_optimizacion_economica(story, resultado, pal, styles, content_w)
    _section_layout_preliminar(story, resultado, pal, styles, content_w)
    insertar_layout_paneles(story, paths, styles, content_w, safe_image)

    story.append(PageBreak())

    # =========================================================
    # GENERAR STRING FV (CORRECTO)
    # =========================================================
    string_fv_path = None

    try:
        if strings:

            ruta = Path("outputs/string_fv.png")
            ruta.parent.mkdir(parents=True, exist_ok=True)

            from reportes.generar_string_fv import generar_string_fv

            generar_string_fv(strings, ruta)

            string_fv_path = str(ruta)
            paths["string_fv"] = string_fv_path

    except Exception as e:
        print("Error generando string FV:", e)
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

        # 🔥 TEXTO CORRECTO (NO MIENTE)
        story.append(
            Paragraph(
                "Configuración real del generador fotovoltaico. "
                "Cada string se conecta a su respectivo MPPT del inversor. "
                "Solo se presentan conexiones en paralelo cuando múltiples strings "
                "comparten el mismo MPPT.",
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 12))

    else:

        msg = "No se pudo generar el diagrama del string fotovoltaico."

        if not strings:
            msg += " (Sin datos de strings en resultado.paneles)"
        else:
            msg += " (Error al generar imagen o archivo no encontrado)"

        story.append(Paragraph(msg, styles["BodyText"]))
        story.append(Spacer(1, 6))

        # 🔥 DEBUG REAL (NO basura vieja)
        story.append(
            Paragraph(
                f"DEBUG → strings_detectados={len(strings)}",
                styles["BodyText"]
            )
        )

        story.append(Spacer(1, 12))

    return story

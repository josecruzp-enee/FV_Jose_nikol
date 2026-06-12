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
from reportes.secciones_tecnicas.conclusiones import agregar_pagina_conclusiones_ejecutivas
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

    opt = leer(resultado, "optimizacion_economica", None)

    if not opt:
        energia = leer(resultado, "energia", None)
        if energia is not None:
            opt = leer(energia, "optimizacion_economica", None)

    if not opt or not isinstance(opt, dict):
        return

    sin = opt.get("sin_inyeccion", {}) or {}
    con = opt.get("con_inyeccion", {}) or {}

    if not sin and not con:
        return

    story.append(Paragraph("Optimización económica del sistema FV", styles["Heading2"]))
    story.append(Spacer(1, 6))

    pdc_sin = float(sin.get("pdc_kw", sin.get("kwp", 0.0)) or 0.0)
    pdc_con = float(con.get("pdc_kw", con.get("kwp", 0.0)) or 0.0)

    exc_sin = float(sin.get("excedente_pct_generacion", 0.0) or 0.0)
    exc_con = float(con.get("excedente_pct_generacion", 0.0) or 0.0)

    ben_sin = float(sin.get("beneficio_neto_l_anual", 0.0) or 0.0)
    ben_con = float(con.get("beneficio_neto_l_anual", 0.0) or 0.0)

    texto_conclusion = (
        f"<b>Resultado de optimización:</b> el escenario sin inyección recomienda "
        f"<b>{pdc_sin:,.1f} kWp</b>, con beneficio neto anual estimado de "
        f"<b>L {ben_sin:,.0f}</b> y excedente de <b>{exc_sin:,.1f}%</b>. "
    )

    if con:
        texto_conclusion += (
            f"El escenario con inyección aumenta el tamaño recomendado a "
            f"<b>{pdc_con:,.1f} kWp</b>, con beneficio neto anual de "
            f"<b>L {ben_con:,.0f}</b>, pero eleva el excedente a "
            f"<b>{exc_con:,.1f}%</b>. "
        )

    texto_conclusion += (
        "Para diseño base se recomienda el escenario sin inyección. "
        "El escenario con inyección debe evaluarse únicamente si existe contrato "
        "formal o reconocimiento real de excedentes."
    )

    story.append(Paragraph(texto_conclusion, styles["BodyText"]))
    story.append(Spacer(1, 8))

    data = [[
        "Escenario",
        "kWp recomendado",
        "Paneles",
        "Gen. anual",
        "Autocons.",
        "Excedente",
        "Cobertura",
        "Benef. neto",
    ]]

    if sin:
        data.append([
            "Sin inyección",
            f"{pdc_sin:,.1f}",
            f"{int(sin.get('n_paneles', 0) or 0):,}",
            f"{float(sin.get('generacion_kwh_anual', 0.0) or 0.0):,.0f}",
            f"{float(sin.get('autoconsumo_kwh_anual', 0.0) or 0.0):,.0f}",
            f"{exc_sin:,.1f}%",
            f"{float(sin.get('cobertura_directa_pct', 0.0) or 0.0):,.1f}%",
            f"L {ben_sin:,.0f}",
        ])

    if con:
        data.append([
            "Con inyección",
            f"{pdc_con:,.1f}",
            f"{int(con.get('n_paneles', 0) or 0):,}",
            f"{float(con.get('generacion_kwh_anual', 0.0) or 0.0):,.0f}",
            f"{float(con.get('autoconsumo_kwh_anual', 0.0) or 0.0):,.0f}",
            f"{exc_con:,.1f}%",
            f"{float(con.get('cobertura_directa_pct', 0.0) or 0.0):,.1f}%",
            f"L {ben_con:,.0f}",
        ])

    tabla_pdf = Table(
        data,
        colWidths=[
            content_w * 0.15,
            content_w * 0.12,
            content_w * 0.09,
            content_w * 0.13,
            content_w * 0.13,
            content_w * 0.11,
            content_w * 0.11,
            content_w * 0.16,
        ],
        repeatRows=1,
    )

    tabla_pdf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3551")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(tabla_pdf)
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "<b>Decisión recomendada:</b> usar el escenario sin inyección "
            "como diseño base. El escenario con inyección debe presentarse como "
            "alternativa comercial condicionada a contrato formal de compra de excedentes.",
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 12))

    tabla = sin.get("tabla_evaluacion", [])

    if not tabla:
        return

    pdc_optimo = pdc_sin

    puntos_interes = {
        20,
        40,
        50,
        60,
        int(round(pdc_optimo)),
        70,
        80,
        100,
        120,
    }

    filas_filtradas = []

    for r in tabla:
        pdc_float = float(r.get("pdc_kw", 0.0) or 0.0)
        pdc_int = int(round(pdc_float))

        if pdc_int in puntos_interes or abs(pdc_float - pdc_optimo) < 0.5:
            filas_filtradas.append(r)

    filas_unicas = {}

    for r in filas_filtradas:
        pdc_float = float(r.get("pdc_kw", 0.0) or 0.0)
        filas_unicas[pdc_float] = r

    filas_filtradas = sorted(
        filas_unicas.values(),
        key=lambda x: float(x.get("pdc_kw", 0.0) or 0.0)
    )

    if not filas_filtradas:
        return

    story.append(
        Paragraph(
            "Evaluación resumida del escenario base sin inyección",
            styles["Heading3"]
        )
    )
    story.append(Spacer(1, 6))

    data_eval = [[
        "kWp",
        "Gen.",
        "Autocons.",
        "Exced.",
        "Cobertura",
        "CAPEX",
        "Benef. neto",
    ]]

    for r in filas_filtradas:
        pdc = float(r.get("pdc_kw", 0.0) or 0.0)

        marca = "★ " if abs(pdc - pdc_optimo) < 0.5 else ""

        data_eval.append([
            f"{marca}{pdc:,.1f}",
            f"{float(r.get('generacion_kwh_anual', 0.0) or 0.0):,.0f}",
            f"{float(r.get('autoconsumo_kwh_anual', 0.0) or 0.0):,.0f}",
            f"{float(r.get('excedente_pct_generacion', 0.0) or 0.0):,.1f}%",
            f"{float(r.get('cobertura_directa_pct', 0.0) or 0.0):,.1f}%",
            f"L {float(r.get('capex_estimado_l', 0.0) or 0.0):,.0f}",
            f"L {float(r.get('beneficio_neto_l_anual', 0.0) or 0.0):,.0f}",
        ])

    tabla_eval_pdf = Table(
        data_eval,
        colWidths=[
            content_w * 0.10,
            content_w * 0.14,
            content_w * 0.14,
            content_w * 0.12,
            content_w * 0.12,
            content_w * 0.18,
            content_w * 0.20,
        ],
        repeatRows=1,
    )

    tabla_eval_pdf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3551")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ]))

    story.append(tabla_eval_pdf)
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "La fila marcada con ★ corresponde al tamaño usado como diseño base "
            "del sistema fotovoltaico. Los demás puntos se muestran solo como "
            "referencia comparativa.",
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

    if isinstance(layout, dict):
        layout = layout.get("layout") or layout

    def val(campo, default=None):
        if isinstance(layout, dict):
            return layout.get(campo, default)
        return getattr(layout, campo, default)

    story.append(Paragraph("Layout preliminar del sistema FV", styles["Heading2"]))
    story.append(Spacer(1, 6))

    data = [
        ["Concepto", "Valor"],
        ["Cantidad de paneles", f"{int(val('n_paneles', 0)):,}"],
        ["Filas", f"{int(val('filas', 0)):,}"],
        ["Columnas", f"{int(val('columnas', 0)):,}"],
        ["Paneles colocados", f"{int(val('paneles_colocados', 0)):,}"],
        ["Espacios sobrantes", f"{int(val('paneles_sobrantes', 0)):,}"],
        ["Ancho total estimado", f"{float(val('ancho_total_m', 0.0)):,.2f} m"],
        ["Largo total estimado", f"{float(val('largo_total_m', 0.0)):,.2f} m"],
        ["Área rectangular estimada", f"{float(val('area_rectangular_m2', 0.0)):,.2f} m²"],
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
            "Layout preliminar informativo. No considera obstáculos, sombras, "
            "orientación real ni verificación estructural.",
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
    agregar_pagina_conclusiones_ejecutivas(story, styles, resultado, datos)
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

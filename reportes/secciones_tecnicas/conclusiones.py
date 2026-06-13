# reportes/secciones_tecnicas/conclusiones.py

from __future__ import annotations

from typing import Any, Optional


# ======================================================
# UTILIDADES SEGURAS
# ======================================================

def _get(obj: Any, *paths: str, default: Any = None) -> Any:
    """
    Obtiene valores desde objetos, dataclasses o dicts sin romper el PDF.

    Uso:
        _get(resultado, "financiero.dscr", "finanzas.dscr", default=0)
    """
    for path in paths:
        actual = obj
        ok = True

        for part in path.split("."):
            if actual is None:
                ok = False
                break

            if isinstance(actual, dict):
                actual = actual.get(part)
            else:
                actual = getattr(actual, part, None)

        if ok and actual is not None:
            return actual

    return default


def _num(valor: Any, default: float = 0.0) -> float:
    try:
        if valor is None:
            return default
        return float(valor)
    except Exception:
        return default


def _fmt_lps(valor: Any) -> str:
    return f"L {_num(valor):,.2f}"


def _fmt_kwh(valor: Any) -> str:
    return f"{_num(valor):,.0f} kWh"


def _fmt_kwp(valor: Any) -> str:
    return f"{_num(valor):,.2f} kWp"


def _fmt_pct(valor: Any) -> str:
    return f"{_num(valor):,.1f}%"


# ======================================================
# EXTRACCIÓN DE MÉTRICAS PRINCIPALES
# ======================================================
def extraer_metricas_conclusion(resultado: Any, datos: Any = None) -> dict:
    """
    Extrae métricas principales del resultado consolidado.

    Prioridad:
    1. Sistema FV real conectado desde resultado.paneles.strings.
    2. Fallback desde sizing / optimización económica.
    """

    energia = _get(resultado, "energia", default=None)
    financiero = _get(
        resultado,
        "finanzas",
        "financiero",
        "resultado_financiero",
        default=None,
    )
    
    # ======================================================
    # LAYOUT
    # ======================================================

    layout = layout_preliminar

    if isinstance(layout, dict):
        layout = layout.get("layout") or layout

    area_layout = 0.0
    ancho_layout_m = 0.0
    largo_layout_m = 0.0

    if layout is not None:
        if isinstance(layout, dict):
            ancho_layout_m = _num(
                layout.get("ancho_total_m", 0.0)
                or layout.get("ancho_layout_grafico_m", 0.0)
            )

            largo_layout_m = _num(
                layout.get("largo_total_m", 0.0)
                or layout.get("largo_layout_grafico_m", 0.0)
            )

            area_layout = _num(
                layout.get("area_rectangular_m2", 0.0)
                or layout.get("area_necesaria_m2", 0.0)
            )

        else:
            ancho_layout_m = _num(
                getattr(layout, "ancho_total_m", 0.0)
                or getattr(layout, "ancho_layout_grafico_m", 0.0)
            )

            largo_layout_m = _num(
                getattr(layout, "largo_total_m", 0.0)
                or getattr(layout, "largo_layout_grafico_m", 0.0)
            )

            area_layout = _num(
                getattr(layout, "area_rectangular_m2", 0.0)
                or getattr(layout, "area_necesaria_m2", 0.0)
            )

    if ancho_layout_m > 0 and largo_layout_m > 0:
        area_layout = ancho_layout_m * largo_layout_m

    opt = _get(resultado, "optimizacion_economica", default=None)

    if not opt and energia is not None:
        opt = _get(energia, "optimizacion_economica", default=None)

    sin = {}
    con = {}

    if isinstance(opt, dict):
        sin = opt.get("sin_inyeccion", {}) or {}
        con = opt.get("con_inyeccion", {}) or {}

    # ======================================================
    # ENERGÍA
    # ======================================================

    consumo_anual = 0.0
    consumo_12m = []

    if datos is not None:
        consumo_12m = _get(datos, "consumo_12m", default=[]) or []

    consumo_anual = sum(_num(x) for x in consumo_12m)

    if not consumo_anual:
        consumo_anual = _get(
            resultado,
            "consumo_anual",
            "consumo_anual_kwh",
            default=0,
        )

    produccion_anual = _get(
        resultado,
        "produccion_anual",
        "produccion_anual_kwh",
        "energia.produccion_anual",
        "energia.generacion_anual",
        "energia.produccion_anual_kwh",
        "energia.generacion_anual_kwh",
        "energia.energia_anual_kwh",
        "energia.energia_util_anual",
        "sizing.produccion_anual",
        "sizing.produccion_anual_kwh",
        default=0,
    )

    if not produccion_anual:
        produccion_anual = sin.get("generacion_kwh_anual", 0.0)

    cobertura_real = _get(
        resultado,
        "cobertura_real",
        "cobertura_real_pct",
        "energia.cobertura_real",
        "energia.cobertura_real_pct",
        "sizing.cobertura_real",
        "sizing.cobertura_real_pct",
        default=0,
    )

    if not cobertura_real:
        cobertura_real = sin.get("cobertura_directa_pct", 0.0)

    if _num(consumo_anual) > 0 and _num(produccion_anual) > 0:
        cobertura_real = (_num(produccion_anual) / _num(consumo_anual)) * 100.0

    # ======================================================
    # SISTEMA FV REAL CONECTADO
    # ======================================================

    strings = _get(resultado, "paneles.strings", default=[]) or []
    panel = _get(resultado, "paneles.panel", default=None)

    panel_wp_real = _num(
        _get(
            panel,
            "pmax_w",
            "potencia_wp",
            default=0,
        )
    )

    n_paneles_reales = sum(
        int(_get(s, "n_series", default=0) or 0)
        for s in strings
    )

    if n_paneles_reales > 0 and panel_wp_real > 0:
        n_paneles = n_paneles_reales
        potencia_panel_wp = panel_wp_real
        kwp = n_paneles * potencia_panel_wp / 1000.0

    else:
        kwp = _get(
            resultado,
            "kwp",
            "pdc_kw",
            "potencia_dc_kwp",
            "sizing.kwp",
            "sizing.pdc_kw",
            "sizing.potencia_kwp",
            "sizing.potencia_dc_kwp",
            "paneles.kwp",
            "paneles.pdc_kw",
            "paneles.potencia_dc_kwp",
            "paneles.kwp_total",
            default=0,
        )

        if not kwp:
            kwp = sin.get("pdc_kw", sin.get("kwp", 0.0))

        n_paneles = _get(
            resultado,
            "n_paneles",
            "numero_paneles",
            "paneles.n_paneles",
            "paneles.numero_paneles",
            "sizing.n_paneles",
            "sizing.numero_paneles",
            default=0,
        )

        if not n_paneles:
            n_paneles = sin.get("n_paneles", 0)

        potencia_panel_wp = _get(
            resultado,
            "potencia_panel_wp",
            "paneles.potencia_panel_wp",
            "paneles.potencia_wp",
            "paneles.modulo_wp",
            "sizing.potencia_panel_wp",
            default=0,
        )

        if not potencia_panel_wp and _num(kwp) > 0 and _num(n_paneles) > 0:
            potencia_panel_wp = (_num(kwp) * 1000.0) / _num(n_paneles)

    cantidad_inversores = _get(
        resultado,
        "cantidad_inversores",
        "electrical.cantidad_inversores",
        "paneles.cantidad_inversores",
        "sizing.cantidad_inversores",
        "sizing.n_inversores",
        default=0,
    )

    kw_ac_total = _get(
        resultado,
        "kw_ac_total",
        "potencia_ac_kw",
        "electrical.kw_ac_total",
        "paneles.kw_ac_total",
        "sizing.kw_ac_total",
        default=0,
    )

    # ======================================================
    # FINANZAS
    # ======================================================

    capex = _get(
        resultado,
        "capex",
        "capex_L",
        "capex_total",
        "financiero.capex",
        "financiero.capex_L",
        "financiero.capex_total",
        "finanzas.capex",
        "finanzas.capex_L",
        "finanzas.capex_total",
        "resultado_financiero.capex_L",
        default=0,
    )

    if not capex:
        capex = sin.get("capex_estimado_l", 0.0)

    dscr = _get(
        resultado,
        "dscr",
        "indicadores.dscr",
        "resumen.dscr",
        "financiero.evaluacion.dscr",
        "finanzas.evaluacion.dscr",
        "resultado_financiero.evaluacion.dscr",
        default=0,
    )

    if not dscr and financiero:
        try:
            if isinstance(financiero, dict):
                dscr = financiero.get("evaluacion", {}).get("dscr", 0.0)
            else:
                evaluacion = getattr(financiero, "evaluacion", None)

                if isinstance(evaluacion, dict):
                    dscr = evaluacion.get("dscr", 0.0)
                else:
                    dscr = getattr(evaluacion, "dscr", 0.0)
        except Exception:
            dscr = 0.0

    ahorro_mensual = _get(
        resultado,
        "ahorro_neto_mensual",
        "financiero.ahorro_neto_mensual",
        "finanzas.ahorro_neto_mensual",
        "financiero.evaluacion.neto_prom",
        "finanzas.evaluacion.neto_prom",
        default=0,
    )

    ahorro_anual = _get(
        resultado,
        "ahorro_neto_anual",
        "beneficio_neto_anual",
        "financiero.ahorro_neto_anual",
        "financiero.ahorro_anual_L",
        "finanzas.ahorro_neto_anual",
        "finanzas.ahorro_anual_L",
        default=0,
    )

    if not ahorro_anual:
        ahorro_anual = sin.get("beneficio_neto_l_anual", 0.0)

    if not ahorro_mensual and _num(ahorro_anual) > 0:
        ahorro_mensual = _num(ahorro_anual) / 12.0

    beneficio_bruto_anual = _num(ahorro_anual)

    beneficio_neto_anual = 0.0

    if _num(ahorro_mensual) > 0:
        beneficio_neto_anual = _num(ahorro_mensual) * 12.0

    pago_actual = _get(
        resultado,
        "pago_actual",
        "pago_actual_mensual",
        "financiero.pago_actual",
        "financiero.pago_actual_mensual",
        "finanzas.pago_actual",
        "finanzas.pago_actual_mensual",
        default=0,
    )

    pago_total_fv = _get(
        resultado,
        "pago_total_con_fv",
        "total_pago_con_fv",
        "financiero.pago_total_con_fv",
        "finanzas.pago_total_con_fv",
        default=0,
    )

    cuota = _get(
        resultado,
        "cuota_mensual",
        "financiero.cuota_mensual",
        "finanzas.cuota_mensual",
        "resultado_financiero.cuota_mensual",
        default=0,
    )

    peor_mes = _get(
        resultado,
        "peor_mes",
        "financiero.evaluacion.peor_mes",
        "finanzas.evaluacion.peor_mes",
        "resultado_financiero.evaluacion.peor_mes",
        default=0,
    )

    if not peor_mes and financiero:
        try:
            if isinstance(financiero, dict):
                peor_mes = financiero.get("evaluacion", {}).get("peor_mes", 0.0)
            else:
                evaluacion = getattr(financiero, "evaluacion", None)

                if isinstance(evaluacion, dict):
                    peor_mes = evaluacion.get("peor_mes", 0.0)
                else:
                    peor_mes = getattr(evaluacion, "peor_mes", 0.0)
        except Exception:
            peor_mes = 0.0

    # ======================================================
    # FALLBACK DESDE TABLA 12 MESES
    # ======================================================

    tabla_12m = None

    if financiero:
        if isinstance(financiero, dict):
            tabla_12m = financiero.get("tabla_12m")
        else:
            tabla_12m = getattr(financiero, "tabla_12m", None)

    if isinstance(tabla_12m, list) and tabla_12m:

        if not pago_actual:
            pago_actual = sum(
                float(x.get("factura_base_L", 0.0) or 0.0)
                for x in tabla_12m
            ) / len(tabla_12m)

        if not pago_total_fv:
            pago_total_fv = sum(
                (
                    float(x.get("pago_enee_L", 0.0) or 0.0)
                    + float(x.get("cuota_L", 0.0) or 0.0)
                    + float(x.get("om_L", 0.0) or 0.0)
                )
                for x in tabla_12m
            ) / len(tabla_12m)

        if not cuota:
            cuota = sum(
                float(x.get("cuota_L", 0.0) or 0.0)
                for x in tabla_12m
            ) / len(tabla_12m)

        if not ahorro_mensual:
            ahorro_mensual = sum(
                float(x.get("neto_L", 0.0) or 0.0)
                for x in tabla_12m
            ) / len(tabla_12m)

        if not peor_mes:
            peor_mes = min(
                float(x.get("neto_L", 0.0) or 0.0)
                for x in tabla_12m
            )

    # ======================================================
    # LAYOUT
    # ======================================================

    layout = layout_preliminar

    if isinstance(layout, dict):
        layout = layout.get("layout") or layout

    area_layout = 0.0

    if layout is not None:
        if isinstance(layout, dict):
            area_layout = (
                layout.get("area_rectangular_m2", 0.0)
                or layout.get("area_necesaria_m2", 0.0)
                or 0.0
            )
        else:
            area_layout = (
                getattr(layout, "area_rectangular_m2", 0.0)
                or getattr(layout, "area_necesaria_m2", 0.0)
                or 0.0
            )

    return {
        "consumo_anual": _num(consumo_anual),
        "produccion_anual": _num(produccion_anual),
        "cobertura_real": _num(cobertura_real),
        "kwp": _num(kwp),
        "capex": _num(capex),
        "dscr": _num(dscr),
        "ahorro_mensual": _num(ahorro_mensual),
        "ahorro_anual": _num(ahorro_anual),
        "beneficio_bruto_anual": _num(beneficio_bruto_anual),
        "beneficio_neto_anual": _num(beneficio_neto_anual),
        "pago_actual": _num(pago_actual),
        "pago_total_fv": _num(pago_total_fv),
        "cuota": _num(cuota),
        "peor_mes": _num(peor_mes),
        "n_paneles": int(_num(n_paneles)),
        "potencia_panel_wp": _num(potencia_panel_wp),
        "cantidad_inversores": int(_num(cantidad_inversores)),
        "kw_ac_total": _num(kw_ac_total),
        "area_layout": _num(area_layout),
        "escenario_base": sin,
        "escenario_inyeccion": con,
        "ancho_layout_m": _num(ancho_layout_m),
        "largo_layout_m": _num(largo_layout_m),
    }
# ======================================================
# CLASIFICACIÓN EJECUTIVA
# ======================================================

def clasificar_viabilidad(m: dict) -> tuple[str, str]:
    """
    Devuelve estado ejecutivo y explicación corta.
    """

    dscr = m["dscr"]
    ahorro = m["ahorro_mensual"]
    peor_mes = m["peor_mes"]

    if dscr >= 1.20 and ahorro > 0 and peor_mes >= 0:
        return (
            "VIABLE",
            "El proyecto presenta capacidad financiera adecuada, ahorro neto positivo y margen de pago suficiente bajo las condiciones evaluadas.",
        )

    if dscr >= 1.00 and ahorro > 0:
        return (
            "VIABLE CON OBSERVACIONES",
            "El proyecto genera ahorro, pero el margen financiero debe revisarse con mayor detalle antes de comprometer financiamiento.",
        )

    return (
        "NO RECOMENDADO",
        "El proyecto no muestra suficiente margen financiero bajo las condiciones actuales y requiere ajuste de tamaño, CAPEX o esquema de financiamiento.",
    )


# ======================================================
# TEXTO AUTOMÁTICO DE CONCLUSIONES
# ======================================================

def generar_conclusiones_ejecutivas(resultado: Any, datos: Any = None) -> dict:
    """
    Genera contenido estructurado para la página de conclusiones.
    """

    m = extraer_metricas_conclusion(resultado, datos)
    estado, criterio_estado = clasificar_viabilidad(m)

    conclusiones = []

    conclusiones.append({
        "titulo": "1. Viabilidad general del proyecto",
        "texto": (
            f"El proyecto se clasifica como {estado}. "
            f"{criterio_estado} "
            f"El indicador DSCR calculado es {m['dscr']:.2f}, "
            f"con un ahorro neto mensual estimado de {_fmt_lps(m['ahorro_mensual'])}."
        ),
    })

    conclusiones.append({
        "titulo": "2. Resultado energético esperado",
        "texto": (
            f"El sistema fotovoltaico propuesto tiene una potencia instalada de {_fmt_kwp(m['kwp'])} "
            f"y una producción anual estimada de {_fmt_kwh(m['produccion_anual'])}. "
            f"Esta generación cubre aproximadamente {_fmt_pct(m['cobertura_real'])} "
            f"del consumo anual del cliente, cuyo consumo total es de {_fmt_kwh(m['consumo_anual'])}."
        ),
    })

    conclusiones.append({
        "titulo": "3. Impacto financiero esperado",
        "texto": (
            f"El pago energético mensual actual se estima en {_fmt_lps(m['pago_actual'])}. "
            f"Con el sistema FV y el financiamiento considerado, el pago total mensual proyectado "
            f"se reduce a aproximadamente {_fmt_lps(m['pago_total_fv'])}, incluyendo una cuota "
            f"de financiamiento de {_fmt_lps(m['cuota'])}. "
            f"El beneficio económico anual generado por la energía fotovoltaica "
            f"se estima en {_fmt_lps(m['beneficio_bruto_anual'])}. "
            f"Después de considerar el financiamiento del proyecto, "
            f"el ahorro neto anual esperado para el cliente es de "
            f"{_fmt_lps(m['beneficio_neto_anual'])}."
        ),
    })

    conclusiones.append({
        "titulo": "4. Criterio técnico de dimensionamiento",
        "texto": (
            f"El tamaño seleccionado prioriza autoconsumo, estabilidad financiera y control del excedente energético. "
            f"Aunque un sistema de mayor potencia puede incrementar la generación anual, también puede aumentar "
            f"la energía excedente y la dependencia de condiciones comerciales o regulatorias externas."
        ),
    })

    conclusiones.append({
        "titulo": "5. Alcance físico preliminar",
        "texto": (
            f"La solución considera {m['n_paneles']} módulos fotovoltaicos "
            f"de {m['potencia_panel_wp']:.0f} Wp. "
            f"El área preliminar estimada para el arreglo es de {m['area_layout']:.2f} m². "
            f"Este valor debe validarse en campo considerando obstáculos, sombras, orientación real, "
            f"accesos de mantenimiento y revisión estructural de la cubierta."
        ),
    })

    conclusiones.append({
        "titulo": "6. Recomendación final",
        "texto": (
            f"Se recomienda avanzar con el diseño base evaluado, manteniendo como prioridad el autoconsumo "
            f"y la reducción directa de la factura eléctrica. Antes de ejecución, se recomienda validar "
            f"perfil horario real de demanda, condiciones de instalación, disponibilidad de área útil, "
            f"capacidad estructural y condiciones definitivas de interconexión."
        ),
    })

    return {
        "estado": estado,
        "metricas": m,
        "conclusiones": conclusiones,
    }


# ======================================================
# FUNCIÓN REPORTLAB PARA INSERTAR PÁGINA
# ======================================================

def agregar_pagina_conclusiones_ejecutivas(story, styles, resultado, datos=None):
    """
    Agrega una página completa de conclusiones ejecutivas al PDF.

    Requiere:
        from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm

    Se importa dentro de la función para no afectar otros módulos.
    """

    from reportlab.platypus import Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.styles import ParagraphStyle

    if "BodyJustify" not in styles:
        styles.add(
            ParagraphStyle(
                name="BodyJustify",
                parent=styles["BodyText"],
                alignment=TA_JUSTIFY,
        )
    )
    
    data = generar_conclusiones_ejecutivas(resultado, datos)
    m = data["metricas"]
    estado = data["estado"]

    story.append(PageBreak())

    story.append(Paragraph("Conclusiones Ejecutivas y Recomendaciones", styles["Title"]))
    story.append(Spacer(1, 0.35 * cm))

    resumen = [
        ["Indicador", "Resultado"],
        ["Estado del proyecto", estado],
        ["Potencia FV propuesta", _fmt_kwp(m["kwp"])],
        ["Producción anual estimada", _fmt_kwh(m["produccion_anual"])],
        ["Cobertura energética real", _fmt_pct(m["cobertura_real"])],
        ["Ahorro neto mensual", _fmt_lps(m["ahorro_mensual"])],
        ["DSCR", f"{m['dscr']:.2f}"],
        ["CAPEX estimado", _fmt_lps(m["capex"])],
    ]

    tabla = Table(resumen, colWidths=[7.0 * cm, 8.5 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B3D5C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B8C2CC")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4F6F8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(tabla)
    story.append(Spacer(1, 0.45 * cm))

    for bloque in data["conclusiones"]:
        story.append(Paragraph(bloque["titulo"], styles["Heading2"]))
        story.append(Spacer(1, 0.10 * cm))
        story.append(Paragraph(bloque["texto"], styles["BodyJustify"]))
        story.append(Spacer(1, 0.25 * cm))

    story.append(Spacer(1, 0.25 * cm))

    nota = (
        "Nota: Las conclusiones anteriores corresponden a una evaluación preliminar basada en los datos "
        "ingresados y resultados calculados por FV Engine. Para etapa constructiva se requiere validación "
        "final de sitio, ingeniería de detalle, interconexión, protecciones, canalización y revisión estructural."
    )

    story.append(Paragraph(nota, styles["Italic"]))

# exportadores/comentarios_pdf_fv.py

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

def extraer_metricas_conclusion(resultado: Any) -> dict:
    """
    Extrae métricas principales del resultado consolidado.
    No calcula ingeniería nueva. Solo interpreta datos existentes.
    """

    consumo_anual = _get(
        resultado,
        "datos.consumo_anual",
        "proyecto.consumo_anual",
        "energia.consumo_anual",
        "energia.consumo_anual_kwh",
        "consumo_anual",
        default=0,
    )

    produccion_anual = _get(
        resultado,
        "energia.produccion_anual",
        "energia.generacion_anual",
        "energia.produccion_anual_kwh",
        "sizing.produccion_anual",
        "produccion_anual",
        default=0,
    )

    cobertura_real = _get(
        resultado,
        "energia.cobertura_real_pct",
        "sizing.cobertura_real_pct",
        "financiero.cobertura_real_pct",
        "cobertura_real_pct",
        default=0,
    )

    if not cobertura_real and _num(consumo_anual) > 0:
        cobertura_real = (_num(produccion_anual) / _num(consumo_anual)) * 100

    kwp = _get(
        resultado,
        "sizing.kwp",
        "sizing.potencia_kwp",
        "paneles.potencia_dc_kwp",
        "paneles.kwp_total",
        "potencia_dc_kwp",
        default=0,
    )

    capex = _get(
        resultado,
        "financiero.capex",
        "finanzas.capex",
        "capex",
        default=0,
    )

    dscr = _get(
        resultado,
        "financiero.dscr",
        "finanzas.dscr",
        "dscr",
        default=0,
    )

    ahorro_mensual = _get(
        resultado,
        "financiero.ahorro_neto_mensual",
        "finanzas.ahorro_neto_mensual",
        "financiero.ahorro_mensual",
        "ahorro_neto_mensual",
        default=0,
    )

    ahorro_anual = _get(
        resultado,
        "financiero.ahorro_neto_anual",
        "finanzas.ahorro_neto_anual",
        "financiero.beneficio_neto_anual",
        "beneficio_neto_anual",
        default=0,
    )

    if not ahorro_anual and ahorro_mensual:
        ahorro_anual = _num(ahorro_mensual) * 12

    pago_actual = _get(
        resultado,
        "financiero.pago_actual_mensual",
        "finanzas.pago_actual_mensual",
        "pago_actual_mensual",
        default=0,
    )

    pago_total_fv = _get(
        resultado,
        "financiero.pago_total_con_fv",
        "finanzas.pago_total_con_fv",
        "pago_total_con_fv",
        default=0,
    )

    cuota = _get(
        resultado,
        "financiero.cuota_mensual",
        "finanzas.cuota_mensual",
        "cuota_mensual",
        default=0,
    )

    peor_mes = _get(
        resultado,
        "financiero.peor_mes",
        "finanzas.peor_mes",
        "peor_mes",
        default=0,
    )

    n_paneles = _get(
        resultado,
        "paneles.n_paneles",
        "paneles.numero_paneles",
        "sizing.n_paneles",
        "n_paneles",
        default=0,
    )

    potencia_panel_wp = _get(
        resultado,
        "paneles.potencia_panel_wp",
        "sizing.potencia_panel_wp",
        "potencia_panel_wp",
        default=0,
    )

    inversores = _get(
        resultado,
        "paneles.inversores",
        "sizing.inversores",
        "inversores",
        default=None,
    )

    cantidad_inversores = _get(
        resultado,
        "electrical.cantidad_inversores",
        "paneles.cantidad_inversores",
        "sizing.cantidad_inversores",
        "cantidad_inversores",
        default=0,
    )

    kw_ac_total = _get(
        resultado,
        "electrical.kw_ac_total",
        "paneles.kw_ac_total",
        "sizing.kw_ac_total",
        "potencia_ac_kw",
        default=0,
    )

    area_layout = _get(
        resultado,
        "layout.area_rectangular_m2",
        "layout.area_necesaria_m2",
        "sizing.area_necesaria_m2",
        "area_necesaria_m2",
        default=0,
    )

    escenario_base = _get(
        resultado,
        "optimizacion.sin_inyeccion",
        "optimizacion.resultado_sin_inyeccion",
        "sin_inyeccion",
        default=None,
    )

    escenario_inyeccion = _get(
        resultado,
        "optimizacion.con_inyeccion",
        "optimizacion.resultado_con_inyeccion",
        "con_inyeccion",
        default=None,
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
        "pago_actual": _num(pago_actual),
        "pago_total_fv": _num(pago_total_fv),
        "cuota": _num(cuota),
        "peor_mes": _num(peor_mes),
        "n_paneles": int(_num(n_paneles)),
        "potencia_panel_wp": _num(potencia_panel_wp),
        "cantidad_inversores": int(_num(cantidad_inversores)),
        "kw_ac_total": _num(kw_ac_total),
        "area_layout": _num(area_layout),
        "escenario_base": escenario_base,
        "escenario_inyeccion": escenario_inyeccion,
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

def generar_conclusiones_ejecutivas(resultado: Any) -> dict:
    """
    Genera contenido estructurado para la página de conclusiones.
    """

    m = extraer_metricas_conclusion(resultado)
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
            f"del consumo anual del cliente, equivalente a {_fmt_kwh(m['consumo_anual'])}."
        ),
    })

    conclusiones.append({
        "titulo": "3. Resultado financiero para el cliente",
        "texto": (
            f"El pago energético mensual actual se estima en {_fmt_lps(m['pago_actual'])}. "
            f"Con el sistema FV y el financiamiento considerado, el pago total mensual proyectado "
            f"se reduce a aproximadamente {_fmt_lps(m['pago_total_fv'])}, incluyendo una cuota "
            f"de financiamiento de {_fmt_lps(m['cuota'])}. "
            f"Esto representa un ahorro anual estimado de {_fmt_lps(m['ahorro_anual'])}."
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

def agregar_pagina_conclusiones_ejecutivas(story, styles, resultado):
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

    data = generar_conclusiones_ejecutivas(resultado)
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
        story.append(Paragraph(bloque["texto"], styles["BodyText"]))
        story.append(Spacer(1, 0.25 * cm))

    story.append(Spacer(1, 0.25 * cm))

    nota = (
        "Nota: Las conclusiones anteriores corresponden a una evaluación preliminar basada en los datos "
        "ingresados y resultados calculados por FV Engine. Para etapa constructiva se requiere validación "
        "final de sitio, ingeniería de detalle, interconexión, protecciones, canalización y revisión estructural."
    )

    story.append(Paragraph(nota, styles["Italic"]))

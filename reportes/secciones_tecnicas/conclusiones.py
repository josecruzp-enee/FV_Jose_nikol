# -*- coding: utf-8 -*-
# reportes/secciones_tecnicas/conclusiones.py

from __future__ import annotations

from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle


# ======================================================
# UTILIDADES
# ======================================================

def _leer(obj: Any, campo: str, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(campo, default)
    return getattr(obj, campo, default)


def _num(valor: Any, default: float = 0.0) -> float:
    try:
        return default if valor is None else float(valor)
    except (TypeError, ValueError):
        return default


def _fmt_lps(valor: Any) -> str:
    return f"L {_num(valor):,.2f}"


def _fmt_kwh(valor: Any) -> str:
    return f"{_num(valor):,.0f} kWh"


def _fmt_kwp(valor: Any) -> str:
    return f"{_num(valor):,.2f} kWp"


def _fmt_pct(valor: Any) -> str:
    return f"{_num(valor):,.1f}%"


def _es_pago_contado(m: dict) -> bool:
    return _num(m["cuota"]) <= 0.000001


def _fmt_dscr(m: dict) -> str:
    if _es_pago_contado(m):
        return "No aplica"

    dscr = m["dscr"]
    return "No disponible" if dscr is None else f"{_num(dscr):.2f}"


# ======================================================
# EXTRACCIÓN ANCLADA DE MÉTRICAS
# ======================================================

def _metricas_energia(resultado: Any, datos: Any) -> dict:
    energia = resultado.energia

    consumo_12m = _leer(datos, "consumo_12m", []) or []
    consumo_anual = sum(_num(x) for x in consumo_12m)
    produccion_anual = sum(_num(x) for x in energia.energia_util_12m)

    produccion_vs_consumo_pct = (
        produccion_anual / consumo_anual * 100.0
        if consumo_anual > 0
        else 0.0
    )

    return {
        "consumo_anual": consumo_anual,
        "produccion_anual": produccion_anual,
        "produccion_vs_consumo_pct": produccion_vs_consumo_pct,
    }


def _metricas_sistema(resultado: Any) -> dict:
    paneles = resultado.paneles
    strings = paneles.strings
    panel = paneles.panel
    sizing = resultado.sizing

    n_paneles = sum(int(s.n_series) for s in strings)
    potencia_panel_wp = _num(panel.pmax_w)
    kwp = n_paneles * potencia_panel_wp / 1000.0

    return {
        "kwp": kwp,
        "n_paneles": n_paneles,
        "potencia_panel_wp": potencia_panel_wp,
        "cantidad_inversores": int(_num(sizing.n_inversores)),
        "kw_ac_total": _num(sizing.kw_ac_total),
    }


def _metricas_financieras(resultado: Any) -> dict:
    financiero = resultado.financiero
    evaluacion = _leer(financiero, "evaluacion", {}) or {}
    tabla_12m = _leer(financiero, "tabla_12m", []) or []

    pago_actual = sum(
        _num(fila["factura_base_L"])
        for fila in tabla_12m
    ) / len(tabla_12m)

    pago_total_fv = sum(
        _num(fila["pago_enee_L"])
        + _num(fila["cuota_L"])
        + _num(fila["om_L"])
        for fila in tabla_12m
    ) / len(tabla_12m)

    ahorro_mensual = _num(_leer(evaluacion, "neto_prom", 0.0))
    ahorro_anual = _num(_leer(financiero, "ahorro_anual_L", 0.0))

    return {
        "capex": _num(_leer(financiero, "capex_L", 0.0)),
        "dscr": _leer(evaluacion, "dscr", None),
        "ahorro_mensual": ahorro_mensual,
        "ahorro_anual": ahorro_anual,
        "beneficio_bruto_anual": ahorro_anual,
        "beneficio_neto_anual": ahorro_mensual * 12.0,
        "pago_actual": pago_actual,
        "pago_total_fv": pago_total_fv,
        "cuota": _num(_leer(financiero, "cuota_mensual", 0.0)),
        "peor_mes": _num(_leer(evaluacion, "peor_mes", 0.0)),
    }


def _metricas_layout(resultado: Any) -> dict:
    layout = resultado.layout_preliminar

    if isinstance(layout, dict):
        layout = layout.get("layout", layout)

    return {
        "area_layout": _num(
            _leer(layout, "area_rectangular_m2", 0.0)
        )
    }


def extraer_metricas_conclusion(
    resultado: Any,
    datos: Any = None,
) -> dict:
    """
    Extrae métricas desde una única fuente oficial por indicador.

    No busca nombres alternativos ni calcula fallbacks silenciosos.
    Si cambia el contrato de un módulo, debe corregirse aquí.
    """

    if datos is None:
        raise ValueError("datos es obligatorio para generar conclusiones.")

    metricas = {}
    metricas.update(_metricas_energia(resultado, datos))
    metricas.update(_metricas_sistema(resultado))
    metricas.update(_metricas_financieras(resultado))
    metricas.update(_metricas_layout(resultado))

    return metricas


# ======================================================
# CLASIFICACIÓN EJECUTIVA
# ======================================================

def clasificar_viabilidad(m: dict) -> tuple[str, str]:
    ahorro = _num(m["ahorro_mensual"])
    peor_mes = _num(m["peor_mes"])
    capex = _num(m["capex"])

    if _es_pago_contado(m):
        ahorro_anual = ahorro * 12.0
        payback = capex / ahorro_anual if ahorro_anual > 0 else None

        if ahorro <= 0:
            return (
                "NO RECOMENDADO",
                "El proyecto no produce una reducción económica positiva "
                "bajo las condiciones evaluadas.",
            )

        if peor_mes < 0:
            return (
                "VIABLE CON OBSERVACIONES",
                "El proyecto produce una reducción económica promedio "
                "positiva, aunque presenta meses que requieren revisión.",
            )

        if payback is not None and payback <= 10:
            return (
                "VIABLE PRELIMINAR",
                "El proyecto produce ahorros operativos positivos y presenta "
                f"un período simple de recuperación aproximado de {payback:.1f} años.",
            )

        return (
            "VIABLE CON OBSERVACIONES",
            "El proyecto produce una reducción económica positiva, aunque "
            "el período de recuperación requiere revisión.",
        )

    dscr = _num(m["dscr"])

    if dscr >= 1.20 and ahorro > 0 and peor_mes >= 0:
        return (
            "VIABLE PRELIMINAR",
            "El proyecto presenta capacidad financiera adecuada y margen "
            "suficiente para atender la deuda.",
        )

    if dscr >= 1.00 and ahorro > 0:
        return (
            "VIABLE CON OBSERVACIONES",
            "El proyecto genera ahorro y cubre la deuda, pero su margen "
            "financiero debe revisarse.",
        )

    return (
        "NO RECOMENDADO",
        "Los ahorros generados no proporcionan cobertura suficiente "
        "para atender la deuda.",
    )


# ======================================================
# NARRATIVA
# ======================================================

def _texto_viabilidad(m: dict, estado: str, criterio: str) -> str:
    ahorro = _fmt_lps(m["ahorro_mensual"])

    if _es_pago_contado(m):
        return (
            f"El proyecto se clasifica como {estado}. {criterio} "
            f"El escenario corresponde a pago de contado, por lo que el "
            f"indicador DSCR no aplica. La reducción promedio mensual "
            f"estimada de la factura es de {ahorro}."
        )

    return (
        f"El proyecto se clasifica como {estado}. {criterio} "
        f"El indicador DSCR calculado es {_fmt_dscr(m)}, con una reducción "
        f"mensual estimada de {ahorro}."
    )


def _texto_resultado_energetico(m: dict) -> str:
    return (
        f"El sistema fotovoltaico propuesto tiene una potencia instalada "
        f"de {_fmt_kwp(m['kwp'])} y una producción fotovoltaica anual "
        f"estimada de {_fmt_kwh(m['produccion_anual'])}. Esta producción "
        f"equivale aproximadamente a "
        f"{_fmt_pct(m['produccion_vs_consumo_pct'])} del "
        f"consumo anual del cliente, cuyo consumo total es de "
        f"{_fmt_kwh(m['consumo_anual'])}."
    )


def _texto_impacto_financiero(m: dict) -> str:
    if _es_pago_contado(m):
        reduccion_anual = _num(m["beneficio_neto_anual"])
        payback = (
            _num(m["capex"]) / reduccion_anual
            if reduccion_anual > 0
            else None
        )

        texto_payback = (
            f" El período simple estimado de recuperación de la inversión "
            f"es de {payback:.1f} años."
            if payback is not None
            else ""
        )

        return (
            f"El pago energético mensual actual se estima en "
            f"{_fmt_lps(m['pago_actual'])}. El proyecto fue evaluado bajo "
            f"modalidad de pago de contado, sin cuota ni deuda financiera. "
            f"La reducción promedio mensual estimada es de "
            f"{_fmt_lps(m['ahorro_mensual'])}, equivalente a "
            f"{_fmt_lps(reduccion_anual)} durante el primer año."
            f"{texto_payback}"
        )

    return (
        f"El pago energético mensual actual se estima en "
        f"{_fmt_lps(m['pago_actual'])}. Con el sistema FV y el financiamiento "
        f"considerado, el pago total mensual proyectado es de "
        f"{_fmt_lps(m['pago_total_fv'])}, incluyendo una cuota de "
        f"{_fmt_lps(m['cuota'])}. Después del financiamiento, la reducción "
        f"económica anual estimada es de "
        f"{_fmt_lps(m['beneficio_neto_anual'])}."
    )


def _texto_dimensionamiento() -> str:
    return (
        "El tamaño seleccionado prioriza autoconsumo, estabilidad financiera "
        "y control del excedente energético. Un sistema de mayor potencia puede "
        "incrementar la generación, pero también el excedente y la dependencia "
        "de condiciones comerciales o regulatorias externas."
    )


def _texto_alcance_fisico(m: dict) -> str:
    return (
        f"La solución considera {m['n_paneles']} módulos fotovoltaicos de "
        f"{m['potencia_panel_wp']:.0f} Wp. El área rectangular preliminar "
        f"del arreglo es de {m['area_layout']:.2f} m². Este valor debe "
        f"validarse en campo considerando obstáculos, sombras, orientación, "
        f"accesos de mantenimiento y revisión estructural."
    )


def _texto_recomendacion_final(estado: str) -> str:
    if estado == "NO RECOMENDADO":
        return (
            "No se recomienda avanzar a ejecución bajo las condiciones "
            "económicas actuales. Deben revisarse CAPEX, tamaño del sistema, "
            "tarifa eléctrica y perfil horario real de demanda."
        )

    if estado == "VIABLE CON OBSERVACIONES":
        return (
            "Se puede avanzar a una revisión técnica y económica más detallada. "
            "Deben validarse el perfil horario, el área útil, la estructura, "
            "la interconexión y las condiciones financieras definitivas."
        )

    return (
        "Se recomienda avanzar con el diseño base evaluado, manteniendo como "
        "prioridad el autoconsumo y la reducción directa de la factura. Antes "
        "de ejecutar deben validarse el sitio, el perfil horario, el área útil, "
        "la estructura y las condiciones de interconexión."
    )


# ======================================================
# CONTENIDO ESTRUCTURADO
# ======================================================

def generar_conclusiones_ejecutivas(
    resultado: Any,
    datos: Any = None,
) -> dict:
    m = extraer_metricas_conclusion(resultado, datos)
    estado, criterio = clasificar_viabilidad(m)

    return {
        "estado": estado,
        "metricas": m,
        "conclusiones": [
            {
                "titulo": "1. Viabilidad general del proyecto",
                "texto": _texto_viabilidad(m, estado, criterio),
            },
            {
                "titulo": "2. Resultado energético esperado",
                "texto": _texto_resultado_energetico(m),
            },
            {
                "titulo": "3. Impacto financiero esperado",
                "texto": _texto_impacto_financiero(m),
            },
            {
                "titulo": "4. Criterio técnico de dimensionamiento",
                "texto": _texto_dimensionamiento(),
            },
            {
                "titulo": "5. Alcance físico preliminar",
                "texto": _texto_alcance_fisico(m),
            },
            {
                "titulo": "6. Recomendación final",
                "texto": _texto_recomendacion_final(estado),
            },
        ],
    }


# ======================================================
# RENDER REPORTLAB
# ======================================================

def agregar_pagina_conclusiones_ejecutivas(
    story,
    styles,
    resultado,
    datos=None,
    paths=None,
):
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

    paths = paths or {}
    area_layout = paths.get("layout_area_rectangular_m2")

    if area_layout is not None:
        m["area_layout"] = _num(area_layout)
        data["conclusiones"][4]["texto"] = _texto_alcance_fisico(m)

    story.append(PageBreak())
    story.append(
        Paragraph(
            "Conclusiones Ejecutivas y Recomendaciones",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 0.35 * cm))

    resumen = [
        ["Indicador", "Resultado"],
        ["Estado del proyecto", data["estado"]],
        ["Potencia FV propuesta", _fmt_kwp(m["kwp"])],
        ["Producción fotovoltaica anual", _fmt_kwh(m["produccion_anual"])],
        ["Producción FV respecto al consumo",
        _fmt_pct(m["produccion_vs_consumo_pct"]),],
        ["Reducción mensual estimada", _fmt_lps(m["ahorro_mensual"])],
        ["DSCR", _fmt_dscr(m)],
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

    nota = (
        "Nota: Las conclusiones corresponden a una evaluación preliminar "
        "basada en los datos ingresados y resultados calculados por FV Engine. "
        "Para etapa constructiva se requiere validación final de sitio, "
        "ingeniería de detalle, interconexión, protecciones, canalización y "
        "revisión estructural."
    )

    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(nota, styles["Italic"]))

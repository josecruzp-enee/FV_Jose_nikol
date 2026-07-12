# -*- coding: utf-8 -*-
# reportes/analisis_financiero.py

from __future__ import annotations

from typing import Any, Dict, List

from reportlab.platypus import (
    Paragraph,
    Spacer,
    PageBreak,
    TableStyle,
)

from reportes.helpers_pdf import (
    make_table,
    table_style_uniform,
    box_paragraph,
    get_field,
    money_L,
)


# =========================================================
# CAPÍTULO 3
# ANÁLISIS FINANCIERO
# =========================================================
# Responsabilidad:
# - Presentar la modalidad económica evaluada.
# - Mostrar CAPEX y condiciones de pago.
# - Mostrar la evolución del préstamo cuando corresponda.
# - Mostrar amortización anual.
# - Mostrar prima, monto financiado, tasa, plazo y cuota.
#
# Reglas de mantenimiento:
# - No cambiar la firma de build_analisis_financiero().
# - No cambiar nombres públicos.
# - No calcular VAN ni TIR en esta capa.
# - Mantener amortizacion_anual() por compatibilidad.
# =========================================================


# =========================================================
# 1. UTILIDADES
# =========================================================

def leer(obj, campo, default=None):

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


def _leer_sistema_fv(datos: Any) -> Dict[str, Any]:

    sistema_fv = get_field(
        datos,
        "sistema_fv",
        {},
    ) or {}

    if isinstance(sistema_fv, dict):
        return sistema_fv

    return {}


def _leer_financiero(resultado: Any) -> Dict[str, Any]:

    financiero = leer(
        resultado,
        "financiero",
        {},
    ) or {}

    if isinstance(financiero, dict):
        return financiero

    return {}


# =========================================================
# 2. AMORTIZACIÓN ANUAL
# =========================================================

def amortizacion_anual(
    principal: float,
    tasa_anual: float,
    cuota_mensual: float,
    plazo_anios: int | None = None,
    plazo_meses: int | None = None,
) -> List[Dict[str, float]]:

    principal = float(principal)
    tasa_anual = float(tasa_anual)
    cuota_mensual = float(cuota_mensual)

    if principal <= 0:
        return []

    if plazo_meses is None:

        plazo_anios = int(plazo_anios or 0)

        if plazo_anios <= 0:
            raise ValueError("Plazo inválido.")

        plazo_meses = plazo_anios * 12

    else:

        plazo_meses = int(plazo_meses)

        if plazo_meses <= 0:
            raise ValueError("Plazo inválido.")

        plazo_anios = (plazo_meses + 11) // 12

    tasa_mensual = tasa_anual / 12.0
    saldo = principal

    resultado: List[Dict[str, float]] = []
    meses_transcurridos = 0

    for anio in range(1, plazo_anios + 1):

        interes_anual = 0.0
        principal_anual = 0.0
        pago_anual = 0.0

        for _ in range(12):

            if (
                saldo <= 0
                or meses_transcurridos >= plazo_meses
            ):
                break

            interes_mes = saldo * tasa_mensual
            principal_mes = cuota_mensual - interes_mes

            if principal_mes <= 0:
                principal_mes = 0.0

            if principal_mes > saldo:
                principal_mes = saldo

            saldo -= principal_mes

            interes_anual += interes_mes
            principal_anual += principal_mes
            pago_anual += interes_mes + principal_mes

            meses_transcurridos += 1

        resultado.append({
            "anio": anio,
            "meses_acumulados": meses_transcurridos,
            "pago_anual": float(pago_anual),
            "interes_anual": float(interes_anual),
            "principal_anual": float(principal_anual),
            "saldo_fin": float(max(0.0, saldo)),
        })

        if saldo <= 0:
            break

    return resultado


# =========================================================
# 3. PARÁMETROS FINANCIEROS
# =========================================================

def _leer_parametros_financieros(
    resultado: Any,
    datos: Any,
) -> Dict[str, Any]:

    financiero = _leer_financiero(resultado)
    sistema_fv = _leer_sistema_fv(datos)

    capex = float(
        leer(
            financiero,
            "capex_L",
            0.0,
        )
        or 0.0
    )

    porcentaje_financiado_ui = float(
        sistema_fv.get(
            "porcentaje_financiado",
            get_field(
                datos,
                "porcentaje_financiado",
                1.0,
            ),
        )
        or 0.0
    )

    usa_financiamiento_ui = bool(
        sistema_fv.get(
            "usa_financiamiento",
            porcentaje_financiado_ui > 0,
        )
    )

    if usa_financiamiento_ui:

        porcentaje_financiado = float(
            leer(
                financiero,
                "porcentaje_financiado",
                porcentaje_financiado_ui,
            )
            or 0.0
        )

    else:

        porcentaje_financiado = 0.0

    porcentaje_financiado = max(
        0.0,
        min(1.0, porcentaje_financiado),
    )

    prima_pct = float(
        leer(
            financiero,
            "prima_pct",
            max(
                0.0,
                1.0 - porcentaje_financiado,
            ),
        )
        or 0.0
    )

    monto_financiado = float(
        leer(
            financiero,
            "monto_financiado_L",
            capex * porcentaje_financiado,
        )
        or 0.0
    )

    cuota_mensual = float(
        leer(
            financiero,
            "cuota_mensual_L",
            leer(
                financiero,
                "cuota_mensual",
                0.0,
            ),
        )
        or 0.0
    )

    tasa_anual = float(
        leer(
            financiero,
            "tasa_anual",
            sistema_fv.get(
                "tasa_anual",
                get_field(
                    datos,
                    "tasa_anual",
                    0.0,
                ),
            ),
        )
        or 0.0
    )

    plazo_anios = int(
        leer(
            financiero,
            "plazo_anios",
            sistema_fv.get(
                "plazo_anios",
                get_field(
                    datos,
                    "plazo_anios",
                    0,
                ),
            ),
        )
        or 0
    )

    plazo_meses = int(
        leer(
            financiero,
            "plazo_meses",
            plazo_anios * 12,
        )
        or 0
    )

    usa_financiamiento = bool(
        usa_financiamiento_ui
        and porcentaje_financiado > 0
        and monto_financiado > 0
    )

    if not usa_financiamiento:

        porcentaje_financiado = 0.0
        prima_pct = 1.0
        monto_financiado = 0.0
        cuota_mensual = 0.0
        tasa_anual = 0.0
        plazo_anios = 0
        plazo_meses = 0

    prima_L = float(
        leer(
            financiero,
            "prima_L",
            capex * prima_pct,
        )
        or 0.0
    )

    return {
        "financiero": financiero,
        "usa_financiamiento": usa_financiamiento,
        "capex": capex,
        "cuota": cuota_mensual,
        "pct_fin": porcentaje_financiado,
        "prima_pct": prima_pct,
        "prima_L": prima_L,
        "principal": monto_financiado,
        "tasa_anual": tasa_anual,
        "cat": leer(financiero, "cat", None),
        "plazo_anios": plazo_anios,
        "plazo_meses": plazo_meses,
        "nombre_financiamiento": str(
            leer(
                financiero,
                "nombre_financiamiento",
                (
                    "Financiamiento seleccionado"
                    if usa_financiamiento
                    else "Pago de contado"
                ),
            )
            or ""
        ),
        "entidad_financiera": str(
            leer(
                financiero,
                "entidad_financiera",
                "",
            )
            or ""
        ),
        "nota_financiamiento": str(
            leer(
                financiero,
                "nota_financiamiento",
                "",
            )
            or ""
        ),
    }


# =========================================================
# 4. PAGO DE CONTADO
# =========================================================

def _build_bloque_contado(
    params: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):

    story: List[Any] = []

    story.append(
        Paragraph(
            "Evaluación económica — Pago de contado",
            styles["Title"],
        )
    )

    story.append(Spacer(1, 10))

    texto = (
        "<b>Lectura ejecutiva</b><br/>"
        "• Modalidad evaluada: <b>Pago de contado</b><br/>"
        f"• Inversión total estimada: "
        f"<b>{money_L(params['capex'])}</b><br/>"
        "• Prima inicial: "
        f"<b>{money_L(params['capex'])}</b><br/>"
        "• Monto financiado: <b>L 0.00</b><br/>"
        "• Cuota mensual de financiamiento: "
        "<b>L 0.00</b><br/>"
        "• El proyecto no contempla deuda bancaria, por lo que "
        "no aplican tasa, plazo, amortización ni DSCR asociado "
        "al servicio de deuda."
    )

    if params["nota_financiamiento"]:

        texto += (
            "<br/><br/>"
            f"<i>{params['nota_financiamiento']}</i>"
        )

    story.append(
        box_paragraph(
            texto,
            pal,
            content_w,
            font_size=10,
        )
    )

    story.append(PageBreak())

    return story


# =========================================================
# 5. TABLA DE AMORTIZACIÓN
# =========================================================

def _tabla_amortizacion_pdf(
    anual: List[Dict[str, Any]],
    cuota: float,
    pal: dict,
    content_w: float,
):

    header = [
        "Año",
        "Cuota (L/mes)",
        "Pago anual (L)",
        "Interés (L)",
        "Principal (L)",
        "Saldo fin (L)",
    ]

    rows: List[List[str]] = []

    for fila in anual:

        rows.append([
            str(int(fila.get("anio", 0))),
            f"{cuota:,.2f}",
            f"{float(fila.get('pago_anual', 0.0) or 0.0):,.0f}",
            f"{float(fila.get('interes_anual', 0.0) or 0.0):,.0f}",
            f"{float(fila.get('principal_anual', 0.0) or 0.0):,.0f}",
            f"{float(fila.get('saldo_fin', 0.0) or 0.0):,.0f}",
        ])

    if not rows:
        rows = [["—", "—", "—", "—", "—", "—"]]

    tabla = make_table(
        [header] + rows,
        content_w,
        ratios=[
            0.8,
            1.4,
            1.5,
            1.3,
            1.3,
            1.4,
        ],
        repeatRows=1,
    )

    tabla.setStyle(
        table_style_uniform(
            pal,
            font_header=9,
            font_body=9,
        )
    )

    tabla.setStyle(
        TableStyle([
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    return tabla


# =========================================================
# 6. LECTURA DEL FINANCIAMIENTO
# =========================================================

def _nota_financiamiento(
    params: Dict[str, Any],
    anual: List[Dict[str, Any]],
) -> str:

    saldo_final = params["principal"]

    if anual:
        saldo_final = float(
            anual[-1].get(
                "saldo_fin",
                params["principal"],
            )
            or 0.0
        )

    entidad_txt = ""

    if params["entidad_financiera"]:

        entidad_txt = (
            "• Entidad financiera: "
            f"<b>{params['entidad_financiera']}</b><br/>"
        )

    cat_txt = ""

    if params["cat"] is not None:

        cat_txt = (
            "• CAT referencial: "
            f"<b>{float(params['cat']) * 100:.2f}%</b><br/>"
        )

    nota_extra = ""

    if params["nota_financiamiento"]:

        nota_extra = (
            "<br/>"
            f"<i>{params['nota_financiamiento']}</i>"
        )

    return (
        "<b>Lectura ejecutiva</b><br/>"
        "• Producto financiero: "
        f"<b>{params['nombre_financiamiento']}</b><br/>"
        f"{entidad_txt}"
        "• CAPEX total: "
        f"<b>{money_L(params['capex'])}</b><br/>"
        "• Prima estimada: "
        f"<b>{money_L(params['prima_L'])}</b> "
        f"({params['prima_pct'] * 100:.2f}%).<br/>"
        "• Monto financiado: "
        f"<b>{money_L(params['principal'])}</b> "
        f"({params['pct_fin'] * 100:.2f}% del CAPEX).<br/>"
        "• Plazo: "
        f"<b>{params['plazo_meses']}</b> meses / "
        f"<b>{params['plazo_anios']}</b> años.<br/>"
        "• Tasa anual referencial: "
        f"<b>{params['tasa_anual'] * 100:.2f}%</b><br/>"
        f"{cat_txt}"
        "• Cuota fija estimada: "
        f"<b>{money_L(params['cuota'])}/mes</b><br/>"
        "• Saldo al cierre del plazo: "
        f"<b>{money_L(saldo_final)}</b>."
        f"{nota_extra}"
    )


# =========================================================
# 7. FINANCIAMIENTO
# =========================================================

def _build_bloque_financiado(
    params: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):

    story: List[Any] = []

    story.append(
        Paragraph(
            "Evaluación financiera — Evolución del préstamo",
            styles["Title"],
        )
    )

    story.append(Spacer(1, 10))

    anual = leer(
        params["financiero"],
        "tabla_amortizacion",
        [],
    ) or []

    if not anual:

        anual = amortizacion_anual(
            principal=params["principal"],
            tasa_anual=params["tasa_anual"],
            cuota_mensual=params["cuota"],
            plazo_anios=params["plazo_anios"],
            plazo_meses=params["plazo_meses"],
        )

    story.append(
        _tabla_amortizacion_pdf(
            anual,
            params["cuota"],
            pal,
            content_w,
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        box_paragraph(
            _nota_financiamiento(
                params,
                anual,
            ),
            pal,
            content_w,
            font_size=10,
        )
    )

    story.append(PageBreak())

    return story


# =========================================================
# 8. ORQUESTADOR
# =========================================================

def build_analisis_financiero(
    resultado: Dict[str, Any],
    datos: Any,
    paths: Dict[str, Any],
    pal: dict,
    styles,
    content_w: float,
):

    params = _leer_parametros_financieros(
        resultado,
        datos,
    )

    if params["usa_financiamiento"]:

        return _build_bloque_financiado(
            params,
            pal,
            styles,
            content_w,
        )

    return _build_bloque_contado(
        params,
        pal,
        styles,
        content_w,
    )

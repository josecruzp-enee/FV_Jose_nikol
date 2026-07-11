# reportes/resumen_ejecutivo.py

from __future__ import annotations

from datetime import datetime

from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.platypus import TableStyle

from reportes.pdf_utils import (
    section_bar,
    tabla_4cols,
    tabla_2cols,
    make_table,
    table_style_uniform,
    box_paragraph,
    get_field,
)

from reportes.pdf_utils import money_L, num


# =========================================================
# CAPÍTULO 1
# RESUMEN EJECUTIVO
# =========================================================
# Responsabilidad:
# - Presentar la información principal del estudio FV.
# - Mostrar datos del cliente.
# - Mostrar solución propuesta.
# - Mostrar impacto económico mensual.
# - Mostrar conclusión ejecutiva.
#
# Reglas de mantenimiento:
# - No cambiar nombres de funciones p1_* sin revisar llamadas.
# - No cambiar la firma de build_resumen_ejecutivo().
# - No mover cálculos todavía.
# - No cambiar variables de entrada/salida.
# =========================================================


# =========================================================
# 1. UTILIDADES INTERNAS DEL CAPÍTULO
# =========================================================

def leer(obj, campo, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(campo, default)
    return getattr(obj, campo, default)


def _financiero_para_pdf(financiero):
    """
    Usa la batería óptima en el resumen ejecutivo si existe
    y si no es el escenario 'Sin batería'.

    Si no hay batería óptima válida, conserva el financiero base.
    """

    bateria_optima = leer(financiero, "bateria_optima", None)

    if isinstance(bateria_optima, dict):
        nombre = str(bateria_optima.get("nombre", "")).strip().lower()
        tabla_bat = bateria_optima.get("tabla_12m", [])

        if nombre and nombre != "sin batería" and tabla_bat:
            return bateria_optima

    return financiero


# =========================================================
# 2. SECCIÓN: DATOS DEL CLIENTE Y SITUACIÓN ENERGÉTICA
# =========================================================

def p1_tabla_cliente(datos, sizing, fecha, pal, content_w):

    consumo_12m = get_field(datos, "consumo_12m", [])
    consumo_anual = sum(consumo_12m) if isinstance(consumo_12m, list) else 0.0

    tarifa = float(get_field(datos, "tarifa_energia", 0.0))
    cargos = float(get_field(datos, "cargos_fijos", 0.0))

    rows = [
        ["Cliente", get_field(datos, "cliente", ""), "Ubicación", get_field(datos, "ubicacion", "")],
        ["Fecha", fecha, "Consumo anual", f"{consumo_anual:,.0f} kWh/año"],
        ["Tarifa energía", f"{tarifa:.3f} L/kWh", "Cargos fijos", f"{money_L(cargos)}/mes"],
    ]

    t = tabla_4cols(
        header=["Dato", "Valor", "Dato", "Valor"],
        rows=rows,
        content_w=content_w,
        pal=pal,
        font_header=9,
        font_body=9,
    )

    return [
        section_bar("Datos del cliente y situación energética", pal, content_w),
        Spacer(1, 6),
        t,
        Spacer(1, 12),
    ]


# =========================================================
# 3. SECCIÓN: SOLUCIÓN PROPUESTA E INDICADORES CLAVE
# =========================================================

def p1_tabla_solucion_unica(
    datos,
    sizing,
    energia,
    financiero,
    pal,
    content_w,
    paneles=None,
):

    financiero_pdf = _financiero_para_pdf(financiero)

    capex = float(
        leer(
            financiero_pdf,
            "capex_total_L",
            leer(financiero_pdf, "capex_L", 0.0),
        )
    )

    # =====================================================
    # SISTEMA FV REAL CONECTADO
    # Prioridad: strings reales > sizing preliminar
    # =====================================================

    strings = leer(paneles, "strings", []) if paneles else []
    panel_obj = leer(paneles, "panel", None) if paneles else None

    panel_wp = (
        float(leer(panel_obj, "pmax_w", 0.0))
        if panel_obj
        else 0.0
    )

    n_paneles = sum(
        int(leer(s, "n_series", 0) or 0)
        for s in strings
    )

    if n_paneles > 0 and panel_wp > 0:
        kwp = n_paneles * panel_wp / 1000.0
    else:
        kwp = float(
            leer(
                sizing,
                "kwp_dc",
                leer(sizing, "pdc_kw", 0.0),
            )
        )

        n_paneles = int(leer(sizing, "n_paneles", 0))

        panel_wp = (
            int((kwp * 1000) / n_paneles)
            if n_paneles > 0
            else 0
        )

    # =====================================================
    # ENERGÍA REAL USADA EN EL PDF
    # =====================================================

    tabla_pdf = leer(financiero_pdf, "tabla_12m", [])

    consumo_12m = get_field(datos, "consumo_12m", [])

    consumo_anual = (
        sum(consumo_12m)
        if isinstance(consumo_12m, list)
        else 0.0
    )

    if tabla_pdf:
        prod_anual = sum(
            float(x.get("fv_kwh", 0.0))
            for x in tabla_pdf
            if isinstance(x, dict)
        )
    else:
        energia_12m = leer(
            energia,
            "energia_util_12m",
            [],
        )

        prod_anual = (
            sum(energia_12m)
            if isinstance(energia_12m, list)
            else 0.0
        )

    cobertura_real = (
        prod_anual / consumo_anual
        if consumo_anual > 0
        else 0.0
    )

    evaluacion = leer(
        financiero_pdf,
        "evaluacion",
        {},
    ) or {}

    estado_original = str(
        evaluacion.get("estado", "")
    ).upper().strip()

    if estado_original == "VIABLE":
        estado_txt = "VIABLE A NIVEL PRELIMINAR"
    else:
        estado_txt = estado_original or "EN EVALUACIÓN"

    ds_val = evaluacion.get("dscr", None)

    ds_txt = (
        "No aplica"
        if ds_val is None
        else f"{ds_val:.2f}"
    )

    bateria_nombre = str(
        leer(financiero_pdf, "nombre", "") or ""
    )

    capacidad_bateria = float(
        leer(
            financiero_pdf,
            "capacidad_bateria_kwh",
            0.0,
        ) or 0.0
    )

    sistema_txt = f"{num(kwp, 2)} kWp"

    if capacidad_bateria > 0:
        sistema_txt += (
            f" + batería {capacidad_bateria:.0f} kWh"
        )

    data = [
        ["Dato", "Valor", "Dato", "Valor"],

        [
            "Cobertura solicitada",
            (
                f"{get_field(datos, 'cobertura_objetivo', 0) * 100:.0f}%"
            ),
            "Cobertura recomendada",
            f"{cobertura_real * 100:.1f}%",
        ],

        [
            "Sistema",
            sistema_txt,
            "CAPEX estimado",
            money_L(capex),
        ],

        [
            "Producción útil anual",
            f"{prod_anual:,.0f} kWh/año",
            "DSCR",
            ds_txt,
        ],

        [
            "Módulos FV",
            f"{int(n_paneles)} × {int(panel_wp)} Wp",
            "Estado",
            estado_txt,
        ],
    ]

    if capacidad_bateria > 0:
        data.append(
            [
                "Batería evaluada",
                bateria_nombre,
                "Capacidad",
                f"{capacidad_bateria:.1f} kWh",
            ]
        )

    t = make_table(
        data,
        content_w,
        ratios=[1.25, 2.15, 1.25, 2.15],
        repeatRows=1,
    )

    t.setStyle(
        table_style_uniform(
            pal,
            font_header=9,
            font_body=9,
        )
    )

    return [
        section_bar(
            "Solución propuesta e indicadores clave",
            pal,
            content_w,
        ),
        Spacer(1, 6),
        t,
        Spacer(1, 12),
    ]

# =========================================================
# 4. SECCIÓN: DECISIÓN DEL CLIENTE / IMPACTO MENSUAL
# =========================================================

def p1_tabla_decision(financiero, pal, content_w):

    financiero_pdf = _financiero_para_pdf(financiero)

    tabla = leer(financiero_pdf, "tabla_12m", [])

    if tabla:
        pago_actual = sum(
            float(x.get("factura_base_L", 0.0))
            for x in tabla
            if isinstance(x, dict)
        ) / 12.0

        pago_residual = sum(
            float(x.get("pago_enee_L", 0.0))
            for x in tabla
            if isinstance(x, dict)
        ) / 12.0
    else:
        pago_actual = 0.0
        pago_residual = 0.0

    cuota = float(
        leer(
            financiero_pdf,
            "cuota_mensual_L",
            leer(financiero_pdf, "cuota_mensual", 0.0),
        )
    )

    pago_total = pago_residual + cuota
    ahorro = pago_actual - pago_total

    capacidad_bateria = float(
        leer(
            financiero_pdf,
            "capacidad_bateria_kwh",
            0.0,
        ) or 0.0
    )

    rows = [
        [
            "Pago actual ENEE (sin FV)",
            money_L(pago_actual),
        ],
        [
            "Pago ENEE después del proyecto",
            money_L(pago_residual),
        ],
        [
            "Cuota de financiamiento",
            money_L(cuota),
        ],
    ]

    if capacidad_bateria > 0:
        rows.append(
            [
                "Batería incluida",
                f"{capacidad_bateria:.1f} kWh",
            ]
        )

    rows += [
        [
            "Pago total mensual estimado",
            money_L(pago_total),
        ],
        [
            "Reducción mensual estimada",
            money_L(ahorro),
        ],
    ]

    t = tabla_2cols(
        header=["Concepto", "Monto (L/mes)"],
        rows=rows,
        content_w=content_w,
        pal=pal,
        highlight_row=len(rows) - 1,
    )

    return [
        section_bar(
            "Impacto mensual para el cliente",
            pal,
            content_w,
        ),
        Spacer(1, 6),
        t,
        Spacer(1, 12),
    ]
# =========================================================
# 5. SECCIÓN: CONCLUSIÓN EJECUTIVA
# =========================================================

def p1_conclusion(financiero, sizing, datos, pal, content_w, paneles=None):

    financiero_pdf = _financiero_para_pdf(financiero)

    evaluacion = leer(financiero_pdf, "evaluacion", {}) or {}

    ds_val = evaluacion.get("dscr", None)
    ds_txt = "—" if ds_val is None else f"{ds_val:.2f}"

    peor = float(evaluacion.get("peor_mes", 0.0))

    strings = leer(paneles, "strings", []) if paneles else []
    panel_obj = leer(paneles, "panel", None) if paneles else None

    panel_wp = float(leer(panel_obj, "pmax_w", 0.0)) if panel_obj else 0.0

    n_paneles = sum(
        int(leer(s, "n_series", 0) or 0)
        for s in strings
    )

    if n_paneles > 0 and panel_wp > 0:
        kwp = n_paneles * panel_wp / 1000.0
    else:
        kwp = float(leer(sizing, "kwp_dc", 0.0))

    # =====================================================
    # IMPACTO FINANCIERO REAL
    # Si hay batería óptima, usa tabla_12m de esa batería.
    # =====================================================

    tabla = leer(financiero_pdf, "tabla_12m", [])

    if tabla:
        pago_actual = sum(
            float(x.get("factura_base_L", 0.0))
            for x in tabla
            if isinstance(x, dict)
        ) / 12.0

        pago_residual = sum(
            float(x.get("pago_enee_L", 0.0))
            for x in tabla
            if isinstance(x, dict)
        ) / 12.0
    else:
        pago_actual = 0.0
        pago_residual = 0.0

    cuota = float(
        leer(
            financiero_pdf,
            "cuota_mensual_L",
            leer(financiero_pdf, "cuota_mensual", 0.0),
        )
    )

    pago_total = pago_residual + cuota
    impacto = pago_actual - pago_total

    # =====================================================
    # COBERTURA REAL
    # =====================================================

    consumo_12m = get_field(datos, "consumo_12m", [])
    consumo_anual = sum(consumo_12m) if isinstance(consumo_12m, list) else 0.0

    energia_real = sum(
        float(x.get("fv_kwh", 0.0))
        for x in tabla
        if isinstance(x, dict)
    ) if tabla else 0.0

    cobertura_real = energia_real / consumo_anual if consumo_anual > 0 else 0.0

    cobertura_obj = float(get_field(datos, "cobertura_objetivo", 0.0))

    capacidad_bateria = float(leer(financiero_pdf, "capacidad_bateria_kwh", 0.0) or 0.0)

    linea_bateria = ""

    if capacidad_bateria > 0:
        linea_bateria = f"• Batería evaluada: <b>{capacidad_bateria:.1f} kWh</b><br/>"

    concl = f"""
    <b>Conclusión ejecutiva</b><br/><br/>
    • Impacto financiero: <b>{money_L(impacto)}/mes</b><br/>
    • DSCR: <b>{ds_txt}</b><br/>
    • Peor mes: <b>{money_L(peor)}</b><br/>
    • Sistema: {kwp:.2f} kWp<br/>
    {linea_bateria}
    • Cobertura objetivo: {cobertura_obj * 100:.0f}%<br/>
    • Cobertura real: <b>{cobertura_real * 100:.1f}%</b><br/>
    """

    return [box_paragraph(concl, pal, content_w)]


# =========================================================
# 6. ORQUESTADOR DEL CAPÍTULO
# =========================================================
# Esta función es llamada desde BLOQUES_REPORTE.
# No cambiar su firma sin revisar generar_pdf_profesional.py.
# =========================================================

def build_resumen_ejecutivo(resultado, datos, paths, pal, styles, content_w):

    sizing = leer(resultado, "sizing", {})
    energia = leer(resultado, "energia", {})
    financiero = leer(resultado, "financiero", {})
    paneles = leer(resultado, "paneles", None)

    fecha = datetime.now().strftime("%Y-%m-%d")

    story = []

    story.append(Paragraph("Reporte Ejecutivo — Evaluación Fotovoltaica", styles["Title"]))
    story.append(Spacer(1, 10))

    # -----------------------------------------------------
    # Orden visual del capítulo
    # -----------------------------------------------------
    story += p1_tabla_cliente(datos, sizing, fecha, pal, content_w)
    story += p1_tabla_solucion_unica(datos, sizing, energia, financiero, pal, content_w, paneles=paneles)
    story += p1_tabla_decision(financiero, pal, content_w)
    story += p1_conclusion(financiero, sizing, datos, pal, content_w, paneles=paneles)

    story.append(PageBreak())

    return story

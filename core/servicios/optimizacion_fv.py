from __future__ import annotations

from math import ceil
from typing import Dict, List


def construir_demanda_8760_desde_24h(
    demanda_24h: Dict[int, float],
    n_horas: int,
) -> List[float]:

    return [
        float(demanda_24h.get(i % 24, 0.0) or 0.0)
        for i in range(n_horas)
    ]


def construir_perfil_unitario_fv_8760(
    energia_horaria_kwh: List[float],
    pdc_kw_base: float,
) -> List[float]:

    if pdc_kw_base <= 0:
        raise ValueError("pdc_kw_base inválido")

    return [
        float(e or 0.0) / pdc_kw_base
        for e in energia_horaria_kwh
    ]


def calcular_factor_recuperacion_capital(
    *,
    tasa_descuento_anual: float,
    vida_util_anios: int,
) -> float:

    if vida_util_anios <= 0:
        raise ValueError("vida_util_anios inválida")

    i = float(tasa_descuento_anual)

    if i <= 0:
        return 1.0 / vida_util_anios

    return (
        i * (1.0 + i) ** vida_util_anios
    ) / (
        (1.0 + i) ** vida_util_anios - 1.0
    )


def evaluar_balance_8760(
    *,
    demanda_8760_kwh: List[float],
    fv_unitario_8760_kwh_kwp: List[float],
    kwp: float,
    tarifa_compra_l_kwh: float,
    precio_inyeccion_l_kwh: float,
) -> dict:

    autoconsumo = 0.0
    excedente = 0.0
    compra_red = 0.0
    generacion = 0.0

    for d, fv_unit in zip(
        demanda_8760_kwh,
        fv_unitario_8760_kwh_kwp,
    ):

        d = float(d or 0.0)
        f = float(fv_unit or 0.0) * kwp

        generacion += f
        autoconsumo += min(d, f)
        excedente += max(f - d, 0.0)
        compra_red += max(d - f, 0.0)

    valor_autoconsumo = (
        autoconsumo *
        tarifa_compra_l_kwh
    )

    valor_inyeccion = (
        excedente *
        precio_inyeccion_l_kwh
    )

    demanda_total = sum(
        float(d or 0.0)
        for d in demanda_8760_kwh
    )

    beneficio_bruto = (
        valor_autoconsumo +
        valor_inyeccion
    )

    return {
        "kwp": kwp,

        "demanda_kwh_anual": demanda_total,
        "generacion_kwh_anual": generacion,

        "autoconsumo_kwh_anual": autoconsumo,
        "excedente_kwh_anual": excedente,
        "compra_red_kwh_anual": compra_red,

        "valor_autoconsumo_l_anual": valor_autoconsumo,
        "valor_inyeccion_l_anual": valor_inyeccion,

        "beneficio_bruto_l_anual": beneficio_bruto,

        # Alias para compatibilidad con código existente
        "beneficio_l_anual": beneficio_bruto,

        "cobertura_directa_pct": (
            autoconsumo / demanda_total * 100.0
            if demanda_total > 0
            else 0.0
        ),

        "cobertura_generacion_pct": (
            generacion / demanda_total * 100.0
            if demanda_total > 0
            else 0.0
        ),

        "excedente_pct_generacion": (
            excedente / generacion * 100.0
            if generacion > 0
            else 0.0
        ),
    }


def evaluar_economia_sistema(
    *,
    resultado_balance: dict,
    pdc_kw_real: float,
    costo_l_kwp: float,
    tasa_descuento_anual: float,
    vida_util_anios: int,
) -> dict:

    if pdc_kw_real <= 0:
        raise ValueError("pdc_kw_real inválido")

    if costo_l_kwp < 0:
        raise ValueError("costo_l_kwp inválido")

    crf = calcular_factor_recuperacion_capital(
        tasa_descuento_anual=tasa_descuento_anual,
        vida_util_anios=vida_util_anios,
    )

    capex_estimado_l = (
        pdc_kw_real *
        costo_l_kwp
    )

    costo_anualizado_l = (
        capex_estimado_l *
        crf
    )

    beneficio_bruto = float(
        resultado_balance.get(
            "beneficio_bruto_l_anual",
            resultado_balance.get("beneficio_l_anual", 0.0),
        )
        or 0.0
    )

    beneficio_neto = (
        beneficio_bruto -
        costo_anualizado_l
    )

    resultado = dict(resultado_balance)

    resultado.update({
        "capex_estimado_l": capex_estimado_l,
        "costo_l_kwp": costo_l_kwp,
        "factor_recuperacion_capital": crf,
        "costo_anualizado_l": costo_anualizado_l,
        "beneficio_neto_l_anual": beneficio_neto,
    })

    return resultado

def calcular_factor_recuperacion_capital(
    *,
    tasa_descuento_anual: float,
    vida_util_anios: int,
) -> float:

    if vida_util_anios <= 0:
        raise ValueError("vida_util_anios inválida")

    i = float(tasa_descuento_anual)

    if i <= 0:
        return 1.0 / vida_util_anios

    return (
        i * (1.0 + i) ** vida_util_anios
    ) / (
        (1.0 + i) ** vida_util_anios - 1.0
    )

def optimizar_kwp_maximo_ahorro(
    *,
    demanda_24h: Dict[int, float],
    energia_horaria_base_kwh: List[float],
    pdc_kw_base: float,
    panel_w: float,
    tarifa_compra_l_kwh: float,
    precio_inyeccion_l_kwh: float = 2.20,

    costo_l_kwp: float = 26000.0,
    tasa_descuento_anual: float = 0.10,
    vida_util_anios: int = 20,

    kwp_min: float = 1.0,
    kwp_max: float = 500.0,
    paso_kwp: float = 1.0,
) -> dict:

    demanda_8760 = construir_demanda_8760_desde_24h(
        demanda_24h=demanda_24h,
        n_horas=len(energia_horaria_base_kwh),
    )

    fv_unitario = construir_perfil_unitario_fv_8760(
        energia_horaria_kwh=energia_horaria_base_kwh,
        pdc_kw_base=pdc_kw_base,
    )

    crf = calcular_factor_recuperacion_capital(
        tasa_descuento_anual=tasa_descuento_anual,
        vida_util_anios=vida_util_anios,
    )

    mejor = None
    tabla_evaluacion = []

    kwp = float(kwp_min)

    while kwp <= kwp_max:

        n_paneles = int(ceil((kwp * 1000.0) / panel_w))
        pdc_kw_real = n_paneles * panel_w / 1000.0

        r = evaluar_balance_8760(
            demanda_8760_kwh=demanda_8760,
            fv_unitario_8760_kwh_kwp=fv_unitario,
            kwp=pdc_kw_real,
            tarifa_compra_l_kwh=tarifa_compra_l_kwh,
            precio_inyeccion_l_kwh=precio_inyeccion_l_kwh,
        )

        capex_estimado_l = pdc_kw_real * costo_l_kwp
        costo_anualizado_l = capex_estimado_l * crf

        beneficio_bruto_l_anual = float(
            r.get("beneficio_l_anual", 0.0) or 0.0
        )

        beneficio_neto_l_anual = (
            beneficio_bruto_l_anual -
            costo_anualizado_l
        )

        r["n_paneles"] = n_paneles
        r["pdc_kw"] = pdc_kw_real
        r["kwp"] = pdc_kw_real

        r["costo_l_kwp"] = costo_l_kwp
        r["capex_estimado_l"] = capex_estimado_l
        r["factor_recuperacion_capital"] = crf
        r["costo_anualizado_l"] = costo_anualizado_l

        r["beneficio_bruto_l_anual"] = beneficio_bruto_l_anual
        r["beneficio_neto_l_anual"] = beneficio_neto_l_anual

        tabla_evaluacion.append(dict(r))

        if (
            mejor is None
            or beneficio_neto_l_anual > mejor["beneficio_neto_l_anual"]
        ):
            mejor = dict(r)

        kwp += paso_kwp

    if mejor is None:
        raise ValueError("No se pudo optimizar el sistema FV")

    mejor["criterio_optimizacion"] = "Máximo beneficio neto anual"
    mejor["tabla_evaluacion"] = tabla_evaluacion

    return mejor

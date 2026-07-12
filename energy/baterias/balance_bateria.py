# -*- coding: utf-8 -*-
from __future__ import annotations

from math import sqrt
from typing import List

from energy.baterias.modelos import ConfigBateria
from energy.baterias.resultado_bateria import ResultadoBateria


DIAS_MES_NORMAL = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DIAS_MES_BISIESTO = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _to_lista(valores) -> List[float]:
    if valores is None:
        return []

    if isinstance(valores, dict):
        return [
            max(0.0, float(valores.get(h, valores.get(str(h), 0.0)) or 0.0))
            for h in range(24)
        ]

    if isinstance(valores, (list, tuple)):
        return [max(0.0, float(valor or 0.0)) for valor in valores]

    return []


def _validar_series(demanda, fv) -> List[str]:
    errores = []

    if len(demanda) not in (24, 8760, 8784):
        errores.append("La demanda debe contener 24, 8760 o 8784 valores.")

    if len(fv) != len(demanda):
        errores.append("La demanda y la generación FV deben tener igual longitud.")

    return errores


def _leer_config_economica(cfg: ConfigBateria):
    capacidad = float(getattr(cfg, "capacidad_util_kwh", 0.0) or 0.0)
    potencia = float(getattr(cfg, "potencia_max_kw", 0.0) or 0.0)
    costo_usd_kwh = float(getattr(cfg, "costo_usd_kwh", 0.0) or 0.0)
    vida_util_anios = int(getattr(cfg, "vida_util_anios", 0) or 0)

    return {
        "capacidad_util_kwh": capacidad,
        "potencia_max_kw": potencia,
        "costo_usd_kwh": costo_usd_kwh,
        "capex_bateria_usd": capacidad * costo_usd_kwh,
        "vida_util_anios": vida_util_anios,
    }


def _validar_config_bateria(capacidad, potencia):
    errores = []

    if capacidad <= 0:
        errores.append("La capacidad de batería debe ser mayor que 0 kWh.")

    if potencia <= 0:
        errores.append("La potencia máxima de batería debe ser mayor que 0 kW.")

    return errores


def _calcular_soc(cfg: ConfigBateria, capacidad: float):
    soc_min = max(0.0, min(100.0, float(cfg.soc_min_pct or 0.0)))
    soc_max = max(soc_min, min(100.0, float(cfg.soc_max_pct or 100.0)))
    soc_inicial = max(
        soc_min,
        min(soc_max, float(cfg.soc_inicial_pct or soc_min)),
    )

    return (
        capacidad * soc_min / 100.0,
        capacidad * soc_max / 100.0,
        capacidad * soc_inicial / 100.0,
    )


def _calcular_eficiencias(cfg: ConfigBateria):
    eficiencia_rt = max(
        0.01,
        min(1.0, float(cfg.eficiencia_ida_vuelta or 0.90)),
    )
    eficiencia = sqrt(eficiencia_rt)
    return eficiencia, eficiencia


def _simular_hora(
    *,
    carga,
    gen,
    energia_bateria,
    energia_min,
    energia_max,
    potencia,
    eficiencia_carga,
    eficiencia_descarga,
):
    directo = min(carga, gen)
    excedente = max(gen - carga, 0.0)
    deficit = max(carga - gen, 0.0)

    espacio = max(energia_max - energia_bateria, 0.0)
    energia_para_cargar = min(
        excedente,
        potencia,
        espacio / eficiencia_carga,
    )
    energia_bateria += energia_para_cargar * eficiencia_carga

    disponible = max(energia_bateria - energia_min, 0.0)
    energia_entregable = min(
        deficit,
        potencia,
        disponible * eficiencia_descarga,
    )
    energia_bateria -= energia_entregable / eficiencia_descarga

    return {
        "directo": directo,
        "energia_bateria": energia_bateria,
        "compra_red_sin": deficit,
        "compra_red_con": max(deficit - energia_entregable, 0.0),
        "excedente_sin": excedente,
        "excedente_con": max(excedente - energia_para_cargar, 0.0),
        "carga_bateria": energia_para_cargar,
        "descarga_bateria": energia_entregable,
    }


def _promedio_24h(serie) -> List[float]:
    if not serie:
        return [0.0] * 24

    if len(serie) == 24:
        return list(serie)

    suma = [0.0] * 24
    conteo = [0] * 24

    for indice, valor in enumerate(serie):
        hora = indice % 24
        suma[hora] += float(valor or 0.0)
        conteo[hora] += 1

    return [
        suma[hora] / conteo[hora] if conteo[hora] else 0.0
        for hora in range(24)
    ]


def _agregar_12m(serie) -> List[float]:
    if len(serie) not in (8760, 8784):
        return []

    dias_mes = DIAS_MES_BISIESTO if len(serie) == 8784 else DIAS_MES_NORMAL
    resultado = []
    inicio = 0

    for dias in dias_mes:
        fin = inicio + dias * 24
        resultado.append(sum(serie[inicio:fin]))
        inicio = fin

    return resultado


def _calcular_totales(
    *,
    demanda,
    fv,
    compra_red_sin,
    compra_red_con,
    excedente_sin,
    excedente_con,
    carga_bat,
    descarga_bat,
    autoconsumo_directo,
    capacidad_utilizable,
):
    demanda_total = sum(demanda)
    compra_sin_total = sum(compra_red_sin)
    compra_con_total = sum(compra_red_con)
    energia_cargada = sum(carga_bat)
    energia_descargada = sum(descarga_bat)

    return {
        "demanda_total_kwh": demanda_total,
        "fv_total_kwh": sum(fv),
        "autoconsumo_directo_kwh": autoconsumo_directo,
        "energia_cargada_bateria_kwh": energia_cargada,
        "energia_descargada_bateria_kwh": energia_descargada,
        "perdidas_bateria_kwh": max(energia_cargada - energia_descargada, 0.0),
        "ciclos_equivalentes": (
            energia_descargada / capacidad_utilizable
            if capacidad_utilizable > 0 else 0.0
        ),
        "compra_red_sin_bateria_kwh": compra_sin_total,
        "compra_red_con_bateria_kwh": compra_con_total,
        "excedente_sin_bateria_kwh": sum(excedente_sin),
        "excedente_con_bateria_kwh": sum(excedente_con),
        "cobertura_sin_bateria_pct": (
            100.0 * (demanda_total - compra_sin_total) / demanda_total
            if demanda_total > 0 else 0.0
        ),
        "cobertura_con_bateria_pct": (
            100.0 * (demanda_total - compra_con_total) / demanda_total
            if demanda_total > 0 else 0.0
        ),
        "reduccion_compra_red_pct": (
            100.0 * (compra_sin_total - compra_con_total) / compra_sin_total
            if compra_sin_total > 0 else 0.0
        ),
    }


def _construir_resultado(
    *,
    demanda,
    fv,
    compra_sin,
    compra_con,
    excedente_sin,
    excedente_con,
    carga_bat,
    descarga_bat,
    soc_pct,
    autoconsumo,
    capacidad_utilizable,
    eco,
) -> ResultadoBateria:
    totales = _calcular_totales(
        demanda=demanda,
        fv=fv,
        compra_red_sin=compra_sin,
        compra_red_con=compra_con,
        excedente_sin=excedente_sin,
        excedente_con=excedente_con,
        carga_bat=carga_bat,
        descarga_bat=descarga_bat,
        autoconsumo_directo=autoconsumo,
        capacidad_utilizable=capacidad_utilizable,
    )

    return ResultadoBateria(
        ok=True,
        errores=[],
        warnings=[],
        **eco,
        demanda_24h_kwh=_promedio_24h(demanda),
        fv_24h_kwh=_promedio_24h(fv),
        compra_red_sin_bateria_24h=_promedio_24h(compra_sin),
        compra_red_con_bateria_24h=_promedio_24h(compra_con),
        excedente_sin_bateria_24h=_promedio_24h(excedente_sin),
        excedente_con_bateria_24h=_promedio_24h(excedente_con),
        carga_bateria_24h=_promedio_24h(carga_bat),
        descarga_bateria_24h=_promedio_24h(descarga_bat),
        soc_24h_pct=_promedio_24h(soc_pct),
        demanda_horaria_kwh=demanda,
        fv_horaria_kwh=fv,
        compra_red_sin_bateria_horaria_kwh=compra_sin,
        compra_red_con_bateria_horaria_kwh=compra_con,
        excedente_sin_bateria_horaria_kwh=excedente_sin,
        excedente_con_bateria_horaria_kwh=excedente_con,
        carga_bateria_horaria_kwh=carga_bat,
        descarga_bateria_horaria_kwh=descarga_bat,
        soc_horario_pct=soc_pct,
        demanda_12m_kwh=_agregar_12m(demanda),
        fv_12m_kwh=_agregar_12m(fv),
        compra_red_sin_bateria_12m_kwh=_agregar_12m(compra_sin),
        compra_red_con_bateria_12m_kwh=_agregar_12m(compra_con),
        excedente_sin_bateria_12m_kwh=_agregar_12m(excedente_sin),
        excedente_con_bateria_12m_kwh=_agregar_12m(excedente_con),
        carga_bateria_12m_kwh=_agregar_12m(carga_bat),
        descarga_bateria_12m_kwh=_agregar_12m(descarga_bat),
        **totales,
    )


def simular_balance_bateria_horario(
    demanda_horaria_kwh,
    fv_horaria_kwh,
    cfg: ConfigBateria,
) -> ResultadoBateria:
    demanda = _to_lista(demanda_horaria_kwh)
    fv = _to_lista(fv_horaria_kwh)
    errores = _validar_series(demanda, fv)

    if errores:
        return ResultadoBateria(ok=False, errores=errores)

    if not cfg or not cfg.usar_bateria:
        return _resultado_sin_bateria(demanda, fv)

    eco = _leer_config_economica(cfg)
    capacidad = eco["capacidad_util_kwh"]
    potencia = eco["potencia_max_kw"]
    errores = _validar_config_bateria(capacidad, potencia)

    if errores:
        return ResultadoBateria(ok=False, errores=errores, **eco)

    energia_min, energia_max, energia_bateria = _calcular_soc(cfg, capacidad)
    eficiencia_carga, eficiencia_descarga = _calcular_eficiencias(cfg)

    compra_sin, compra_con = [], []
    excedente_sin, excedente_con = [], []
    carga_bat, descarga_bat, soc_pct = [], [], []
    autoconsumo = 0.0

    for carga, gen in zip(demanda, fv):
        resultado = _simular_hora(
            carga=carga,
            gen=gen,
            energia_bateria=energia_bateria,
            energia_min=energia_min,
            energia_max=energia_max,
            potencia=potencia,
            eficiencia_carga=eficiencia_carga,
            eficiencia_descarga=eficiencia_descarga,
        )
        energia_bateria = resultado["energia_bateria"]
        autoconsumo += resultado["directo"]
        compra_sin.append(resultado["compra_red_sin"])
        compra_con.append(resultado["compra_red_con"])
        excedente_sin.append(resultado["excedente_sin"])
        excedente_con.append(resultado["excedente_con"])
        carga_bat.append(resultado["carga_bateria"])
        descarga_bat.append(resultado["descarga_bateria"])
        soc_pct.append(100.0 * energia_bateria / capacidad)

    return _construir_resultado(
        demanda=demanda,
        fv=fv,
        compra_sin=compra_sin,
        compra_con=compra_con,
        excedente_sin=excedente_sin,
        excedente_con=excedente_con,
        carga_bat=carga_bat,
        descarga_bat=descarga_bat,
        soc_pct=soc_pct,
        autoconsumo=autoconsumo,
        capacidad_utilizable=max(energia_max - energia_min, 0.0),
        eco=eco,
    )


def simular_balance_bateria_24h(
    demanda_24h_kwh,
    fv_24h_kwh,
    cfg: ConfigBateria,
) -> ResultadoBateria:
    """Acceso compatible; también admite series de 8760 o 8784 horas."""

    return simular_balance_bateria_horario(
        demanda_horaria_kwh=demanda_24h_kwh,
        fv_horaria_kwh=fv_24h_kwh,
        cfg=cfg,
    )


def _resultado_sin_bateria(demanda, fv) -> ResultadoBateria:
    compra = [max(carga - gen, 0.0) for carga, gen in zip(demanda, fv)]
    excedente = [max(gen - carga, 0.0) for carga, gen in zip(demanda, fv)]
    autoconsumo = sum(min(carga, gen) for carga, gen in zip(demanda, fv))
    ceros = [0.0] * len(demanda)

    eco = {
        "capacidad_util_kwh": 0.0,
        "potencia_max_kw": 0.0,
        "costo_usd_kwh": 0.0,
        "capex_bateria_usd": 0.0,
        "vida_util_anios": 0,
    }

    return _construir_resultado(
        demanda=demanda,
        fv=fv,
        compra_sin=compra,
        compra_con=compra,
        excedente_sin=excedente,
        excedente_con=excedente,
        carga_bat=ceros,
        descarga_bat=ceros,
        soc_pct=ceros,
        autoconsumo=autoconsumo,
        capacidad_utilizable=0.0,
        eco=eco,
    )

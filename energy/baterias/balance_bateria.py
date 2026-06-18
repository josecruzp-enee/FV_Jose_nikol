# -*- coding: utf-8 -*-
from __future__ import annotations

from math import sqrt
from typing import List

from energy.baterias.modelos import ConfigBateria
from energy.baterias.resultado_bateria import ResultadoBateria


def _to_24h_lista(valores) -> List[float]:
    if valores is None:
        return [0.0] * 24

    if isinstance(valores, dict):
        return [float(valores.get(h, 0.0) or 0.0) for h in range(24)]

    if isinstance(valores, (list, tuple)):
        data = [float(x or 0.0) for x in valores]
        if len(data) >= 24:
            return data[:24]
        return data + [0.0] * (24 - len(data))

    return [0.0] * 24


def _leer_config_economica(cfg: ConfigBateria):
    capacidad = float(getattr(cfg, "capacidad_util_kwh", 0.0) or 0.0)
    potencia = float(getattr(cfg, "potencia_max_kw", 0.0) or 0.0)
    costo_usd_kwh = float(getattr(cfg, "costo_usd_kwh", 0.0) or 0.0)
    vida_util_anios = int(getattr(cfg, "vida_util_anios", 0) or 0)

    capex_bateria_usd = capacidad * costo_usd_kwh

    return {
        "capacidad_util_kwh": capacidad,
        "potencia_max_kw": potencia,
        "costo_usd_kwh": costo_usd_kwh,
        "capex_bateria_usd": capex_bateria_usd,
        "vida_util_anios": vida_util_anios,
    }


def _validar_config_bateria(capacidad, potencia):
    errores = []

    if capacidad <= 0:
        errores.append("La capacidad útil de batería debe ser mayor que 0 kWh.")

    if potencia <= 0:
        errores.append("La potencia máxima de batería debe ser mayor que 0 kW.")

    return errores


def _calcular_soc(cfg: ConfigBateria, capacidad: float):
    soc_min_pct = max(0.0, min(100.0, float(cfg.soc_min_pct or 0.0)))
    soc_max_pct = max(soc_min_pct, min(100.0, float(cfg.soc_max_pct or 100.0)))
    soc_ini_pct = max(
        soc_min_pct,
        min(soc_max_pct, float(cfg.soc_inicial_pct or soc_min_pct))
    )

    energia_min = capacidad * soc_min_pct / 100.0
    energia_max = capacidad * soc_max_pct / 100.0
    energia_ini = capacidad * soc_ini_pct / 100.0

    return energia_min, energia_max, energia_ini


def _calcular_eficiencias(cfg: ConfigBateria):
    eficiencia_rt = max(
        0.01,
        min(1.0, float(cfg.eficiencia_ida_vuelta or 0.90))
    )

    eficiencia_carga = sqrt(eficiencia_rt)
    eficiencia_descarga = sqrt(eficiencia_rt)

    return eficiencia_carga, eficiencia_descarga


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

    compra_red_sin = deficit
    excedente_sin = excedente

    espacio = max(energia_max - energia_bateria, 0.0)

    energia_para_cargar = min(
        excedente,
        potencia,
        espacio / eficiencia_carga if eficiencia_carga > 0 else 0.0,
    )

    energia_almacenada = energia_para_cargar * eficiencia_carga
    energia_bateria += energia_almacenada

    excedente_restante = excedente - energia_para_cargar

    disponible = max(energia_bateria - energia_min, 0.0)

    energia_entregable = min(
        deficit,
        potencia,
        disponible * eficiencia_descarga,
    )

    energia_extraida = (
        energia_entregable / eficiencia_descarga
        if eficiencia_descarga > 0
        else 0.0
    )

    energia_bateria -= energia_extraida

    deficit_restante = deficit - energia_entregable

    return {
        "directo": directo,
        "energia_bateria": energia_bateria,
        "compra_red_sin": compra_red_sin,
        "compra_red_con": max(deficit_restante, 0.0),
        "excedente_sin": excedente_sin,
        "excedente_con": max(excedente_restante, 0.0),
        "carga_bateria": energia_para_cargar,
        "descarga_bateria": energia_entregable,
    }


def _calcular_totales(
    demanda,
    fv,
    compra_red_sin,
    compra_red_con,
    excedente_sin,
    excedente_con,
    carga_bat,
    descarga_bat,
    autoconsumo_directo,
):
    demanda_total = sum(demanda)
    fv_total = sum(fv)

    compra_sin_total = sum(compra_red_sin)
    compra_con_total = sum(compra_red_con)

    excedente_sin_total = sum(excedente_sin)
    excedente_con_total = sum(excedente_con)

    energia_cargada = sum(carga_bat)
    energia_descargada = sum(descarga_bat)

    cobertura_sin = (
        100.0 * (demanda_total - compra_sin_total) / demanda_total
        if demanda_total > 0
        else 0.0
    )

    cobertura_con = (
        100.0 * (demanda_total - compra_con_total) / demanda_total
        if demanda_total > 0
        else 0.0
    )

    reduccion_compra = (
        100.0 * (compra_sin_total - compra_con_total) / compra_sin_total
        if compra_sin_total > 0
        else 0.0
    )

    return {
        "demanda_total_kwh": demanda_total,
        "fv_total_kwh": fv_total,
        "autoconsumo_directo_kwh": autoconsumo_directo,
        "energia_cargada_bateria_kwh": energia_cargada,
        "energia_descargada_bateria_kwh": energia_descargada,
        "compra_red_sin_bateria_kwh": compra_sin_total,
        "compra_red_con_bateria_kwh": compra_con_total,
        "excedente_sin_bateria_kwh": excedente_sin_total,
        "excedente_con_bateria_kwh": excedente_con_total,
        "cobertura_sin_bateria_pct": cobertura_sin,
        "cobertura_con_bateria_pct": cobertura_con,
        "reduccion_compra_red_pct": reduccion_compra,
    }


def simular_balance_bateria_24h(
    demanda_24h_kwh,
    fv_24h_kwh,
    cfg: ConfigBateria,
) -> ResultadoBateria:

    demanda = _to_24h_lista(demanda_24h_kwh)
    fv = _to_24h_lista(fv_24h_kwh)

    if not cfg or not cfg.usar_bateria:
        return _resultado_sin_bateria(demanda, fv)

    eco = _leer_config_economica(cfg)

    capacidad = eco["capacidad_util_kwh"]
    potencia = eco["potencia_max_kw"]

    errores = _validar_config_bateria(capacidad, potencia)

    if errores:
        return ResultadoBateria(
            ok=False,
            errores=errores,
            demanda_24h_kwh=demanda,
            fv_24h_kwh=fv,
            **eco,
        )

    energia_min, energia_max, energia_bateria = _calcular_soc(cfg, capacidad)
    eficiencia_carga, eficiencia_descarga = _calcular_eficiencias(cfg)

    compra_red_sin = []
    compra_red_con = []

    excedente_sin = []
    excedente_con = []

    carga_bat = []
    descarga_bat = []
    soc_pct = []

    autoconsumo_directo = 0.0

    for h in range(24):
        r = _simular_hora(
            carga=demanda[h],
            gen=fv[h],
            energia_bateria=energia_bateria,
            energia_min=energia_min,
            energia_max=energia_max,
            potencia=potencia,
            eficiencia_carga=eficiencia_carga,
            eficiencia_descarga=eficiencia_descarga,
        )

        energia_bateria = r["energia_bateria"]
        autoconsumo_directo += r["directo"]

        compra_red_sin.append(r["compra_red_sin"])
        compra_red_con.append(r["compra_red_con"])

        excedente_sin.append(r["excedente_sin"])
        excedente_con.append(r["excedente_con"])

        carga_bat.append(r["carga_bateria"])
        descarga_bat.append(r["descarga_bateria"])

        soc_pct.append(
            100.0 * energia_bateria / capacidad
            if capacidad > 0
            else 0.0
        )

    totales = _calcular_totales(
        demanda=demanda,
        fv=fv,
        compra_red_sin=compra_red_sin,
        compra_red_con=compra_red_con,
        excedente_sin=excedente_sin,
        excedente_con=excedente_con,
        carga_bat=carga_bat,
        descarga_bat=descarga_bat,
        autoconsumo_directo=autoconsumo_directo,
    )

    return ResultadoBateria(
        ok=True,
        errores=[],
        warnings=[],

        **eco,

        demanda_24h_kwh=demanda,
        fv_24h_kwh=fv,

        compra_red_sin_bateria_24h=compra_red_sin,
        compra_red_con_bateria_24h=compra_red_con,

        excedente_sin_bateria_24h=excedente_sin,
        excedente_con_bateria_24h=excedente_con,

        carga_bateria_24h=carga_bat,
        descarga_bateria_24h=descarga_bat,
        soc_24h_pct=soc_pct,

        **totales,
    )


def _resultado_sin_bateria(demanda, fv) -> ResultadoBateria:
    compra_red = []
    excedente = []
    autoconsumo = 0.0

    for carga, gen in zip(demanda, fv):
        directo = min(carga, gen)
        autoconsumo += directo

        compra_red.append(max(carga - gen, 0.0))
        excedente.append(max(gen - carga, 0.0))

    totales = _calcular_totales(
        demanda=demanda,
        fv=fv,
        compra_red_sin=compra_red,
        compra_red_con=compra_red,
        excedente_sin=excedente,
        excedente_con=excedente,
        carga_bat=[0.0] * 24,
        descarga_bat=[0.0] * 24,
        autoconsumo_directo=autoconsumo,
    )

    return ResultadoBateria(
        ok=True,

        capacidad_util_kwh=0.0,
        potencia_max_kw=0.0,
        costo_usd_kwh=0.0,
        capex_bateria_usd=0.0,
        vida_util_anios=0,

        demanda_24h_kwh=demanda,
        fv_24h_kwh=fv,

        compra_red_sin_bateria_24h=compra_red,
        compra_red_con_bateria_24h=compra_red,

        excedente_sin_bateria_24h=excedente,
        excedente_con_bateria_24h=excedente,

        carga_bateria_24h=[0.0] * 24,
        descarga_bateria_24h=[0.0] * 24,
        soc_24h_pct=[0.0] * 24,

        **totales,
    )

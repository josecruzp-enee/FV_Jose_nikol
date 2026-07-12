# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List


def convertir_a_perfil_24h(valores) -> List[float]:
    """
    Convierte dict, lista de 24 valores o serie 8760
    en un perfil promedio de 24 horas.
    """

    if valores is None:
        return [0.0] * 24

    if isinstance(valores, dict):
        return [
            max(
                0.0,
                float(
                    valores.get(
                        hora,
                        valores.get(str(hora), 0.0),
                    )
                    or 0.0
                ),
            )
            for hora in range(24)
        ]

    if isinstance(valores, (list, tuple)):
        datos = [
            max(0.0, float(valor or 0.0))
            for valor in valores
        ]

        if len(datos) == 24:
            return datos

        if len(datos) > 24:
            return promediar_energia_8760_a_24h(datos)

        return datos + [0.0] * (24 - len(datos))

    return [0.0] * 24


def normalizar_demanda_24h(
    demanda_24h,
    consumo_anual_kwh: float | None = None,
) -> List[float]:
    """
    Normaliza exclusivamente el perfil utilizado por baterías.

    Mantiene la forma horaria y ajusta su suma para que,
    repetida durante 365 días, coincida con el consumo anual.

    No modifica el objeto Datosproyecto ni el perfil original.
    """

    demanda = convertir_a_perfil_24h(demanda_24h)

    if consumo_anual_kwh is None:
        return demanda

    consumo_anual = max(
        0.0,
        float(consumo_anual_kwh or 0.0),
    )

    consumo_diario_actual = sum(demanda)

    if consumo_anual <= 0 or consumo_diario_actual <= 0:
        return demanda

    consumo_diario_objetivo = consumo_anual / 365.0

    factor_ajuste = (
        consumo_diario_objetivo /
        consumo_diario_actual
    )

    return [
        valor * factor_ajuste
        for valor in demanda
    ]


def promediar_energia_8760_a_24h(
    energia_horaria_kwh,
) -> List[float]:
    """
    Convierte una serie horaria en un perfil promedio de 24h.

    Mantiene el corrimiento horario utilizado actualmente:
        hora = (idx - 6) % 24
    """

    if not energia_horaria_kwh:
        return [0.0] * 24

    suma = [0.0] * 24
    conteo = [0] * 24

    for indice, valor in enumerate(energia_horaria_kwh):
        hora = (indice - 6) % 24

        suma[hora] += max(
            0.0,
            float(valor or 0.0),
        )

        conteo[hora] += 1

    return [
        suma[hora] / conteo[hora]
        if conteo[hora]
        else 0.0
        for hora in range(24)
    ]


def preparar_perfiles_bateria(
    *,
    demanda_24h,
    fv_24h,
    consumo_anual_kwh: float | None = None,
) -> Dict[str, List[float]]:
    """
    Punto único para preparar los perfiles utilizados
    por recomendación y simulación de baterías.
    """

    demanda = normalizar_demanda_24h(
        demanda_24h=demanda_24h,
        consumo_anual_kwh=consumo_anual_kwh,
    )

    fv = convertir_a_perfil_24h(fv_24h)

    return {
        "demanda_24h": demanda,
        "fv_24h": fv,
    }

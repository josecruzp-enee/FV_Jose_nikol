# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List


DIAS_MES_NORMAL = [
    31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31,
]

DIAS_MES_BISIESTO = [
    31, 29, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31,
]


def _lista_positiva(valores) -> List[float]:
    return [
        max(0.0, float(valor or 0.0))
        for valor in valores
    ]


def convertir_a_perfil_24h(valores) -> List[float]:
    """
    Convierte dict, lista de 24 valores o serie horaria anual
    en un perfil promedio de 24 horas.

    Esta función se conserva para gráficas y compatibilidad.
    La simulación anual utiliza la serie completa.
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
        datos = _lista_positiva(valores)

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
    """Mantiene la compatibilidad con el perfil diario anterior."""

    demanda = convertir_a_perfil_24h(demanda_24h)

    if consumo_anual_kwh is None:
        return demanda

    consumo_anual = max(
        0.0,
        float(consumo_anual_kwh or 0.0),
    )
    consumo_diario = sum(demanda)

    if consumo_anual <= 0 or consumo_diario <= 0:
        return demanda

    factor = (
        consumo_anual /
        365.0 /
        consumo_diario
    )

    return [valor * factor for valor in demanda]


def _dias_mes(n_horas: int) -> List[int]:
    if n_horas == 8784:
        return DIAS_MES_BISIESTO[:]

    return DIAS_MES_NORMAL[:]


def _normalizar_consumo_12m(
    consumo_12m_kwh,
    consumo_anual_kwh: float | None,
    dias_mes: List[int],
) -> List[float]:
    if consumo_12m_kwh and len(consumo_12m_kwh) == 12:
        return _lista_positiva(consumo_12m_kwh)

    consumo_anual = max(
        0.0,
        float(consumo_anual_kwh or 0.0),
    )

    total_dias = sum(dias_mes)

    if consumo_anual <= 0 or total_dias <= 0:
        return [0.0] * 12

    return [
        consumo_anual * dias / total_dias
        for dias in dias_mes
    ]


def construir_demanda_horaria_anual(
    *,
    demanda_24h,
    consumo_12m_kwh=None,
    consumo_anual_kwh: float | None = None,
    n_horas: int = 8760,
) -> List[float]:
    """
    Repite la forma del perfil de 24 horas y normaliza cada mes
    para que coincida exactamente con su consumo mensual.
    """

    if n_horas not in (8760, 8784):
        raise ValueError(
            "La demanda anual debe contener 8760 o 8784 horas."
        )

    perfil = convertir_a_perfil_24h(demanda_24h)
    suma_perfil = sum(perfil)
    dias_mes = _dias_mes(n_horas)
    consumos = _normalizar_consumo_12m(
        consumo_12m_kwh,
        consumo_anual_kwh,
        dias_mes,
    )

    if suma_perfil <= 0:
        return [0.0] * n_horas

    demanda_anual: List[float] = []

    for consumo_mes, dias in zip(consumos, dias_mes):
        factor = consumo_mes / (suma_perfil * dias)
        perfil_mes = [valor * factor for valor in perfil]

        for _ in range(dias):
            demanda_anual.extend(perfil_mes)

    return demanda_anual


def _ajustar_hora_honduras(
    energia_horaria_kwh,
) -> List[float]:
    """
    Conserva el corrimiento histórico UTC-6 del módulo.

    El índice UTC se asigna a la hora local (índice - 6).
    """

    energia = _lista_positiva(energia_horaria_kwh)

    if len(energia) not in (8760, 8784):
        return energia

    return energia[6:] + energia[:6]


def promediar_energia_8760_a_24h(
    energia_horaria_kwh,
) -> List[float]:
    """Convierte una serie anual en un perfil local promedio de 24 h."""

    if not energia_horaria_kwh:
        return [0.0] * 24

    energia_local = _ajustar_hora_honduras(
        energia_horaria_kwh
    )
    return _promediar_serie_local_a_24h(energia_local)


def _promediar_serie_local_a_24h(
    energia_local,
) -> List[float]:
    suma = [0.0] * 24
    conteo = [0] * 24

    for indice, valor in enumerate(energia_local):
        hora = indice % 24
        suma[hora] += valor
        conteo[hora] += 1

    return [
        suma[hora] / conteo[hora]
        if conteo[hora]
        else 0.0
        for hora in range(24)
    ]


def _preparar_fv_horaria(fv_horaria) -> List[float]:
    if not isinstance(fv_horaria, (list, tuple)):
        return []

    fv = _lista_positiva(fv_horaria)

    if len(fv) in (8760, 8784):
        return _ajustar_hora_honduras(fv)

    if len(fv) == 24:
        return fv * 365

    raise ValueError(
        "El perfil FV debe contener 24, 8760 o 8784 valores."
    )


def preparar_perfiles_bateria(
    *,
    demanda_24h,
    fv_24h,
    consumo_anual_kwh: float | None = None,
    consumo_12m_kwh=None,
) -> Dict[str, List[float]]:
    """
    Prepara los perfiles anuales usados por el simulador y
    los perfiles promedio de 24 horas usados por la gráfica.

    `fv_24h` conserva su nombre por compatibilidad, pero puede
    recibir 24, 8760 o 8784 valores.
    """

    fv_horaria = _preparar_fv_horaria(fv_24h)
    n_horas = len(fv_horaria)

    demanda_horaria = construir_demanda_horaria_anual(
        demanda_24h=demanda_24h,
        consumo_12m_kwh=consumo_12m_kwh,
        consumo_anual_kwh=consumo_anual_kwh,
        n_horas=n_horas,
    )

    demanda_promedio = _promediar_serie_local_a_24h(
        demanda_horaria
    )
    fv_promedio = _promediar_serie_local_a_24h(
        fv_horaria
    )

    return {
        "demanda_24h": demanda_promedio,
        "fv_24h": fv_promedio,
        "demanda_8760": demanda_horaria,
        "fv_8760": fv_horaria,
        "demanda_horaria": demanda_horaria,
        "fv_horaria": fv_horaria,
    }

from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO SOLAR / CLIMA — FV Engine
=================================================

Responsabilidad
---------------

Este módulo transforma datos climáticos horarios (8760)
en un estado físico utilizable por el dominio energía.

Pipeline representado:

    clima (GHI, DNI, DHI, T_amb)
            ↓
    posición solar
            ↓
    irradiancia en plano (POA)
            ↓
    temperatura de celda
            ↓
    EstadoSolarHora (salida final)

Este módulo NO calcula energía.
Este módulo NO conoce paneles eléctricos.
Este módulo NO conoce inversores.

Frontera del dominio
--------------------

Entrada:
    ResultadoClima  ← dominio clima

Salida:
    ResultadoClima8760  ← consumido por energy

Dependencias:
    energy.solar.*              → geometría solar
    energy.panel_energia.*      → modelo térmico

Regla arquitectónica
--------------------

    ✔ Convierte clima → estado físico solar
    ✔ Es independiente del modelo energético
    ❌ NO calcula potencia
    ❌ NO usa parámetros eléctricos del panel
"""

from dataclasses import dataclass
from typing import List

# ----------------------------------------------------------
# DEPENDENCIAS DE DOMINIO
# ----------------------------------------------------------

from energy.solar.posicion_solar import (
    calcular_posicion_solar,
    SolarInput,
)

from energy.solar.irradiancia_plano import (
    calcular_irradiancia_plano,
    IrradianciaInput
)

from energy.panel_energia.modelo_termico import (
    calcular_temperatura_celda,
    ModeloTermicoInput
)

from .resultado_clima import ResultadoClima, validar_clima_8760


# ==========================================================
# ESTADO SOLAR HORARIO
# ==========================================================

@dataclass(frozen=True)
class EstadoSolarHora:
    """
    Estado físico del sistema FV en una hora específica.

    Este objeto representa las condiciones físicas que
    luego serán consumidas por el dominio energía.

    No contiene información eléctrica.
    """

    # ------------------------------------------------------
    # IRRADIANCIA
    # ------------------------------------------------------

    poa_wm2: float
    # Irradiancia en el plano del generador (Plane of Array)

    # ------------------------------------------------------
    # TEMPERATURA
    # ------------------------------------------------------

    temp_amb_c: float
    # Temperatura ambiente

    temp_celda_c: float
    # Temperatura de la celda FV (modelo térmico)

    # ------------------------------------------------------
    # GEOMETRÍA SOLAR
    # ------------------------------------------------------

    zenith: float
    # Ángulo cenital del sol

    azimuth: float
    # Azimut solar


# ==========================================================
# RESULTADO DEL DOMINIO SOLAR
# ==========================================================

@dataclass(frozen=True)
class ResultadoClima8760:
    """
    Resultado del procesamiento solar/climático.

    Este objeto representa el estado físico completo del año.
    """

    horas: List[EstadoSolarHora]
    # Lista de 8760 estados horarios

    poa_total_kwh_m2: float
    # Energía total incidente sobre el plano (kWh/m²)


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def simular_clima_8760(
    clima: ResultadoClima,
    tilt: float,
    azimuth: float
) -> ResultadoClima8760:
    """
    Ejecuta la simulación solar completa para 8760 horas.

    Flujo interno:

        1) Validar clima
        2) Calcular posición solar
        3) Calcular POA
        4) Calcular temperatura de celda
        5) Construir estado horario

    Parámetros
    ----------
    clima:
        Datos climáticos base (GHI, DNI, DHI, temperatura)

    tilt:
        Inclinación del panel

    azimuth:
        Orientación del panel

    Retorna
    -------
    ResultadoClima8760
    """

    # ------------------------------------------------------
    # VALIDACIÓN DE ENTRADA
    # ------------------------------------------------------

    validar_clima_8760(clima)

    horas: List[EstadoSolarHora] = []
    poa_total_kwh_m2 = 0.0

    # ------------------------------------------------------
    # ITERACIÓN HORARIA
    # ------------------------------------------------------

    for hora in clima.horas:

        # ==================================================
        # 1. POSICIÓN SOLAR
        # ==================================================

        pos = calcular_posicion_solar(
            SolarInput(
                latitud_deg=clima.latitud,
                longitud_deg=clima.longitud,
                fecha_hora=hora.timestamp
            )
        )

        # ==================================================
        # 2. IRRADIANCIA EN PLANO (POA)
        # ==================================================

        irr = calcular_irradiancia_plano(
            IrradianciaInput(
                dni=hora.dni_wm2,
                dhi=hora.dhi_wm2,
                ghi=hora.ghi_wm2,
                solar_zenith_deg=pos.zenith_deg,
                solar_azimuth_deg=pos.azimuth_deg,
                panel_tilt_deg=tilt,
                panel_azimuth_deg=azimuth
            )
        )

        poa = max(0.0, irr.poa_total)

        # ==================================================
        # 3. MODELO TÉRMICO
        # ==================================================

        r_termico = calcular_temperatura_celda(
            ModeloTermicoInput(
                irradiancia_poa_wm2=poa,
                temperatura_ambiente_c=hora.temp_amb_c,
                noct_c=45  # valor típico
            )
        )

        temp_celda = r_termico.temperatura_celda_c

        # ==================================================
        # 4. ACUMULACIÓN DE ENERGÍA
        # ==================================================

        poa_total_kwh_m2 += poa / 1000

        # ==================================================
        # 5. CONSTRUCCIÓN DEL ESTADO
        # ==================================================

        horas.append(
            EstadoSolarHora(
                poa_wm2=poa,
                temp_amb_c=hora.temp_amb_c,
                temp_celda_c=temp_celda,
                zenith=pos.zenith_deg,
                azimuth=pos.azimuth_deg
            )
        )

    # ------------------------------------------------------
    # DEBUG CONTROLADO
    # ------------------------------------------------------

    print("DEBUG CLIMA:")
    print("Horas:", len(clima.horas))
    print("DNI total:", sum(h.dni_wm2 for h in clima.horas))
    print("Ejemplo:", clima.horas[0])

    # ------------------------------------------------------
    # SALIDA FINAL
    # ------------------------------------------------------

    return ResultadoClima8760(
        horas=horas,
        poa_total_kwh_m2=poa_total_kwh_m2
    )


# ==========================================================
# ESTRUCTURA DEL DOMINIO
# ==========================================================

"""
Este módulo produce:

ResultadoClima8760


Estructura:

ResultadoClima8760
    ├─ horas (8760)
    │      ├─ poa_wm2
    │      ├─ temp_amb_c
    │      ├─ temp_celda_c
    │      ├─ zenith
    │      └─ azimuth
    │
    └─ poa_total_kwh_m2


Flujo de integración:

clima (ResultadoClima)
        ↓
simular_clima_8760
        ↓
ResultadoClima8760
        ↓
energy (motor energético)


Fronteras:

✔ clima → datos
✔ solar → geometría + POA
✔ térmico → temperatura celda
✔ energy → potencia y energía

Este módulo NO cruza esas fronteras.
"""

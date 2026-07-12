# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EntradaBateria:
    """
    Entrada única para recomendación, simulación y evaluación
    económica del sistema de baterías.

    No depende de Datosproyecto ni de EnergiaResultado.
    """

    # ======================================================
    # PERFILES ENERGÉTICOS
    # ======================================================

    demanda_24h_kwh: Dict[int, float] | List[float]

    # Puede contener 24 o 8760 valores.
    fv_horaria_kwh: List[float]

    consumo_12m_kwh: List[float]
    energia_fv_util_12m_kwh: List[float]

    # Generación total antes de limitarla por autoconsumo.
    energia_fv_generada_12m_kwh: List[float] = field(
        default_factory=list
    )

    # ======================================================
    # CONFIGURACIÓN TÉCNICA
    # ======================================================

    usar_bateria: bool = True

    factor_aprovechamiento: float = 0.80

    capacidades_comerciales_kwh: List[float] = field(
        default_factory=lambda: [
            5.0,
            10.0,
            15.0,
            20.0,
            30.0,
            40.0,
        ]
    )

    soc_inicial_pct: float = 20.0
    soc_min_pct: float = 20.0
    soc_max_pct: float = 100.0

    eficiencia_ida_vuelta: float = 0.90
    vida_util_bateria_anios: int = 10

    # ======================================================
    # COSTOS
    # ======================================================

    costo_bateria_usd_kwh: float = 250.0
    tipo_cambio_l_usd: float = 26.61

    capex_fv_l: float = 0.0
    tarifa_compra_l_kwh: float = 0.0
    cargos_fijos_l_mes: float = 0.0
    om_anual_pct: float = 0.0

    # ======================================================
    # FINANCIAMIENTO
    # ======================================================

    modo_financiamiento: str = "contado"
    tasa_anual: float = 0.0
    plazo_anios: int = 0
    porcentaje_financiado: float = 0.0

    # ======================================================
    # PROPIEDADES CALCULADAS
    # ======================================================

    @property
    def consumo_anual_kwh(self) -> float:
        return sum(
            max(0.0, float(valor or 0.0))
            for valor in self.consumo_12m_kwh
        )

    @property
    def costo_bateria_l_kwh(self) -> float:
        return (
            max(0.0, float(self.costo_bateria_usd_kwh))
            * max(0.0, float(self.tipo_cambio_l_usd))
        )

    # ======================================================
    # VALIDACIÓN
    # ======================================================

    def validar(self) -> List[str]:
        errores: List[str] = []

        if not self.demanda_24h_kwh:
            errores.append(
                "No se recibió el perfil horario de demanda."
            )

        if not self.fv_horaria_kwh:
            errores.append(
                "No se recibió el perfil horario fotovoltaico."
            )

        if len(self.consumo_12m_kwh) != 12:
            errores.append(
                "consumo_12m_kwh debe contener 12 valores."
            )

        if len(self.energia_fv_util_12m_kwh) != 12:
            errores.append(
                "energia_fv_util_12m_kwh debe contener 12 valores."
            )

        if (
            self.energia_fv_generada_12m_kwh
            and len(self.energia_fv_generada_12m_kwh) != 12
        ):
            errores.append(
                "energia_fv_generada_12m_kwh debe contener "
                "12 valores."
            )

        if self.consumo_anual_kwh <= 0:
            errores.append(
                "El consumo anual debe ser mayor que cero."
            )

        if not 0.0 < self.factor_aprovechamiento <= 1.0:
            errores.append(
                "factor_aprovechamiento debe estar entre 0 y 1."
            )

        if not 0.0 < self.eficiencia_ida_vuelta <= 1.0:
            errores.append(
                "eficiencia_ida_vuelta debe estar entre 0 y 1."
            )

        if not 0.0 <= self.soc_min_pct <= 100.0:
            errores.append(
                "soc_min_pct debe estar entre 0 y 100."
            )

        if not 0.0 <= self.soc_max_pct <= 100.0:
            errores.append(
                "soc_max_pct debe estar entre 0 y 100."
            )

        if self.soc_max_pct <= self.soc_min_pct:
            errores.append(
                "soc_max_pct debe ser mayor que soc_min_pct."
            )

        if not (
            self.soc_min_pct
            <= self.soc_inicial_pct
            <= self.soc_max_pct
        ):
            errores.append(
                "soc_inicial_pct debe estar dentro de los "
                "límites mínimo y máximo."
            )

        if self.costo_bateria_usd_kwh < 0:
            errores.append(
                "El costo de batería no puede ser negativo."
            )

        if self.tipo_cambio_l_usd <= 0:
            errores.append(
                "El tipo de cambio debe ser mayor que cero."
            )

        if self.tarifa_compra_l_kwh < 0:
            errores.append(
                "La tarifa de compra no puede ser negativa."
            )

        if not 0.0 <= self.porcentaje_financiado <= 1.0:
            errores.append(
                "porcentaje_financiado debe estar entre 0 y 1."
            )

        if (
            self.modo_financiamiento != "contado"
            and self.porcentaje_financiado > 0
            and self.plazo_anios <= 0
        ):
            errores.append(
                "El plazo debe ser mayor que cero para un "
                "proyecto financiado."
            )

        capacidades_validas = [
            float(capacidad)
            for capacidad in self.capacidades_comerciales_kwh
            if float(capacidad or 0.0) > 0
        ]

        if self.usar_bateria and not capacidades_validas:
            errores.append(
                "No existen capacidades comerciales válidas."
            )

        return errores

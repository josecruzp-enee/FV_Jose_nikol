# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ==========================================================
# RESULTADO TÉCNICO DE UNA SIMULACIÓN
# ==========================================================

@dataclass
class ResultadoBateria:
    ok: bool

    errores: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    capacidad_util_kwh: float = 0.0
    potencia_max_kw: float = 0.0

    costo_usd_kwh: float = 0.0
    capex_bateria_usd: float = 0.0
    vida_util_anios: int = 0

    demanda_24h_kwh: List[float] = field(
        default_factory=list
    )

    fv_24h_kwh: List[float] = field(
        default_factory=list
    )

    compra_red_sin_bateria_24h: List[float] = field(
        default_factory=list
    )

    compra_red_con_bateria_24h: List[float] = field(
        default_factory=list
    )

    excedente_sin_bateria_24h: List[float] = field(
        default_factory=list
    )

    excedente_con_bateria_24h: List[float] = field(
        default_factory=list
    )

    carga_bateria_24h: List[float] = field(
        default_factory=list
    )

    descarga_bateria_24h: List[float] = field(
        default_factory=list
    )

    soc_24h_pct: List[float] = field(
        default_factory=list
    )

    demanda_total_kwh: float = 0.0
    fv_total_kwh: float = 0.0

    autoconsumo_directo_kwh: float = 0.0
    energia_cargada_bateria_kwh: float = 0.0
    energia_descargada_bateria_kwh: float = 0.0

    compra_red_sin_bateria_kwh: float = 0.0
    compra_red_con_bateria_kwh: float = 0.0

    excedente_sin_bateria_kwh: float = 0.0
    excedente_con_bateria_kwh: float = 0.0

    cobertura_sin_bateria_pct: float = 0.0
    cobertura_con_bateria_pct: float = 0.0

    reduccion_compra_red_pct: float = 0.0


# ==========================================================
# ESCENARIO TÉCNICO Y ECONÓMICO
# ==========================================================

@dataclass
class EscenarioBateria:
    nombre: str

    capacidad_bateria_kwh: float = 0.0
    potencia_bateria_kw: float = 0.0

    capex_bateria_l: float = 0.0
    capex_total_l: float = 0.0

    energia_descargada_dia_kwh: float = 0.0
    energia_objetivo_dia_kwh: float = 0.0

    ahorro_anual_l: float = 0.0
    ahorro_incremental_anual_l: float = 0.0

    cuota_mensual_l: float = 0.0
    om_mensual_l: float = 0.0

    payback_total_anios: Optional[float] = None
    payback_bateria_anios: Optional[float] = None

    roi_total_pct: float = 0.0
    roi_bateria_pct: float = 0.0

    dscr: Optional[float] = None

    estado: str = "SIN EVALUAR"
    criterio_seleccion: str = ""

    energia_util_12m_kwh: List[float] = field(
        default_factory=list
    )

    tabla_12m: List[Dict[str, Any]] = field(
        default_factory=list
    )

    resultado_tecnico: Optional[ResultadoBateria] = None


# ==========================================================
# SALIDA ÚNICA DEL MÓDULO DE BATERÍAS
# ==========================================================

@dataclass
class ResultadoSistemaBateria:
    ok: bool

    errores: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    consumo_anual_kwh: float = 0.0

    demanda_diaria_original_kwh: float = 0.0
    demanda_diaria_normalizada_kwh: float = 0.0
    factor_normalizacion_demanda: float = 1.0

    excedente_fv_diario_kwh: float = 0.0
    consumo_nocturno_diario_kwh: float = 0.0
    energia_objetivo_diaria_kwh: float = 0.0

    escenarios: List[EscenarioBateria] = field(
        default_factory=list
    )

    escenario_sin_bateria: Optional[
        EscenarioBateria
    ] = None

    escenario_seleccionado: Optional[
        EscenarioBateria
    ] = None

    # ------------------------------------------------------
    # ACCESOS DE COMPATIBILIDAD
    # ------------------------------------------------------

    @property
    def bateria_recomendada(self) -> Optional[EscenarioBateria]:
        return self.escenario_seleccionado

    @property
    def bateria_optima(self) -> Optional[EscenarioBateria]:
        return self.escenario_seleccionado

    @property
    def resultado_bateria(self) -> Optional[ResultadoBateria]:
        if self.escenario_seleccionado is None:
            return None

        return self.escenario_seleccionado.resultado_tecnico

    @property
    def capacidad_bateria_kwh(self) -> float:
        if self.escenario_seleccionado is None:
            return 0.0

        return float(
            self.escenario_seleccionado.capacidad_bateria_kwh
        )

    @property
    def potencia_bateria_kw(self) -> float:
        if self.escenario_seleccionado is None:
            return 0.0

        return float(
            self.escenario_seleccionado.potencia_bateria_kw
        )

    @property
    def capex_bateria_l(self) -> float:
        if self.escenario_seleccionado is None:
            return 0.0

        return float(
            self.escenario_seleccionado.capex_bateria_l
        )

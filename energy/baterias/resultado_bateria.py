# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ResultadoBateria:
    ok: bool
    errores: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # ======================================================
    # CONFIGURACIÓN / RESULTADO TÉCNICO DE BATERÍA
    # ======================================================
    capacidad_util_kwh: float = 0.0
    potencia_max_kw: float = 0.0
    costo_usd_kwh: float = 0.0
    capex_bateria_usd: float = 0.0
    capex_bateria_lps: float = 0.0
    vida_util_anios: int = 0

    demanda_24h_kwh: List[float] = field(default_factory=list)
    fv_24h_kwh: List[float] = field(default_factory=list)

    compra_red_sin_bateria_24h: List[float] = field(default_factory=list)
    compra_red_con_bateria_24h: List[float] = field(default_factory=list)

    excedente_sin_bateria_24h: List[float] = field(default_factory=list)
    excedente_con_bateria_24h: List[float] = field(default_factory=list)

    carga_bateria_24h: List[float] = field(default_factory=list)
    descarga_bateria_24h: List[float] = field(default_factory=list)
    soc_24h_pct: List[float] = field(default_factory=list)

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

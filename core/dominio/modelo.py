from __future__ import annotations

"""
MODELO DE ENTRADA — FV ENGINE

Reglas:
- Una sola fuente de verdad para Datosproyecto
- Tipado fuerte en el contenedor
- Campos dinámicos controlados como dict
- Sin duplicaciones
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


# =========================================================
# DATOS DEL PROYECTO (ENTRADA ÚNICA DEL SISTEMA)
# =========================================================

@dataclass
class Datosproyecto:

    # -------------------------------
    # Información general
    # -------------------------------
    cliente: str
    ubicacion: str

    lat: float
    lon: float

    # -------------------------------
    # Consumo
    # -------------------------------
    consumo_12m: List[float]

    tarifa_energia: float
    cargos_fijos: float

    # -------------------------------
    # Producción FV
    # -------------------------------
    prod_base_kwh_kwp_mes: List[float]
    factores_fv_12m: List[float]

    cobertura_objetivo: float

    # -------------------------------
    # Costos
    # -------------------------------
    costo_usd_kwp: float
    tcambio: float

    # -------------------------------
    # Financiamiento
    # -------------------------------
    tasa_anual: float
    plazo_anios: int
    porcentaje_financiado: float

    # -------------------------------
    # O&M
    # -------------------------------
    om_anual_pct: float = 0.0

    # =====================================================
    # CAMPOS DEL PIPELINE (DICT CONTROLADO)
    # =====================================================

    # 🔥 Sistema FV (modo, valor, zonas, etc.)
    sistema_fv: Dict[str, Any] = field(default_factory=dict)

    # 🔥 Equipos (panel_id, inversor_id, etc.)
    equipos: Dict[str, Any] = field(default_factory=dict)

    # 🔥 Eléctrico (vac, fases, distancias, etc.)
    electrico: Dict[str, Any] = field(default_factory=dict)

    # =====================================================
    # HELPERS (opcional pero útil)
    # =====================================================

    def validar_minimo(self) -> None:
        """
        Validación mínima antes de entrar al orquestador.
        Lanza excepción si algo crítico falta.
        """

        if not self.equipos:
            raise ValueError("equipos no definido")

        if not self.sistema_fv:
            raise ValueError("sistema_fv no definido")

        if self.lat == 0 and self.lon == 0:
            raise ValueError("lat/lon inválidos (0,0)")

        if "panel_id" not in self.equipos:
            raise ValueError("panel_id no definido en equipos")

        if "inversor_id" not in self.equipos:
            raise ValueError("inversor_id no definido en equipos")

        modo = self.sistema_fv.get("modo")

        if not modo:
            raise ValueError("modo no definido en sistema_fv")

        if modo in ["cobertura", "offset"]:
            if self.sistema_fv.get("valor") is None:
                raise ValueError("valor no definido para modo cobertura/offset")

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

    errores = []

    # =====================================================
    # BASE
    # =====================================================
    if not self.equipos:
        errores.append("equipos no definido")

    if not self.sistema_fv:
        errores.append("sistema_fv no definido")

    if self.lat == 0 and self.lon == 0:
        errores.append("lat/lon inválidos (0,0)")

    if "panel_id" not in self.equipos:
        errores.append("panel_id no definido en equipos")

    if "inversor_id" not in self.equipos:
        errores.append("inversor_id no definido en equipos")

    modo = self.sistema_fv.get("modo")

    if not modo:
        errores.append("modo no definido en sistema_fv")

    if modo in ["cobertura", "offset"]:
        if self.sistema_fv.get("valor") is None:
            errores.append("valor no definido para modo cobertura/offset")

    # =====================================================
    # CONSUMO
    # =====================================================
    if not self.consumo_12m or len(self.consumo_12m) != 12:
        errores.append("consumo_12m inválido")

    elif sum(self.consumo_12m) <= 0:
        errores.append("consumo anual inválido (todo en cero)")

    # =====================================================
    # PRODUCCIÓN
    # =====================================================
    if not self.prod_base_kwh_kwp_mes or len(self.prod_base_kwh_kwp_mes) != 12:
        errores.append("prod_base_kwh_kwp_mes inválido")

    elif sum(self.prod_base_kwh_kwp_mes) <= 0:
        errores.append("producción base FV inválida (todo en cero)")

    # =====================================================
    # FACTORES FV
    # =====================================================
    if not self.factores_fv_12m or len(self.factores_fv_12m) != 12:
        errores.append("factores_fv_12m inválido")

    # =====================================================
    # ZONAS
    # =====================================================
    if modo == "multizona":

        zonas = self.sistema_fv.get("zonas", [])

        if not zonas:
            errores.append("modo multizona sin zonas")

        for i, z in enumerate(zonas):

            n_paneles = z.get("n_paneles")
            area = z.get("area")

            if (n_paneles is None or n_paneles <= 0) and (area is None or area <= 0):
                errores.append(f"Zona {i+1}: sin paneles ni área válida")

    # =====================================================
    # ELÉCTRICO
    # =====================================================
    if not self.electrico:
        errores.append("electrico no definido")

    else:
        vac = self.electrico.get("vac", 0)

        if vac <= 0:
            errores.append("Voltaje AC inválido")

        fases = self.electrico.get("fases", 0)

        if fases not in [1, 2, 3]:
            errores.append("Número de fases inválido")

    # =====================================================
    # FINAL
    # =====================================================
    if errores:
        raise ValueError(" | ".join(errores))

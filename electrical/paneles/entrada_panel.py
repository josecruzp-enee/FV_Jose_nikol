from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO PANELES

Define la estructura de datos que recibe el dominio paneles.

Reglas:
- Este módulo NO contiene lógica de cálculo
- Solo define el contrato de entrada
- Es inmutable (frozen=True)
- Valida consistencia mínima

Consumido por:
    electrical.paneles.orquestador_paneles
"""

from dataclasses import dataclass
from typing import Optional

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# ENTRADA DEL DOMINIO PANELES
# ==========================================================

@dataclass(frozen=True)
class EntradaPaneles:

    # ------------------------------------------------------
    # Equipos
    # ------------------------------------------------------
    panel: PanelSpec
    inversor: InversorSpec

    # ------------------------------------------------------
    # Sistema
    # ------------------------------------------------------
    n_paneles_total: int
    n_inversores: Optional[int] = None

    # ------------------------------------------------------
    # Condiciones térmicas
    # ------------------------------------------------------
    t_min_c: float = -5.0
    t_oper_c: float = 45.0

    # ------------------------------------------------------
    # Instalación
    # ------------------------------------------------------
    dos_aguas: bool = False

    # ------------------------------------------------------
    # Objetivos de diseño
    # ------------------------------------------------------
    objetivo_dc_ac: Optional[float] = None
    pdc_kw_objetivo: Optional[float] = None

    # ======================================================
    # VALIDACIÓN BÁSICA (CRÍTICA)
    # ======================================================

    def __post_init__(self):

        errores = []

        # -------------------------
        # Validaciones numéricas
        # -------------------------
        if self.n_paneles_total <= 0:
            errores.append("n_paneles_total debe ser > 0")

        if self.n_inversores is not None and self.n_inversores <= 0:
            errores.append("n_inversores debe ser > 0")

        # -------------------------
        # Temperaturas
        # -------------------------
        if self.t_min_c > self.t_oper_c:
            errores.append("t_min_c no puede ser mayor que t_oper_c")

        # -------------------------
        # Objetivos incompatibles
        # -------------------------
        if self.objetivo_dc_ac is not None and self.pdc_kw_objetivo is not None:
            errores.append("No puedes definir objetivo_dc_ac y pdc_kw_objetivo al mismo tiempo")

        # -------------------------
        # Resultado
        # -------------------------
        if errores:
            raise ValueError(f"EntradaPaneles inválida: {errores}")

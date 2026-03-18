from __future__ import annotations

"""
CONTRATO DEL DOMINIO ENERGÍA — FV Engine
========================================

Define las estructuras de entrada y salida del motor energético.

Soporta:

    1) Modelo mensual (HSP)
    2) Modelo físico horario (8760)

Este módulo NO contiene lógica de cálculo.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional


# ==========================================================
# (OPCIONAL) TIPO FUERTE PARA CLIMA
# ==========================================================
# 👉 Reemplaza esto cuando tengas contrato real de clima
ResultadoClima = object


# ==========================================================
# ENTRADA DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:

    # ------------------------------------------------------
    # POTENCIA
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float

    # ------------------------------------------------------
    # MODO
    # ------------------------------------------------------

    modo_simulacion: Literal["mensual", "8760"] = "8760"

    # ------------------------------------------------------
    # HSP (MODELO MENSUAL)
    # ------------------------------------------------------

    hsp_12m: Optional[List[float]] = None
    dias_mes: Optional[List[int]] = None

    # ------------------------------------------------------
    # ORIENTACIÓN
    # ------------------------------------------------------

    tipo_superficie: Optional[str] = None
    azimut_deg: Optional[float] = None
    azimut_a_deg: Optional[float] = None
    azimut_b_deg: Optional[float] = None
    reparto_pct_a: Optional[float] = None
    hemisferio: Optional[str] = None

    # ------------------------------------------------------
    # 8760 (MODELO FÍSICO)
    # ------------------------------------------------------

    tilt_deg: Optional[float] = None
    clima: Optional[ResultadoClima] = None

    # ------------------------------------------------------
    # ARREGLO FV (8760)
    # ------------------------------------------------------

    paneles_por_string: Optional[int] = None
    n_strings_total: Optional[int] = None

    pmax_stc_w: Optional[float] = None
    vmp_stc_v: Optional[float] = None
    voc_stc_v: Optional[float] = None

    coef_pmax_pct_per_c: Optional[float] = None
    coef_voc_pct_per_c: Optional[float] = None
    coef_vmp_pct_per_c: Optional[float] = None

    # ------------------------------------------------------
    # PÉRDIDAS
    # ------------------------------------------------------

    perdidas_dc_pct: float = 0.0
    perdidas_ac_pct: float = 0.0
    sombras_pct: float = 0.0

    # ------------------------------------------------------
    # INVERSOR
    # ------------------------------------------------------

    eficiencia_inversor: float = 0.97
    permitir_clipping: bool = True

    # ------------------------------------------------------
    # AMBIENTE
    # ------------------------------------------------------

    latitud: Optional[float] = None
    longitud: Optional[float] = None
    temp_ambiente_c: float = 25.0

    # ======================================================
    # VALIDACIÓN DEL CONTRATO
    # ======================================================

    def validar(self) -> List[str]:

        errores: List[str] = []

        modo = str(self.modo_simulacion).strip().lower()

        # -------------------------------
        # VALIDACIONES GENERALES
        # -------------------------------

        if self.pdc_instalada_kw <= 0:
            errores.append("pdc_instalada_kw debe ser > 0")

        if self.pac_nominal_kw <= 0:
            errores.append("pac_nominal_kw debe ser > 0")

        # -------------------------------
        # MODO MENSUAL (HSP)
        # -------------------------------

        if modo == "mensual":

            if not self.hsp_12m:
                errores.append("hsp_12m requerido para modo mensual")

            if not self.dias_mes:
                errores.append("dias_mes requerido para modo mensual")

        # -------------------------------
        # MODO 8760
        # -------------------------------

        if modo == "8760":

            if self.clima is None:
                errores.append("clima requerido para 8760")

            if self.tilt_deg is None:
                errores.append("tilt_deg requerido para 8760")

            if self.paneles_por_string is None:
                errores.append("paneles_por_string requerido")

            if self.n_strings_total is None:
                errores.append("n_strings_total requerido")

            if self.pmax_stc_w is None:
                errores.append("pmax_stc_w requerido")

            if self.vmp_stc_v is None:
                errores.append("vmp_stc_v requerido")

            if self.voc_stc_v is None:
                errores.append("voc_stc_v requerido")

        # -------------------------------
        # MODO INVÁLIDO
        # -------------------------------

        if modo not in ("mensual", "8760"):
            errores.append(f"modo_simulacion inválido: {modo}")

        return errores


# ==========================================================
# RESULTADO DEL MOTOR ENERGÉTICO
# ==========================================================

@dataclass(frozen=True)
class EnergiaResultado:

    # ------------------------------------------------------
    # ESTADO
    # ------------------------------------------------------

    ok: bool
    errores: List[str]

    # ------------------------------------------------------
    # POTENCIA
    # ------------------------------------------------------

    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    # ------------------------------------------------------
    # ENERGÍA MENSUAL
    # ------------------------------------------------------

    energia_bruta_12m: List[float]
    energia_perdidas_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_clipping_12m: List[float]
    energia_util_12m: List[float]

    # ------------------------------------------------------
    # ENERGÍA ANUAL
    # ------------------------------------------------------

    energia_bruta_anual: float
    energia_perdidas_anual: float
    energia_despues_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float

    # ------------------------------------------------------
    # METADATA
    # ------------------------------------------------------

    meta: Dict[str, object] = field(default_factory=dict)


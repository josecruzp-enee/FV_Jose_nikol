from dataclasses import dataclass
from typing import List, Dict, Any


# ======================================================
# INPUT
# ======================================================

@dataclass
class EnergiaInput:
    n_series: int
    n_strings: int
    pdc_kw: float

    panel: any
    pac_nominal_kw: float

    clima: any

    tilt_deg: float
    azimut_deg: float

    # 🔥 CAMBIO AQUÍ
    perdidas_dc_frac: float
    sombras_frac: float
    eficiencia_inversor: float
    perdidas_ac_frac: float

    def validar(self):
        errores = []

        # -----------------------------------------
        # CLIMA (CRÍTICO)
        # -----------------------------------------
        if self.clima is None:
            errores.append("Clima no definido")

        elif not hasattr(self.clima, "horas") or not self.clima.horas:
            errores.append("Clima sin datos horarios")

        elif len(self.clima.horas) < 8000:
            errores.append("Clima incompleto (no 8760)")

        # -----------------------------------------
        # CONFIGURACIÓN
        # -----------------------------------------
        if self.pdc_kw <= 0:
            errores.append("pdc_kw inválido")

        if self.pac_nominal_kw <= 0:
            errores.append("pac_nominal_kw inválido")

        if self.n_series <= 0 or self.n_strings <= 0:
            errores.append("Configuración de strings inválida")

        # -----------------------------------------
        # PANEL
        # -----------------------------------------
        if self.panel is None:
            errores.append("Panel no definido")

        # -----------------------------------------
        # GEOMETRÍA
        # -----------------------------------------
        if self.tilt_deg is None or self.azimut_deg is None:
            errores.append("Geometría inválida")

        # -----------------------------------------
        # 🔥 VALIDACIÓN DE FRACCIONES
        # -----------------------------------------
        for nombre, valor in [
            ("perdidas_dc_frac", self.perdidas_dc_frac),
            ("sombras_frac", self.sombras_frac),
            ("perdidas_ac_frac", self.perdidas_ac_frac),
        ]:
            if not (0 <= valor <= 1):
                errores.append(f"{nombre} debe estar entre 0 y 1")

        if not (0 < self.eficiencia_inversor <= 1):
            errores.append("eficiencia_inversor inválida (0–1)")

        return errores


# ======================================================
# RESULTADO
# ======================================================

@dataclass(frozen=True)
class EnergiaResultado:
    ok: bool
    errores: List[str]

    # ======================================================
    # CONFIGURACIÓN DEL SISTEMA
    # ======================================================
    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    # ======================================================
    # ENERGÍA HORARIA (8760)
    # ======================================================
    energia_horaria_kwh: List[float]

    # ======================================================
    # ENERGÍA MENSUAL (kWh)
    # ======================================================
    energia_bruta_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_perdidas_12m: List[float]
    energia_clipping_12m: List[float]
    energia_util_12m: List[float]

    # ======================================================
    # ENERGÍA ANUAL (kWh)
    # ======================================================
    energia_bruta_anual: float
    energia_despues_perdidas_anual: float
    energia_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float

    # ======================================================
    # KPIs
    # ======================================================
    produccion_especifica_kwh_kwp: float
    performance_ratio: float

    # ======================================================
    # TRAZABILIDAD
    # ======================================================
    meta: Dict[str, Any]

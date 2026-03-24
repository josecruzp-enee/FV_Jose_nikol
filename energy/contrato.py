from dataclasses import dataclass
from typing import List, Dict, Any

from dataclasses import dataclass

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

    perdidas_dc_pct: float
    sombras_pct: float
    eficiencia_inversor: float
    perdidas_ac_pct: float

    def validar(self):
    errores = []

    # CLIMA (CRÍTICO)
    if self.clima is None:
        errores.append("Clima no definido")

    elif not hasattr(self.clima, "horas") or not self.clima.horas:
        errores.append("Clima sin datos horarios")

    elif len(self.clima.horas) < 8000:
        errores.append("Clima incompleto (no 8760)")

    # CONFIGURACIÓN
    if self.pdc_kw <= 0:
        errores.append("pdc_kw inválido")

    if self.pac_nominal_kw <= 0:
        errores.append("pac_nominal_kw inválido")

    if self.n_series <= 0 or self.n_strings <= 0:
        errores.append("Configuración de strings inválida")

    # PANEL
    if self.panel is None:
        errores.append("Panel no definido")

    # GEOMETRÍA
    if self.tilt_deg is None or self.azimut_deg is None:
        errores.append("Geometría inválida")

    return errores
        
        
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
    # Siempre en kWh (1 valor = 1 hora integrada)
    # ======================================================
    energia_horaria_kwh: List[float]

    # ======================================================
    # ENERGÍA MENSUAL (kWh)
    # ======================================================

    # Energía DC antes de pérdidas
    energia_bruta_12m: List[float]

    # Energía después de pérdidas DC + AC (ANTES de clipping)
    energia_despues_perdidas_12m: List[float]

    # Pérdidas físicas (DC + AC)
    energia_perdidas_12m: List[float]

    # Pérdidas por clipping del inversor
    energia_clipping_12m: List[float]

    # Energía final útil AC (después de TODO)
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

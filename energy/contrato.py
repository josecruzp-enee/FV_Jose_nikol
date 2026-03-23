from dataclasses import dataclass, field
from typing import List, Dict, Any

# 🔥 IMPORTANTE: tipo fuerte
from energy.clima.resultado_clima import ResultadoClima


# ==========================================================
# INPUT
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:
    paneles: Any                 # ResultadoPaneles
    pac_nominal_kw: float

    # 🔥 FIX REAL
    clima: ResultadoClima

    tilt_deg: float
    azimut_deg: float

    eficiencia_inversor: float = 0.97
    permitir_clipping: bool = True
    perdidas_dc_pct: float = 0.0
    perdidas_ac_pct: float = 0.0
    sombras_pct: float = 0.0

    def validar(self) -> List[str]:
        errores: List[str] = []

        # --------------------------------------------------
        # PANELes
        # --------------------------------------------------
        if self.paneles is None:
            errores.append("paneles requerido")
        else:
            if not getattr(self.paneles, "ok", False):
                errores.append("paneles no válido")
            if not hasattr(self.paneles, "array"):
                errores.append("paneles sin atributo array")

        # --------------------------------------------------
        # POTENCIA
        # --------------------------------------------------
        if self.pac_nominal_kw <= 0:
            errores.append("pac_nominal_kw inválido")

        # --------------------------------------------------
        # GEOMETRÍA
        # --------------------------------------------------
        if self.tilt_deg is None:
            errores.append("tilt_deg requerido")

        if self.azimut_deg is None:
            errores.append("azimut_deg requerido")

        # --------------------------------------------------
        # CLIMA (🔥 FIX IMPORTANTE)
        # --------------------------------------------------
        if self.clima is None:
            errores.append("clima requerido")
        else:
            # ✔ estructura mínima obligatoria
            if not hasattr(self.clima, "horas"):
                errores.append("clima inválido: falta 'horas'")
            else:
                if not self.clima.horas:
                    errores.append("clima vacío")
                elif len(self.clima.horas) != 8760:
                    errores.append("clima no tiene 8760 horas")

        return errores


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass
class EnergiaResultado:
    ok: bool
    errores: List[str]

    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    energia_bruta_12m: List[float]
    energia_perdidas_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_clipping_12m: List[float]
    energia_util_12m: List[float]

    energia_bruta_anual: float
    energia_perdidas_anual: float
    energia_despues_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float

    # ---- defaults SIEMPRE al final ----
    energia_horaria_kwh: List[float] = field(default_factory=list)
    produccion_especifica_kwh_kwp: float = 0.0
    performance_ratio: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)

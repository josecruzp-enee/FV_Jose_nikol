from dataclasses import dataclass, field
from typing import List, Dict, Any

from energy.clima.resultado_clima import ResultadoClima
from electrical.modelos.paneles import PanelSpec


# ==========================================================
# INPUT
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:

    # -------------------------------
    # CONFIGURACIÓN DEL ARREGLO
    # -------------------------------
    n_series: int
    n_strings: int
    pdc_kw: float

    # -------------------------------
    # PANEL (MODELO FÍSICO)
    # -------------------------------
    panel: PanelSpec

    # -------------------------------
    # INVERSOR
    # -------------------------------
    pac_nominal_kw: float

    # -------------------------------
    # CLIMA
    # -------------------------------
    clima: ResultadoClima

    # -------------------------------
    # GEOMETRÍA
    # -------------------------------
    tilt_deg: float
    azimut_deg: float

    # -------------------------------
    # PARÁMETROS
    # -------------------------------
    eficiencia_inversor: float = 0.97
    permitir_clipping: bool = True

    perdidas_dc_pct: float = 0.02
    perdidas_ac_pct: float = 0.01
    sombras_pct: float = 0.0


    # ==================================================
    # VALIDACIÓN
    # ==================================================
    def validar(self) -> List[str]:

        errores: List[str] = []

        if self.n_series <= 0:
            errores.append("n_series inválido")

        if self.n_strings <= 0:
            errores.append("n_strings inválido")

        if self.pdc_kw <= 0:
            errores.append("pdc_kw inválido")

        if self.panel is None:
            errores.append("panel requerido")

        if self.pac_nominal_kw <= 0:
            errores.append("pac_nominal_kw inválido")

        if self.tilt_deg is None:
            errores.append("tilt_deg requerido")

        if self.azimut_deg is None:
            errores.append("azimut_deg requerido")

        if self.clima is None:
            errores.append("clima requerido")
        else:
            horas = getattr(self.clima, "horas", None)

            if horas is None:
                errores.append("clima inválido")
            elif len(horas) != 8760:
                errores.append("clima debe tener 8760 horas")

        if not (0 <= self.eficiencia_inversor <= 1):
            errores.append("eficiencia_inversor fuera de rango")

        for nombre, valor in {
            "perdidas_dc_pct": self.perdidas_dc_pct,
            "perdidas_ac_pct": self.perdidas_ac_pct,
            "sombras_pct": self.sombras_pct,
        }.items():
            if not (0 <= valor <= 1):
                errores.append(f"{nombre} fuera de rango (0–1)")

        return errores

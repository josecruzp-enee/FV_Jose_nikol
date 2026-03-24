from dataclasses import dataclass, field
from typing import List, Dict, Any

from energy.clima.resultado_clima import ResultadoClima


# ==========================================================
# INPUT
# ==========================================================

@dataclass(frozen=True)
class EnergiaInput:
    """
    Entrada oficial del motor energético FV (8760).

    Este contrato define TODO lo necesario para simular
    la generación real de un sistema fotovoltaico.

    Responsabilidades:
    ------------------
    ✔ Recibe configuración eléctrica (paneles)
    ✔ Recibe modelo físico (panel catálogo)
    ✔ Recibe clima (8760)
    ✔ Define parámetros de sistema (pérdidas, inversor)
    """

    # --------------------------------------------------
    # CONFIGURACIÓN (DESDE ELECTRICAL)
    # --------------------------------------------------
    paneles: Any   # ResultadoPaneles

    # --------------------------------------------------
    # PANEL (CATÁLOGO - MODELO FÍSICO)
    # --------------------------------------------------
    panel: Any     # PanelSpec

    # --------------------------------------------------
    # INVERSOR
    # --------------------------------------------------
    pac_nominal_kw: float

    # --------------------------------------------------
    # CLIMA
    # --------------------------------------------------
    clima: ResultadoClima

    # --------------------------------------------------
    # GEOMETRÍA DEL SISTEMA
    # --------------------------------------------------
    tilt_deg: float
    azimut_deg: float

    # --------------------------------------------------
    # PARÁMETROS DEL SISTEMA
    # --------------------------------------------------
    eficiencia_inversor: float = 0.97
    permitir_clipping: bool = True

    perdidas_dc_pct: float = 0.02
    perdidas_ac_pct: float = 0.01
    sombras_pct: float = 0.0


    # ==================================================
    # VALIDACIÓN
    # ==================================================
    def validar(self) -> List[str]:
        """
        Valida la consistencia mínima del input.
        NO valida física, solo estructura.
        """

        errores: List[str] = []

        # -----------------------------
        # PANELes (configuración)
        # -----------------------------
        if self.paneles is None:
            errores.append("paneles requerido")
        else:
            if not getattr(self.paneles, "ok", False):
                errores.append("paneles no válido")

            if not hasattr(self.paneles, "array"):
                errores.append("paneles sin atributo array")

        # -----------------------------
        # PANEL (catálogo)
        # -----------------------------
        if self.panel is None:
            errores.append("panel requerido")

        # -----------------------------
        # POTENCIA AC
        # -----------------------------
        if self.pac_nominal_kw <= 0:
            errores.append("pac_nominal_kw inválido")

        # -----------------------------
        # GEOMETRÍA
        # -----------------------------
        if self.tilt_deg is None:
            errores.append("tilt_deg requerido")

        if self.azimut_deg is None:
            errores.append("azimut_deg requerido")

        # -----------------------------
        # CLIMA
        # -----------------------------
        if self.clima is None:
            errores.append("clima requerido")
        else:
            horas = getattr(self.clima, "horas", None)

            if horas is None:
                errores.append("clima inválido: falta 'horas'")
            elif not horas:
                errores.append("clima vacío")
            elif len(horas) != 8760:
                errores.append("clima no tiene 8760 horas")

        # -----------------------------
        # RANGOS
        # -----------------------------
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


# ==========================================================
# RESULTADO
# ==========================================================

@dataclass
class EnergiaResultado:
    """
    Resultado oficial del motor energético FV.

    Representa la simulación completa del sistema.
    """

    # --------------------------------------------------
    # ESTADO
    # --------------------------------------------------
    ok: bool
    errores: List[str]

    # --------------------------------------------------
    # POTENCIAS
    # --------------------------------------------------
    pdc_instalada_kw: float
    pac_nominal_kw: float
    dc_ac_ratio: float

    # --------------------------------------------------
    # ENERGÍA MENSUAL (kWh)
    # --------------------------------------------------
    energia_bruta_12m: List[float]
    energia_perdidas_12m: List[float]
    energia_despues_perdidas_12m: List[float]
    energia_clipping_12m: List[float]
    energia_util_12m: List[float]

    # --------------------------------------------------
    # ENERGÍA ANUAL (kWh)
    # --------------------------------------------------
    energia_bruta_anual: float
    energia_perdidas_anual: float
    energia_despues_perdidas_anual: float
    energia_clipping_anual: float
    energia_util_anual: float

    # --------------------------------------------------
    # DETALLE HORARIO
    # --------------------------------------------------
    energia_horaria_kwh: List[float] = field(default_factory=list)

    # --------------------------------------------------
    # KPIs
    # --------------------------------------------------
    produccion_especifica_kwh_kwp: float = 0.0
    performance_ratio: float = 0.0

    # --------------------------------------------------
    # METADATA
    # --------------------------------------------------
    meta: Dict[str, Any] = field(default_factory=dict)

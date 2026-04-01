from dataclasses import dataclass
from typing import Optional, Literal, List

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# ZONA FV (FUERTE)
# ==========================================================
@dataclass(frozen=True)
class ZonaFV:
    n_paneles: int
    azimut: float = 180.0
    inclinacion: float = 15.0


# ==========================================================
# ENTRADA PANELES (FUERTE)
# ==========================================================
@dataclass(frozen=True)
class EntradaPaneles:

    # ===============================
    # ESPECIFICACIONES (OBLIGATORIO)
    # ===============================
    panel: PanelSpec
    inversor: InversorSpec

    # ===============================
    # CONTROL DE FLUJO (OBLIGATORIO)
    # ===============================
    modo: Literal[
        "manual",
        "consumo",
        "area",
        "kw_objetivo",
        "multizona"
    ]

    # ===============================
    # CONFIGURACIÓN BASE
    # ===============================
    n_paneles_total: Optional[int] = None
    n_inversores: int = 1  # 🔥 default fuerte (no None)

    # ===============================
    # MULTIZONA
    # ===============================
    zonas: Optional[List[ZonaFV]] = None

    # ===============================
    # OBJETIVOS
    # ===============================
    objetivo_dc_ac: Optional[float] = None
    pdc_kw_objetivo: Optional[float] = None

    # ===============================
    # CONDICIONES TÉRMICAS
    # ===============================
    t_min_c: float = 25.0
    t_oper_c: float = 55.0

    # ===============================
    # TOPOLOGÍA
    # ===============================
    dos_aguas: bool = False

    # ======================================================
    # VALIDACIÓN INTERNA (CLAVE 🔥)
    # ======================================================
    def __post_init__(self):

    # ======================================================
    # VALIDACIÓN MULTIZONA
    # ======================================================
    if self.modo == "multizona":

        if not self.zonas or len(self.zonas) == 0:
            raise ValueError("Modo multizona requiere zonas válidas")

    # ======================================================
    # VALIDACIÓN MODOS NORMALES
    # ======================================================
    else:

        # 🔥 SOLO exigir paneles en modo manual
        if self.modo == "manual":

            if self.n_paneles_total is None or self.n_paneles_total <= 0:
                raise ValueError("n_paneles_total requerido en modo manual")

        # 🔥 EN OTROS MODOS:
        # consumo / area / kw_objetivo
        # → se permite n_paneles_total = None
        # → paneles se dimensiona automáticamente

    # ======================================================
    # VALIDACIÓN INVERSORES
    # ======================================================
    if self.n_inversores <= 0:
        raise ValueError("n_inversores debe ser >= 1")

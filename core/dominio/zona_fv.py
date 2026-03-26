from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ZonaFV:
    nombre: str

    # modo de dimensionamiento
    modo: str  # "consumo" | "area" | "manual"

    # parámetros
    area_m2: Optional[float] = None
    paneles_manual: Optional[int] = None
    cobertura_pct: Optional[float] = None

    # selección de panel
    panel_id: str = ""

    # opcional (futuro)
    inclinacion: Optional[float] = None
    orientacion: Optional[float] = None

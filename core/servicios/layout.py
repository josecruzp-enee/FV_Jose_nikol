from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt
from typing import Optional


AREA_PANEL_DEFAULT_M2 = 2.60
FACTOR_OCUPACION_DEFAULT = 0.75


@dataclass(frozen=True)
class AreaSistemaFV:
    n_paneles: int
    area_panel_m2: float
    area_bruta_m2: float
    factor_ocupacion: float
    area_necesaria_m2: float


@dataclass(frozen=True)
class LayoutCuadriculaFV:
    n_paneles: int
    filas: int
    columnas: int
    paneles_colocados: int
    paneles_sobrantes: int
    ancho_total_m: float
    largo_total_m: float
    area_rectangular_m2: float
    largo_panel_m: float
    ancho_panel_m: float
    separacion_x_m: float
    separacion_y_m: float


def calcular_area_sistema_fv(
    *,
    n_paneles: int,
    largo_panel_m: Optional[float] = None,
    ancho_panel_m: Optional[float] = None,
    factor_ocupacion: float = FACTOR_OCUPACION_DEFAULT,
) -> AreaSistemaFV:
    """
    Calcula el área física aproximada requerida para un sistema FV.

    No considera sombras, obstáculos, orientación real ni estructura.
    """

    if n_paneles <= 0:
        raise ValueError("n_paneles debe ser mayor que cero.")

    if factor_ocupacion <= 0 or factor_ocupacion > 1:
        raise ValueError("factor_ocupacion debe estar entre 0 y 1.")

    if largo_panel_m and ancho_panel_m and largo_panel_m > 0 and ancho_panel_m > 0:
        area_panel_m2 = largo_panel_m * ancho_panel_m
    else:
        area_panel_m2 = AREA_PANEL_DEFAULT_M2

    area_bruta_m2 = n_paneles * area_panel_m2
    area_necesaria_m2 = area_bruta_m2 / factor_ocupacion

    return AreaSistemaFV(
        n_paneles=n_paneles,
        area_panel_m2=round(area_panel_m2, 3),
        area_bruta_m2=round(area_bruta_m2, 2),
        factor_ocupacion=round(factor_ocupacion, 3),
        area_necesaria_m2=round(area_necesaria_m2, 2),
    )


def generar_layout_cuadricula_fv(
    *,
    n_paneles: int,
    largo_panel_m: Optional[float] = None,
    ancho_panel_m: Optional[float] = None,
    separacion_x_m: float = 0.20,
    separacion_y_m: float = 0.40,
    max_columnas: Optional[int] = None,
) -> LayoutCuadriculaFV:
    """
    Genera un layout rectangular preliminar en cuadrícula.

    No considera obstáculos, sombras, orientación real ni cálculo estructural.
    """

    if n_paneles <= 0:
        raise ValueError("n_paneles debe ser mayor que cero.")

    largo = largo_panel_m if largo_panel_m and largo_panel_m > 0 else 2.20
    ancho = ancho_panel_m if ancho_panel_m and ancho_panel_m > 0 else 1.18

    if separacion_x_m < 0:
        raise ValueError("separacion_x_m no puede ser negativa.")

    if separacion_y_m < 0:
        raise ValueError("separacion_y_m no puede ser negativa.")

    if max_columnas is not None and max_columnas <= 0:
        raise ValueError("max_columnas debe ser mayor que cero.")

    columnas = max_columnas if max_columnas else ceil(sqrt(n_paneles))
    columnas = min(columnas, n_paneles)

    filas = ceil(n_paneles / columnas)

    capacidad_cuadricula = filas * columnas
    paneles_sobrantes = capacidad_cuadricula - n_paneles

    ancho_total_m = columnas * ancho + max(columnas - 1, 0) * separacion_x_m
    largo_total_m = filas * largo + max(filas - 1, 0) * separacion_y_m
    area_rectangular_m2 = ancho_total_m * largo_total_m

    return LayoutCuadriculaFV(
        n_paneles=n_paneles,
        filas=filas,
        columnas=columnas,
        paneles_colocados=n_paneles,
        paneles_sobrantes=paneles_sobrantes,
        ancho_total_m=round(ancho_total_m, 2),
        largo_total_m=round(largo_total_m, 2),
        area_rectangular_m2=round(area_rectangular_m2, 2),
        largo_panel_m=round(largo, 3),
        ancho_panel_m=round(ancho, 3),
        separacion_x_m=round(separacion_x_m, 3),
        separacion_y_m=round(separacion_y_m, 3),
    )

def construir_layout_preliminar_fv(
    *,
    n_paneles: int,
    largo_panel_m: Optional[float] = None,
    ancho_panel_m: Optional[float] = None,
    factor_ocupacion: float = FACTOR_OCUPACION_DEFAULT,
    separacion_x_m: float = 0.20,
    separacion_y_m: float = 0.40,
    max_columnas: Optional[int] = None,
) -> dict:
    """
    Devuelve el paquete informativo completo de área + layout preliminar.

    Regla actual:
    - El área principal debe venir del layout geométrico real.
    - El cálculo por factor de ocupación queda solo como referencia/fallback.
    """

    layout = generar_layout_cuadricula_fv(
        n_paneles=n_paneles,
        largo_panel_m=largo_panel_m,
        ancho_panel_m=ancho_panel_m,
        separacion_x_m=separacion_x_m,
        separacion_y_m=separacion_y_m,
        max_columnas=max_columnas,
    )

    area_fallback = calcular_area_sistema_fv(
        n_paneles=n_paneles,
        largo_panel_m=largo_panel_m,
        ancho_panel_m=ancho_panel_m,
        factor_ocupacion=factor_ocupacion,
    )

    area_real_m2 = float(getattr(layout, "area_rectangular_m2", 0.0) or 0.0)

    return {
        "area": area_fallback,
        "layout": layout,

        # Campo nuevo principal
        "area_real_m2": round(area_real_m2, 2),
        "area_layout_real_m2": round(area_real_m2, 2),
        "area_necesaria_m2": round(area_real_m2, 2),

        # Campo viejo queda como referencia
        "area_fallback_m2": float(getattr(area_fallback, "area_necesaria_m2", 0.0) or 0.0),
        "factor_ocupacion_fallback": float(getattr(area_fallback, "factor_ocupacion", 0.0) or 0.0),

        "nota": (
            "Layout preliminar informativo. El área reportada corresponde al "
            "rectángulo geométrico generado por filas, columnas y separaciones. "
            "No considera obstáculos, sombras reales, orientación final ni verificación estructural."
        ),
    }

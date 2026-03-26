from typing import List, Any
from core.dominio.zona_fv import ZonaFV


def extraer_zonas(datos: Any) -> List[ZonaFV]:
    """
    Devuelve lista de zonas desde objeto DatosProyecto.

    ✔ Multizona
    ✔ Fallback a zona única
    """

    # ------------------------------------------------------
    # MULTIZONA
    # ------------------------------------------------------
    if getattr(datos, "zonas", None):

        zonas = []

        for z in datos.zonas:

            zonas.append(
                ZonaFV(
                    nombre=getattr(z, "nombre", "Zona"),
                    modo=getattr(z, "modo", "consumo"),
                    area_m2=getattr(z, "area", None),
                    paneles_manual=getattr(z, "n_paneles", None),
                    cobertura_pct=getattr(z, "cobertura_pct", None),
                    panel_id=getattr(z, "panel_id", ""),
                    inclinacion=getattr(z, "inclinacion", None),
                    orientacion=getattr(z, "azimut", None),
                )
            )

        return zonas

    # ------------------------------------------------------
    # LEGACY (1 zona)
    # ------------------------------------------------------
    return [
        ZonaFV(
            nombre="Zona única",
            modo=getattr(datos, "modo_dimensionado", "consumo"),
            area_m2=getattr(datos, "area_m2", None),
            paneles_manual=getattr(datos, "n_paneles", None),
            cobertura_pct=getattr(datos, "cobertura_pct", None),
            panel_id=getattr(datos, "panel_id", ""),
        )
    ]

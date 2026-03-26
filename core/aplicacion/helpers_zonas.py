from typing import List, Any
from core.dominio.zona_fv import ZonaFV


def extraer_zonas(datos: Any) -> List[ZonaFV]:
    """
    Devuelve lista de zonas.
    
    ✔ Si no hay zonas → crea una zona única (compatibilidad)
    ✔ Si hay zonas → las normaliza
    """

    # -----------------------------
    # CASO MULTIZONA
    # -----------------------------
    if isinstance(datos, dict) and "zonas" in datos:

        zonas = []

        for z in datos["zonas"]:

            zonas.append(
                ZonaFV(
                    nombre=z.get("nombre", "Zona"),
                    modo=z.get("modo", "consumo"),
                    area_m2=z.get("area_m2"),
                    paneles_manual=z.get("paneles_manual"),
                    cobertura_pct=z.get("cobertura_pct"),
                    panel_id=z.get("panel_id", ""),
                    inclinacion=z.get("inclinacion"),
                    orientacion=z.get("orientacion"),
                )
            )

        return zonas

    # -----------------------------
    # CASO LEGACY (1 zona)
    # -----------------------------
    return [
        ZonaFV(
            nombre="Zona única",
            modo=datos.get("modo_dimensionado", "consumo"),
            area_m2=datos.get("area_m2"),
            paneles_manual=datos.get("n_paneles"),
            cobertura_pct=datos.get("cobertura_pct"),
            panel_id=datos.get("panel_id", ""),
        )
    ]

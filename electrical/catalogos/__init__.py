"""
API pública del dominio catalogos.

FRONTERA DEL PAQUETE
====================

Entrada:
    - data/paneles.yaml
    - data/inversores.yaml

Salida hacia el motor eléctrico:
    - PanelSpec
    - InversorSpec

API pública expuesta:
    get_panel()
    get_inversor()

    ids_paneles()
    ids_inversores()

    catalogo_paneles()      ← usado por UI
    catalogo_inversores()   ← usado por UI

Consumido por:
    core.servicios.sizing
    electrical.paneles
    electrical.inversor
"""

from .catalogos import (
    get_panel,
    get_inversor,
    ids_paneles,
    ids_inversores,
    catalogo_paneles,
    catalogo_inversores,
)

__all__ = [
    "get_panel",
    "get_inversor",
    "ids_paneles",
    "ids_inversores",
    "catalogo_paneles",
    "catalogo_inversores",
]

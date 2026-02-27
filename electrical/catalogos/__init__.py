# API pública del dominio catalogos

from .modelos import Panel, Inversor

from .catalogos import (
    get_panel,
    get_inversor,
    ids_paneles,
    ids_inversores,
    catalogo_paneles,
    catalogo_inversores,
)

__all__ = [
    # modelos
    "Panel",
    "Inversor",

    # funciones catálogo
    "get_panel",
    "get_inversor",
    "ids_paneles",
    "ids_inversores",
    "catalogo_paneles",
    "catalogo_inversores",
]

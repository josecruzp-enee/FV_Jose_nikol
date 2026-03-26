from typing import List, Any

from electrical.paneles.adapter_multizona import expandir_paneles


def construir_strings_globales(paneles) -> List[Any]:
    """
    Extrae TODOS los strings de todas las zonas.

    ❗ No recalcula
    ❗ No mezcla
    ❗ Solo consolida
    """

    paneles_lista = expandir_paneles(paneles)

    strings_global = []

    for p in paneles_lista:

        if not hasattr(p, "strings"):
            raise ValueError("ResultadoPaneles sin atributo strings")

        for s in p.strings:
            strings_global.append(s)

    if not strings_global:
        raise ValueError("No se generaron strings")

    return strings_global

from typing import List, Union

from electrical.paneles.resultado_paneles import ResultadoPaneles, StringFV


def consolidar_strings(paneles: Union[ResultadoPaneles, List[ResultadoPaneles]]) -> List[StringFV]:
    """
    Consolida strings de múltiples zonas.

    ✔ Dominio eléctrico
    ✔ No recalcula
    ✔ No rompe paneles
    """

    if not isinstance(paneles, list):
        return paneles.strings

    strings_global: List[StringFV] = []

    for zona in paneles:

        if not zona.ok:
            raise ValueError("Zona inválida en paneles")

        strings_global.extend(zona.strings)

    if not strings_global:
        raise ValueError("No hay strings")

    return strings_global

from typing import List, Union

from electrical.paneles.resultado_paneles import ResultadoPaneles


def expandir_paneles(paneles: Union[ResultadoPaneles, List[ResultadoPaneles]]) -> List[ResultadoPaneles]:
    """
    Devuelve lista uniforme de ResultadoPaneles.

    ✔ Legacy → [paneles]
    ✔ Multizona → paneles
    """

    if isinstance(paneles, list):
        return paneles

    return [paneles]

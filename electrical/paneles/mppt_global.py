from typing import List

from electrical.paneles.resultado_paneles import ResultadoPaneles, StringFV


def asignar_mppt_global(paneles) -> List[StringFV]:
    """
    Reasigna MPPT globales a todos los strings.

    ✔ Evita colisiones
    ✔ Respeta distribución interna por zona
    ✔ No recalcula nada eléctrico
    """

    # -------------------------
    # NORMALIZAR EN LISTA
    # -------------------------
    if not isinstance(paneles, list):
        paneles = [paneles]

    strings_global: List[StringFV] = []

    mppt_offset = 0

    # -------------------------
    # RECORRER ZONAS
    # -------------------------
    for zona in paneles:

        if not zona.ok:
            raise ValueError("Zona inválida en paneles")

        n_mppt_zona = zona.array.n_mppt

        for s in zona.strings:

            nuevo_mppt = s.mppt + mppt_offset

            strings_global.append(
                StringFV(
                    mppt=nuevo_mppt,
                    n_series=s.n_series,
                    vmp_string_v=s.vmp_string_v,
                    voc_frio_string_v=s.voc_frio_string_v,
                    imp_string_a=s.imp_string_a,
                    isc_string_a=s.isc_string_a,
                )
            )

        mppt_offset += n_mppt_zona

    if not strings_global:
        raise ValueError("No hay strings después de asignación MPPT")

    return strings_global

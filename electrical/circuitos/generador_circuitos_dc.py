from electrical.paneles.distribucion_mppt import distribuir_strings


def generar_circuitos_dc(
    strings_totales: int,
    mppts: int,
    isc_string: float,
    factor_nec: float = 1.25,
):

    """
    Genera circuitos DC por MPPT.

    Cada circuito representa la corriente total
    que llega a un MPPT del inversor.
    """

    distribucion = distribuir_strings(strings_totales, mppts)

    circuitos = []

    for i, n in enumerate(distribucion):

        # corriente de operación
        i_oper = n * isc_string

        # corriente de diseño NEC
        i_dis = i_oper * factor_nec

        circuitos.append({
            "mppt": i + 1,
            "strings": int(n),

            "i_operacion_a": float(i_oper),
            "i_diseno_nec_a": float(i_dis),

        })

    return circuitos

from electrical.paneles.distribucion_mppt import distribuir_strings
def distribuir_strings(strings_totales, mppts):

    base = strings_totales // mppts
    extra = strings_totales % mppts

    distribucion = []

    for i in range(mppts):

        n = base

        if i < extra:
            n += 1

        distribucion.append(n)

    return distribucion

def crear_circuitos_mppt(strings_totales, mppts, imp):

    distribucion = distribuir_strings(strings_totales, mppts)

    circuitos = []

    for i, n in enumerate(distribucion):

        i_oper = n * imp

        # NEC 690.8
        i_dis = i_oper * 1.25

        circuitos.append({

            "mppt": i + 1,

            "strings": n,

            "i_operacion": i_oper,

            "i_diseno": i_dis

        })

    return circuitos

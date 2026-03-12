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

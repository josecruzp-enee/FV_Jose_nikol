from electrical.paneles.distribucion_mppt import distribuir_strings

def generar_circuitos_dc(strings_totales, mppts, imp):

    distribucion = distribuir_strings(strings_totales, mppts)

    circuitos = []

    for i, n in enumerate(distribucion):

        i_oper = n * imp
        i_dis = i_oper * 1.25

        circuitos.append({
            "mppt": i + 1,
            "strings": n,
            "i_operacion": i_oper,
            "i_diseno": i_dis
        })

    return circuitos

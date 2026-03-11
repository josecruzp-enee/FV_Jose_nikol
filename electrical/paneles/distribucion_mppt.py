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

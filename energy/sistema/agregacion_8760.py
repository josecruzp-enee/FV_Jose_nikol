def agregar_energia_por_mes(potencia_horaria_kw: List[float]) -> List[float]:

    if len(potencia_horaria_kw) not in (8760, 8784):
        raise ValueError("Serie inválida")

    DIAS_MES = [31,28,31,30,31,30,31,31,30,31,30,31]

    energia_mensual = []
    idx = 0

    for dias in DIAS_MES:

        horas_mes = dias * 24

        bloque = potencia_horaria_kw[idx : idx + horas_mes]

        energia_mensual.append(sum(bloque))

        idx += horas_mes

    return energia_mensual

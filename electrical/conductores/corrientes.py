"""
Subdominio corrientes — FV Engine (dentro de conductores por decisión de empaquetado).

Responsabilidad:
- Calcular corrientes de diseño DC/AC a partir de strings e inversor.
- Entregar ResultadoCorrientes para protecciones/conductores.
"""

from __future__ import annotations

from electrical.modelos import ResultadoStrings, EntradaInversor, ResultadoCorrientes


# Calcula corrientes de diseño DC/AC usando el mejor dato disponible del motor de strings e inversor.
def calcular_corrientes(strings: ResultadoStrings, inv: EntradaInversor, cfg_tecnicos: dict) -> ResultadoCorrientes:
    f_dc = float(cfg_tecnicos.get("factor_seguridad_dc", 1.25))
    f_ac = float(cfg_tecnicos.get("factor_seguridad_ac", 1.25))

    # DC: prioriza Isc del arreglo total si existe; si no, aproxima con Isc_string * n_strings_total.
    isc_array = getattr(strings, "isc_array_a", None)
    n_strings_total = getattr(strings, "n_strings_total", None)

    if isc_array is not None and float(isc_array) > 0:
        isc_total = float(isc_array)
    elif n_strings_total is not None and float(getattr(strings, "isc_string_a", 0.0)) > 0 and int(n_strings_total) > 0:
        isc_total = float(getattr(strings, "isc_string_a")) * int(n_strings_total)
    else:
        isc_total = float(getattr(strings, "isc_string_a", 0.0))

    i_dc_diseno = isc_total * f_dc

    # AC: usa i_ac_max de datasheet si existe; si no, estima por potencia y tensión nominal.
    if inv.i_ac_max_a is not None and float(inv.i_ac_max_a) > 0:
        i_ac_max = float(inv.i_ac_max_a)
    else:
        p_w = float(inv.potencia_ac_kw) * 1000.0
        v = float(inv.v_ac_nom_v) if float(inv.v_ac_nom_v) > 0 else 0.0

        if v <= 0:
            i_ac_max = 0.0
        else:
            if int(inv.fases) == 3:
                import math
                i_ac_max = p_w / (math.sqrt(3) * v)
            else:
                i_ac_max = p_w / v

    i_ac_diseno = i_ac_max * f_ac

    return ResultadoCorrientes(
        i_dc_diseno_a=float(i_dc_diseno),
        i_ac_diseno_a=float(i_ac_diseno),
        i_ac_max_a=float(i_ac_max),
    )

from __future__ import annotations

from typing import List
from dataclasses import dataclass

from energy.contrato import EnergiaResultado, EnergiaInput
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

# ==========================================================
# RESULTADO ERROR
# ==========================================================
def _resultado_error(inp: EnergiaInput, errores: List[str]) -> EnergiaResultado:

    return EnergiaResultado(
        ok=False,
        errores=errores,

        pdc_instalada_kw=inp.pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=0.0,

        energia_horaria_kwh=[],

        energia_bruta_12m=[],
        energia_perdidas_12m=[],
        energia_despues_perdidas_12m=[],
        energia_clipping_12m=[],
        energia_util_12m=[],

        energia_bruta_anual=0.0,
        energia_perdidas_anual=0.0,
        energia_despues_perdidas_anual=0.0,
        energia_clipping_anual=0.0,
        energia_util_anual=0.0,

        produccion_especifica_kwh_kwp=0.0,
        performance_ratio=0.0,

        meta={}
    )


# ==========================================================
# MAIN
# ==========================================================
def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    try:

        # ==================================================
        # 1. CLIMA 8760
        # ==================================================
        from energy.clima.simulacion_8760 import simular_clima_8760

        clima = simular_clima_8760(
            clima=inp.clima,
        )

        # clima.horas → lista 8760 con:
        # ghi, dni, dhi, temp_amb, viento, etc.

        # ==================================================
        # 2. POA (IRRADIANCIA EN PLANO)
        # ==================================================
        from energy.solar.poa import calcular_poa_8760

        poa = calcular_poa_8760(
            horas=clima.horas,
            tilt_deg=inp.tilt_deg,
            azimut_deg=inp.azimut_deg,
        )

        # ==================================================
        # 3. TEMPERATURA DE CELDA
        # ==================================================
        from energy.solar.temperatura import calcular_temp_celda_8760

        temp_celda = calcular_temp_celda_8760(
            poa_wm2=poa,
            temp_amb=[h.temp_c for h in clima.horas],
            noct=inp.panel.noct_c,
        )

        # ==================================================
        # 4. PANEL (MODELO FÍSICO)
        # ==================================================
        from energy.solar.panel import potencia_panel_8760

        p_panel = potencia_panel_8760(
            poa_wm2=poa,
            temp_celda=temp_celda,
            panel=inp.panel,
        )

        # ==================================================
        # 5. STRING
        # ==================================================
        from energy.solar.string import potencia_string_8760

        p_string = potencia_string_8760(
            p_panel=p_panel,
            n_series=inp.n_series,
        )

        # ==================================================
        # 6. ARRAY
        # ==================================================
        from energy.solar.array import potencia_array_8760

        p_array = potencia_array_8760(
            p_string=p_string,
            n_strings=inp.n_strings,
        )

        # ==================================================
        # 7. DC BRUTA
        # ==================================================
        dc_bruta_kw = [p / 1000.0 for p in p_array]

        # ==================================================
        # 8. PÉRDIDAS DC
        # ==================================================
        from energy.sistema.perdidas_fisicas import (
            aplicar_perdidas_fisicas, PerdidasInput
        )

        dc_neta = aplicar_perdidas_fisicas(
            PerdidasInput(
                potencia_kw=dc_bruta_kw,
                perdidas_dc_pct=inp.perdidas_dc_pct,
                sombras_pct=inp.sombras_pct,
            )
        ).potencia_kw

        perdidas_dc_kw = [
            b - n for b, n in zip(dc_bruta_kw, dc_neta)
        ]

        # ==================================================
        # 9. INVERSOR (CLIPPING + EFICIENCIA)
        # ==================================================
        from energy.sistema.modelo_energetico_inversor import (
            calcular_inversor_8760, Inversor8760Input
        )

        inv = calcular_inversor_8760(
            Inversor8760Input(
                potencia_dc_kw=dc_neta,
                p_ac_nominal_kw=inp.pac_nominal_kw,
                eficiencia_nominal=inp.eficiencia_inversor,
            )
        )

        ac_bruta_kw = inv.potencia_ac_kw
        clipping_kw = inv.clipping_kw

        # ==================================================
        # 10. PÉRDIDAS AC
        # ==================================================
        from energy.sistema.perdidas_ac import (
            aplicar_perdidas_ac, PerdidasACInput
        )

        ac_neta = aplicar_perdidas_ac(
            PerdidasACInput(
                potencia_kw=ac_bruta_kw,
                perdidas_ac_pct=inp.perdidas_ac_pct,
            )
        ).potencia_kw

        perdidas_ac_kw = [
            b - n for b, n in zip(ac_bruta_kw, ac_neta)
        ]

        # ==================================================
        # 11. ENERGÍA (kWh)
        # ==================================================
        energia_bruta_12m = agregar_energia_por_mes(dc_bruta_kw)
        energia_final_12m = agregar_energia_por_mes(ac_neta)
        energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

        energia_bruta_anual = sum(dc_bruta_kw)
        energia_final_anual = sum(ac_neta)
        energia_clipping_anual = sum(clipping_kw)

        # ==================================================
        # 12. RESULTADO FINAL
        # ==================================================
        pdc_kw = inp.pdc_kw

        return EnergiaResultado(
            ok=True,
            errores=[],

            pdc_instalada_kw=pdc_kw,
            pac_nominal_kw=inp.pac_nominal_kw,
            dc_ac_ratio=(
                pdc_kw / inp.pac_nominal_kw
                if inp.pac_nominal_kw else 0.0
            ),

            energia_horaria_kwh=ac_neta,

            energia_bruta_12m=energia_bruta_12m,
            energia_perdidas_12m=[
                b - f for b, f in zip(energia_bruta_12m, energia_final_12m)
            ],
            energia_despues_perdidas_12m=energia_final_12m,
            energia_clipping_12m=energia_clipping_12m,
            energia_util_12m=energia_final_12m,

            energia_bruta_anual=energia_bruta_anual,
            energia_perdidas_anual=energia_bruta_anual - energia_final_anual,
            energia_despues_perdidas_anual=energia_final_anual,
            energia_clipping_anual=energia_clipping_anual,
            energia_util_anual=energia_final_anual,

            produccion_especifica_kwh_kwp=(
                energia_final_anual / pdc_kw if pdc_kw > 0 else 0.0
            ),

            performance_ratio=(
                energia_final_anual / energia_bruta_anual
                if energia_bruta_anual > 0 else 0.0
            ),

            meta={
                "modelo": "fisico_8760",
                "pipeline": "clima→poa→temp→panel→string→array→dc→inv→ac"
            }
        )

    except Exception as e:
        return _resultado_error(inp, [str(e)])

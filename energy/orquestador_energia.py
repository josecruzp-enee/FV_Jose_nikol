from __future__ import annotations

from .contrato import EnergiaInput, EnergiaResultado

from .sistema.orientacion import factor_orientacion_total
from .sistema.generacion_bruta import calcular_energia_bruta_dc
from .sistema.perdidas_fisicas import aplicar_perdidas
from .sistema.perdidas_ac import aplicar_perdidas_ac

from .sistema.modelo_energetico_inversor import (
    calcular_energia_inversor,
    EnergiaInversorInput
)


# ==========================================================
# RESULTADO ERROR
# ==========================================================

def _resultado_error(inp: EnergiaInput, errores: list[str]) -> EnergiaResultado:

    return EnergiaResultado(
        ok=False,
        errores=errores,

        pdc_instalada_kw=inp.pdc_instalada_kw,
        pac_nominal_kw=inp.pac_nominal_kw,

        dc_ac_ratio=0.0,

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

        meta={"estado": "error"},
    )


# ==========================================================
# MODELO HSP
# ==========================================================

def _modelo_hsp(inp: EnergiaInput):

    # ------------------------------------------------------
    # ORIENTACIÓN
    # ------------------------------------------------------

    factor_orientacion = factor_orientacion_total(

        tipo_superficie=inp.tipo_superficie,
        azimut_deg=inp.azimut_deg,
        azimut_a_deg=inp.azimut_a_deg,
        azimut_b_deg=inp.azimut_b_deg,
        reparto_pct_a=inp.reparto_pct_a,
        hemisferio=inp.hemisferio,
    )

    # ------------------------------------------------------
    # GENERACIÓN DC BRUTA
    # ------------------------------------------------------

    r_bruta = calcular_energia_bruta_dc(
        pdc_kw=inp.pdc_instalada_kw,
        hsp_12m=inp.hsp_12m,
        dias_mes=inp.dias_mes,
        factor_orientacion=factor_orientacion,
    )

    if not r_bruta.ok:
        return None, r_bruta.errores

    energia_bruta = r_bruta.energia_mensual_dc_kwh

    # ------------------------------------------------------
    # PÉRDIDAS DC + SOMBRAS
    # ------------------------------------------------------

    r_perdidas = aplicar_perdidas(
        energia_dc_12m=energia_bruta,
        perdidas_dc_pct=inp.perdidas_dc_pct,
        perdidas_ac_pct=0.0,
        sombras_pct=inp.sombras_pct,
    )

    if not r_perdidas.ok:
        return None, r_perdidas.errores

    energia_despues_perdidas_dc = r_perdidas.energia_neta_12m_kwh

    energia_perdidas = [
        b - d for b, d in zip(energia_bruta, energia_despues_perdidas_dc)
    ]

    # ------------------------------------------------------
    # INVERSOR
    # ------------------------------------------------------

    inv_input = EnergiaInversorInput(

        energia_dc_12m_kwh=energia_despues_perdidas_dc,

        kw_ac=inp.pac_nominal_kw,

        pdc_kw=inp.pdc_instalada_kw,

        eficiencia_nominal=inp.eficiencia_inversor,
    )

    r_inv = calcular_energia_inversor(inv_input)

    energia_ac_pre = r_inv.energia_ac_12m_kwh
    energia_clipping = r_inv.energia_clipping_12m_kwh

    # ------------------------------------------------------
    # PÉRDIDAS AC
    # ------------------------------------------------------

    r_ac = aplicar_perdidas_ac(
        energia_ac_12m=energia_ac_pre,
        perdidas_ac_pct=inp.perdidas_ac_pct,
    )

    if not r_ac.ok:
        return None, r_ac.errores

    energia_util = r_ac.energia_final_12m_kwh

    energia_perdidas_ac = [
        a - b for a, b in zip(energia_ac_pre, energia_util)
    ]

    energia_perdidas = [
        dc + ac for dc, ac in zip(energia_perdidas, energia_perdidas_ac)
    ]

    return (
        energia_bruta,
        energia_perdidas,
        energia_despues_perdidas_dc,
        energia_util,
        energia_clipping,
        factor_orientacion,
    ), []


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def ejecutar_motor_energia(inp):

    """
    Orquestador del motor energético FV.

    Permite ejecutar dos modos:

        • HSP mensual (rápido)
        • simulación 8760 (preciso)
    """

    errores = []

    try:

        # ==================================================
        # SELECCIÓN DEL MOTOR
        # ==================================================

        modo = getattr(inp, "modo_motor", "mensual")


        # ==================================================
        # MOTOR HSP MENSUAL
        # ==================================================

        if modo == "mensual":

            resultado, errores = _modelo_hsp(inp)

            # metadatos del motor
            resultado.meta = {

                "motor": "mensual",
                "meses": 12,
                "factor_orientacion": getattr(inp, "factor_orientacion", 1.0)

            }

            return resultado


        # ==================================================
        # MOTOR 8760 HORARIO
        # ==================================================

        elif modo == "8760":

            from energy.clima.pvgis import (
                descargar_clima_pvgis,
                EntradaClimaPVGIS
            )

            from energy.solar.irradiancia_plano import (
                calcular_irradiancia_plano,
                IrradianciaInput
            )

            from energy.panel_energia.modelo_termico import (
                calcular_temperatura_celda,
                ModeloTermicoInput
            )

            from electrical.paneles.array_8760 import (
                calcular_array_8760,
                Array8760Input
            )

            from energy.sistema.inversor import (
                calcular_inversor_8760
            )


            # ----------------------------------------------
            # CLIMA 8760
            # ----------------------------------------------

            clima = descargar_clima_pvgis(

                EntradaClimaPVGIS(

                    lat=inp.lat,
                    lon=inp.lon

                )

            )


            # ----------------------------------------------
            # IRRADIANCIA + TEMPERATURA
            # ----------------------------------------------

            estados = []

            for hora in clima.horas:

                irr = calcular_irradiancia_plano(

                    IrradianciaInput(

                        dni=hora.dni_wm2,
                        dhi=hora.dhi_wm2,
                        ghi=hora.ghi_wm2,

                        solar_zenith_deg=hora.solar_zenith_deg,
                        solar_azimuth_deg=hora.solar_azimuth_deg,

                        panel_tilt_deg=inp.tilt,
                        panel_azimuth_deg=inp.azimut

                    )

                )

                temp = calcular_temperatura_celda(

                    ModeloTermicoInput(

                        irradiancia_poa_wm2=irr.poa_total,
                        temperatura_ambiente_c=hora.temp_amb_c,
                        noct_c=inp.noct

                    )

                )

                estados.append({

                    "poa_wm2": irr.poa_total,
                    "temp_celda_c": temp.temperatura_celda_c

                })


            # ----------------------------------------------
            # ARRAY FV
            # ----------------------------------------------

            array = calcular_array_8760(

                Array8760Input(

                    estado_solar=estados,

                    paneles_por_string=inp.paneles_por_string,
                    strings_totales=inp.n_strings,

                    pmax_stc_w=inp.pmax_panel_w,
                    vmp_stc_v=inp.vmp_panel_v,
                    voc_stc_v=inp.voc_panel_v,

                    coef_pmax_pct_per_c=inp.coef_pmax,
                    coef_voc_pct_per_c=inp.coef_voc,
                    coef_vmp_pct_per_c=inp.coef_vmp

                )

            )


            # ----------------------------------------------
            # INVERSOR
            # ----------------------------------------------

            inv = calcular_inversor_8760(

                potencia_dc_kw_8760=array.potencia_dc_kw,

                p_ac_nominal_kw=inp.kw_ac,

                eficiencia_nominal=inp.eficiencia_inversor

            )


            energia_anual = inv["energia_ac_anual_kwh"]


            # ----------------------------------------------
            # RESULTADO
            # ----------------------------------------------

            resultado, _ = _modelo_hsp(inp)

            resultado.energia_util_anual = energia_anual

            resultado.meta = {

                "motor": "8760",
                "horas": 8760

            }

            return resultado


        else:

            raise ValueError(
                f"modo_motor inválido: {modo}"
            )


    except Exception as e:

        errores.append(str(e))

        return EnergiaResultado(

            ok=False,
            errores=errores

        )

from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO ENERGÍA — FV Engine
===========================================

Responsabilidad
---------------

Coordinar el cálculo energético del sistema FV en modo 8760.

Flujo del proceso
-----------------

    1) Validación de entrada
    2) Simulación clima + POA
    3) Cálculo potencia DC
    4) Aplicación pérdidas DC
    5) Modelo de inversor
    6) Aplicación pérdidas AC
    7) Agregación mensual/anual
    8) Construcción del resultado

Regla arquitectónica
--------------------

Este módulo:

    ✔ CONSUME ResultadoPaneles
    ❌ NO reconstruye parámetros eléctricos

Este módulo NO contiene lógica física detallada,
solo orquesta módulos especializados.
"""

from .contrato import EnergiaInput, EnergiaResultado, EstadoEnergiaHora
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

import streamlit as st


# ==========================================================
# RESULTADO ERROR
# ==========================================================

def _resultado_error(inp: EnergiaInput, errores: list[str]) -> EnergiaResultado:
    """
    Construye un resultado estándar cuando ocurre un error.
    """

    pdc_kw = inp.paneles.array.potencia_dc_w / 1000 if inp.paneles else 0.0

    return EnergiaResultado(
        ok=False,
        errores=errores,

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=0.0,

        energia_horaria=[],

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
# 1. CLIMA + POA
# ==========================================================

def _simular_estado_8760(inp: EnergiaInput):
    """
    Genera el estado solar horario.

    Salida:
        Lista de objetos con:
            • irradiancia POA
            • temperatura ambiente
            • otros parámetros solares
    """

    from energy.clima.simulacion_8760 import simular_clima_8760

    resultado = simular_clima_8760(
        clima=inp.clima,
        tilt=inp.tilt_deg,
        azimuth=inp.azimut_deg,
    )

    return resultado.horas


# ==========================================================
# 2. POTENCIA DC
# ==========================================================

def _calcular_dc(inp: EnergiaInput, estado):
    """
    Calcula la potencia DC del sistema en cada hora.

    Fuente de verdad:
        inp.paneles (ResultadoPaneles)

    No se reconstruyen parámetros eléctricos.
    """

    from energy.panel_energia.modelo_termico import (
        calcular_temperatura_celda, ModeloTermicoInput
    )
    from energy.panel_energia.potencia_panel import (
        calcular_potencia_panel, PotenciaPanelInput
    )

    paneles = inp.paneles
    array = paneles.array

    potencia_dc_kw = []

    for hora in estado:

        # Sin irradiancia → sin producción
        if hora.poa_wm2 <= 0:
            potencia_dc_kw.append(0.0)
            continue

        # ---------------- TÉRMICO ----------------
        t_cell = calcular_temperatura_celda(
            ModeloTermicoInput(
                irradiancia_poa_wm2=hora.poa_wm2,
                temperatura_ambiente_c=hora.temp_amb_c,
                noct_c=45.0,  # valor típico (puedes parametrizar luego)
            )
        ).temperatura_celda_c

        # ---------------- PANEL ----------------
        panel = calcular_potencia_panel(
            PotenciaPanelInput(
                irradiancia_poa_wm2=hora.poa_wm2,
                temperatura_celda_c=t_cell,

                # 👉 tomado desde paneles (NO desde energia)
                p_panel_w=array.p_panel_w,
                vmp_panel_v=paneles.strings[0].vmp_string_v / paneles.strings[0].n_series,
                voc_panel_v=paneles.strings[0].voc_frio_string_v / paneles.strings[0].n_series,

                imp_panel_a=paneles.strings[0].imp_string_a,
                isc_panel_a=paneles.strings[0].isc_string_a,

                coef_potencia=None,
                coef_vmp=None,
                coef_voc=None,
            )
        )

        # ---------------- ESCALADO A ARRAY ----------------
        p_array_w = panel.pmp_w * array.n_paneles_total

        potencia_dc_kw.append(max(0.0, p_array_w / 1000.0))

    return potencia_dc_kw


# ==========================================================
# 3. PÉRDIDAS DC
# ==========================================================

def _aplicar_perdidas_dc(inp: EnergiaInput, potencia_dc_kw):
    """
    Aplica pérdidas en el lado DC.
    """

    from energy.sistema.perdidas_fisicas import (
        aplicar_perdidas_fisicas, PerdidasInput
    )

    return aplicar_perdidas_fisicas(
        PerdidasInput(
            potencia_kw=potencia_dc_kw,
            perdidas_dc_pct=inp.perdidas_dc_pct,
            sombras_pct=inp.sombras_pct,
        )
    )


# ==========================================================
# 4. INVERSOR
# ==========================================================

def _aplicar_inversor(inp: EnergiaInput, potencia_dc_kw):
    """
    Convierte potencia DC a AC considerando:

        • eficiencia
        • límite del inversor
        • clipping
    """

    from energy.sistema.modelo_energetico_inversor import (
        calcular_inversor_8760
    )

    return calcular_inversor_8760(
        potencia_dc_kw_8760=potencia_dc_kw,
        p_ac_nominal_kw=inp.pac_nominal_kw,
        eficiencia_nominal=inp.eficiencia_inversor,
    )


# ==========================================================
# 5. PÉRDIDAS AC
# ==========================================================

def _aplicar_perdidas_ac(inp: EnergiaInput, potencia_ac_kw):
    """
    Aplica pérdidas en el lado AC.
    """

    from energy.sistema.perdidas_ac import (
        aplicar_perdidas_ac, PerdidasACInput
    )

    return aplicar_perdidas_ac(
        PerdidasACInput(
            potencia_kw=potencia_ac_kw,
            perdidas_ac_pct=inp.perdidas_ac_pct,
        )
    )


# ==========================================================
# 6. CONSTRUCCIÓN RESULTADO
# ==========================================================

def _construir_resultado(
    inp: EnergiaInput,
    potencia_dc_kw,
    potencia_ac_kw,
    clipping_kw,
):
    """
    Consolida resultados horarios, mensuales y anuales.
    """

    energia_bruta_12m = agregar_energia_por_mes(potencia_dc_kw)
    energia_final_12m = agregar_energia_por_mes(potencia_ac_kw)
    energia_clipping_12m = agregar_energia_por_mes(clipping_kw)

    energia_bruta_anual = sum(potencia_dc_kw)
    energia_final_anual = sum(potencia_ac_kw)
    energia_clipping_anual = sum(clipping_kw)

    pdc_kw = inp.paneles.array.potencia_dc_w / 1000

    return EnergiaResultado(
        ok=True,
        errores=[],

        pdc_instalada_kw=pdc_kw,
        pac_nominal_kw=inp.pac_nominal_kw,
        dc_ac_ratio=pdc_kw / inp.pac_nominal_kw,

        energia_horaria=[],  # opcional: puedes llenar luego

        energia_bruta_12m=energia_bruta_12m,
        energia_perdidas_12m=[b - f for b, f in zip(energia_bruta_12m, energia_final_12m)],
        energia_despues_perdidas_12m=energia_final_12m,
        energia_clipping_12m=energia_clipping_12m,
        energia_util_12m=energia_final_12m,

        energia_bruta_anual=energia_bruta_anual,
        energia_perdidas_anual=energia_bruta_anual - energia_final_anual,
        energia_despues_perdidas_anual=energia_final_anual,
        energia_clipping_anual=energia_clipping_anual,
        energia_util_anual=energia_final_anual,

        meta={
            "motor": "8760",
            "horas": 8760,
        }
    )


# ==========================================================
# ORQUESTADOR PRINCIPAL
# ==========================================================

def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:
    """
    Punto de entrada del dominio energía.
    """

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    try:

        st.success("Ejecutando modelo 8760")

        # 1. clima
        estado = _simular_estado_8760(inp)

        # 2. DC
        potencia_dc = _calcular_dc(inp, estado)

        # 3. pérdidas DC
        r_dc = _aplicar_perdidas_dc(inp, potencia_dc)

        # 4. inversor
        inv = _aplicar_inversor(inp, r_dc.potencia_kw)

        # 5. pérdidas AC
        r_ac = _aplicar_perdidas_ac(inp, inv["potencia_ac_kw_8760"])

        # 6. resultado
        return _construir_resultado(
            inp,
            potencia_dc,
            r_ac.potencia_kw,
            inv["clipping_kw_8760"],
        )

    except Exception as e:

        print("🔥 ERROR MOTOR ENERGIA:", str(e))
        raise

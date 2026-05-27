from __future__ import annotations

from typing import List

from energy.contrato import EnergiaInput
from energy.resultado_energia import EnergiaResultado
from energy.sistema.agregacion_8760 import agregar_energia_por_mes

# MODELOS
from energy.panel_energia.modelo_termico import (
    calcular_temperatura_celda, ModeloTermicoInput
)
from energy.panel_energia.potencia_panel import (
    calcular_potencia_panel, PotenciaPanelInput
)
from energy.panel_energia.potencia_string import (
    calcular_potencia_string, PotenciaStringInput
)
from energy.panel_energia.potencia_arreglo import (
    calcular_potencia_arreglo, PotenciaArregloInput
)

from energy.solar.orquestador_solar import ejecutar_solar
from energy.solar.entrada_solar import EntradaSolar

from energy.sistema.modelo_energetico_inversor import calcular_inversor, InversorInput
from energy.sistema.perdidas_fisicas import aplicar_perdidas_fisicas, PerdidasInput
from energy.sistema.perdidas_ac import aplicar_perdidas_ac, PerdidasACInput


# ==========================================================
# ERROR
# ==========================================================
def _resultado_error(inp: EnergiaInput, errores: List[str]) -> EnergiaResultado:
    return EnergiaResultado(
        ok=False,
        errores=errores,
        pdc_instalada_kw=inp.pdc_kw,
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
        energia_horaria_kwh=[],
        produccion_especifica_kwh_kwp=0.0,
        performance_ratio=0.0,
        meta={}
    )


# ==========================================================
# BLOQUES DEL PIPELINE
# ==========================================================

def _calcular_poa(h, inp):

    # 🔥 SI YA VIENE DE 8760 → usar directo
    if hasattr(h, "poa_wm2"):
        return max(0.0, h.poa_wm2)

    # 🔥 fallback (legacy)
    solar = ejecutar_solar(
        EntradaSolar(
            lat=inp.clima.latitud,
            lon=inp.clima.longitud,
            fecha_hora=h.timestamp,
            dni_wm2=h.dni_wm2,
            dhi_wm2=h.dhi_wm2,
            ghi_wm2=h.ghi_wm2,
            temp_amb_c=h.temp_amb_c,
            tilt_deg=inp.tilt_deg,
            azimuth_panel_deg=inp.azimut_deg
        )
    )

    return max(0.0, solar.poa_total_wm2)

def _calcular_temperatura(poa, h, inp):
    return calcular_temperatura_celda(
        ModeloTermicoInput(
            irradiancia_poa_wm2=poa,
            temperatura_ambiente_c=h.temp_amb_c,
            noct_c=inp.panel.noct_c
        )
    ).temperatura_celda_c


def _calcular_panel(poa, t_cell, inp):
    return calcular_potencia_panel(
        PotenciaPanelInput(
            irradiancia_poa_wm2=poa,
            temperatura_celda_c=t_cell,
            p_panel_w=inp.panel.pmax_w,
            vmp_panel_v=inp.panel.vmp_v,
            voc_panel_v=inp.panel.voc_v,
            imp_panel_a=inp.panel.imp_a,
            isc_panel_a=inp.panel.isc_a,
            coef_potencia=inp.panel.coef_potencia_pct_c / 100,
            coef_vmp=inp.panel.coef_vmp_pct_c / 100,
            coef_voc=inp.panel.coef_voc_pct_c / 100,
        )
    )


def _calcular_string(panel, inp):
    return calcular_potencia_string(
        PotenciaStringInput(
            n_series=inp.n_series,
            p_panel_w=panel.pmp_w,
            vmp_panel_v=panel.vmp_v,
            voc_panel_v=panel.voc_v,
            imp_panel_a=panel.imp_a,
            isc_panel_a=panel.isc_a,
        )
    )


def _calcular_array(string, inp):
    return calcular_potencia_arreglo(
        PotenciaArregloInput(
            n_strings_total=inp.n_strings,
            vmp_string_v=string.vmp_string_v,
            voc_string_v=string.voc_string_v,
            imp_string_a=string.imp_string_a,
            isc_string_a=string.isc_string_a,
            potencia_string_w=string.potencia_string_w,
        )
    )


def _aplicar_perdidas_dc(dc_bruta, inp):
    return aplicar_perdidas_fisicas(
        PerdidasInput(
            potencia_kw=dc_bruta,
            perdidas_dc_frac=inp.perdidas_dc_frac,
            sombras_frac=inp.sombras_frac,
        )
    ).potencia_kw


def _pasar_inversor(dc_neta, inp):
    return calcular_inversor(
        InversorInput(
            potencia_dc_kw=dc_neta,
            p_ac_nominal_kw=inp.pac_nominal_kw,
            eficiencia_nominal=inp.eficiencia_inversor,
        )
    )


def _calcular_ac(inv, inp):
    ac_sin = aplicar_perdidas_ac(
        PerdidasACInput(
            potencia_kw=inv.potencia_ac_sin_clip_kw,
            perdidas_ac_frac=inp.perdidas_ac_frac
        )
    ).potencia_kw

    ac_final = aplicar_perdidas_ac(
        PerdidasACInput(
            potencia_kw=inv.potencia_ac_kw,
            perdidas_ac_frac=inp.perdidas_ac_frac
        )
    ).potencia_kw

    return ac_sin, ac_final, inv.clipping_kw


# ==========================================================
# MOTOR
# ==========================================================
def ejecutar_motor_energia(inp: EnergiaInput) -> EnergiaResultado:

    errores = inp.validar()
    if errores:
        return _resultado_error(inp, errores)

    try:

        if not inp.clima or not inp.clima.horas:
            raise Exception("Clima vacío o no definido")

        horas = inp.clima.horas

        dc_bruta_kw: List[float] = []
        ac_sin_clipping_kw: List[float] = []
        ac_final_kw: List[float] = []

        poa_total_kwh = 0.0

        # ==================================================
        # LOOP PRINCIPAL
        # ==================================================
        for h in horas:

            poa = _calcular_poa(h, inp)
            poa_total_kwh += poa / 1000.0

            t_cell = _calcular_temperatura(poa, h, inp)
            panel = _calcular_panel(poa, t_cell, inp)
            string = _calcular_string(panel, inp)
            array = _calcular_array(string, inp)

            dc_bruta = array.potencia_array_w / 1000.0
            dc_bruta_kw.append(dc_bruta)

            dc_neta = _aplicar_perdidas_dc(dc_bruta, inp)

            inv = _pasar_inversor(dc_neta, inp)

            ac_sin, ac_final, _ = _calcular_ac(inv, inp)

            ac_sin_clipping_kw.append(ac_sin)
            ac_final_kw.append(ac_final)

        # ==================================================
        # VALIDACIÓN
        # ==================================================
        if len(ac_final_kw) not in (8760, 8784):
            raise ValueError("Serie horaria inválida")

        # ==================================================
        # AGREGACIÓN (RESPETA CONTRATO)
        # ==================================================
        energia_bruta_12m = agregar_energia_por_mes(dc_bruta_kw)
        energia_despues_perdidas_12m = agregar_energia_por_mes(ac_sin_clipping_kw)
        energia_util_12m = agregar_energia_por_mes(ac_final_kw)

        energia_clipping_12m = [
            d - u for d, u in zip(energia_despues_perdidas_12m, energia_util_12m)
        ]

        energia_perdidas_12m = [
            b - d for b, d in zip(energia_bruta_12m, energia_despues_perdidas_12m)
        ]

        # ==================================================
        # ANUAL
        # ==================================================
        energia_bruta_anual = sum(dc_bruta_kw)
        energia_despues_perdidas_anual = sum(ac_sin_clipping_kw)
        energia_util_anual = sum(ac_final_kw)

        energia_clipping_anual = energia_despues_perdidas_anual - energia_util_anual
        energia_perdidas_anual = energia_bruta_anual - energia_despues_perdidas_anual

        # ==================================================
        # DC/AC SEGURO
        # ==================================================
        dc_ac_ratio = (
            inp.pdc_kw / inp.pac_nominal_kw
            if inp.pac_nominal_kw > 0 else 0.0
        )

        performance_ratio = (
            energia_util_anual / (poa_total_kwh * inp.pdc_kw)
            if poa_total_kwh > 0 else 0.0
        )

        return EnergiaResultado(
            ok=True,
            errores=[],
            pdc_instalada_kw=inp.pdc_kw,
            pac_nominal_kw=inp.pac_nominal_kw,
            dc_ac_ratio=dc_ac_ratio,

            energia_bruta_12m=energia_bruta_12m,
            energia_perdidas_12m=energia_perdidas_12m,
            energia_despues_perdidas_12m=energia_despues_perdidas_12m,
            energia_clipping_12m=energia_clipping_12m,
            energia_util_12m=energia_util_12m,

            energia_bruta_anual=energia_bruta_anual,
            energia_perdidas_anual=energia_perdidas_anual,
            energia_despues_perdidas_anual=energia_despues_perdidas_anual,
            energia_clipping_anual=energia_clipping_anual,
            energia_util_anual=energia_util_anual,

            energia_horaria_kwh=ac_final_kw,

            produccion_especifica_kwh_kwp=(
                energia_util_anual / inp.pdc_kw if inp.pdc_kw > 0 else 0.0
            ),

            performance_ratio=performance_ratio,

            meta={
                "modelo": "8760_fisico",
                "pipeline": "clima→solar→dc→ac",
            }
        )

    except Exception as e:
        return _resultado_error(inp, [str(e)])



# ==========================================================
# SUMA DE RESULTADOS POR INVERSOR
# ==========================================================

def _sumar_resultados_energia(
    resultados: List[EnergiaResultado],
) -> EnergiaResultado:

    if not resultados:
        return EnergiaResultado.error("Sin resultados de energía para sumar")

    base = resultados[0]

    def sumar_vector_12m(campo: str) -> List[float]:

        return [
            sum(getattr(r, campo)[i] for r in resultados)
            for i in range(12)
        ]

    energia_horaria = [
        sum(r.energia_horaria_kwh[i] for r in resultados)
        for i in range(len(base.energia_horaria_kwh))
    ]

    pdc_total = sum(r.pdc_instalada_kw for r in resultados)
    pac_total = sum(r.pac_nominal_kw for r in resultados)

    energia_bruta_anual = sum(r.energia_bruta_anual for r in resultados)
    energia_perdidas_anual = sum(r.energia_perdidas_anual for r in resultados)
    energia_despues_perdidas_anual = sum(
        r.energia_despues_perdidas_anual for r in resultados
    )
    energia_clipping_anual = sum(r.energia_clipping_anual for r in resultados)
    energia_util_anual = sum(r.energia_util_anual for r in resultados)

    produccion_especifica = (
        energia_util_anual / pdc_total
        if pdc_total > 0 else 0.0
    )

    performance_ratio = (
        sum(r.performance_ratio * r.pdc_instalada_kw for r in resultados)
        / pdc_total
        if pdc_total > 0 else 0.0
    )

    return EnergiaResultado(
        ok=True,
        errores=[],

        pdc_instalada_kw=pdc_total,
        pac_nominal_kw=pac_total,
        dc_ac_ratio=(
            pdc_total / pac_total
            if pac_total > 0 else 0.0
        ),

        energia_bruta_12m=sumar_vector_12m("energia_bruta_12m"),
        energia_perdidas_12m=sumar_vector_12m("energia_perdidas_12m"),
        energia_despues_perdidas_12m=sumar_vector_12m(
            "energia_despues_perdidas_12m"
        ),
        energia_clipping_12m=sumar_vector_12m("energia_clipping_12m"),
        energia_util_12m=sumar_vector_12m("energia_util_12m"),

        energia_bruta_anual=energia_bruta_anual,
        energia_perdidas_anual=energia_perdidas_anual,
        energia_despues_perdidas_anual=energia_despues_perdidas_anual,
        energia_clipping_anual=energia_clipping_anual,
        energia_util_anual=energia_util_anual,

        energia_horaria_kwh=energia_horaria,

        produccion_especifica_kwh_kwp=produccion_especifica,
        performance_ratio=performance_ratio,

        meta={
            "modelo": "8760_por_inversor",
            "pipeline": "clima→solar→dc_por_inversor→ac_total",
            "n_inversores_calculados": len(resultados),
        },
    )

# ==========================================================
# ADAPTER
# ==========================================================

def ejecutar_energia(datos, sizing, paneles) -> EnergiaResultado:

    if datos is None:
        return EnergiaResultado.error("datos es None")

    if sizing is None:
        return EnergiaResultado.error("sizing es None")

    if paneles is None:
        return EnergiaResultado.error("paneles es None")

    lat = datos.lat
    lon = datos.lon

    if lat == 0 and lon == 0:
        return EnergiaResultado.error("Lat/Lon inválidos")

    from energy.clima.lector_pvgis import descargar_clima_pvgis, EntradaClimaPVGIS

    clima_base = descargar_clima_pvgis(
        EntradaClimaPVGIS(
            lat=lat,
            lon=lon,
        )
    )

    if clima_base is None:
        return EnergiaResultado.error("Clima PVGIS devolvió None")

    from energy.clima.simulacion_8760 import simular_clima_8760

    tilt = getattr(datos, "tilt_deg", 15)
    azimuth = getattr(datos, "azimut_deg", 180)

    clima_8760 = simular_clima_8760(
        clima_base,
        tilt=tilt,
        azimuth=azimuth,
    )

    from electrical.catalogos.catalogos import get_panel

    if not isinstance(datos.equipos, dict):
        return EnergiaResultado.error("datos.equipos inválido")

    panel_id = datos.equipos.get("panel_id")

    if not panel_id:
        return EnergiaResultado.error("panel_id no definido")

    panel_spec = get_panel(panel_id)

    if panel_spec is None:
        return EnergiaResultado.error(
            f"Panel no encontrado: {panel_id}"
        )

    strings = getattr(paneles, "strings", []) or []

    if not strings:
        return EnergiaResultado.error("paneles.strings vacío")

    n_inversores = int(
        getattr(sizing, "n_inversores", 1) or 1
    )

    resultados: List[EnergiaResultado] = []

    for inv_idx in range(1, n_inversores + 1):

        strings_inv = [
            s for s in strings
            if int(getattr(s, "inversor", 0) or 0) == inv_idx
        ]

        if not strings_inv:
            continue

        n_series = int(
            getattr(strings_inv[0], "n_series", 0) or 0
        )

        n_strings = len(strings_inv)

        if n_series <= 0 or n_strings <= 0:
            continue

        pdc_kw_inv = 0.0

        for s in strings_inv:
            n_series_s = int(
                getattr(s, "n_series", 0) or 0
            )

            pdc_kw_inv += (
                n_series_s
                * float(panel_spec.pmax_w)
                / 1000.0
            )

        entrada = EnergiaInput(
            n_series=n_series,
            n_strings=n_strings,
            pdc_kw=pdc_kw_inv,
            panel=panel_spec,

            # Potencia física de UNA unidad inversora
            pac_nominal_kw=float(getattr(sizing, "kw_ac", 0) or 0),

            clima=clima_8760,
            tilt_deg=tilt,
            azimut_deg=azimuth,

            perdidas_dc_frac=getattr(datos, "perdidas_dc_frac", 0.05),
            sombras_frac=getattr(datos, "sombras_frac", 0.02),
            eficiencia_inversor=getattr(datos, "eficiencia_inversor", 0.97),
            perdidas_ac_frac=getattr(datos, "perdidas_ac_frac", 0.02),
        )

        res = ejecutar_motor_energia(entrada)

        if not res.ok:
            return res

        resultados.append(res)

    if not resultados:
        return EnergiaResultado.error(
            "No se pudo calcular energía por inversor"
        )

    return _sumar_resultados_energia(resultados)

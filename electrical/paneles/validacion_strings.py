"""
Validación del dominio paneles.

Verifica coherencia de PanelSpec / InversorSpec y parámetros
previos al cálculo de strings FV.

Este módulo NO ejecuta cálculos eléctricos.

----------------------------------------------------------
ENTRADAS
----------------------------------------------------------

PanelSpec  (modelo eléctrico del panel fotovoltaico)

    voc_v
        Voltaje de circuito abierto del panel (V).
        Es el voltaje máximo que puede producir el panel
        cuando no hay carga conectada, STC. 

    vmp_v
        Voltaje en el punto de máxima potencia (V).
        Voltaje al cual el panel entrega su potencia nominal, STC.

    isc_a
        Corriente de cortocircuito del panel (A).
        Corriente máxima cuando el panel está en corto,STC.

    imp_a
        Corriente en el punto de máxima potencia (A).
        Corriente típica cuando el panel trabaja en operación, STC.

    pmax_w
        Potencia nominal del panel (W) en condiciones STC.

    coef_voc_pct_c
        Coeficiente térmico del voltaje Voc (%/°C).
        Indica cuánto cambia el Voc cuando cambia la temperatura, STC.

    coef_vmp_pct_c
        Coeficiente térmico del voltaje Vmp (%/°C).
        Indica cuánto cambia el Vmp con la temperatura, STC.


----------------------------------------------------------

InversorSpec  (modelo eléctrico del inversor)

    vdc_max_v
        Voltaje máximo DC permitido en la entrada del inversor (V).
        Superar este valor puede dañar el inversor, Nominal.

    mppt_min_v
        Voltaje mínimo de operación del MPPT (V).
        Por debajo de este valor el inversor no puede rastrear potencia, Nominal.

    mppt_max_v
        Voltaje máximo de operación del MPPT (V).
        Por encima de este valor el MPPT deja de operar correctamente, Nominal.

    imppt_max_a
        Corriente máxima admitida por cada MPPT (A), Nominal.

    n_mppt
        Número de MPPT independientes del inversor, configuración.

    kw_ac
        Potencia nominal AC del inversor (kW), nominal.


----------------------------------------------------------

Parámetros generales del sistema FV

    n_paneles_total
        Número total de módulos fotovoltaicos instalados
        en el generador FV.

    t_min_c
        Temperatura mínima ambiente esperada (°C).
        Se utiliza para calcular el Voc frío del string, que es cuando se genera el máximo voltaje.

    t_oper_c
        Temperatura de operación típica del panel (°C).
        Se usa para estimar voltajes reales durante operación.

----------------------------------------------------------
SALIDAS

Todas las funciones retornan:

    (errores: list[str], warnings: list[str])

Consumido por:
    electrical.paneles.orquestador_paneles
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from electrical.modelos.paneles import PanelSpec
from electrical.modelos.inversor import InversorSpec


# ==========================================================
# VALIDACIÓN PANEL
# ==========================================================

def validar_panel(panel: PanelSpec) -> Tuple[List[str], List[str]]:

    errores: List[str] = []
    warnings: List[str] = []

    if panel.voc_v <= 0 or panel.vmp_v <= 0:
        errores.append("Panel inválido: Voc/Vmp deben ser > 0.")

    if panel.isc_a <= 0 or panel.imp_a <= 0:
        errores.append("Panel inválido: Isc/Imp deben ser > 0.")

    if panel.pmax_w <= 0:
        warnings.append("Panel: pmax_w <= 0 (revisar catálogo).")

    if panel.coef_voc_pct_c >= 0:
        warnings.append("Panel: coef_voc_pct_c normalmente es negativo.")

    if panel.coef_vmp_pct_c >= 0:
        warnings.append("Panel: coef_vmp_pct_c normalmente es negativo.")

    # Coherencia eléctrica básica
    if panel.voc_v > 0 and panel.vmp_v > panel.voc_v:
        warnings.append("Panel: Vmp > Voc (posible error de datos).")

    return errores, warnings


# ==========================================================
# VALIDACIÓN INVERSOR
# ==========================================================

def validar_inversor(inversor: InversorSpec) -> Tuple[List[str], List[str]]:

    errores: List[str] = []
    warnings: List[str] = []

    if inversor.vdc_max_v <= 0:
        errores.append("Inversor inválido: vdc_max_v <= 0.")

    if inversor.mppt_min_v <= 0 or inversor.mppt_max_v <= 0:
        errores.append("Inversor inválido: ventana MPPT inválida (<=0).")

    if inversor.mppt_min_v >= inversor.mppt_max_v:
        errores.append("Inversor inválido: mppt_min_v debe ser < mppt_max_v.")

    if inversor.imppt_max_a <= 0:
        errores.append("Inversor inválido: imppt_max_a debe ser > 0.")

    if inversor.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0.")

    # coherencia entre límites
    if inversor.vdc_max_v > 0 and inversor.mppt_max_v > 0:
        if inversor.vdc_max_v < inversor.mppt_max_v:
            warnings.append(
                "Inversor: vdc_max_v < mppt_max_v (revisar datasheet)."
            )

    if inversor.kw_ac <= 0:
        warnings.append(
            "Inversor: kw_ac <= 0 (DC/AC objetivo puede quedar sin referencia)."
        )

    return errores, warnings


# ==========================================================
# VALIDACIÓN PARÁMETROS GENERALES
# ==========================================================

def validar_parametros_generales(
    n_paneles_total: int,
    t_min_c: float,
    t_oper_c: Optional[float] = None,
) -> Tuple[List[str], List[str]]:

    errores: List[str] = []
    warnings: List[str] = []

    if int(n_paneles_total) <= 0:
        errores.append("n_paneles_total inválido (<=0).")

    try:
        float(t_min_c)
    except Exception:
        errores.append("t_min_c no convertible a número.")

    if t_oper_c is not None:
        try:
            float(t_oper_c)
        except Exception:
            errores.append("t_oper_c no convertible a número.")

    return errores, warnings


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# validar_panel(panel)
#   → (errores: list[str], warnings: list[str])
#
# validar_inversor(inversor)
#   → (errores: list[str], warnings: list[str])
#
# validar_parametros_generales(...)
#   → (errores: list[str], warnings: list[str])
#
# Consumido por:
# electrical.paneles.orquestador_paneles
#
# ==========================================================

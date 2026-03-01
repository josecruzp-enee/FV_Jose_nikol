from __future__ import annotations

from typing import Dict, Any

from core.contrato import ResultadoProyecto
from core.validacion import validar_entradas
from core.sizing import calcular_sizing_unificado
from core.finanzas_lp import ejecutar_finanzas
from core.modelo import Datosproyecto

from electrical.energia.contrato import EnergiaInput
from electrical.energia.orquestador_energia import ejecutar_motor_energia
from electrical.energia.irradiancia import hsp_12m_base, DIAS_MES
from electrical.energia.orientacion import factor_orientacion_total

from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
from electrical.nec.orquestador_nec import ejecutar_nec


# ==========================================================
# Validaciones internas
# ==========================================================

def _validar_sizing(s: Dict[str, Any]) -> None:
    required = ["n_paneles", "pdc_kw", "pac_kw"]

    for k in required:
        if k not in s:
            raise ValueError(f"Sizing incompleto. Falta clave: {k}")

    if not isinstance(s["n_paneles"], int) or s["n_paneles"] <= 0:
        raise ValueError("Sizing inválido: n_paneles debe ser > 0.")

    if float(s["pdc_kw"]) <= 0:
        raise ValueError("Sizing inválido: pdc_kw debe ser > 0.")

    if float(s["pac_kw"]) <= 0:
        raise ValueError("Sizing inválido: pac_kw debe ser > 0.")


def _validar_strings(st: Dict[str, Any]) -> None:
    if st.get("ok") is not True:
        raise ValueError("Error en cálculo de strings.")


def _validar_nec(nec: Dict[str, Any]) -> None:
    if nec.get("ok") is not True:
        raise ValueError("Error en cálculo NEC.")


def _validar_financiero(fin: Dict[str, Any]) -> None:
    required = [
        "capex_L",
        "cuota_mensual",
        "tabla_12m",
        "evaluacion",
    ]
    for k in required:
        if k not in fin:
            raise ValueError(f"ResultadoFinanciero incompleto. Falta clave: {k}")


# ==========================================================
# Pipeline principal profesional
# ==========================================================

def ejecutar_estudio(p: Datosproyecto) -> ResultadoProyecto:
    """
    Flujo lineal estricto profesional:
    Entradas → Validación → Sizing → Strings → NEC → Energía → Finanzas → Salida
    """

    # 1️⃣ Validación de entradas
    validar_entradas(p)

    # 2️⃣ Sizing
    sizing = calcular_sizing_unificado(p)
    _validar_sizing(sizing)

    # 3️⃣ Strings
    strings = ejecutar_paneles_desde_sizing(p, sizing)
    _validar_strings(strings)

    # 4️⃣ NEC
    nec = ejecutar_nec(p, sizing, strings)
    _validar_nec(nec)

    # 5️⃣ Motor Energético formal
    sistema_fv = getattr(p, "sistema_fv", {}) or {}

    hsp_12m = hsp_12m_base()

    f_orient = factor_orientacion_total(
        tipo_superficie=sistema_fv.get("tipo_superficie_code", "plano"),
        azimut_deg=sistema_fv.get("azimut_deg", 180),
        azimut_a_deg=sistema_fv.get("azimut_a_deg"),
        azimut_b_deg=sistema_fv.get("azimut_b_deg"),
        reparto_pct_a=sistema_fv.get("reparto_pct_a"),
        hemisferio="norte",
    )

    energia_input = EnergiaInput(
        pdc_instalada_kw=float(sizing["pdc_kw"]),
        pac_nominal_kw=float(sizing["pac_kw"]),
        hsp_12m=hsp_12m,
        dias_mes=DIAS_MES,
        factor_orientacion=f_orient,
        perdidas_dc_pct=float(sistema_fv.get("perdidas_sistema_pct", 10.0)),
        perdidas_ac_pct=5.0,
        sombras_pct=float(sistema_fv.get("sombras_pct", 0.0)),
        permitir_curtailment=True,
    )

    energia = ejecutar_motor_energia(energia_input)

    if not energia.ok:
        raise ValueError("Motor energético inválido.")

    # 6️⃣ Finanzas (usa energía real)
    financiero = ejecutar_finanzas(
        datos=p,
        sizing=sizing,
        energia=energia,
    )
    _validar_financiero(financiero)

    # 7️⃣ Contrato final fuerte
    resultado: ResultadoProyecto = {
        "tecnico": {
            "sizing": sizing,
            "strings": strings,
            "nec": nec,
            "energia": energia,
        },
        "financiero": financiero,
    }

    return resultado

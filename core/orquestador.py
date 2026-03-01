from __future__ import annotations

from typing import Dict, Any

from core.contrato import ResultadoProyecto
from core.validacion import validar_entradas
from core.sizing import calcular_sizing_unificado
from core.finanzas_lp import ejecutar_finanzas
from core.modelo import Datosproyecto

from electrical.energia.parametros_fv import construir_parametros_fv
from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
from electrical.nec.orquestador_nec import ejecutar_nec


# ==========================================================
# Validaciones internas de contrato fuerte
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
    if "ok" not in st:
        raise ValueError("ResultadoStrings inválido: falta 'ok'.")

    if st["ok"] is not True:
        raise ValueError("Error en cálculo de strings.")

    if "strings" not in st or not isinstance(st["strings"], list):
        raise ValueError("ResultadoStrings inválido: falta lista de strings.")


def _validar_nec(nec: Dict[str, Any]) -> None:
    if "ok" not in nec:
        raise ValueError("ResultadoNEC inválido: falta 'ok'.")

    if nec["ok"] is not True:
        raise ValueError("Error en cálculo NEC.")

    if "paq" not in nec or not isinstance(nec["paq"], dict):
        raise ValueError("ResultadoNEC inválido: falta 'paq'.")


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
# Pipeline principal
# ==========================================================

def ejecutar_estudio(p: Datosproyecto) -> ResultadoProyecto:
    """
    Flujo lineal estricto:
    Entradas → Validación → Sizing → Strings → NEC → Finanzas → Salida
    """

    # 1️⃣ Validación de entradas
    validar_entradas(p)

    # 2️⃣ Construcción explícita de parámetros FV
    sistema_fv = getattr(p, "sistema_fv", {}) or {}
    if not isinstance(sistema_fv, dict):
        raise ValueError("sistema_fv debe ser dict.")

    params_fv = construir_parametros_fv(sistema_fv)

    # 3️⃣ Sizing energético
    sizing = calcular_sizing_unificado(p, params_fv)
    _validar_sizing(sizing)

    # 4️⃣ Strings
    strings = ejecutar_paneles_desde_sizing(p, sizing)
    _validar_strings(strings)

    # 5️⃣ NEC
    nec = ejecutar_nec(p, sizing, strings)
    _validar_nec(nec)

    # 6️⃣ Finanzas (usa sizing + params_fv explícito)
    financiero = ejecutar_finanzas(
        datos=p,
        sizing=sizing,
        params_fv=params_fv,
    )
    _validar_financiero(financiero)

    # 7️⃣ Contrato final fuerte
    resultado: ResultadoProyecto = {
        "tecnico": {
            "sizing": sizing,
            "strings": strings,
            "nec": nec,
        },
        "financiero": financiero,
    }

    return resultado

# core/orquestador.py
from __future__ import annotations

from core.contrato import ResultadoProyecto
from core.validacion import validar_entradas
from core.sizing import calcular_sizing_unificado
from core.finanzas_lp import ejecutar_finanzas
from core.modelo import Datosproyecto
from core.sistema_fv_mapper import construir_parametros_fv_desde_dict
from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
from electrical.nec.orquestador_nec import ejecutar_nec


# ==========================================================
# ENTRYPOINT OFICIAL
# ==========================================================

def ejecutar_estudio(p: Datosproyecto) -> ResultadoProyecto:
    """
    Flujo lineal estricto:
    Entradas → Validación → Sizing → Strings → NEC → Finanzas → Salida
    """

    # 1️⃣ Validación
    validar_entradas(p)

    # 2️⃣ Construcción explícita de parámetros FV (sin mutar p)
    sistema_fv = getattr(p, "sistema_fv", None) or {}
    if not isinstance(sistema_fv, dict):
        sistema_fv = {}

    params_fv = construir_parametros_fv_desde_dict(sistema_fv)

    # 3️⃣ Sizing energético
    sizing = calcular_sizing_unificado(p, params_fv)

    if sizing["n_paneles"] <= 0:
        raise ValueError("Sizing inválido.")

    # 4️⃣ Strings (dominio paneles)
    strings = ejecutar_paneles_desde_sizing(p, sizing)

    if not strings["ok"]:
        raise ValueError("Error en cálculo de strings.")

    # 5️⃣ NEC (dominio eléctrico separado)
    nec = ejecutar_nec(p, sizing, strings)

    # 6️⃣ Finanzas
    financiero = ejecutar_finanzas(
        datos=p,
        sizing=sizing,
        strings=strings,
        nec=nec,
    )

    # 7️⃣ Contrato final único y estable
    return {
        "tecnico": {
            "sizing": sizing,
            "strings": strings,
            "nec": nec,
        },
        "financiero": financiero,
    }

from __future__ import annotations

from core.contrato import ResultadoProyecto
from core.validacion import validar_entradas
from core.sizing import calcular_sizing_unificado
from core.finanzas_lp import ejecutar_finanzas
from core.modelo import Datosproyecto
from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
from electrical.nec.orquestador_nec import ejecutar_nec


def ejecutar_estudio(p: Datosproyecto) -> ResultadoProyecto:
    """
    Flujo lineal estricto:
    Entradas → Validación → Sizing → Strings → NEC → Finanzas → Salida
    """

    # 1️⃣ Validación
    validar_entradas(p)

    # 2️⃣ Sizing energético
    sizing = calcular_sizing_unificado(p)

    if sizing.get("n_paneles", 0) <= 0:
        raise ValueError("Sizing inválido.")

    # 3️⃣ Strings (dominio paneles)
    strings = ejecutar_paneles_desde_sizing(p, sizing)

    if not strings.get("ok"):
        raise ValueError("Error en cálculo de strings.")

    # 4️⃣ NEC (dominio eléctrico separado)
    nec = ejecutar_nec(p, sizing, strings)

    if not nec.get("ok", True):
        raise ValueError("Error en cálculo NEC.")

    # 5️⃣ Finanzas (solo depende de sizing)
    financiero = ejecutar_finanzas(
        datos=p,
        sizing=sizing,
    )

    # 6️⃣ Contrato final único y estable
    return {
        "tecnico": {
            "sizing": sizing,
            "strings": strings,
            "nec": nec,
        },
        "financiero": financiero,
    }

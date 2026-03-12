from __future__ import annotations

"""
ESTADO GLOBAL DEL WIZARD
FV Engine

Este módulo define el modelo de estado de la UI.

Responsabilidades
-----------------

- mantener el estado del wizard entre renders
- almacenar inputs del usuario
- almacenar resultados generados por el motor
- controlar navegación y pasos completados

Este módulo pertenece a la capa UI.
No debe contener lógica de negocio ni cálculos FV.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ==========================================================
# Contexto del wizard
# ==========================================================

@dataclass
class WizardCtx:

    # ------------------------------------------------------
    # Navegación
    # ------------------------------------------------------

    paso_actual: int = 1
    completado: Dict[int, bool] = field(default_factory=dict)
    errores: List[str] = field(default_factory=list)

    # banderas para detectar cambios en inputs
    dirty: Dict[str, bool] = field(default_factory=dict)

    # ------------------------------------------------------
    # Datos del proyecto (inputs usuario)
    # ------------------------------------------------------

    datos_cliente: Dict[str, Any] = field(default_factory=dict)

    # estructura final que se envía al core
    datos_proyecto: Optional[Any] = None

    # ------------------------------------------------------
    # Consumo energético
    # ------------------------------------------------------

    consumo: Dict[str, Any] = field(
        default_factory=lambda: {
            "kwh_12m": [0.0] * 12,
            "cargos_fijos_L_mes": 0.0,
            "tarifa_energia_L_kwh": 0.0,
            "fuente": "manual",  # manual | recibo | csv
        }
    )

    # ------------------------------------------------------
    # Sistema FV (inputs técnicos)
    # ------------------------------------------------------

    sistema_fv: Dict[str, Any] = field(default_factory=dict)

    # selección de equipos
    equipos: Dict[str, Any] = field(default_factory=dict)

    # parámetros eléctricos
    electrico: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------
    # RESULTADOS LEGACY (compatibilidad)
    # ------------------------------------------------------

    resultado_core: Optional[Dict[str, Any]] = None
    resultado_electrico: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------
    # RESULTADO OFICIAL DEL SISTEMA
    # ------------------------------------------------------

    resultado_proyecto: Optional[Any] = None

    # ------------------------------------------------------
    # Artefactos generados
    # ------------------------------------------------------

    artefactos: Dict[str, str] = field(default_factory=dict)


# ==========================================================
# Obtener contexto del wizard
# ==========================================================

def ctx_get(st) -> WizardCtx:
    """
    Obtiene el contexto del wizard desde session_state.

    Si no existe, lo crea automáticamente.
    """

    if "wizard_ctx" not in st.session_state:
        st.session_state["wizard_ctx"] = WizardCtx()

    return st.session_state["wizard_ctx"]


# ==========================================================
# Cambiar paso actual
# ==========================================================

def ctx_set_paso(st, paso: int) -> None:

    ctx = ctx_get(st)

    ctx.paso_actual = int(paso)


# ==========================================================
# Marcar sección como modificada
# ==========================================================

def ctx_mark_dirty(ctx: WizardCtx, seccion: str) -> None:
    """
    Marca una sección como modificada.

    Se usa para invalidar resultados posteriores
    si el usuario cambia datos críticos.
    """

    ctx.dirty[str(seccion)] = True


# ==========================================================
# Invalidar pasos posteriores
# ==========================================================

def ctx_invalidate_from(ctx: WizardCtx, paso_desde: int) -> None:
    """
    Marca como NO completados los pasos >= paso_desde.

    Se usa cuando el usuario cambia datos anteriores
    y los resultados dejan de ser válidos.
    """

    for k in list(ctx.completado.keys()):

        if int(k) >= int(paso_desde):
            ctx.completado[k] = False

    # invalidar resultados calculados

    if paso_desde <= 5:

        ctx.resultado_core = None
        ctx.resultado_electrico = None
        ctx.resultado_proyecto = None

        # limpiar artefactos generados
        ctx.artefactos.clear()

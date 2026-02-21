# ui/estado.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ==========================================================
# Contexto global del Wizard
# ==========================================================
@dataclass
class WizardCtx:
    # ------------------------------------------------------
    # Navegación
    # ------------------------------------------------------
    paso_actual: int = 1
    completado: Dict[int, bool] = field(default_factory=dict)
    errores: List[str] = field(default_factory=list)

    # banderas para invalidar pasos posteriores
    dirty: Dict[str, bool] = field(default_factory=dict)

    # ------------------------------------------------------
    # Datos del proyecto (inputs usuario)
    # ------------------------------------------------------
    datos_cliente: Dict[str, Any] = field(default_factory=dict)
    datos_proyecto: Any = None

    # consumo energético (estructura estable)
    consumo: Dict[str, Any] = field(
        default_factory=lambda: {
            "kwh_12m": [0.0] * 12,
            "cargos_fijos_L_mes": 0.0,
            "tarifa_energia_L_kwh": 0.0,
            "fuente": "manual",  # manual | recibo | csv
        }
    )

    sistema_fv: Dict[str, Any] = field(default_factory=dict)
    equipos: Dict[str, Any] = field(default_factory=dict)
    electrico: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------
    # RESULTADOS (LEGACY — mantener por compatibilidad)
    # ------------------------------------------------------
    resultado_core: Optional[Dict[str, Any]] = None
    resultado_electrico: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------
    # RESULTADO NUEVO (ARQUITECTURA OFICIAL)
    # 👉 este será el objeto único del sistema
    # ------------------------------------------------------
    resultado_proyecto: Optional[Dict[str, Any]] = None

    # artefactos generados (charts, layout, pdf)
    artefactos: Dict[str, str] = field(default_factory=dict)


# ==========================================================
# Obtener contexto
# ==========================================================
def ctx_get(st) -> WizardCtx:
    """
    Obtiene el contexto desde session_state.
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

    # también invalidamos resultados calculados
    if paso_desde <= 5:
        ctx.resultado_core = None
        ctx.resultado_electrico = None
        ctx.resultado_proyecto = None

# ui/estado.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WizardCtx:
    # navegación
    paso_actual: int = 1
    completado: Dict[int, bool] = field(default_factory=dict)
    errores: List[str] = field(default_factory=list)

    # banderas de cambios (para invalidar pasos posteriores si aplica)
    dirty: Dict[str, bool] = field(default_factory=dict)

    # datos del proyecto (se van llenando)
    datos_cliente: Dict[str, Any] = field(default_factory=dict)
    datos_proyecto: Any = None

    # consumo: estructura estable (12 meses)
    consumo: Dict[str, Any] = field(default_factory=lambda: {
        "kwh_12m": [0.0] * 12,         # lista de 12
        "cargos_fijos_L_mes": 0.0,     # L/mes
        "tarifa_energia_L_kwh": 0.0,   # L/kWh
        "fuente": "manual",            # manual | recibo | csv (futuro)
    })

    sistema_fv: Dict[str, Any] = field(default_factory=dict)
    equipos: Dict[str, Any] = field(default_factory=dict)

    # resultados (se llenan al ejecutar)
    resultado_core: Optional[Dict[str, Any]] = None
    resultado_electrico: Optional[Dict[str, Any]] = None
    artefactos: Dict[str, str] = field(default_factory=dict)


def ctx_get(st) -> WizardCtx:
    """Obtiene el contexto desde session_state, creándolo si no existe."""
    if "wizard_ctx" not in st.session_state:
        st.session_state["wizard_ctx"] = WizardCtx()
    return st.session_state["wizard_ctx"]


def ctx_set_paso(st, paso: int) -> None:
    ctx = ctx_get(st)
    ctx.paso_actual = int(paso)


def ctx_invalidate_from(ctx: WizardCtx, paso_desde: int) -> None:
    """
    Marca como no-completados los pasos >= paso_desde.
    Útil si cambias datos de pasos tempranos.
    """
    for k in list(ctx.completado.keys()):
        if int(k) >= int(paso_desde):
            ctx.completado[k] = False

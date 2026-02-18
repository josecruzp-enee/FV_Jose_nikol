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

    # datos del proyecto (se van llenando)
    datos_cliente: Dict[str, Any] = field(default_factory=dict)
    consumo: Dict[str, Any] = field(default_factory=dict)
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

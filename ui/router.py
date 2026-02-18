# ui/router.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Tuple

import streamlit as st

from ui.wizard.estado import ctx_get, ctx_set_paso

# ====== Contrato de un paso ======
ValidarFn = Callable[[object], Tuple[bool, List[str]]]
RenderFn = Callable[[object], None]

@dataclass(frozen=True)
class PasoWizard:
    id: int
    titulo: str
    render: RenderFn
    validar: ValidarFn
    requiere: List[int]  # pasos que deben estar completados para habilitar

def _puede_abrir(ctx, paso: PasoWizard) -> bool:
    return all(ctx.completado.get(p, False) for p in paso.requiere)

def _marcar_completado(ctx, paso_id: int, ok: bool) -> None:
    ctx.completado[paso_id] = bool(ok)

def render_wizard(pasos: List[PasoWizard]) -> None:
    ctx = ctx_get(st)

    # ====== sidebar navegación ======
    st.sidebar.title("FV Engine • Wizard")
    for p in pasos:
        habilitado = _puede_abrir(ctx, p) or (p.id == ctx.paso_actual) or (p.id < ctx.paso_actual)
        estado = "✅" if ctx.completado.get(p.id, False) else ("🔒" if not habilitado else "▫️")
        label = f"{estado} {p.id}. {p.titulo}"
        if st.sidebar.button(label, disabled=not habilitado, key=f"nav_{p.id}"):
            ctx_set_paso(st, p.id)
            st.rerun()

    # ====== header + progreso ======
    total = len(pasos)
    st.progress((ctx.paso_actual - 1) / max(total - 1, 1))
    st.subheader(f"Paso {ctx.paso_actual} de {total}")

    # ====== render paso actual ======
    paso = next(p for p in pasos if p.id == ctx.paso_actual)
    ctx.errores = []
    paso.render(ctx)

    # ====== errores del paso ======
    if ctx.errores:
        for e in ctx.errores:
            st.error(e)

    # ====== controles ======
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("⬅️ Atrás", disabled=(ctx.paso_actual == 1)):
            ctx_set_paso(st, ctx.paso_actual - 1)
            st.rerun()

    with col3:
        ok, errores = paso.validar(ctx)
        if st.button("Siguiente ➡️", disabled=not ok):
            _marcar_completado(ctx, paso.id, True)
            ctx_set_paso(st, min(ctx.paso_actual + 1, total))
            st.rerun()

        # refresca errores para feedback (sin bloquear render)
        if not ok and errores:
            ctx.errores = errores

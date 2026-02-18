# ui/router.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple

import streamlit as st

from ui.estado import ctx_get, ctx_set_paso


# ====== Contrato de un paso ======
ValidarFn = Callable[[object], Tuple[bool, List[str]]]
RenderFn = Callable[[object], None]


@dataclass(frozen=True)
class PasoWizard:
    id: int
    titulo: str
    render: RenderFn
    validar: ValidarFn
    requiere: List[int]  # solo informativo (no bloquea navegación)


# ==========================================================
# Defaults (evita KeyError en validaciones)
# ==========================================================

def _init_defaults() -> None:
    s = st.session_state

    # sizing
    s.setdefault("modo_sizing", "offset")
    s.setdefault("offset_pct", 80.0)

    # techo / técnico
    s.setdefault("dos_aguas", True)
    s.setdefault("t_min_c", 10.0)

    # selección catálogos
    s.setdefault("panel_sel", "")
    s.setdefault("inv_sel", "")

    # eléctricos/cableado (legacy)
    s.setdefault("vac", 240.0)
    s.setdefault("fases", 1)
    s.setdefault("fp", 1.0)
    s.setdefault("dist_dc_m", 15.0)
    s.setdefault("dist_ac_m", 25.0)
    s.setdefault("vdrop_obj_dc_pct", 2.0)
    s.setdefault("vdrop_obj_ac_pct", 2.0)
    s.setdefault("incluye_neutro_ac", False)
    s.setdefault("otros_ccc", 0)


def _init_ctx_campos(ctx) -> None:
    # Asegura dicts usados por pasos sin reventar
    if not hasattr(ctx, "completado") or ctx.completado is None:
        ctx.completado = {}
    if not isinstance(ctx.completado, dict):
        ctx.completado = {}

    if not hasattr(ctx, "errores") or ctx.errores is None:
        ctx.errores = []
    if not isinstance(ctx.errores, list):
        ctx.errores = []

    # Paso 3 usa ctx.sistema_fv
    if not hasattr(ctx, "sistema_fv") or ctx.sistema_fv is None:
        ctx.sistema_fv = {}
    if not isinstance(ctx.sistema_fv, dict):
        ctx.sistema_fv = {}

    # Defaults críticos Paso 3
    ctx.sistema_fv.setdefault("modo_sizing", st.session_state.get("modo_sizing", "offset"))
    ctx.sistema_fv.setdefault("offset_pct", st.session_state.get("offset_pct", 80.0))
    ctx.sistema_fv.setdefault("kwp_objetivo", None)
    ctx.sistema_fv.setdefault("dos_aguas", st.session_state.get("dos_aguas", True))
    ctx.sistema_fv.setdefault("t_min_c", st.session_state.get("t_min_c", 10.0))

    # paso actual
    if not hasattr(ctx, "paso_actual") or ctx.paso_actual is None:
        ctx.paso_actual = 1


# ==========================================================
# Sidebar libre (NO bloquea)
# ==========================================================

def _sidebar_nav(pasos: List[PasoWizard], paso_actual: int, ctx) -> None:
    st.sidebar.title("FV Engine • Wizard")

    for p in pasos:
        estado = "✅" if ctx.completado.get(p.id, False) else "▫️"
        label = f"{estado} {p.id}. {p.titulo}"

        # ✅ navegación SIEMPRE habilitada
        if st.sidebar.button(label, disabled=False, key=f"nav_{p.id}"):
            ctx_set_paso(st, p.id)
            st.rerun()


# ==========================================================
# UI del paso: header + errores + botones
# ==========================================================

def _render_header(pasos: List[PasoWizard], paso_actual: int) -> None:
    total = len(pasos)
    st.progress((paso_actual - 1) / max(total - 1, 1))
    st.subheader(f"Paso {paso_actual} de {total}")


def _render_errores(errores: List[str]) -> None:
    for e in errores or []:
        st.error(str(e))


def _marcar_completado(ctx, paso_id: int, ok: bool) -> None:
    ctx.completado[int(paso_id)] = bool(ok)


def _render_botones(ctx, pasos: List[PasoWizard], paso_id: int, ok: bool, errores: List[str]) -> None:
    total = len(pasos)
    col1, _, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("⬅️ Atrás", disabled=(int(paso_id) == 1)):
            ctx_set_paso(st, int(paso_id) - 1)
            st.rerun()

    with col3:
        # ✅ solo bloquea "Siguiente"
        if st.button("Siguiente ➡️", disabled=not bool(ok)):
            _marcar_completado(ctx, paso_id, True)
            ctx_set_paso(st, min(int(paso_id) + 1, total))
            st.rerun()

    # mostrar errores pero NO bloquear navegación lateral
    if not ok and errores:
        _render_errores(errores)


# ==========================================================
# Render principal
# ==========================================================

def render_wizard(pasos: List[PasoWizard]) -> None:
    _init_defaults()

    ctx = ctx_get(st)
    _init_ctx_campos(ctx)

    # ✅ sidebar libre
    _sidebar_nav(pasos, int(ctx.paso_actual), ctx)

    # header
    _render_header(pasos, int(ctx.paso_actual))

    # paso actual
    paso = next(p for p in pasos if p.id == int(ctx.paso_actual))

    # validar SOLO para "Siguiente" y para mostrar errores
    ok, errores = paso.validar(ctx)
    ctx.errores = errores or []

    # render UI
    paso.render(ctx)

    # botones
    _render_botones(ctx, pasos, paso.id, ok, errores)

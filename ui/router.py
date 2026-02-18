# ui/router.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple

import streamlit as st

from ui.estado import ctx_get, ctx_set_paso
# ui/router.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple, Any, Optional

import streamlit as st


@dataclass(frozen=True)
class PasoWizard:
    id: int
    titulo: str
    render: Callable[[Any], None]
    validar: Callable[[Any], Tuple[bool, List[str]]]
    requiere: List[int]


def _get_ctx():
    """
    Contexto simple en session_state.
    Si ya tienes un ctx más elaborado, aquí solo debes retornarlo.
    """
    if "ctx" not in st.session_state:
        # ctx mínimo; tu app ya mete atributos dinámicamente.
        class Ctx: ...
        st.session_state["ctx"] = Ctx()
        st.session_state["ctx"].paso = 1
        st.session_state["ctx"].artefactos = {}
    return st.session_state["ctx"]


def _sidebar_radio_pasos(pasos: List[PasoWizard], paso_actual: int) -> int:
    labels = [f"{p.id}. {p.titulo}" for p in pasos]
    ids = [p.id for p in pasos]

    sel = st.sidebar.radio(
        "FV Engine • Wizard",
        options=ids,
        format_func=lambda i: labels[ids.index(i)],
        index=ids.index(paso_actual),
    )
    return int(sel)


def _botones_nav(ctx, paso_actual: PasoWizard, pasos: List[PasoWizard]) -> None:
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("⬅ Atrás", disabled=int(ctx.paso) <= 1):
            ctx.paso -= 1
            st.rerun()

    with col2:
        ok, errores = paso_actual.validar(ctx)

        if st.button("Siguiente ➡", disabled=not ok or int(ctx.paso) >= len(pasos)):
            ctx.paso += 1
            st.rerun()

        if not ok and errores:
            st.error("\n".join([f"• {e}" for e in errores]))


def render_wizard(pasos: List[PasoWizard]) -> None:
    """
    Wizard profesional:
    - Sidebar SIEMPRE navegable (no bloquea)
    - Validación SOLO para avanzar con 'Siguiente'
    """
    ctx = _get_ctx()

    # ✅ sidebar libre
    ctx.paso = _sidebar_radio_pasos(pasos, int(getattr(ctx, "paso", 1)))

    # Render paso seleccionado
    paso_actual = next(p for p in pasos if p.id == int(ctx.paso))
    paso_actual.render(ctx)

    # ✅ navegación abajo (bloquea solo 'Siguiente')
    _botones_nav(ctx, paso_actual, pasos)


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


def _init_defaults(st_mod) -> None:
    s = st_mod.session_state

    # ===== defaults generales (evita KeyError en validaciones) =====
    s.setdefault("modo_sizing", "offset")
    s.setdefault("offset_pct", 80.0)

    # si tu paso 3 usa otros campos típicos, déjalos seguros también
    s.setdefault("dos_aguas", True)
    s.setdefault("t_min_c", 10.0)

    # selección de catálogos (evita validaciones rompiendo por None)
    s.setdefault("panel_sel", "")
    s.setdefault("inv_sel", "")

    # parámetros eléctricos/cableado (si se usan en ing eléctrica)
    s.setdefault("vac", 240.0)
    s.setdefault("fases", 1)
    s.setdefault("fp", 1.0)
    s.setdefault("dist_dc_m", 15.0)
    s.setdefault("dist_ac_m", 25.0)
    s.setdefault("vdrop_obj_dc_pct", 2.0)
    s.setdefault("vdrop_obj_ac_pct", 2.0)
    s.setdefault("incluye_neutro_ac", False)
    s.setdefault("otros_ccc", 0)


def render_wizard(pasos: List[PasoWizard]) -> None:
    # Defaults en session_state
    _init_defaults(st)

    # Contexto del wizard
    ctx = ctx_get(st)

    # ====== INIT: dict específico de Paso 3 (ctx.sistema_fv) ======
    # Paso 3 usa: s = ctx.sistema_fv
    if not hasattr(ctx, "sistema_fv") or getattr(ctx, "sistema_fv") is None:
        ctx.sistema_fv = {}
    if not isinstance(ctx.sistema_fv, dict):
        ctx.sistema_fv = {}

    # Defaults críticos del Paso 3
    ctx.sistema_fv.setdefault("modo_sizing", st.session_state.get("modo_sizing", "offset"))
    ctx.sistema_fv.setdefault("offset_pct", st.session_state.get("offset_pct", 80.0))
    ctx.sistema_fv.setdefault("kwp_objetivo", None)
    ctx.sistema_fv.setdefault("dos_aguas", st.session_state.get("dos_aguas", True))
    ctx.sistema_fv.setdefault("t_min_c", st.session_state.get("t_min_c", 10.0))

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

    ok, errores = paso.validar(ctx)  # valida antes para mensajes y habilitar botones
    ctx.errores = errores or []

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
        if st.button("Siguiente ➡️", disabled=not ok):
            _marcar_completado(ctx, paso.id, True)
            ctx_set_paso(st, min(ctx.paso_actual + 1, total))
            st.rerun()

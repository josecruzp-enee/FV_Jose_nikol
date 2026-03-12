from __future__ import annotations

"""
ROUTER DEL WIZARD UI
FV Engine

Este módulo controla la navegación del wizard de la interfaz.

RESPONSABILIDAD
----------------

- controlar el flujo entre pasos
- mostrar navegación lateral
- renderizar paso actual
- validar paso actual
- controlar botones Atrás / Siguiente

Este módulo NO contiene lógica de ingeniería.

No llama:
    paneles
    energía
    NEC
    finanzas

Solo coordina la UI.
"""

from dataclasses import dataclass
from typing import Callable, List, Tuple

import streamlit as st

from ui.estado import ctx_get, ctx_set_paso


# ==========================================================
# Contrato de un paso del wizard
# ==========================================================

ValidarFn = Callable[[object], Tuple[bool, List[str]]]
RenderFn = Callable[[object], None]


@dataclass(frozen=True)
class PasoWizard:
    """
    Define un paso del wizard.
    """

    id: int
    titulo: str
    render: RenderFn
    validar: ValidarFn

    # solo informativo (documentación)
    requiere: List[int]


# ==========================================================
# Inicialización de defaults
# ==========================================================

def _init_defaults() -> None:

    s = st.session_state

    # sizing
    s.setdefault("modo_sizing", "offset")
    s.setdefault("offset_pct", 80.0)

    # técnico
    s.setdefault("dos_aguas", True)
    s.setdefault("t_min_c", 10.0)

    # catálogo equipos
    s.setdefault("panel_sel", "")
    s.setdefault("inv_sel", "")

    # eléctricos (legacy)
    s.setdefault("vac", 240.0)
    s.setdefault("fases", 1)
    s.setdefault("fp", 1.0)

    # cableado
    s.setdefault("dist_dc_m", 15.0)
    s.setdefault("dist_ac_m", 25.0)

    s.setdefault("vdrop_obj_dc_pct", 2.0)
    s.setdefault("vdrop_obj_ac_pct", 2.0)

    s.setdefault("incluye_neutro_ac", False)
    s.setdefault("otros_ccc", 0)


# ==========================================================
# Inicialización del contexto del wizard
# ==========================================================

def _init_ctx_campos(ctx):

    # pasos completados
    if not hasattr(ctx, "completado") or not isinstance(ctx.completado, dict):
        ctx.completado = {}

    # errores del paso
    if not hasattr(ctx, "errores") or not isinstance(ctx.errores, list):
        ctx.errores = []

    # datos sistema FV
    if not hasattr(ctx, "sistema_fv") or not isinstance(ctx.sistema_fv, dict):
        ctx.sistema_fv = {}

    # defaults importantes
    ctx.sistema_fv.setdefault(
        "modo_sizing",
        st.session_state.get("modo_sizing", "offset")
    )

    ctx.sistema_fv.setdefault(
        "offset_pct",
        st.session_state.get("offset_pct", 80.0)
    )

    ctx.sistema_fv.setdefault("kwp_objetivo", None)

    ctx.sistema_fv.setdefault(
        "dos_aguas",
        st.session_state.get("dos_aguas", True)
    )

    ctx.sistema_fv.setdefault(
        "t_min_c",
        st.session_state.get("t_min_c", 10.0)
    )

    # paso actual
    if not hasattr(ctx, "paso_actual") or ctx.paso_actual is None:
        ctx.paso_actual = 1


# ==========================================================
# Navegación lateral (sidebar)
# ==========================================================

def _sidebar_nav(pasos: List[PasoWizard], paso_actual: int, ctx):

    st.sidebar.title("FV Engine • Wizard")

    for p in pasos:

        estado = "✅" if ctx.completado.get(p.id, False) else "▫️"

        label = f"{estado} {p.id}. {p.titulo}"

        if st.sidebar.button(label, key=f"nav_{p.id}"):

            ctx_set_paso(st, p.id)

            st.rerun()


# ==========================================================
# Header del wizard
# ==========================================================

def _render_header(pasos: List[PasoWizard], paso_actual: int):

    total = len(pasos)

    progreso = (paso_actual - 1) / max(total - 1, 1)

    st.progress(progreso)

    st.subheader(f"Paso {paso_actual} de {total}")


# ==========================================================
# Mostrar errores
# ==========================================================

def _render_errores(errores: List[str]):

    for e in errores or []:
        st.error(str(e))


# ==========================================================
# Marcar paso completado
# ==========================================================

def _marcar_completado(ctx, paso_id: int, ok: bool):

    ctx.completado[int(paso_id)] = bool(ok)


# ==========================================================
# Botones navegación inferior
# ==========================================================

def _render_botones(ctx, pasos: List[PasoWizard], paso_id: int, ok: bool, errores: List[str]):

    total = len(pasos)

    col1, _, col3 = st.columns([1, 2, 1])

    # -------------------------------
    # botón atrás
    # -------------------------------

    with col1:

        if st.button("⬅️ Atrás", disabled=(paso_id == 1)):

            ctx_set_paso(st, paso_id - 1)

            st.rerun()

    # -------------------------------
    # botón siguiente
    # -------------------------------

    with col3:

        if st.button("Siguiente ➡️", disabled=not bool(ok)):

            _marcar_completado(ctx, paso_id, True)

            ctx_set_paso(st, min(paso_id + 1, total))

            st.rerun()

    # -------------------------------
    # errores
    # -------------------------------

    if not ok and errores:
        _render_errores(errores)


# ==========================================================
# Render principal del wizard
# ==========================================================

def render_wizard(pasos: List[PasoWizard]):

    _init_defaults()

    ctx = ctx_get(st)

    _init_ctx_campos(ctx)

    # --------------------------------
    # normalizar paso actual
    # --------------------------------

    ids = [p.id for p in pasos]

    if int(getattr(ctx, "paso_actual", 1) or 1) not in ids:

        ctx.paso_actual = ids[0] if ids else 1

    # --------------------------------
    # sidebar
    # --------------------------------

    _sidebar_nav(pasos, int(ctx.paso_actual), ctx)

    # --------------------------------
    # header
    # --------------------------------

    _render_header(pasos, int(ctx.paso_actual))

    # --------------------------------
    # paso actual
    # --------------------------------

    paso = next((p for p in pasos if p.id == int(ctx.paso_actual)), None)

    if paso is None:

        st.error("Paso inválido. Revise configuración del wizard.")

        return

    # --------------------------------
    # validación del paso
    # --------------------------------

    ok, errores = paso.validar(ctx)

    ctx.errores = errores or []

    if ok:
        _marcar_completado(ctx, paso.id, True)

    # --------------------------------
    # render del paso
    # --------------------------------

    paso.render(ctx)

    # --------------------------------
    # botones
    # --------------------------------

    _render_botones(ctx, pasos, paso.id, ok, errores)

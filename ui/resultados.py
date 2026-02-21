# ui/resultados.py
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st

from core.rutas import preparar_salida, money_L, num
from core.result_accessors import (
    as_float,
    as_int,
    get_capex_L,
    get_consumo_anual,
    get_kwp_dc,
    get_n_paneles,
    get_sizing,
)
from ui.state_helpers import is_result_stale
from reportes.generar_pdf_profesional import generar_pdf_profesional
from reportes.imagenes import generar_artefactos


# ==========================================================
# Vista (controles UI)
# ==========================================================
def _vista_defaults() -> Dict[str, Any]:
    return {
        "mostrar_teorica": False,
        "inclinacion_deg": 15,
        "orientacion": "Sur",
        "debug": False,
    }


def _ensure_vista_resultados_state() -> Dict[str, Any]:
    if "vista_resultados" not in st.session_state or not isinstance(st.session_state["vista_resultados"], dict):
        st.session_state["vista_resultados"] = _vista_defaults()
    v = st.session_state["vista_resultados"]
    for k, val in _vista_defaults().items():
        v.setdefault(k, val)
    return v


def _render_ajustes_vista(v: Dict[str, Any]) -> None:
    with st.expander("Ajustes de visualización (curva teórica FV)", expanded=False):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            v["mostrar_teorica"] = st.checkbox("Mostrar curva teórica", value=bool(v["mostrar_teorica"]))

        with c2:
            v["inclinacion_deg"] = st.slider(
                "Inclinación (°)",
                min_value=0,
                max_value=45,
                value=int(v["inclinacion_deg"]),
            )

        with c3:
            opciones = ["Norte", "Sur", "Este", "Oeste", "NE", "NO", "SE", "SO"]
            actual = str(v.get("orientacion", "Sur"))
            idx = opciones.index(actual) if actual in opciones else opciones.index("Sur")
            v["orientacion"] = st.selectbox("Orientación", options=opciones, index=idx)

        with c4:
            v["debug"] = st.checkbox("Debug", value=bool(v.get("debug", False)))


# ==========================================================
# Lectura de ctx + validaciones (nuevo contrato)
# ==========================================================
def _validar_ctx(ctx) -> bool:
    if getattr(ctx, "resultado_proyecto", None) is None:
        st.error("No hay resultados del estudio. Genere primero la ingeniería eléctrica (Paso 5).")
        return False
    if not hasattr(ctx, "datos_proyecto") or ctx.datos_proyecto is None:
        st.error("Falta ctx.datos_proyecto. En Paso 5 debes guardar Datosproyecto en ctx.datos_proyecto.")
        return False
    return True


def _get_resultado_proyecto(ctx) -> dict:
    rp = getattr(ctx, "resultado_proyecto", None) or {}
    return rp if isinstance(rp, dict) else {}


def _res_plano_para_ui_y_pdf(resultado_proyecto: dict) -> dict:
    """
    Mientras reportes/charts/layout sigan esperando el dict plano legacy,
    usamos el `_compat` del orquestador. Si no existe, reconstruimos.
    """
    if not isinstance(resultado_proyecto, dict):
        return {}

    compat = resultado_proyecto.get("_compat")
    if isinstance(compat, dict) and compat:
        return compat

    tecnico = (resultado_proyecto.get("tecnico") or {})
    energetico = (resultado_proyecto.get("energetico") or {})
    financiero = (resultado_proyecto.get("financiero") or {})

    out: dict = {}
    out["params_fv"] = tecnico.get("params_fv")
    out["sizing"] = tecnico.get("sizing")
    out["electrico_ref"] = tecnico.get("electrico_ref")
    out["electrico_nec"] = tecnico.get("electrico_nec")
    out["tabla_12m"] = energetico.get("tabla_12m")

    out["cuota_mensual"] = financiero.get("cuota_mensual")
    out["evaluacion"] = financiero.get("evaluacion")
    out["decision"] = financiero.get("decision")
    out["ahorro_anual_L"] = financiero.get("ahorro_anual_L")
    out["payback_simple_anios"] = financiero.get("payback_simple_anios")
    out["finanzas_lp"] = financiero.get("finanzas_lp")
    return out


def _get_nec_paq(resultado_proyecto: dict) -> dict:
    tecnico = (resultado_proyecto.get("tecnico") or {})
    electrico_nec = (tecnico.get("electrico_nec") or {})
    paq = electrico_nec.get("paq")
    return paq if isinstance(paq, dict) else {}


def _validar_datos_para_pdf(ctx) -> bool:
    if not hasattr(ctx, "datos_proyecto") or ctx.datos_proyecto is None:
        st.error("Falta ctx.datos_proyecto. En Paso 5 guarda datos (Datosproyecto) en ctx.datos_proyecto.")
        return False
    return True


# ==========================================================
# Helpers de normalización (contrato UI/PDF tolerante)
# ==========================================================
def _get_sizing(res: dict) -> Dict[str, Any]:
    return get_sizing(res)


def _as_float(x: Any, default: float = 0.0) -> float:
    return as_float(x, default)


def _as_int(x: Any, default: int = 0) -> int:
    return as_int(x, default)


def _kwp_dc_from_sizing(sizing: Dict[str, Any]) -> float:
    return get_kwp_dc({"sizing": dict(sizing or {})})


def _capex_L_from_sizing(sizing: Dict[str, Any]) -> float:
    return get_capex_L({"sizing": dict(sizing or {})})


def _n_paneles_from_sizing(sizing: Dict[str, Any]) -> int:
    return get_n_paneles({"sizing": dict(sizing or {})})


def _ensure_res_pdf_keys(res: dict, ctx) -> None:
    sizing = _get_sizing(res)

    kwp_dc = _kwp_dc_from_sizing(sizing)
    sizing.setdefault("kwp_dc", kwp_dc)
    sizing.setdefault("kwp_recomendado", kwp_dc)

    n_paneles = _n_paneles_from_sizing(sizing)
    sizing.setdefault("n_paneles", n_paneles)

    capex_L = _capex_L_from_sizing(sizing)
    sizing.setdefault("capex_L", capex_L)

    if "consumo_anual" not in res:
        consumo_anual = get_consumo_anual(res, datos=getattr(ctx, "datos_proyecto", None))
        res["consumo_anual"] = float(consumo_anual)


def _datos_pdf_from_ctx(ctx, res: dict) -> Dict[str, Any]:
    dp = ctx.datos_proyecto
    datos_pdf = dict(getattr(dp, "__dict__", {}))
    if "consumo_anual" in res:
        datos_pdf.setdefault("consumo_anual", _as_float(res.get("consumo_anual"), 0.0))
    return datos_pdf


def _debug_pdf_sanity(res: dict) -> None:
    sizing = _get_sizing(res)
    if _as_float(sizing.get("kwp_dc")) <= 0:
        st.warning(f"PDF: sizing sin kwp_dc. keys={sorted(list(sizing.keys()))}")
    if _as_float(res.get("consumo_anual")) <= 0:
        st.warning("PDF: consumo_anual quedó en 0. Verifique consumo_12m / tabla_12m.")
    if _as_int(sizing.get("n_paneles")) <= 0:
        st.warning("PDF: n_paneles quedó en 0. El layout puede omitirse.")


# ==========================================================
# Render: KPIs y bloques
# ==========================================================
def _render_kpis(res: dict) -> None:
    sizing = _get_sizing(res)
    evaluacion = res.get("evaluacion") or {}

    kwp_dc = _kwp_dc_from_sizing(sizing)
    cuota = _as_float(res.get("cuota_mensual"), 0.0)
    estado = str(evaluacion.get("estado") or evaluacion.get("dictamen") or "N/D")

    c1, c2, c3 = st.columns(3)
    c1.metric("Sistema (kWp DC)", num(kwp_dc, 2))
    c2.metric("Cuota mensual", money_L(cuota))
    c3.metric("Estado", estado)

    if kwp_dc <= 0:
        st.warning(f"Sizing incompleto: keys={sorted(list(sizing.keys()))}")


def _render_nec_resumen(paq: dict) -> None:
    st.subheader("Ingeniería eléctrica (NEC 2023)")
    if not paq:
        st.info("Sin paquete NEC disponible.")
        return

    dc = paq.get("dc") or {}
    ac = paq.get("ac") or {}
    cond = paq.get("conductores") or {}
    ocpd = paq.get("ocpd") or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strings", str(dc.get("n_strings", "—")))
    c2.metric("I DC diseño", f"{dc.get('i_array_design_a','—')} A")
    c3.metric("I AC diseño", f"{ac.get('i_ac_design_a','—')} A")
    br = (ocpd.get("breaker_ac") or {})
    c4.metric("Breaker AC", f"{br.get('tamano_a','—')} A")

    with st.expander("Ver paquete NEC (crudo)", expanded=False):
        st.json(paq)


# ==========================================================
# Acciones: PDF
# ==========================================================
def _ui_boton_pdf(disabled: bool = False) -> bool:
    st.markdown("#### Generar propuesta (PDF)")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        run = st.button("Generar PDF", type="primary", disabled=disabled)
    with col_b:
        st.caption("Genera charts, layout y PDF profesional usando los datos ya calculados.")
    return bool(run)


def _generar_pdf_safe(res: dict, ctx, paths: dict) -> str | None:
    try:
        _ensure_res_pdf_keys(res, ctx)
        _debug_pdf_sanity(res)

        datos_pdf = _datos_pdf_from_ctx(ctx, res)
        pdf_path = generar_pdf_profesional(res, datos_pdf, paths)

        if hasattr(ctx, "artefactos") and isinstance(ctx.artefactos, dict):
            ctx.artefactos["pdf"] = str(pdf_path)

        return str(pdf_path)
    except Exception as e:
        st.exception(e)
        st.warning("No se pudo generar PDF aún.")
        return None


def _render_descarga_pdf(pdf_path: str) -> None:
    with open(pdf_path, "rb") as f:
        st.download_button(
            "Descargar PDF",
            data=f,
            file_name="reporte_evaluacion_fv.pdf",
            mime="application/pdf",
        )


def _ejecutar_pipeline_pdf(ctx, res: dict, vista: Dict[str, Any], resultado_proyecto: dict) -> None:
    paths = preparar_salida("salidas")
    _ensure_res_pdf_keys(res, ctx)

    # Inyectar NEC paq en res["electrico"] para páginas legacy
    paq_nec = _get_nec_paq(resultado_proyecto)
    if paq_nec:
        res["electrico"] = paq_nec

    out_dir = paths.get("out_dir") or paths.get("base_dir") or "salidas"

    # dos_aguas desde inputs
    dos_aguas = True
    if hasattr(ctx, "datos_proyecto") and ctx.datos_proyecto is not None:
        e = getattr(ctx.datos_proyecto, "electrico", {}) or {}
        if isinstance(e, dict):
            dos_aguas = bool(e.get("dos_aguas", True))

    try:
        arte = generar_artefactos(
            res=res,
            out_dir=out_dir,
            vista_resultados=vista,
            dos_aguas=dos_aguas,
        )
        paths.update(arte)

        if bool(vista.get("debug", False)):
            lp = paths.get("layout_paneles", "")
            st.write("DEBUG layout_paneles:", lp)
            st.write("DEBUG layout exists:", bool(lp) and Path(lp).exists())
            st.write("DEBUG n_paneles:", _n_paneles_from_sizing(_get_sizing(res)))

    except Exception as e:
        st.exception(e)
        st.warning("No se pudieron generar artefactos (charts/layout). Se intentará generar el PDF igual.")

    if not _validar_datos_para_pdf(ctx):
        return

    pdf_path = _generar_pdf_safe(res, ctx, paths)
    if pdf_path:
        _render_descarga_pdf(pdf_path)
        st.success("PDF generado.")


# ==========================================================
# Paso 6
# ==========================================================
def render(ctx) -> None:
    st.markdown("### Resultados y propuesta")

    if not _validar_ctx(ctx):
        return

    # ✅ Traer resultados ANTES de usarlos
    resultado_proyecto = _get_resultado_proyecto(ctx)

    st.subheader("DEBUG — Panel sizing nuevo")
    tecnico = resultado_proyecto.get("tecnico") or {}
    st.write(tecnico.get("panel_sizing"))   # si existe esa clave

    # Si lo que realmente tienes es "sizing", usa esto en vez de la línea de arriba:
    # st.write(tecnico.get("sizing"))

    res = _res_plano_para_ui_y_pdf(resultado_proyecto)

    _render_kpis(res)
    st.divider()

    vista = _ensure_vista_resultados_state()
    _render_ajustes_vista(vista)
    st.divider()

    # ✅ Mostrar NEC
    paq_nec = _get_nec_paq(resultado_proyecto)
    _render_nec_resumen(paq_nec)
    st.divider()

    stale_inputs = is_result_stale(ctx)
    if stale_inputs:
        st.warning("Los datos de entrada cambiaron después del cálculo del Paso 5. Regenera la ingeniería antes del PDF.")

    if not _ui_boton_pdf(disabled=stale_inputs):
        return

    res_pdf = copy.deepcopy(res)
    _ejecutar_pipeline_pdf(ctx, res_pdf, vista, resultado_proyecto)

def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    if getattr(ctx, "resultado_proyecto", None) is None:
        errores.append("No hay resultados del estudio (genere en Paso 5).")
    if is_result_stale(ctx):
        errores.append("Los resultados están desactualizados. Regenera la ingeniería del Paso 5.")
    return (len(errores) == 0), errores

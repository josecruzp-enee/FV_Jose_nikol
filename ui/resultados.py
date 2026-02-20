# ui/resultados.py
from __future__ import annotations

import copy
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
        c1, c2, c3 = st.columns(3)

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


# ==========================================================
# Lectura de ctx + validaciones
# ==========================================================

def _validar_ctx(ctx) -> bool:
    if getattr(ctx, "resultado_core", None) is None:
        st.error("No hay resultados del motor FV. Genere primero la ingeniería eléctrica (Paso 5).")
        return False
    if getattr(ctx, "resultado_electrico", None) is None:
        st.error("No hay resultados eléctricos. Genere primero la ingeniería eléctrica (Paso 5).")
        return False
    return True


def _get_res_y_pkg(ctx) -> Tuple[dict, dict]:
    return ctx.resultado_core, ctx.resultado_electrico


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
    """
    Asegura llaves que suelen pedir reportes.
    - sizing: kwp_dc, kwp_recomendado, n_paneles, capex_L
    - res: consumo_anual
    """
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


def _render_strings(pkg: dict) -> None:
    st.subheader("Strings DC (referencial)")
    for line in (pkg.get("texto_ui", {}).get("strings") or []):
        st.write("• " + str(line))

    checks = pkg.get("texto_ui", {}).get("checks") or []
    if checks:
        st.warning("\n".join([str(x) for x in checks]))


def _render_cableado(pkg: dict) -> None:
    st.subheader("Cableado AC/DC (referencial)")
    for line in (pkg.get("texto_ui", {}).get("cableado") or []):
        st.write("• " + str(line))

    disc = pkg.get("texto_ui", {}).get("disclaimer") or ""
    if disc:
        st.caption(str(disc))


def _render_resumen_electrico(pkg: dict) -> None:
    _render_strings(pkg)
    _render_cableado(pkg)


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

        # Guarda artefacto si existe el contenedor
        if hasattr(ctx, "artefactos") and isinstance(ctx.artefactos, dict):
            ctx.artefactos["pdf"] = pdf_path

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


def _ejecutar_pipeline_pdf(ctx, res: dict, vista: Dict[str, Any]) -> None:
    paths = preparar_salida("salidas")

    # ✅ CLAVE: asegurar n_paneles/kwp/capex antes de generar artefactos
    _ensure_res_pdf_keys(res, ctx)

    out_dir = paths.get("out_dir") or paths.get("base_dir") or paths.get("salida_dir") or "salidas"

    # dos_aguas: intenta leer de varias ubicaciones
    dos_aguas = True
    if hasattr(ctx, "electrico") and isinstance(ctx.electrico, dict):
        dos_aguas = bool(ctx.electrico.get("dos_aguas", True))
    elif hasattr(ctx, "resultado_electrico") and isinstance(ctx.resultado_electrico, dict):
        dos_aguas = bool(ctx.resultado_electrico.get("dos_aguas", True))

    try:
        arte = generar_artefactos(
            res=res,
            out_dir=out_dir,
            vista_resultados=vista,
            dos_aguas=dos_aguas,
        )
        paths.update(arte)

        # Debug temporal (puedes quitarlo luego)
        st.write("DEBUG layout_paneles:", paths.get("layout_paneles"))
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
# Paso 6 (render + validar)
# ==========================================================

def render(ctx) -> None:
    st.markdown("### Resultados y propuesta")

    if not _validar_ctx(ctx):
        return

    res, pkg = _get_res_y_pkg(ctx)

    _render_kpis(res)
    st.divider()

    vista = _ensure_vista_resultados_state()
    _render_ajustes_vista(vista)
    st.divider()

    _render_resumen_electrico(pkg)
    st.divider()

    stale_inputs = is_result_stale(ctx)
    if stale_inputs:
        st.warning("Los datos de entrada cambiaron después del cálculo del Paso 5. Regenera la ingeniería antes del PDF.")

    if not _ui_boton_pdf(disabled=stale_inputs):
        return

    # Evita mutar ctx.resultado_core (puede estar cacheado/reusado por otros pasos).
    res_pdf = copy.deepcopy(res)
    _ejecutar_pipeline_pdf(ctx, res_pdf, vista)


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    if getattr(ctx, "resultado_core", None) is None:
        errores.append("No hay resultados del motor FV (genere en Paso 5).")
    if getattr(ctx, "resultado_electrico", None) is None:
        errores.append("No hay resultados eléctricos (genere en Paso 5).")
    if is_result_stale(ctx):
        errores.append("Los resultados están desactualizados. Regenera la ingeniería del Paso 5.")
    return (len(errores) == 0), errores

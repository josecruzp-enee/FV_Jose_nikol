# ui/resultados.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import streamlit as st

from core.rutas import preparar_salida, money_L, num
from reportes.generar_charts import generar_charts
from reportes.generar_layout_paneles import generar_layout_paneles
from reportes.generar_pdf_profesional import generar_pdf_profesional


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
            # protege el index si el valor no existe
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
    sizing = res.get("sizing")
    if not isinstance(sizing, dict):
        sizing = {}
        res["sizing"] = sizing
    return sizing


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _as_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def _kwp_dc_from_sizing(sizing: Dict[str, Any]) -> float:
    return _as_float(
        sizing.get("kwp_dc")
        or sizing.get("kwp_recomendado")
        or sizing.get("kwp")
        or sizing.get("pdc_kw")
        or 0.0
    )


def _capex_L_from_sizing(sizing: Dict[str, Any]) -> float:
    return _as_float(sizing.get("capex_L") or sizing.get("capex") or 0.0)


def _n_paneles_from_sizing(sizing: Dict[str, Any]) -> int:
    n = sizing.get("n_paneles")
    if n:
        return _as_int(n, 0)

    cfg = sizing.get("cfg_strings") or {}
    # heurísticos comunes
    return _as_int(cfg.get("n_paneles") or cfg.get("n_modulos") or cfg.get("n_paneles_total") or 0, 0)


def _consumo_anual_from_tabla_12m(res: dict) -> float:
    tabla = res.get("tabla_12m") or []
    if not isinstance(tabla, list) or not tabla:
        return 0.0

    total = 0.0
    for row in tabla:
        if not isinstance(row, dict):
            continue
        total += _as_float(row.get("consumo_kwh") or row.get("consumo_mes_kwh") or 0.0)
    return float(total)


def _consumo_anual_from_datos_proyecto(ctx) -> float:
    dp = getattr(ctx, "datos_proyecto", None)
    if dp is None:
        return 0.0

    consumo_12m = getattr(dp, "consumo_12m", None) or getattr(dp, "consumo_mensual_kwh", None)
    if isinstance(consumo_12m, list) and consumo_12m:
        return float(sum(_as_float(x) for x in consumo_12m))
    return 0.0


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
        consumo_anual = _consumo_anual_from_tabla_12m(res)
        if consumo_anual <= 0:
            consumo_anual = _consumo_anual_from_datos_proyecto(ctx)
        res["consumo_anual"] = float(consumo_anual)


def _datos_pdf_from_ctx(ctx, res: dict) -> Dict[str, Any]:
    """
    Reportes a veces tratan `datos` como dict (datos["..."]).
    Convertimos el objeto (dataclass) a dict y le inyectamos llaves requeridas.
    """
    dp = ctx.datos_proyecto
    datos_pdf = dict(getattr(dp, "__dict__", {}))

    # Inyectar llaves típicas que han estado rompiendo
    if "consumo_anual" in res:
        datos_pdf.setdefault("consumo_anual", _as_float(res.get("consumo_anual"), 0.0))

    # También setear como atributo por compatibilidad (si algún reporte usa datos.consumo_anual)
    try:
        if "consumo_anual" in datos_pdf:
            setattr(dp, "consumo_anual", datos_pdf["consumo_anual"])
    except Exception:
        pass

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
# Acciones: Charts / Layout / PDF
# ==========================================================


def _ui_boton_pdf() -> bool:
    st.markdown("#### Generar propuesta (PDF)")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        run = st.button("Generar PDF", type="primary")
    with col_b:
        st.caption("Genera charts, layout y PDF profesional usando los datos ya calculados.")
    return bool(run)


def _generar_charts_safe(res: dict, paths: dict, vista: Dict[str, Any]) -> None:
    try:
        charts = generar_charts(
            res["tabla_12m"],
            paths["charts_dir"],
            vista_resultados=vista,
        )
        res["charts"] = charts
        paths.update(charts)
    except Exception as e:
        st.warning(f"No se pudieron generar charts: {e}")


def _generar_layout_paneles_safe(res: dict, ctx, paths: dict) -> None:
    try:
        sizing = _get_sizing(res)
        n_paneles = _n_paneles_from_sizing(sizing)
        if n_paneles <= 0:
            st.warning("No se pudo generar layout: falta n_paneles en sizing.")
            return

        dos_aguas = bool(getattr(ctx, "electrico", {}).get("dos_aguas", True)) if hasattr(ctx, "electrico") else True
        generar_layout_paneles(
            n_paneles=int(n_paneles),
            out_path=paths["layout_paneles"],
            max_cols=7,
            dos_aguas=dos_aguas,
            gap_cumbrera_m=0.35,
        )
    except Exception as e:
        st.warning(f"No se pudo generar layout de paneles: {e}")


def _generar_pdf_safe(res: dict, ctx, paths: dict) -> str | None:
    try:
        _ensure_res_pdf_keys(res, ctx)
        _debug_pdf_sanity(res)

        datos_pdf = _datos_pdf_from_ctx(ctx, res)
        pdf_path = generar_pdf_profesional(res, datos_pdf, paths)

        ctx.artefactos["pdf"] = pdf_path
        return str(pdf_path)
    except Exception as e:
        st.warning(f"No se pudo generar PDF aún: {e}")
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

    _generar_charts_safe(res, paths, vista)
    _generar_layout_paneles_safe(res, ctx, paths)

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

    if not _ui_boton_pdf():
        return

    _ejecutar_pipeline_pdf(ctx, res, vista)


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    if getattr(ctx, "resultado_core", None) is None:
        errores.append("No hay resultados del motor FV (genere en Paso 5).")
    if getattr(ctx, "resultado_electrico", None) is None:
        errores.append("No hay resultados eléctricos (genere en Paso 5).")
    return (len(errores) == 0), errores

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


def _get_vista_resultados() -> Dict[str, Any]:
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
            v["orientacion"] = st.selectbox(
                "Orientación",
                options=opciones,
                index=opciones.index(str(v["orientacion"])),
            )


# ==========================================================
# Validaciones / lectura de ctx
# ==========================================================

def _validar_ctx(ctx) -> bool:
    if ctx.resultado_core is None:
        st.error("No hay resultados del motor FV. Genere primero la ingeniería eléctrica (Paso 5).")
        return False
    if ctx.resultado_electrico is None:
        st.error("No hay resultados eléctricos. Genere primero la ingeniería eléctrica (Paso 5).")
        return False
    return True


def _get_res_y_pkg(ctx) -> Tuple[dict, dict]:
    return ctx.resultado_core, ctx.resultado_electrico


# ==========================================================
# Render: KPIs y bloques
# ==========================================================

def _render_kpis(res: dict) -> None:
    sizing = res.get("sizing") or {}
    evaluacion = res.get("evaluacion") or {}

    kwp_dc = float(
        sizing.get("kwp_dc")
        or sizing.get("kwp")
        or sizing.get("pdc_kw")
        or 0.0
    )

    cuota = float(res.get("cuota_mensual") or 0.0)
    estado = str(evaluacion.get("estado") or evaluacion.get("dictamen") or "N/D")

    c1, c2, c3 = st.columns(3)
    c1.metric("Sistema (kWp DC)", num(kwp_dc, 2))
    c2.metric("Cuota mensual", money_L(cuota))
    c3.metric("Estado", estado)

    # Debug útil si kwp_dc vino vacío
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
# Generación de artefactos (PDF)
# ==========================================================

def _ui_boton_pdf() -> bool:
    st.markdown("#### Generar propuesta (PDF)")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        run = st.button("Generar PDF", type="primary")
    with col_b:
        st.caption("Genera charts, layout y PDF profesional usando los datos ya calculados.")
    return bool(run)


def _generar_charts(res: dict, paths: dict, vista: Dict[str, Any]) -> None:
    charts = generar_charts(
        res["tabla_12m"],
        paths["charts_dir"],
        vista_resultados=vista,  # 👈 NUEVO (lo agregaremos en generar_charts.py)
    )
    res["charts"] = charts
    paths.update(charts)


def _generar_layout_paneles(res: dict, ctx, paths: dict) -> None:
    dos_aguas = bool(ctx.electrico.get("dos_aguas", True)) if hasattr(ctx, "electrico") else True
    generar_layout_paneles(
        n_paneles=int(res["sizing"]["n_paneles"]),
        out_path=paths["layout_paneles"],
        max_cols=7,
        dos_aguas=dos_aguas,
        gap_cumbrera_m=0.35,
    )


def _validar_datos_para_pdf(ctx) -> bool:
    if not hasattr(ctx, "datos_proyecto") or ctx.datos_proyecto is None:
        st.error("Falta ctx.datos_proyecto. En Paso 5 guarda datos (Datosproyecto) en ctx.datos_proyecto.")
        return False
    return True


def _generar_pdf(res: dict, ctx, paths: dict) -> str:
    # =========================
    # Normalización (compat PDF)
    # =========================
    sizing = res.get("sizing") or {}
    res["sizing"] = sizing  # asegura dict

    # --- kwp (todos los alias) ---
    kwp_dc = float(
        sizing.get("kwp_dc")
        or sizing.get("kwp_recomendado")
        or sizing.get("kwp")
        or sizing.get("pdc_kw")
        or 0.0
    )
    sizing.setdefault("kwp_dc", kwp_dc)
    sizing.setdefault("kwp_recomendado", kwp_dc)

    # --- n_paneles ---
    if "n_paneles" not in sizing:
        # intenta deducir desde sizing o cfg_strings
        n_paneles = sizing.get("n_paneles")
        if not n_paneles:
            cfg = sizing.get("cfg_strings") or {}
            n_paneles = cfg.get("n_paneles") or cfg.get("n_modulos") or 0
        sizing["n_paneles"] = int(n_paneles or 0)

    # --- capex_L ---
    capex_L = float(sizing.get("capex_L") or sizing.get("capex") or 0.0)
    sizing.setdefault("capex_L", capex_L)

    # --- consumo_anual (para PDF) ---
    if "consumo_anual" not in res:
        consumo_anual = 0.0

        # 1) desde tabla_12m
        tabla = res.get("tabla_12m") or []
        if isinstance(tabla, list) and tabla:
            for row in tabla:
                if isinstance(row, dict):
                    consumo_anual += float(row.get("consumo_kwh", row.get("consumo_mes_kwh", 0.0)) or 0.0)

        # 2) fallback desde Datosproyecto
        if consumo_anual <= 0 and getattr(ctx, "datos_proyecto", None) is not None:
            p = ctx.datos_proyecto
            consumo_12m = getattr(p, "consumo_12m", None) or getattr(p, "consumo_mensual_kwh", None)
            if isinstance(consumo_12m, list) and consumo_12m:
                consumo_anual = sum(float(x or 0.0) for x in consumo_12m)

        res["consumo_anual"] = float(consumo_anual)

    # Debug visible si algo crítico quedó en 0
    if sizing.get("kwp_dc", 0) <= 0:
        st.warning(f"PDF: sizing sin kwp_dc. keys={sorted(list(sizing.keys()))}")
    if res.get("consumo_anual", 0) <= 0:
        st.warning("PDF: consumo_anual quedó en 0. Verifique consumo_12m / tabla_12m.")

    # =========================
    # Generación PDF
    # =========================
    pdf_path = generar_pdf_profesional(res, ctx.datos_proyecto, paths)
    ctx.artefactos["pdf"] = pdf_path
    return str(pdf_path)


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

    try:
        _generar_charts(res, paths, vista)
    except Exception as e:
        st.warning(f"No se pudieron generar charts: {e}")

    try:
        _generar_layout_paneles(res, ctx, paths)
    except Exception as e:
        st.warning(f"No se pudo generar layout de paneles: {e}")

    if not _validar_datos_para_pdf(ctx):
        return

    try:
        pdf_path = _generar_pdf(res, ctx, paths)
        _render_descarga_pdf(pdf_path)
        st.success("PDF generado.")
    except Exception as e:
        st.warning(f"No se pudo generar PDF aún: {e}")


# ==========================================================
# Paso 6
# ==========================================================

def render(ctx) -> None:
    st.markdown("### Resultados y propuesta")

    if not _validar_ctx(ctx):
        return

    res, pkg = _get_res_y_pkg(ctx)

    _render_kpis(res)
    st.divider()

    vista = _get_vista_resultados()
    _render_ajustes_vista(vista)
    st.divider()

    _render_resumen_electrico(pkg)
    st.divider()

    if not _ui_boton_pdf():
        return

    _ejecutar_pipeline_pdf(ctx, res, vista)


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    if ctx.resultado_core is None:
        errores.append("No hay resultados del motor FV (genere en Paso 5).")
    if ctx.resultado_electrico is None:
        errores.append("No hay resultados eléctricos (genere en Paso 5).")
    return (len(errores) == 0), errores

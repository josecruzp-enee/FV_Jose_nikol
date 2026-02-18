# ui/ingenieria_electrica.py
from __future__ import annotations

from typing import List, Tuple

import streamlit as st

from electrical.modelos import ParametrosCableado
from electrical.estimador import calcular_paquete_electrico_desde_inputs

from core.orquestador import ejecutar_evaluacion
from core.modelo import Datosproyecto


# ==========================================================
# Defaults / Helpers (cortos y claros)
# ==========================================================

def _asegurar_dict(ctx, nombre: str) -> dict:
    if nombre not in ctx.__dict__ or ctx.__dict__[nombre] is None:
        ctx.__dict__[nombre] = {}
    if not isinstance(ctx.__dict__[nombre], dict):
        ctx.__dict__[nombre] = {}
    return ctx.__dict__[nombre]


def _defaults_electrico(ctx) -> dict:
    e = _asegurar_dict(ctx, "electrico")
    e.setdefault("vac", 240.0)
    e.setdefault("fases", 1)
    e.setdefault("fp", 1.0)

    e.setdefault("dist_dc_m", 15.0)
    e.setdefault("dist_ac_m", 25.0)

    e.setdefault("vdrop_obj_dc_pct", 2.0)
    e.setdefault("vdrop_obj_ac_pct", 2.0)

    e.setdefault("incluye_neutro_ac", False)
    e.setdefault("otros_ccc", 0)

    e.setdefault("t_min_c", 10.0)
    e.setdefault("dos_aguas", True)
    return e


def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    """
    Consolida TODAS las entradas disponibles del wizard.
    Si faltan campos, deben existir defaults en pasos previos.
    """
    dc = ctx.datos_cliente
    c = ctx.consumo
    s = ctx.sistema_fv

    return Datosproyecto(
        cliente=str(dc.get("cliente", "")).strip(),
        ubicacion=str(dc.get("ubicacion", "")).strip(),

        consumo_12m=[float(x) for x in c.get("kwh_12m", [0.0] * 12)],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0.0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0.0)),

        prod_base_kwh_kwp_mes=float(s.get("produccion_base", 145.0)),
        factores_fv_12m=[float(x) for x in s.get("factores_fv_12m", [1.0] * 12)],
        cobertura_objetivo=float(s.get("offset_pct", 80.0)) / 100.0,

        # Finanzas (defaults temporales; ideal mover a Paso Finanzas)
        costo_usd_kwp=float(s.get("costo_usd_kwp", 1200.0)),
        tcambio=float(s.get("tcambio", 27.0)),
        tasa_anual=float(s.get("tasa_anual", 0.08)),
        plazo_anios=int(s.get("plazo_anios", 10)),
        porcentaje_financiado=float(s.get("porcentaje_financiado", 1.0)),

        # Si tu dataclass lo requiere (tu código ya lo usaba)
        om_anual_pct=float(s.get("om_anual_pct", 0.01)),
    )


def _params_cableado_desde_ui(e: dict) -> ParametrosCableado:
    return ParametrosCableado(
        vac=float(e["vac"]),
        fases=int(e["fases"]),
        fp=float(e["fp"]),
        dist_dc_m=float(e["dist_dc_m"]),
        dist_ac_m=float(e["dist_ac_m"]),
        vdrop_obj_dc_pct=float(e["vdrop_obj_dc_pct"]),
        vdrop_obj_ac_pct=float(e["vdrop_obj_ac_pct"]),
        incluye_neutro_ac=bool(e["incluye_neutro_ac"]),
        otros_ccc=int(e["otros_ccc"]),
        t_min_c=float(e["t_min_c"]),
    )


def _mostrar_resultados(pkg: dict) -> None:
    st.success("Ingeniería eléctrica generada.")

    st.subheader("Strings DC (referencial)")
    for line in (pkg.get("texto_ui", {}).get("strings") or []):
        st.write("• " + line)

    checks = pkg.get("texto_ui", {}).get("checks") or []
    if checks:
        st.warning("\n".join([str(x) for x in checks]))

    st.subheader("Cableado AC/DC (referencial)")
    for line in (pkg.get("texto_ui", {}).get("cableado") or []):
        st.write("• " + line)

    disclaimer = pkg.get("texto_ui", {}).get("disclaimer") or ""
    if disclaimer:
        st.caption(disclaimer)


# ==========================================================
# UI Paso 5
# ==========================================================

def render(ctx) -> None:
    e = _defaults_electrico(ctx)

    # Guardas de consistencia
    if not (ctx.equipos.get("panel_id") and ctx.equipos.get("inversor_id")):
        st.error("Complete la selección de equipos (Paso 4).")
        return

    st.markdown("### Ingeniería eléctrica automática")

    # --- Inputs eléctricos ---
    c1, c2, c3 = st.columns(3)
    with c1:
        e["vac"] = st.number_input("VAC", min_value=100.0, step=1.0, value=float(e["vac"]))
    with c2:
        e["fases"] = st.selectbox("Fases", options=[1, 3], index=[1, 3].index(int(e["fases"])))
    with c3:
        e["fp"] = st.number_input("FP", min_value=0.8, max_value=1.0, step=0.01, value=float(e["fp"]))

    d1, d2 = st.columns(2)
    with d1:
        e["dist_dc_m"] = st.number_input("Distancia DC (m)", min_value=1.0, step=1.0, value=float(e["dist_dc_m"]))
        e["vdrop_obj_dc_pct"] = st.number_input(
            "Vdrop objetivo DC (%)", min_value=0.5, step=0.1, value=float(e["vdrop_obj_dc_pct"])
        )
    with d2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", min_value=1.0, step=1.0, value=float(e["dist_ac_m"]))
        e["vdrop_obj_ac_pct"] = st.number_input(
            "Vdrop objetivo AC (%)", min_value=0.5, step=0.1, value=float(e["vdrop_obj_ac_pct"])
        )

    k1, k2, k3 = st.columns(3)
    with k1:
        e["incluye_neutro_ac"] = st.checkbox("Incluye neutro AC", value=bool(e["incluye_neutro_ac"]))
    with k2:
        e["otros_ccc"] = st.number_input("Otros CCC (agrupamiento)", min_value=0, step=1, value=int(e["otros_ccc"]))
    with k3:
        e["t_min_c"] = st.number_input(
            "T mínima (°C) para Voc frío", min_value=-10.0, step=1.0, value=float(e["t_min_c"])
        )

    e["dos_aguas"] = st.checkbox("Techo dos aguas (reparte strings)", value=bool(e["dos_aguas"]))

    # --- Overrides (UI) -> Config efectiva (core/electrical) ---
    st.session_state["cfg_overrides"] = {
        "tecnicos": {
            "t_min_c": float(e["t_min_c"]),
            "vdrop_obj_dc_pct": float(e["vdrop_obj_dc_pct"]),
            "vdrop_obj_ac_pct": float(e["vdrop_obj_ac_pct"]),
        }
    }

    
    st.divider()

    # --- Ejecutar pipeline ---
    if not st.button("Generar ingeniería eléctrica", type="primary"):
        return

    # 1) Consolidar modelo y guardarlo en ctx (esto resuelve Paso 6)
    datos = _datosproyecto_desde_ctx(ctx)
    ctx.datos_proyecto = datos  # ✅ requerido por Resultados/PDF

    # 2) Ejecutar core (sizing, etc.)
    res = ejecutar_evaluacion(datos)
    ctx.resultado_core = res

    # 3) Ejecutar eléctrico
    params = _params_cableado_desde_ui(e)

    pkg = calcular_paquete_electrico_desde_inputs(
        res=res,
        panel_nombre=str(ctx.equipos["panel_id"]),
        inv_nombre=str(ctx.equipos["inversor_id"]),
        dos_aguas=bool(e["dos_aguas"]),
        params=params,
        t_min_c=float(e["t_min_c"]),
    )
    ctx.resultado_electrico = pkg

    # 4) Mostrar
    _mostrar_resultados(pkg)


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []

    if not (ctx.equipos.get("panel_id") and ctx.equipos.get("inversor_id")):
        errores.append("Falta seleccionar panel e inversor (Paso 4).")

    if ctx.resultado_electrico is None:
        errores.append("Debe generar la ingeniería eléctrica antes de continuar.")

    return (len(errores) == 0), errores

# ui/ingenieria_electrica.py
from __future__ import annotations
from typing import List, Tuple

import streamlit as st

from electrical.modelos import ParametrosCableado
from electrical.estimador import calcular_paquete_electrico_desde_inputs, calcular_iac_estimado

from core.orquestador import ejecutar_evaluacion
from core.modelo import Datosproyecto


def _defaults(ctx) -> None:
    if "electrico" not in ctx.__dict__:
        ctx.electrico = {}

    e = ctx.electrico
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


def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    """
    Fábrica mínima (por ahora).
    En el siguiente paso la movemos a core/ (fabrica_entrada.py) y queda formal.
    """
    dc = ctx.datos_cliente
    c = ctx.consumo
    s = ctx.sistema_fv

    return Datosproyecto(
        cliente=str(dc.get("cliente", "")).strip(),
        ubicacion=str(dc.get("ubicacion", "")).strip(),
        consumo_12m=[float(x) for x in c.get("kwh_12m", [0]*12)],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0.0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0.0)),

        prod_base_kwh_kwp_mes=float(s.get("produccion_base", 145.0)),
        factores_fv_12m=[float(x) for x in s.get("factores_fv_12m", [1.0]*12)],
        cobertura_objetivo=float(s.get("offset_pct", 80.0))/100.0,

        # TODO: mover esto a Paso Finanzas (wizard) y eliminar defaults
        costo_usd_kwp=1200.0,
        tcambio=27.0,
        tasa_anual=0.08,
        plazo_anios=10,
        porcentaje_financiado=1.0,
        om_anual_pct=0.01,
    )


def render(ctx) -> None:
    _defaults(ctx)

    if not ctx.equipos.get("panel_id") or not ctx.equipos.get("inversor_id"):
        st.error("Complete la selección de equipos (Paso 4).")
        return

    st.markdown("### Ingeniería eléctrica automática")

    # Parámetros
    e = ctx.electrico

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
        e["vdrop_obj_dc_pct"] = st.number_input("Vdrop objetivo DC (%)", min_value=0.5, step=0.1, value=float(e["vdrop_obj_dc_pct"]))
    with d2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", min_value=1.0, step=1.0, value=float(e["dist_ac_m"]))
        e["vdrop_obj_ac_pct"] = st.number_input("Vdrop objetivo AC (%)", min_value=0.5, step=0.1, value=float(e["vdrop_obj_ac_pct"]))

    k1, k2, k3 = st.columns(3)
    with k1:
        e["incluye_neutro_ac"] = st.checkbox("Incluye neutro AC", value=bool(e["incluye_neutro_ac"]))
    with k2:
        e["otros_ccc"] = st.number_input("Otros CCC (agrupamiento)", min_value=0, step=1, value=int(e["otros_ccc"]))
    with k3:
        e["t_min_c"] = st.number_input("T mínima (°C) para Voc frío", min_value=-10.0, step=1.0, value=float(e["t_min_c"]))

    e["dos_aguas"] = st.checkbox("Techo dos aguas (reparte strings)", value=bool(e["dos_aguas"]))

    st.divider()

    # Ejecutar (core sizing + eléctrico)
    run = st.button("Generar ingeniería eléctrica", type="primary")

    if not run:
        return

    # 1) Ejecutar core para obtener sizing (n_paneles)
    datos = _datosproyecto_desde_ctx(ctx)
    res = ejecutar_evaluacion(datos)
    ctx.resultado_core = res  # lo guardamos para Paso 6

    # 2) Construir ParametrosCableado
    params = ParametrosCableado(
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

    # 3) Ejecutar eléctrico con API pura
    pkg = calcular_paquete_electrico_desde_inputs(
        res=res,
        panel_nombre=str(ctx.equipos["panel_id"]),
        inv_nombre=str(ctx.equipos["inversor_id"]),
        dos_aguas=bool(e["dos_aguas"]),
        params=params,
        t_min_c=float(e["t_min_c"]),
    )

    ctx.resultado_electrico = pkg

    # 4) Mostrar resumen
    st.success("Ingeniería eléctrica generada.")

    st.subheader("Strings DC (referencial)")
    for line in pkg["texto_ui"]["strings"]:
        st.write("• " + line)
    if pkg["texto_ui"]["checks"]:
        st.warning("\n".join(pkg["texto_ui"]["checks"]))

    st.subheader("Cableado AC/DC (referencial)")
    for line in pkg["texto_ui"]["cableado"]:
        st.write("• " + line)
    st.caption(pkg["texto_ui"]["disclaimer"])


def validar(ctx) -> Tuple[bool, List[str]]:
    errores: List[str] = []
    if not (ctx.equipos.get("panel_id") and ctx.equipos.get("inversor_id")):
        errores.append("Falta seleccionar panel e inversor (Paso 4).")
    if ctx.resultado_electrico is None:
        errores.append("Debe generar la ingeniería eléctrica antes de continuar.")
    return (len(errores) == 0), errores

from __future__ import annotations

"""
PASO 5 — INGENIERÍA ELÉCTRICA
FV Engine (VERSIÓN ESTABLE)
"""

from typing import List, Tuple
import streamlit as st

from core.dominio.modelo import Datosproyecto, InstalacionElectrica, Equipos
from core.aplicacion.orquestador_estudio import ejecutar_estudio
from core.aplicacion.dependencias import construir_dependencias

from ui.validaciones_ui import campos_faltantes_para_paso5
from ui.state_helpers import ensure_dict


# ==========================================================
# UTILIDADES
# ==========================================================
def _fmt(v, unit: str = "") -> str:
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        s = f"{v:.3f}".rstrip("0").rstrip(".")
        return f"{s} {unit}".rstrip() if unit else s
    return str(v)


def _asegurar_dict(ctx, nombre: str) -> dict:
    return ensure_dict(ctx, nombre, dict)


# ==========================================================
# INPUTS ELÉCTRICOS
# ==========================================================
def _ui_inputs_electricos(e: dict):

    st.subheader("Parámetros eléctricos de instalación")

    c1, c2, c3 = st.columns(3)

    with c1:
        e["vac"] = st.number_input(
            "Voltaje AC (V)", 100.0, 600.0,
            float(e.get("vac", 240.0))
        )

    with c2:
        e["fases"] = st.selectbox(
            "Fases", [1, 3],
            index=0 if int(e.get("fases", 1)) == 1 else 1
        )

    with c3:
        e["fp"] = st.number_input(
            "Factor de potencia",
            0.80, 1.00,
            float(e.get("fp", 1.0)),
            step=0.01
        )

    st.markdown("### Distancias")

    d1, d2 = st.columns(2)

    with d1:
        e["dist_dc_m"] = st.number_input(
            "Distancia DC (m)", 1.0,
            value=float(e.get("dist_dc_m", 15.0))
        )

    with d2:
        e["dist_ac_m"] = st.number_input(
            "Distancia AC (m)", 1.0,
            value=float(e.get("dist_ac_m", 25.0))
        )


# ==========================================================
# ctx → DatosProyecto
# ==========================================================
def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf_raw = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")
    e = _asegurar_dict(ctx, "electrico")

    consumo = c.get("consumo_12m", [0] * 12)

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),

        lat=float(sf_raw.get("latitud", 15.8250)),
        lon=float(sf_raw.get("longitud", -87.9500)),

        consumo_12m=[float(x) for x in consumo],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 5.50)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 400)),

        prod_base_kwh_kwp_mes=float(sf_raw.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf_raw.get("factores_fv_12m", [1] * 12)],
        cobertura_objetivo=float(sf_raw.get("cobertura_objetivo", 0.8)),

        costo_usd_kwp=float(sf_raw.get("costo_usd_kwp", 1200)),
        tcambio=float(sf_raw.get("tcambio", 27)),

        tasa_anual=float(sf_raw.get("tasa_anual", 0.08)),
        plazo_anios=int(sf_raw.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf_raw.get("porcentaje_financiado", 1)),

        om_anual_pct=float(sf_raw.get("om_anual_pct", 0.01)),

        instalacion_electrica=InstalacionElectrica(
            vac=float(e.get("vac", 240.0)),
            fases=int(e.get("fases", 1)),
            fp=float(e.get("fp", 1.0)),
            dist_dc_m=float(e.get("dist_dc_m", 15.0)),
            dist_ac_m=float(e.get("dist_ac_m", 25.0)),
        )
    )

    # ======================================================
    # EQUIPOS
    # ======================================================
    p.equipos = Equipos(
        panel_id=eq.get("panel_id"),
        inversor_id=eq.get("inversor_id"),
    )

    # ======================================================
    # 🔥 NORMALIZACIÓN SIZING (CORRECTA Y ROBUSTA)
    # ======================================================
    sf = {}

    # ------------------------------------------------------
    # MULTIZONA
    # ------------------------------------------------------
    if sf_raw.get("usar_zonas"):

        zonas_norm = []

        for i, z in enumerate(sf_raw.get("zonas", [])):

            if z.get("modo") == "Paneles":

                n = int(z.get("n_paneles") or 0)

                if n <= 0:
                    raise ValueError(f"Zona {i+1}: n_paneles inválido")

                zonas_norm.append({
                    "n_paneles": n
                })

            else:

                a = float(z.get("area") or 0.0)

                if a <= 0:
                    raise ValueError(f"Zona {i+1}: área inválida")

                zonas_norm.append({
                    "area": a
                })

        if not zonas_norm:
            raise ValueError("Multizona sin zonas válidas")

        sf["modo"] = "multizona"
        sf["zonas"] = zonas_norm

    # ------------------------------------------------------
    # AUTOMÁTICO / MANUAL SIMPLE
    # ------------------------------------------------------
    else:

        sizing = sf_raw.get("sizing_input", {})

        modo = sizing.get("modo")
        valor = sizing.get("valor")

        # 🔥 VALIDACIONES FUERTES
        if not modo:
            raise ValueError("sizing_input sin 'modo'")

        modos_validos = [
            "cobertura",
            "area",
            "kw_objetivo",
            "paneles"
        ]

        if modo not in modos_validos:
            raise ValueError(f"Modo inválido: {modo}")

        if valor is None or float(valor) <= 0:
            raise ValueError(f"Valor inválido en sizing_input: {sizing}")

        sf["modo"] = modo
        sf["valor"] = float(valor)

    # 🔥 ASIGNACIÓN FINAL
    p.sistema_fv = sf

    return p


# ==========================================================
# MOSTRAR SIZING
# ==========================================================
def _mostrar_sizing(sizing, sistema_fv):

    st.markdown("### 📐 Sizing del sistema FV")

    if not sistema_fv:
        st.warning("Sistema FV no definido")
        return

    col1, col2, col3 = st.columns(3)

    col1.metric("Paneles", getattr(sizing, "n_paneles", 0))
    col2.metric("Potencia DC (kWp)", round(getattr(sizing, "pdc_kw", 0.0), 2))
    col3.metric("Potencia AC (kW)", round(getattr(sizing, "kw_ac", 0.0), 2))

    if sistema_fv.get("modo") == "multizona":
        st.markdown("#### 🔀 Configuración multizona")

        for i, z in enumerate(sistema_fv.get("zonas", []), start=1):
            if "n_paneles" in z:
                st.write(f"Zona {i}: {z['n_paneles']} paneles")
            else:
                st.write(f"Zona {i}: {z.get('area', 0)} m²")


# ==========================================================
# MOSTRAR ELECTRICAL
# ==========================================================
def _mostrar_electrical(electrical):

    st.subheader("Ingeniería eléctrica")

    if electrical is None:
        st.info("Sin resultados eléctricos.")
        return

    ok = getattr(electrical, "ok", False)

    st.success("Cálculo correcto") if ok else st.error("Errores en ingeniería")

    corrientes = getattr(electrical, "corrientes", None)
    conductores = getattr(electrical, "conductores", None)
    protecciones = getattr(electrical, "protecciones", None)

    if corrientes:
        st.markdown("### ⚡ Corrientes")
        c1, c2, c3 = st.columns(3)
        c1.metric("String", f"{corrientes.string.i_diseno_a:.2f} A")
        c2.metric("MPPT", f"{corrientes.mppt.i_diseno_a:.2f} A")
        c3.metric("AC", f"{corrientes.ac.i_diseno_a:.2f} A")

    if conductores and hasattr(conductores, "tramos"):
        st.markdown("### 🧵 Conductores")
        dc = conductores.tramos.dc
        c1, c2, c3 = st.columns(3)
        c1.metric("Calibre", f"{dc.calibre} AWG")
        c2.metric("Ampacidad", f"{dc.ampacidad_ajustada_a} A")
        c3.metric("VD", f"{dc.vd_pct:.2f} %")

    if protecciones:
        st.markdown("### ⚠ Protecciones")
        c1, c2, c3 = st.columns(3)
        c1.metric("Breaker AC", f"{protecciones.ocpd_ac.tamano_a} A")
        c2.metric("DC", f"{protecciones.ocpd_dc_array.tamano_a} A")
        c3.metric("Fusible", f"{protecciones.fusible_string.tamano_a} A")


def _mostrar_trazas(resultado):

    st.markdown("### 🔍 Estado del motor")

    if not hasattr(resultado, "trazas"):
        st.warning("Sin trazas disponibles")
        return

    for k, v in resultado.trazas.items():

        if "OK" in v:
            st.success(f"{k.upper()} → {v}")
        elif "ERROR" in v:
            st.error(f"{k.upper()} → {v}")
        elif "FAIL" in v:
            st.warning(f"{k.upper()} → {v}")
        else:
            st.info(f"{k.upper()} → {v}")

def _mostrar_zonas(paneles, corrientes):

    st.markdown("### 🔀 Zonas FV (reales)")

    if not paneles or not corrientes:
        st.warning("No hay datos de zonas")
        return

    strings = getattr(paneles, "strings", [])
    mppt_detalle = getattr(corrientes, "mppt_detalle", [])

    if not strings:
        st.info("Sin strings disponibles")
        return

    # ======================================================
    # 🔥 AGRUPAR POR LONGITUD DE STRING (CLAVE)
    # ======================================================
    zonas = {}

    for s in strings:

        n = s.n_series  # 🔥 CLAVE

        if n not in zonas:
            zonas[n] = {
                "n_paneles": 0,
                "n_strings": 0
            }

        zonas[n]["n_paneles"] += n
        zonas[n]["n_strings"] += 1

    zonas_list = list(zonas.items())

    # ======================================================
    # MOSTRAR
    # ======================================================
    for i, (n_series, data) in enumerate(zonas_list):

        corriente = mppt_detalle[i] if i < len(mppt_detalle) else None

        st.markdown(f"#### Zona {i+1}")

        c1, c2, c3 = st.columns(3)

        c1.metric("Paneles", data["n_paneles"])
        c2.metric("Strings", data["n_strings"])

        if corriente:
            c3.metric("Corriente", f"{corriente.i_diseno_a:.2f} A")
        else:
            c3.metric("Corriente", "—")
# ==========================================================
# RENDER
# ==========================================================
def render(ctx):

    # ======================================================
    # INPUTS
    # ======================================================
    e = _asegurar_dict(ctx, "electrico")
    _ui_inputs_electricos(e)

    # ======================================================
    # EJECUCIÓN
    # ======================================================
    try:
        p = _datosproyecto_desde_ctx(ctx)
        deps = construir_dependencias()

        resultado = ejecutar_estudio(p, deps)
        ctx.resultado = resultado

    except Exception:
        import traceback
        st.error("Error en motor FV")
        st.code(traceback.format_exc())
        return

    sistema_fv = _asegurar_dict(ctx, "sistema_fv")

    # ======================================================
    # OUTPUTS
    # ======================================================

    if not resultado:
        st.error("No se generó resultado")
        return

    # ======================================================
    # 🔍 TRAZAS (PRIMERO)
    # ======================================================
    _mostrar_trazas(resultado)

    # ======================================================
    # 🔹 SIZING
    # ======================================================
    if getattr(resultado, "sizing", None):
        _mostrar_sizing(resultado.sizing, sistema_fv)
    else:
        st.warning("Sizing no disponible")

    # ======================================================
    # 🔀 ZONAS FV
    # ======================================================
    if resultado and resultado.strings and resultado.electrical:
        _mostrar_zonas(resultado.strings, resultado.electrical.corrientes)
        
    # ======================================================
    # ⚡ ELECTRICAL (SIEMPRE MOSTRAR)
    # ======================================================
    st.markdown("## ⚡ Ingeniería eléctrica")

    electrical = getattr(resultado, "electrical", None)

    # 🔥 CLAVE: usar trazas para explicar
    trazas = getattr(resultado, "trazas", {})

    if electrical is None:

        motivo = trazas.get("electrical", "No ejecutado")

        if "ERROR" in motivo:
            st.error(f"Electrical falló → {motivo}")
        elif motivo == "NONE":
            st.warning("Electrical no devolvió resultados")
        else:
            st.info(f"Electrical no disponible → {motivo}")

    else:
        _mostrar_electrical(electrical)
# ==========================================================
# VALIDACIÓN
# ==========================================================
def validar(ctx) -> Tuple[bool, List[str]]:

    if not getattr(ctx, "resultado", None):
        return False, ["Debe generar ingeniería."]

    return True, []

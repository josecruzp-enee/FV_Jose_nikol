from __future__ import annotations

"""
PASO 5 — INGENIERÍA ELÉCTRICA
FV Engine
"""

from typing import List, Tuple
import streamlit as st

from core.dominio.modelo import Datosproyecto
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
        e["vac"] = st.number_input("Voltaje AC (V)", 100.0, 600.0, float(e.get("vac", 240.0)))

    with c2:
        e["fases"] = st.selectbox("Fases", [1, 3], index=0 if int(e.get("fases", 1)) == 1 else 1)

    with c3:
        e["fp"] = st.number_input("Factor de potencia", 0.80, 1.00, float(e.get("fp", 1.0)), step=0.01)

    st.markdown("### Distancias")

    d1, d2 = st.columns(2)

    with d1:
        e["dist_dc_m"] = st.number_input("Distancia DC (m)", 1.0, value=float(e.get("dist_dc_m", 15.0)))

    with d2:
        e["dist_ac_m"] = st.number_input("Distancia AC (m)", 1.0, value=float(e.get("dist_ac_m", 25.0)))


# ==========================================================
# ctx → DatosProyecto
# ==========================================================

def _datosproyecto_desde_ctx(ctx) -> Datosproyecto:

    dc = _asegurar_dict(ctx, "datos_cliente")
    c = _asegurar_dict(ctx, "consumo")
    sf = _asegurar_dict(ctx, "sistema_fv")
    eq = _asegurar_dict(ctx, "equipos")
    e = _asegurar_dict(ctx, "electrico")

    consumo = c.get("kwh_12m", [0] * 12)

    if "panel_id" not in eq:
        eq["panel_id"] = "JA_550"

    if "inversor_id" not in eq:
        eq["inversor_id"] = "HUAWEI_50K"

    p = Datosproyecto(
        cliente=str(dc.get("cliente", "")),
        ubicacion=str(dc.get("ubicacion", "")),

        lat=float(sf.get("latitud", 15.8250)),
        lon=float(sf.get("longitud", -87.9500)),

        consumo_12m=[float(x) for x in consumo],
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 5.50)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 400)),

        prod_base_kwh_kwp_mes=float(sf.get("produccion_base_kwh_kwp_mes", 145)),
        factores_fv_12m=[float(x) for x in sf.get("factores_fv_12m", [1] * 12)],
        cobertura_objetivo=float(sf.get("cobertura_objetivo", 0.8)),

        costo_usd_kwp=float(sf.get("costo_usd_kwp", 1200)),
        tcambio=float(sf.get("tcambio", 27)),

        tasa_anual=float(sf.get("tasa_anual", 0.08)),
        plazo_anios=int(sf.get("plazo_anios", 10)),
        porcentaje_financiado=float(sf.get("porcentaje_financiado", 1)),

        om_anual_pct=float(sf.get("om_anual_pct", 0.01)),

        instalacion_electrica=dict(e)
    )

    # Equipos
    p.equipos = dict(eq)

    # 🔥 SISTEMA FV (clave)
    p.sistema_fv = dict(sf)

    return p


# ==========================================================
# MOSTRAR SIZING (MEJORADO)
# ==========================================================

def _mostrar_sizing(sizing, sistema_fv):

    st.subheader("Sizing del sistema FV")

    modo = sistema_fv.get("modo_diseno", "manual")

    if modo == "zonas":
        st.info("Modo: Diseño por zonas")
    else:
        st.info("Modo: Diseño por cantidad / consumo")

    c1, c2, c3 = st.columns(3)

    c1.metric("Paneles", sizing.n_paneles)
    c2.metric("Potencia DC", f"{sizing.pdc_kw} kWp")
    c3.metric("Potencia AC", f"{sizing.kw_ac} kW")

    # 🔥 MOSTRAR ZONAS
    if modo == "zonas":

        st.markdown("### Zonas consideradas")

        for z in sistema_fv.get("zonas", []):
            st.write(
                f"- {z.get('nombre')}: "
                f"{z.get('area')} m² | "
                f"{z.get('azimut')}° | "
                f"{z.get('inclinacion')}°"
            )


# ==========================================================
# MOSTRAR NEC
# ==========================================================
def _safe_show(obj):
    import pandas as pd
    import streamlit as st

    try:
        if isinstance(obj, dict):
            df = pd.DataFrame([obj])
        elif isinstance(obj, list):
            df = pd.DataFrame(obj)
        else:
            st.write(str(obj))
            return

        df = df.astype(str)   # 🔥 CLAVE: evita error Arrow
        st.dataframe(df, width="stretch")

    except Exception:
        st.write(str(obj))


def _mostrar_nec(nec):

    import streamlit as st

    st.subheader("Ingeniería eléctrica")

    if nec is None:
        st.info("Sin resultados eléctricos.")
        return

    if not getattr(nec, "ok", False):
        st.error("Error en cálculo eléctrico")

        for err in getattr(nec, "errores", []):
            st.write(f"• {err}")

        return

    st.success("Cálculo eléctrico correcto")

    # 🔥 RESULTADOS
    if hasattr(nec, "corrientes"):
        st.write("### Corrientes")
        _safe_show(nec.corrientes)

    if hasattr(nec, "conductores"):
        st.write("### Conductores")
        _safe_show(nec.conductores)

    if hasattr(nec, "protecciones"):
        st.write("### Protecciones")
        _safe_show(nec.protecciones)
# ==========================================================
# RENDER PRINCIPAL
# ==========================================================

def render(ctx):

    e = _asegurar_dict(ctx, "electrico")

    _ui_inputs_electricos(e)

    st.markdown("### Ingeniería eléctrica automática")

    faltantes = campos_faltantes_para_paso5(ctx)

    if faltantes:
        st.warning("Complete los datos requeridos antes de generar ingeniería.")

    if not st.button("Generar ingeniería", disabled=bool(faltantes)):
        return

    try:

        datos = _datosproyecto_desde_ctx(ctx)

        ctx.datos_proyecto = datos

        deps = construir_dependencias()

        resultado = ejecutar_estudio(datos, deps)
        st.write("DEBUG RESULTADO COMPLETO:", resultado)
        st.write("DEBUG ELECTRICO:", getattr(resultado, "nec", None))

        ctx.resultado_proyecto = resultado

        st.success("Ingeniería generada correctamente.")

        _mostrar_sizing(resultado.sizing, datos.sistema_fv)
        resultado_electrico = getattr(resultado, "nec", None) or getattr(resultado, "electrical", None)
        _mostrar_nec(resultado_electrico)

    except Exception as e:

        msg = str(e)

        if "DC/AC" in msg:
            st.error(msg)

            try:
                datos = _datosproyecto_desde_ctx(ctx)

                if hasattr(ctx, "resultado_proyecto") and ctx.resultado_proyecto:
                    pdc = ctx.resultado_proyecto.sizing.pdc_kw
                else:
                    pdc = None

                if pdc:
                    pac_obj = pdc / 1.2
                    st.info(f"Inversor recomendado ≈ {pac_obj:.1f} kW AC")

            except Exception:
                pass

        else:
            import traceback
            st.error("Error en motor FV")
            st.code(traceback.format_exc())

        st.stop()


# ==========================================================
# VALIDACIÓN
# ==========================================================

def validar(ctx) -> Tuple[bool, List[str]]:

    errores = []

    if not getattr(ctx, "resultado_proyecto", None):
        errores.append("Debe generar ingeniería.")

    return len(errores) == 0, errores

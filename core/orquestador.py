# nucleo/orquestador.py
from __future__ import annotations

from typing import Any, Dict
from typing import Any, Dict, Tuple
from .validacion import validar_entradas
from .sizing import calcular_sizing_unificado
from .simular_12_meses import simular_12_meses, calcular_cuota_mensual
from .evaluacion import evaluar_viabilidad, resumen_decision_mensual, payback_simple
from .finanzas_lp import proyectar_flujos_anuales
from .electrico_ref import simular_electrico_fv_para_pdf
from .modelo import Datosproyecto
from electrical.adaptador_nec import generar_electrico_nec
from core.sistema_fv_mapper import construir_parametros_fv_desde_dict
from electrical.adaptador_nec import generar_electrico_nec

# =========================
# Helpers (locales y seguros)
# =========================
def _set_attr_safe(obj: Any, name: str, value: Any) -> None:
    """Setea atributo si es posible; si el dataclass es frozen o no tiene campo, no revienta."""
    try:
        setattr(obj, name, value)
    except Exception:
        pass


def _consolidar_parametros_fv_en_datos(p: Datosproyecto, params_fv: Dict[str, Any]) -> None:
    """
    Consolidación: aplica lo mínimo que el motor DEBE consumir, y guarda trazabilidad.
    - Obligatorio para motor: prod_base_kwh_kwp_mes, factores_fv_12m
    - Trazabilidad: hsp, pérdidas, sombras, geometría (y dos aguas si aplica)
    """
    # --- contrato mínimo motor ---
    _set_attr_safe(p, "prod_base_kwh_kwp_mes", float(params_fv["prod_base_kwh_kwp_mes"]))
    _set_attr_safe(p, "factores_fv_12m", list(params_fv["factores_fv_12m"]))

    # --- trazabilidad útil ---
    _set_attr_safe(p, "hsp", float(params_fv.get("hsp", 0.0)))
    _set_attr_safe(p, "perdidas_sistema_pct", float(params_fv.get("perdidas_sistema_pct", 0.0)))
    _set_attr_safe(p, "sombras_pct", float(params_fv.get("sombras_pct", 0.0)))
    _set_attr_safe(p, "azimut_deg", float(params_fv.get("azimut_deg", 180.0)))
    _set_attr_safe(p, "inclinacion_deg", float(params_fv.get("inclinacion_deg", 0.0)))
    _set_attr_safe(p, "tipo_superficie", str(params_fv.get("tipo_superficie", "plano")))

    # --- dos aguas (opcional) ---
    if params_fv.get("tipo_superficie") == "dos_aguas":
        _set_attr_safe(p, "azimut_a_deg", float(params_fv.get("azimut_a_deg", 180.0)))
        _set_attr_safe(p, "azimut_b_deg", float(params_fv.get("azimut_b_deg", 0.0)))
        _set_attr_safe(p, "reparto_pct_a", float(params_fv.get("reparto_pct_a", 50.0)))

    # --- siempre guardamos el dict limpio (útil para PDF / debug / pruebas) ---
    _set_attr_safe(p, "params_fv", dict(params_fv))


# =========================
# Orquestador (pipeline lineal)
# =========================




def ejecutar_evaluacion(p: Datosproyecto) -> Dict[str, Any]:
    validar_entradas(p)
    params_fv = _params_y_consolidacion(p)
    sizing = calcular_sizing_unificado(p)
    electrico_nec = _build_electrico_nec_safe(p, sizing)
    kwp_dc, capex_L = _extraer_kwp_y_capex(sizing)
    cuota, tabla = _cuota_y_tabla_12m(p, kwp_dc, capex_L)
    eval_, decision, ahorro_anual, pb = _evaluacion_y_payback(p, tabla, cuota, capex_L)
    electrico = _build_electrico_ref_para_pdf(sizing)
    return _armar_salida(params_fv, sizing, cuota, tabla, eval_, decision, ahorro_anual, pb, electrico, electrico_nec, p)


# ==========================================================
# Helpers
# ==========================================================
def _params_y_consolidacion(p: Datosproyecto) -> Dict[str, Any]:
    params_fv = _build_params_fv(p)
    _consolidar_parametros_fv_en_datos(p, params_fv)
    return params_fv


def _cuota_y_tabla_12m(p: Datosproyecto, kwp_dc: float, capex_L: float) -> Tuple[float, Any]:
    cuota = _calcular_cuota(p, capex_L)
    tabla = simular_12_meses(p, kwp_dc, cuota, capex_L)
    return cuota, tabla


def _evaluacion_y_payback(p: Datosproyecto, tabla: Any, cuota: float, capex_L: float) -> Tuple[Any, Any, float, float]:
    eval_ = evaluar_viabilidad(tabla, cuota)
    decision = resumen_decision_mensual(tabla, cuota, p)
    ahorro_anual = sum(float(x.get("ahorro_L", 0.0)) for x in tabla)
    pb = payback_simple(float(capex_L), float(ahorro_anual))
    return eval_, decision, ahorro_anual, pb


def _armar_salida(
    params_fv: Dict[str, Any],
    sizing: Dict[str, Any],
    cuota: float,
    tabla: Any,
    eval_: Any,
    decision: Any,
    ahorro_anual: float,
    pb: float,
    electrico: Any,
    electrico_nec: Dict[str, Any],
    p: Datosproyecto,
) -> Dict[str, Any]:
    finanzas_lp = proyectar_flujos_anuales(
        datos=p,
        resultado={"sizing": sizing, "cuota_mensual": cuota, "tabla_12m": tabla},
        horizonte_anios=15,
        crecimiento_tarifa_anual=0.06,
        degradacion_fv_anual=0.006,
        tasa_descuento=0.14,
        reemplazo_inversor_anio=12,
        reemplazo_inversor_pct_capex=0.15,
    )
    return {
        "params_fv": params_fv,
        "sizing": sizing,
        "cuota_mensual": cuota,
        "tabla_12m": tabla,
        "evaluacion": eval_,
        "decision": decision,
        "ahorro_anual_L": ahorro_anual,
        "payback_simple_anios": pb,
        "electrico": electrico,
        "electrico_nec": electrico_nec,
        "finanzas_lp": finanzas_lp,
    }


def _build_params_fv(p: Datosproyecto) -> Dict[str, Any]:
    sfv = getattr(p, "sistema_fv", None) or {}
    if not isinstance(sfv, dict):
        sfv = {}
    return construir_parametros_fv_desde_dict(sfv)


def _build_electrico_nec_safe(p: Datosproyecto, sizing: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from electrical.adaptador_nec import generar_electrico_nec
        return generar_electrico_nec(p=p, sizing=sizing)
    except Exception as e:
        return {"ok": False, "errores": [f"NEC: {type(e).__name__}: {e}"], "input": {}}


def _extraer_kwp_y_capex(sizing: Dict[str, Any]) -> Tuple[float, float]:
    kwp_dc = float(sizing.get("kwp_dc") or sizing.get("kwp") or sizing.get("pdc_kw") or 0.0)
    capex_L = float(sizing.get("capex_L") or sizing.get("capex") or 0.0)
    if kwp_dc <= 0 or capex_L <= 0:
        raise KeyError(
            f"sizing incompleto: kwp_dc={kwp_dc}, capex_L={capex_L}. keys={sorted(list((sizing or {}).keys()))}"
        )
    return kwp_dc, capex_L


def _calcular_cuota(p: Datosproyecto, capex_L: float) -> float:
    return calcular_cuota_mensual(
        capex_L_=float(capex_L),
        tasa_anual=float(p.tasa_anual),
        plazo_anios=int(p.plazo_anios),
        pct_fin=float(p.porcentaje_financiado),
    )


def _build_electrico_ref_para_pdf(sizing: Dict[str, Any]) -> Any:
    cfg = sizing.get("cfg_strings") or {}
    strings = cfg.get("strings") or []
    iac = cfg.get("iac_estimada_a", None)
    if not strings or iac is None:
        return None

    vmp_string = max(float(s.get("vmp_string_v", 0.0)) for s in strings)
    imp = max(float(s.get("imp_a", 0.0)) for s in strings)
    isc = max(float(s.get("isc_a", 0.0)) for s in strings)
    if vmp_string <= 0 or imp <= 0 or isc <= 0:
        return None

    return simular_electrico_fv_para_pdf(
        v_ac=240.0,
        i_ac_estimado=float(iac),
        dist_ac_m=15.0,
        objetivo_vdrop_ac_pct=2.0,
        vmp_string_v=vmp_string,
        imp_a=imp,
        isc_a=isc,
        dist_dc_m=10.0,
        objetivo_vdrop_dc_pct=2.0,
        incluye_neutro_ac=False,
        otros_ccc_en_misma_tuberia=0,
    )

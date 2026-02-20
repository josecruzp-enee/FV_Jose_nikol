# nucleo/orquestador.py
from __future__ import annotations

from typing import Any, Dict

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
    # 1) Entradas + Validación
    validar_entradas(p)

    # 2) Cálculos (mapper UI->motor)
    sfv = getattr(p, "sistema_fv", None) or {}
    if not isinstance(sfv, dict):
        sfv = {}

    params_fv = construir_parametros_fv_desde_dict(sfv)

    # 3) Consolidación (aplicar params FV al modelo)
    _consolidar_parametros_fv_en_datos(p, params_fv)

    # 4) Cálculos (sizing, cuota, simulación)
    sizing = calcular_sizing_unificado(p)
    # ===== NUEVO (NEC ENGINE) =====
    from electrical.adaptador_nec import generar_electrico_nec
    electrico_nec = generar_electrico_nec(p=p, sizing=sizing)
    # ===============================

cuota = calcular_cuota_mensual(
    cuota = calcular_cuota_mensual(
        capex_L_=float(sizing["capex_L"]),
        tasa_anual=p.tasa_anual,
        plazo_anios=p.plazo_anios,
        pct_fin=p.porcentaje_financiado,
    )
    
    tabla = simular_12_meses(p, float(sizing["kwp_dc"]), cuota, float(sizing["capex_L"]))
    eval_ = evaluar_viabilidad(tabla, cuota)
    decision = resumen_decision_mensual(tabla, cuota, p)

    ahorro_anual = sum(float(x["ahorro_L"]) for x in tabla)
    pb = payback_simple(float(sizing["capex_L"]), ahorro_anual)

    # 5) Salidas auxiliares (eléctrico ref para PDF)
    electrico = None
    cfg = sizing.get("cfg_strings") or {}
    strings = cfg.get("strings") or []
    if strings and (cfg.get("iac_estimada_a") is not None):
        vmp_string = max(float(s["vmp_string_v"]) for s in strings)
        imp = max(float(s["imp_a"]) for s in strings)
        isc = max(float(s["isc_a"]) for s in strings)

        electrico = simular_electrico_fv_para_pdf(
            v_ac=240.0,
            i_ac_estimado=float(cfg["iac_estimada_a"]),
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

    # 6) Finanzas largo plazo
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
        "params_fv": params_fv,  # útil para debug / PDF
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

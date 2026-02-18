from nucleo.validacion import validar_entradas
from nucleo.sizing import calcular_sizing_unificado
from nucleo.simulacion_12m import simular_12_meses, calcular_cuota_mensual
from nucleo.evaluacion import evaluar_viabilidad, resumen_decision_mensual, payback_simple
from nucleo.finanzas_lp import proyectar_flujos_anuales
from nucleo.electrico_ref import simular_electrico_fv_para_pdf

def ejecutar_evaluacion(p):
    validar_entradas(p)

    sizing = calcular_sizing_unificado(p)

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

    # eléctrico (opcional)
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
        )

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
        "sizing": sizing,
        "cuota_mensual": cuota,
        "tabla_12m": tabla,
        "evaluacion": eval_,
        "decision": decision,
        "ahorro_anual_L": ahorro_anual,
        "payback_simple_anios": pb,
        "electrico": electrico,
        "finanzas_lp": finanzas_lp,
    }

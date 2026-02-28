# core/orquestador.py
from __future__ import annotations

from typing import Any, Dict, Tuple

from .validacion import validar_entradas
from .sizing import calcular_sizing_unificado
from .simular_12_meses import simular_12_meses, calcular_cuota_mensual
from .evaluacion import evaluar_viabilidad, resumen_decision_mensual, payback_simple
from .finanzas_lp import proyectar_flujos_anuales
from .modelo import Datosproyecto
from .result_accessors import get_capex_L, get_kwp_dc
from core.sistema_fv_mapper import construir_parametros_fv_desde_dict


# ==========================================================
# Helpers seguros
# ==========================================================
def _set_attr_safe(obj: Any, name: str, value: Any) -> None:
    try:
        setattr(obj, name, value)
    except Exception:
        pass


def _consolidar_parametros_fv_en_datos(p: Datosproyecto, params_fv: Dict[str, Any]) -> None:
    # contrato mínimo para el motor energético
    _set_attr_safe(p, "prod_base_kwh_kwp_mes", float(params_fv["prod_base_kwh_kwp_mes"]))
    _set_attr_safe(p, "factores_fv_12m", list(params_fv["factores_fv_12m"]))

    # trazabilidad
    _set_attr_safe(p, "hsp", float(params_fv.get("hsp", 0.0)))
    _set_attr_safe(p, "perdidas_sistema_pct", float(params_fv.get("perdidas_sistema_pct", 0.0)))
    _set_attr_safe(p, "sombras_pct", float(params_fv.get("sombras_pct", 0.0)))
    _set_attr_safe(p, "azimut_deg", float(params_fv.get("azimut_deg", 180.0)))
    _set_attr_safe(p, "inclinacion_deg", float(params_fv.get("inclinacion_deg", 0.0)))
    _set_attr_safe(p, "tipo_superficie", str(params_fv.get("tipo_superficie", "plano")))

    if params_fv.get("tipo_superficie") == "dos_aguas":
        _set_attr_safe(p, "azimut_a_deg", float(params_fv.get("azimut_a_deg", 180.0)))
        _set_attr_safe(p, "azimut_b_deg", float(params_fv.get("azimut_b_deg", 0.0)))
        _set_attr_safe(p, "reparto_pct_a", float(params_fv.get("reparto_pct_a", 50.0)))

    _set_attr_safe(p, "params_fv", dict(params_fv))


# ==========================================================
# ENTRYPOINT LEGACY (se mantiene)
# ==========================================================
def ejecutar_evaluacion(p: Datosproyecto) -> Dict[str, Any]:
    validar_entradas(p)

    params_fv = _params_y_consolidacion(p)
    sizing = calcular_sizing_unificado(p)

    electrico_nec = _build_electrico_nec_safe(p, sizing)

    kwp_dc, capex_l = _extraer_kwp_y_capex(sizing)
    cuota, tabla = _cuota_y_tabla_12m(p, kwp_dc, capex_l)

    eval_, decision, ahorro_anual, pb = _evaluacion_y_payback(p, tabla, cuota, capex_l)

    return _armar_salida(
        params_fv=params_fv,
        sizing=sizing,
        cuota=cuota,
        tabla=tabla,
        eval_=eval_,
        decision=decision,
        ahorro_anual=ahorro_anual,
        pb=pb,
        electrico_nec=electrico_nec,
        p=p,
    )


# ==========================================================
# ENTRYPOINT OFICIAL (ARQUITECTURA)
# ==========================================================
def ejecutar_estudio(p: Datosproyecto) -> Dict[str, Any]:
    """
    Flujo lineal estricto:
    Entradas → Sizing → Strings → NEC → Financiero
    NEC SIEMPRE se ejecuta.
    """

    # -------------------------------------------------
    # 1️⃣ Validaciones base
    # -------------------------------------------------
    validar_entradas(p)

    params_fv = _params_y_consolidacion(p)

    # -------------------------------------------------
    # 2️⃣ SIZING
    # -------------------------------------------------
    sizing = calcular_sizing_unificado(p)

    if not sizing or sizing.get("n_paneles", 0) <= 0:
        raise ValueError("Sizing inválido.")

    # -------------------------------------------------
    # 3️⃣ Selección de equipos
    # -------------------------------------------------
    from electrical.catalogos.catalogos import get_panel, get_inversor
    from electrical.paneles.orquestador_paneles import ejecutar_calculo_strings
    from electrical.paquete_nec import armar_paquete_nec

    panel = get_panel(sizing.get("panel_id"))
    inversor = get_inversor(sizing.get("inversor_recomendado"))

    pdc_kw = float(sizing.get("pdc_kw", 0.0))
    pac_kw = float(getattr(inversor, "kw_ac", 0.0))

    # -------------------------------------------------
    # 4️⃣ DC/AC ratio (warning, NO bloqueo)
    # -------------------------------------------------
    dc_ac_warning = None
    if pac_kw > 0:
        dc_ac_ratio = pdc_kw / pac_kw
        if dc_ac_ratio < 0.8 or dc_ac_ratio > 1.35:
            dc_ac_warning = f"DC/AC ratio fuera de rango ({dc_ac_ratio:.2f})."

    # -------------------------------------------------
    # 5️⃣ STRINGS (NO corta flujo)
    # -------------------------------------------------
    res_strings = ejecutar_calculo_strings(
        n_paneles_total=int(sizing["n_paneles"]),
        panel=panel,
        inversor=inversor,
        t_min_c=float(getattr(p, "t_min_c", 10.0)),
        dos_aguas=bool(getattr(p, "dos_aguas", False)),
        objetivo_dc_ac=(pdc_kw / pac_kw) if pac_kw > 0 else None,
        pdc_kw_objetivo=float(pdc_kw),
    )
    
    sizing["strings"] = res_strings
    strings_warning = None
    strings_errors = []

    if not res_strings.get("ok"):
        strings_warning = "Strings inválido."
        strings_errors = list(res_strings.get("errores") or [])

    # -------------------------------------------------
    # 6️⃣ NEC (SIEMPRE)
    # -------------------------------------------------
    nec_input = {
        "potencia_dc_kw": pdc_kw,
        "potencia_ac_kw": pac_kw,
        "vdc_nom": (res_strings.get("recomendacion") or {}).get("vmp_string_v"),
        "n_strings": res_strings.get("n_strings"),
        "isc_mod_a": res_strings.get("isc_mod_a"),
        "vac_ll": getattr(p, "vac", 240.0),
        "fases": getattr(p, "fases", 1),
        "fp": getattr(p, "fp", 1.0),
        "dist_dc_m": getattr(p, "dist_dc_m", 15.0),
        "dist_ac_m": getattr(p, "dist_ac_m", 25.0),
        "vdrop_obj_dc_pct": getattr(p, "vdrop_obj_dc_pct", 2.0),
        "vdrop_obj_ac_pct": getattr(p, "vdrop_obj_ac_pct", 2.0),
    }

    paq = armar_paquete_nec(nec_input)

    electrico_nec = {
        "ok": True,
        "errores": [],
        "warnings": [],
        "paq": paq,
    }

    if dc_ac_warning:
        electrico_nec["warnings"].append(dc_ac_warning)

    if strings_warning:
        electrico_nec["warnings"].append(strings_warning)

    if strings_errors:
        electrico_nec["warnings"].extend(strings_errors)

    # -------------------------------------------------
    # 7️⃣ FINANCIERO
    # -------------------------------------------------
    kwp_dc, capex_l = _extraer_kwp_y_capex(sizing)
    cuota, tabla = _cuota_y_tabla_12m(p, kwp_dc, capex_l)

    eval_, decision, ahorro_anual, pb = _evaluacion_y_payback(
        p, tabla, cuota, capex_l
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

    # -------------------------------------------------
    # 8️⃣ SALIDA FINAL
    # -------------------------------------------------
    return {
        "params_fv": params_fv,
        "sizing": sizing,
        "cuota_mensual": cuota,
        "tabla_12m": tabla,
        "evaluacion": eval_,
        "decision": decision,
        "ahorro_anual_L": ahorro_anual,
        "payback_simple_anios": pb,
        "electrico_nec": electrico_nec,
        "finanzas_lp": finanzas_lp,
    }

# ==========================================================
# Helpers pipeline
# ==========================================================
def _params_y_consolidacion(p: Datosproyecto) -> Dict[str, Any]:
    params_fv = _build_params_fv(p)
    _consolidar_parametros_fv_en_datos(p, params_fv)
    return params_fv


def _cuota_y_tabla_12m(p: Datosproyecto, kwp_dc: float, capex_l: float) -> Tuple[float, Any]:
    cuota = _calcular_cuota(p, capex_l)
    tabla = simular_12_meses(p, kwp_dc, cuota, capex_l)
    return cuota, tabla


def _evaluacion_y_payback(p: Datosproyecto, tabla: Any, cuota: float, capex_l: float):
    eval_ = evaluar_viabilidad(tabla, cuota)
    decision = resumen_decision_mensual(tabla, cuota, p)
    ahorro_anual = sum(float(x.get("ahorro_L", 0.0)) for x in (tabla or []))
    pb = payback_simple(float(capex_l), float(ahorro_anual))
    return eval_, decision, ahorro_anual, pb


def _armar_salida(
    *,
    params_fv: Dict[str, Any],
    sizing: Dict[str, Any],
    cuota: float,
    tabla: Any,
    eval_: Any,
    decision: Any,
    ahorro_anual: float,
    pb: float,
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
        # Unificado: un solo paquete eléctrico para UI/PDF
        "electrico_nec": electrico_nec,
        "finanzas_lp": finanzas_lp,
    }


def _build_params_fv(p: Datosproyecto) -> Dict[str, Any]:
    sfv = getattr(p, "sistema_fv", None) or {}
    if not isinstance(sfv, dict):
        sfv = {}
    return construir_parametros_fv_desde_dict(sfv)


def _build_electrico_nec_safe(p: Datosproyecto, sizing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper seguro para construir el paquete NEC.
    Contrato de salida:
      { ok: bool, errores: [..], input: {...}, paq: {...} }
    """
    try:
        from electrical.paquete_nec import armar_paquete_nec

        # -----------------------------
        # 1) Fuente canónica de inputs
        # -----------------------------
        s = dict(sizing or {})
        entrada_electrica = (s.get("electrico") or s.get("electrico_inputs") or {})  # ✅ FIX
        if not isinstance(entrada_electrica, dict) or not entrada_electrica:
            return {"ok": False, "errores": ["NEC: sizing sin 'electrico_inputs' (ni 'electrico')"], "input": {}, "paq": {}}

        # Copia defensiva (evita mutar el dict original)
        ee = dict(entrada_electrica)

        # -----------------------------
        # 2) Enriquecer potencias base
        # -----------------------------
        # sizing trae pdc_kw y pac_kw (según tu calcular_sizing_unificado)
        try:
            pdc_kw = float(s.get("pdc_kw", 0.0) or 0.0)
        except Exception:
            pdc_kw = 0.0

        try:
            pac_kw = float(s.get("pac_kw", 0.0) or 0.0)
        except Exception:
            pac_kw = 0.0

        if pdc_kw > 0 and "potencia_dc_kw" not in ee and "potencia_dc_w" not in ee:
            ee["potencia_dc_kw"] = pdc_kw

        if pac_kw > 0 and "potencia_ac_kw" not in ee and "potencia_ac_w" not in ee:
            ee["potencia_ac_kw"] = pac_kw

        # Voltaje AC: si es 1φ, usa vac_ln; si es 3φ, usa vac_ll.
        # (paquete_nec ya intenta inferir, pero lo dejamos claro)
        vac = ee.get("vac", None)
        fases = ee.get("fases", None)
        try:
            vac_f = float(vac) if vac is not None else None
        except Exception:
            vac_f = None

        try:
            fases_i = int(fases) if fases is not None else None
        except Exception:
            fases_i = None

        if vac_f is not None:
            if fases_i == 3:
                ee.setdefault("vac_ll", vac_f)
            else:
                ee.setdefault("vac_ln", vac_f)

        # --------------------------------------
        # 3) Calcular STRINGS (para DC “real”)
        # --------------------------------------
        # Esto NO dimensiona NEC; solo produce:
        # - n_strings_total, voc_frio_string_v, vmp_string_v, etc.
        try:
            from electrical.catalogos.catalogos import get_panel, get_inversor
            from electrical.paneles.calculo_de_strings import (
                PanelSpec,
                InversorSpec,
                calcular_strings_fv,
            )

            eq = getattr(p, "equipos", {}) or {}
            panel_id = (eq or {}).get("panel_id")
            inversor_id = (eq or {}).get("inversor_id")

            if panel_id and inversor_id:
                pan = get_panel(panel_id)
                inv = get_inversor(inversor_id)

                # Normalización a contrato interno estable (PanelSpec/InversorSpec)
                # Panel catálogo: w,vmp,voc,imp,isc,tc_voc_frac_c
                coef_voc_pct_c = float(getattr(pan, "tc_voc_frac_c", -0.0029) or -0.0029) * 100.0  # frac/°C → %/°C

                panel_spec = PanelSpec(
                    pmax_w=float(getattr(pan, "w")),
                    vmp_v=float(getattr(pan, "vmp")),
                    voc_v=float(getattr(pan, "voc")),
                    imp_a=float(getattr(pan, "imp")),
                    isc_a=float(getattr(pan, "isc")),
                    coef_voc_pct_c=float(coef_voc_pct_c),
                    # coef_vmp_pct_c queda default (-0.34) en tu dataclass
                )

                imppt = getattr(inv, "imppt_max", None)
                if imppt is None:
                    # fallback ultra alto para no falsear corriente (como tú ya haces)
                    imppt = 1e9

                inversor_spec = InversorSpec(
                    pac_kw=float(getattr(inv, "kw_ac")),
                    vdc_max_v=float(getattr(inv, "vdc_max_v", getattr(inv, "vdc_max"))),  # tolera legacy
                    mppt_min_v=float(getattr(inv, "vmppt_min")),
                    mppt_max_v=float(getattr(inv, "vmppt_max")),
                    n_mppt=int(getattr(inv, "n_mppt", 1) or 1),
                    imppt_max_a=float(imppt),
                )

                # n_paneles_total: sizing["n_paneles"]
                n_paneles_total = int(s.get("n_paneles") or 0)
                t_min_c = float(ee.get("t_min_c", 10.0) or 10.0)
                dos_aguas = bool(ee.get("dos_aguas", True))

                strings = calcular_strings_fv(
                    n_paneles_total=n_paneles_total,
                    panel=panel_spec,
                    inversor=inversor_spec,
                    t_min_c=t_min_c,
                    dos_aguas=dos_aguas,
                    objetivo_dc_ac=float((s.get("traza") or {}).get("dc_ac_objetivo", 1.2) or 1.2),
                    pdc_kw_objetivo=float(pdc_kw) if pdc_kw > 0 else None,
                    t_oper_c=55.0,
                )

                ee["strings"] = strings

                # Usar Vmp string como Vdc nominal para conductores (si no venía)
                try:
                    vdc_nom = (strings.get("recomendacion") or {}).get("vmp_string_v")
                    if vdc_nom and "vdc_nom" not in ee and "vdc" not in ee:
                        ee["vdc_nom"] = float(vdc_nom)
                except Exception:
                    pass

        except Exception:
            # Si strings falla, NEC igual corre con lo base
            pass

        # ------------------------------------------------
        # 4) Circuitos mínimos (DC y AC) para conductores
        # ------------------------------------------------
        # paquete_nec soporta modo mínimo, pero esto ayuda a tramo_conductor.
        circuitos = ee.get("circuitos")
        if not isinstance(circuitos, list) or not circuitos:
            c_list = []

            # DC
            c_list.append(
                {
                    "tipo": "DC",
                    "l_m": float(ee.get("dist_dc_m", 15.0) or 15.0),
                    "v_base_v": float(ee.get("vdc_nom", ee.get("vdc", 0.0)) or 0.0),
                }
            )

            # AC
            c_list.append(
                {
                    "tipo": "AC",
                    "l_m": float(ee.get("dist_ac_m", 25.0) or 25.0),
                    "v_base_v": float(ee.get("vac", 240.0) or 240.0),
                    "fases": int(ee.get("fases", 1) or 1),
                }
            )

            ee["circuitos"] = c_list

        # -----------------------------
        # 5) Ejecutar paquete NEC
        # -----------------------------
        paq = armar_paquete_nec(ee)
        if paq is None:
            print("⚠ NEC devolvió None")

        return {"ok": True, "errores": [], "input": ee, "paq": paq}

    except Exception as e:
        return {
            "ok": False,
            "errores": [f"NEC: {type(e).__name__}: {e}"],
            "input": {
                "equipos": getattr(p, "equipos", None),
                "electrico": (sizing or {}).get("electrico_inputs") or (sizing or {}).get("electrico") or getattr(p, "electrico", None),
            },
            "paq": {},
        }


def _extraer_kwp_y_capex(sizing: Dict[str, Any]) -> Tuple[float, float]:
    res_tmp = {"sizing": dict(sizing or {})}
    kwp_dc = float(get_kwp_dc(res_tmp))
    capex_l = float(get_capex_L(res_tmp))
    if kwp_dc <= 0 or capex_l <= 0:
        raise KeyError("Sizing incompleto.")
    return kwp_dc, capex_l


def _calcular_cuota(p: Datosproyecto, capex_l: float) -> float:
    return calcular_cuota_mensual(
        capex_L_=float(capex_l),
        tasa_anual=float(p.tasa_anual),
        plazo_anios=int(p.plazo_anios),
        pct_fin=float(p.porcentaje_financiado),
    )

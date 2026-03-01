# core/orquestador.py
from __future__ import annotations

from typing import Any, Dict

from .validacion import validar_entradas
from .sizing import calcular_sizing_unificado
from .modelo import Datosproyecto
from .finanzas_lp import ejecutar_finanzas
from core.sistema_fv_mapper import construir_parametros_fv_desde_dict


# ==========================================================
# Helpers internos mínimos
# ==========================================================

def _set_attr_safe(obj: Any, name: str, value: Any) -> None:
    try:
        setattr(obj, name, value)
    except Exception:
        pass


def _consolidar_parametros_fv_en_datos(
    p: Datosproyecto,
    params_fv: Dict[str, Any],
) -> None:
    _set_attr_safe(p, "prod_base_kwh_kwp_mes", float(params_fv["prod_base_kwh_kwp_mes"]))
    _set_attr_safe(p, "factores_fv_12m", list(params_fv["factores_fv_12m"]))
    _set_attr_safe(p, "params_fv", dict(params_fv))


def _build_params_fv(p: Datosproyecto) -> Dict[str, Any]:
    sfv = getattr(p, "sistema_fv", None) or {}
    if not isinstance(sfv, dict):
        sfv = {}
    return construir_parametros_fv_desde_dict(sfv)


def _build_electrico_nec_safe(
    p: Datosproyecto,
    sizing: Dict[str, Any],
) -> Dict[str, Any]:

    try:
        from electrical.paquete_nec import armar_paquete_nec

        s = dict(sizing or {})
        ee = {}

        # -------------------------------
        # 1️⃣ Base eléctrica UI
        # -------------------------------
        base = (
            s.get("electrico_inputs")
            or s.get("electrico")
            or getattr(p, "electrico", {})
            or {}
        )

        if isinstance(base, dict):
            ee.update(base)

        # -------------------------------
        # 2️⃣ Potencias desde sizing
        # -------------------------------
        pdc_kw = float(s.get("pdc_kw") or 0.0)
        pac_kw = float(s.get("pac_kw") or 0.0)

        if pdc_kw > 0:
            ee["potencia_dc_kw"] = pdc_kw

        if pac_kw > 0:
            ee["potencia_ac_kw"] = pac_kw

        # -------------------------------
        # 3️⃣ Información real desde strings
        # -------------------------------
        strings = s.get("strings") or {}

        if strings.get("ok"):
            rec = strings.get("recomendacion") or {}

            vmp_string = float(rec.get("vmp_string_v") or 0.0)
            if vmp_string > 0:
                ee["vdc_nom"] = vmp_string

            # Corriente nominal DC recomendada
            idesign = 0.0
            for st in strings.get("strings", []):
                idesign = max(idesign, float(st.get("idesign_cont_a") or 0.0))

            if idesign > 0:
                ee["idc_nom"] = idesign

        # -------------------------------
        # 4️⃣ Ejecutar NEC
        # -------------------------------
        paq = armar_paquete_nec(ee)

        return {
            "ok": True,
            "errores": [],
            "input": ee,
            "paq": paq,
        }

    except Exception as e:
        return {
            "ok": False,
            "errores": [f"NEC: {type(e).__name__}: {e}"],
            "input": {},
            "paq": {},
        }

# ==========================================================
# ENTRYPOINT OFICIAL
# ==========================================================

def ejecutar_estudio(p: Datosproyecto) -> Dict[str, Any]:

    # 1️⃣ Validación
    validar_entradas(p)

    # 2️⃣ Parámetros FV
    params_fv = _build_params_fv(p)
    _consolidar_parametros_fv_en_datos(p, params_fv)

    # 3️⃣ Sizing
    sizing = calcular_sizing_unificado(p)

    if not sizing or sizing.get("n_paneles", 0) <= 0:
        raise ValueError("Sizing inválido.")

    # 4️⃣ Strings
    from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing

    strings = ejecutar_paneles_desde_sizing(p, sizing)
    sizing["strings"] = strings

    if not strings.get("ok"):
        raise ValueError("Error en cálculo de strings.")

    # 5️⃣ NEC
    electrico_nec = _build_electrico_nec_safe(p, sizing)

    if not electrico_nec.get("ok"):
        raise ValueError("Error en cálculo NEC.")

    # 6️⃣ Finanzas
    finanzas = ejecutar_finanzas(
        datos=p,
        sizing=sizing,
    )

    return {
        "tecnico": {
            "params_fv": params_fv,
            "sizing": sizing,
            "electrico_nec": electrico_nec,
        },
        "financiero": finanzas,
    }
        "financiero": finanzas,
    }

    return resultado_proyecto

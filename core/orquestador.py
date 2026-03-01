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
    """
    Wrapper seguro para construir el paquete NEC.
    Contrato:
        {
            ok: bool,
            errores: [...],
            input: {...},
            paq: {...}
        }
    """
    try:
        from electrical.paquete_nec import armar_paquete_nec

        s = dict(sizing or {})

        entrada = (
            s.get("electrico")
            or s.get("electrico_inputs")
            or getattr(p, "electrico", {})
            or {}
        )

        if not isinstance(entrada, dict):
            entrada = {}

        ee = dict(entrada)

        # Enriquecer potencias
        pdc_kw = float(s.get("pdc_kw") or 0.0)
        pac_kw = float(s.get("pac_kw") or 0.0)

        if pdc_kw > 0:
            ee.setdefault("potencia_dc_kw", pdc_kw)

        if pac_kw > 0:
            ee.setdefault("potencia_ac_kw", pac_kw)

        # Ejecutar NEC
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
    """
    Flujo lineal estricto:

        Entradas
            ↓
        Sizing
            ↓
        Strings
            ↓
        NEC
            ↓
        Finanzas
            ↓
        Salida consolidada
    """

    # 1️⃣ Validación
    validar_entradas(p)

    # 2️⃣ Parámetros FV
    params_fv = _build_params_fv(p)
    _consolidar_parametros_fv_en_datos(p, params_fv)

    # 3️⃣ Sizing técnico
    sizing = calcular_sizing_unificado(p)

    if not sizing or sizing.get("n_paneles", 0) <= 0:
        raise ValueError("Sizing inválido.")

    # 4️⃣ Strings (dominio paneles)
    from electrical.paneles.orquestador_paneles import ejecutar_paneles_desde_sizing
    sizing["strings"] = ejecutar_paneles_desde_sizing(p, sizing)

    # 5️⃣ NEC
    electrico_nec = _build_electrico_nec_safe(p, sizing)

    # 6️⃣ Finanzas
    finanzas = ejecutar_finanzas(
        datos=p,
        sizing=sizing,
    )

    # 7️⃣ Salida consolidada
    return {
        "params_fv": params_fv,
        "sizing": sizing,
        "electrico_nec": electrico_nec,
        **finanzas,
    }

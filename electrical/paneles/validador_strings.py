from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from .strings_auto import calcular_strings_fv

@dataclass(frozen=True)
class PanelFV:
    voc_stc: float
    vmp_stc: float
    isc: float
    imp: float
    coef_voc_pct_c: float  # ej -0.28

@dataclass(frozen=True)
class InversorFV:
    vdc_max: float
    mppt_min: float
    mppt_max: float
    imppt_max: float
    n_mppt: int

def validar_string(panel: PanelFV, inversor: InversorFV, n_paneles_string: int, temp_min: float) -> Dict[str, Any]:
    """
    Compat UI. Si n_paneles_string parece total, usamos motor para sugerir ns válido.
    """
    try:
        n = int(n_paneles_string)
    except Exception:
        n = 0

    warns: list[str] = []
    if n <= 0:
        return {"string_valido": False, "ok_vdc": False, "ok_mppt": False, "ok_corriente": False, "warnings": ["n_paneles_string inválido (<=0)."]}

    # Heurística: si n es “demasiado grande”, probablemente es total del sistema, no ns.
    # En ese caso dejamos que el motor recomiende ns.
    n_total = n

    # Adaptar PanelFV/InversorFV a objetos con atributos esperados por strings_auto
    class _P:
        pass
    class _I:
        pass
    p = _P()
    p.voc = float(panel.voc_stc)
    p.vmp = float(panel.vmp_stc)
    p.isc = float(panel.isc)
    p.imp = float(panel.imp)
    p.coef_voc_pct_c = float(panel.coef_voc_pct_c)

    inv = _I()
    inv.vdc_max = float(inversor.vdc_max)
    inv.vmppt_min = float(inversor.mppt_min)
    inv.vmppt_max = float(inversor.mppt_max)
    inv.imppt_max_a = float(inversor.imppt_max)
    inv.n_mppt = int(inversor.n_mppt)

    res = calcular_strings_fv(
        n_paneles_total=n_total,
        panel=p,
        inversor=inv,
        t_min_c=float(temp_min),
        dos_aguas=False,
    )

    if not res.get("ok", False):
        return {
            "string_valido": False,
            "ok_vdc": False,
            "ok_mppt": False,
            "ok_corriente": False,
            "warnings": list(res.get("warnings") or []) + list(res.get("errores") or []),
        }

    r = res.get("recomendacion") or {}
    voc_frio_total = float(r.get("voc_frio_string_v") or 0.0)
    vmp_operativo = float(r.get("vmp_string_v") or 0.0)
    corriente_mppt = float(r.get("i_mppt_a") or 0.0)

    ok_vdc = voc_frio_total > 0 and voc_frio_total <= float(inversor.vdc_max)
    ok_mppt = vmp_operativo >= float(inversor.mppt_min) and vmp_operativo <= float(inversor.mppt_max)
    ok_corr = corriente_mppt <= float(inversor.imppt_max)

    return {
        "voc_frio_total": voc_frio_total,
        "vmp_operativo": vmp_operativo,
        "corriente_mppt": corriente_mppt,
        "ok_vdc": ok_vdc,
        "ok_mppt": ok_mppt,
        "ok_corriente": ok_corr,
        "string_valido": bool(ok_vdc and ok_mppt and ok_corr),
        "warnings": list(res.get("warnings") or []),
        "meta": {"ns_recomendado": int(r.get("n_paneles_string") or 0)},
    }

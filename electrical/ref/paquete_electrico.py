# electrical/paquete_electrico.py
from __future__ import annotations
from typing import Any, Dict, List, Optional

from electrical.modelos import ParametrosCableado
from electrical.calculos_regulacion import tramo_dc_ref, tramo_ac_1f_ref, tramo_ac_3f_ref
from electrical.protecciones import armar_ocpd
from electrical.canalizacion import conduit_ac_heuristico, canalizacion_fv


def _cfg(cfg: Optional[Dict[str, Any]], k: str, d: float) -> float:
    try:
        return float((cfg or {}).get(k, d))
    except Exception:
        return float(d)


def _tierra_awg(awg_fase: str) -> str:
    return "10" if awg_fase in ["6", "4", "3", "2", "1", "1/0", "2/0", "3/0", "4/0"] else "12"


def _calc_tramos(*, p: ParametrosCableado, vmp: float, imp: float, isc: Optional[float], iac: float,
                 fases_ac: int, cfg: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    fdc = _cfg(cfg, "factor_seguridad_dc", 1.25); fac = _cfg(cfg, "factor_seguridad_ac", 1.25)
    vdd = _cfg(cfg, "vdrop_obj_dc_pct", float(getattr(p, "vdrop_obj_dc_pct", 2.0)))
    vda = _cfg(cfg, "vdrop_obj_ac_pct", float(getattr(p, "vdrop_obj_ac_pct", 2.0)))
    dc = tramo_dc_ref(vmp_v=vmp, imp_a=imp, isc_a=isc, dist_m=float(p.dist_dc_m), factor_seguridad=fdc, vd_obj_pct=vdd)
    fn_ac = tramo_ac_3f_ref if int(fases_ac) == 3 else tramo_ac_1f_ref
    ac = fn_ac(vac_v=float(p.vac), iac_a=iac, dist_m=float(p.dist_ac_m), factor_seguridad=fac, vd_obj_pct=vda)
    ac["tierra_awg"] = _tierra_awg(str(ac["awg"]))
    return {"dc": dc, "ac": ac}


def _calc_protecciones(*, ac: Dict[str, Any], n_strings: int = 0, isc_mod_a: float = 0.0,
                       has_combiner: bool = False) -> Dict[str, Any]:
    return armar_ocpd(iac_nom_a=float(ac.get("i_nom_a", 0.0)), n_strings=int(n_strings),
                      isc_mod_a=float(isc_mod_a), has_combiner=bool(has_combiner))


def _calc_canalizacion(*, p: ParametrosCableado, ac: Dict[str, Any], fases_ac: int) -> Dict[str, Any]:
    conduit = conduit_ac_heuristico(awg_ac=str(ac["awg"]), incluye_neutro=bool(p.incluye_neutro_ac),
                                    extra_ccc=int(p.otros_ccc))
    can = canalizacion_fv(tiene_trunk=False, fases_ac=int(fases_ac), incluye_neutro=bool(p.incluye_neutro_ac))
    return {"conduit_ac": conduit, "canalizacion": can}


def _resumen_pdf(*, p: ParametrosCableado, ac: Dict[str, Any], dc: Dict[str, Any], conduit: str, breaker: int) -> List[str]:
    a = f"Conductores AC: {ac['awg']} AWG Cu THHN/THWN-2 (L1+L2)" + (" + N" if p.incluye_neutro_ac else "")
    a += f" + tierra {ac['tierra_awg']} AWG. Dist {p.dist_ac_m:.1f} m | caída {ac['vd_pct']:.2f}% (obj {ac['vd_obj_pct']:.1f}%)."
    d = f"Conductores DC (string): {dc['awg']} AWG Cu PV Wire/USE-2. Dist {p.dist_dc_m:.1f} m | caída {dc['vd_pct']:.2f}% (obj {dc['vd_obj_pct']:.1f}%)."
    return [d, a, f"Tubería AC sugerida: {conduit} EMT/PVC (ref).", f"Breaker AC sugerido (ref): {breaker} A (validar datasheet)."]


def _disclaimer() -> str:
    return ("Cálculo referencial. Calibre final sujeto a: temperatura, agrupamiento (CCC), "
            "factores de ajuste/corrección, fill real de tubería, terminales 75°C y normativa aplicable.")


def calcular_paquete_electrico_ref(
    *, params: ParametrosCableado, vmp_string_v: float, imp_a: float, isc_a: Optional[float],
    iac_estimado_a: float, fases_ac: int = 1, cfg_tecnicos: Optional[Dict[str, Any]] = None,
    n_strings: int = 0, isc_mod_a: float = 0.0, has_combiner: bool = False,
) -> Dict[str, Any]:
    tr = _calc_tramos(p=params, vmp=vmp_string_v, imp=imp_a, isc=isc_a, iac=iac_estimado_a, fases_ac=fases_ac, cfg=cfg_tecnicos)
    ocpd = _calc_protecciones(ac=tr["ac"], n_strings=n_strings, isc_mod_a=isc_mod_a, has_combiner=has_combiner)
    can = _calc_canalizacion(p=params, ac=tr["ac"], fases_ac=fases_ac)
    brk = int(ocpd.get("breaker_ac", {}).get("tamano_sugerido_a", 0) or ocpd.get("breaker_ac", {}).get("tamano_a", 0) or 0)
    pdf = _resumen_pdf(p=params, ac=tr["ac"], dc=tr["dc"], conduit=can["conduit_ac"], breaker=brk)
    return {"modo": "ref", "dc": tr["dc"], "ac": {**tr["ac"], "conduit": can["conduit_ac"]},
            "ocpd": ocpd, "canalizacion": can["canalizacion"], "resumen_pdf": pdf,
            "disclaimer": _disclaimer(), "warnings": []}

# electrical/strings_auto.py
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PanelSpec:
    pmax_w: float
    vmp_v: float
    voc_v: float
    imp_a: float
    isc_a: float
    coef_voc_pct_c: float  # ej -0.25 (%/°C)


@dataclass(frozen=True)
class InversorSpec:
    pac_kw: float
    vdc_max_v: float
    mppt_min_v: float
    mppt_max_v: float
    n_mppt: int
    imppt_max_a: float


def _voc_frio(voc_stc: float, coef_voc_pct_c: float, t_min_c: float, t_stc_c: float = 25.0) -> float:
    # Voc(T) = Voc_STC * (1 + coef%/°C/100 * (T - 25))
    return voc_stc * (1.0 + (coef_voc_pct_c / 100.0) * (t_min_c - t_stc_c))


def _bounds_por_voltaje(panel: PanelSpec, inv: InversorSpec, t_min_c: float) -> Dict[str, Any]:
    voc_cold = _voc_frio(panel.voc_v, panel.coef_voc_pct_c, t_min_c)

    # límites por Voc frío (Vdc max del inversor)
    max_por_vdc = floor(inv.vdc_max_v / max(voc_cold, 1e-9))

    # límites por MPPT (usamos Vmp STC como aproximación base; luego podrás mejorar con Vmp(T))
    min_por_mppt = ceil(inv.mppt_min_v / max(panel.vmp_v, 1e-9))
    max_por_mppt = floor(inv.mppt_max_v / max(panel.vmp_v, 1e-9))

    # límite final superior: el más restrictivo entre Vdc_max y MPPT_max
    n_max = max(0, min(max_por_vdc, max_por_mppt))
    n_min = max(1, min_por_mppt)

    return {
        "voc_frio_v": float(voc_cold),
        "n_min": int(n_min),
        "n_max": int(n_max),
        "max_por_vdc": int(max_por_vdc),
        "min_por_mppt": int(min_por_mppt),
        "max_por_mppt": int(max_por_mppt),
    }


def _bounds_corriente(panel: PanelSpec, inv: InversorSpec, n_strings_por_mppt: int) -> Dict[str, Any]:
    # Corriente MPPT ~ sum de Imp por string (referencial)
    i_mppt = panel.imp_a * n_strings_por_mppt
    ok = i_mppt <= inv.imppt_max_a + 1e-9
    return {"i_mppt_a": float(i_mppt), "ok": bool(ok)}


def _score_n(n: int, panel: PanelSpec, inv: InversorSpec) -> float:
    # score simple: acercar Vmp_string al centro de la ventana MPPT
    vmp_string = n * panel.vmp_v
    mid = (inv.mppt_min_v + inv.mppt_max_v) / 2.0
    return abs(vmp_string - mid)


def recomendar_string(
    *,
    panel: PanelSpec,
    inversor: InversorSpec,
    t_min_c: float,
    objetivo_dc_ac: float,
    pdc_kw_objetivo: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Devuelve recomendación de N paneles por string + strings sugeridos.
    - Si pdc_kw_objetivo no se pasa, se usa objetivo_dc_ac * pac_kw.
    """
    errores: List[str] = []
    warnings: List[str] = []

    if inversor.n_mppt <= 0:
        errores.append("Inversor inválido: n_mppt <= 0")
    if panel.pmax_w <= 0 or panel.vmp_v <= 0 or panel.voc_v <= 0:
        errores.append("Panel inválido: revisar STC (pmax/vmp/voc).")
    if errores:
        return {"ok": False, "errores": errores, "warnings": warnings}

    bounds = _bounds_por_voltaje(panel, inversor, t_min_c=t_min_c)
    n_min, n_max = bounds["n_min"], bounds["n_max"]

    if n_max < n_min:
        errores.append(
            f"No existe N válido: n_min={n_min}, n_max={n_max}. "
            f"Revisa MPPT o Vdc_max vs Voc frío."
        )
        return {"ok": False, "errores": errores, "warnings": warnings, "bounds": bounds}

    # elegir N recomendado (mejor score)
    candidatos = list(range(n_min, n_max + 1))
    n_rec = min(candidatos, key=lambda n: _score_n(n, panel, inversor))

    # potencia DC objetivo
    pdc_obj = pdc_kw_objetivo if pdc_kw_objetivo is not None else (objetivo_dc_ac * inversor.pac_kw)
    pdc_obj_w = float(pdc_obj) * 1000.0

    # string power (STC)
    p_string_w = n_rec * panel.pmax_w

    # strings totales requeridos (ceil)
    n_strings_total = max(1, int(ceil(pdc_obj_w / max(p_string_w, 1e-9))))

    # repartir por MPPT (lo más parejo)
    strings_por_mppt = max(1, int(ceil(n_strings_total / max(inversor.n_mppt, 1))))

    # verificar corriente por MPPT (referencial)
    corr = _bounds_corriente(panel, inversor, n_strings_por_mppt=strings_por_mppt)
    if not corr["ok"]:
        warnings.append(
            f"Corriente MPPT alta: {corr['i_mppt_a']:.2f} A > {inversor.imppt_max_a:.2f} A. "
            f"Reduce strings por MPPT o cambia inversor."
        )

    # checks voltaje finales
    voc_frio_total = bounds["voc_frio_v"] * n_rec
    if voc_frio_total > inversor.vdc_max_v + 1e-9:
        errores.append(f"Voc frío total excede Vdc_max: {voc_frio_total:.1f} V > {inversor.vdc_max_v:.1f} V")

    vmp_total = panel.vmp_v * n_rec
    if vmp_total < inversor.mppt_min_v - 1e-9 or vmp_total > inversor.mppt_max_v + 1e-9:
        warnings.append(
            f"Vmp string fuera de MPPT (referencial): {vmp_total:.1f} V vs "
            f"{inversor.mppt_min_v:.1f}-{inversor.mppt_max_v:.1f} V."
        )

    # salida
    return {
        "ok": len(errores) == 0,
        "errores": errores,
        "warnings": warnings,
        "bounds": bounds,
        "recomendacion": {
            "n_paneles_string": int(n_rec),
            "n_strings_total": int(n_strings_total),
            "strings_por_mppt": int(strings_por_mppt),
            "pdc_obj_kw": float(pdc_obj),
            "p_string_kw_stc": float(p_string_w / 1000.0),
            "vmp_string_v": float(vmp_total),
            "voc_frio_string_v": float(voc_frio_total),
            "i_mppt_a": float(corr["i_mppt_a"]),
        },
    }

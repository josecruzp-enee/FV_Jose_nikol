# electrical/paquete_electrico.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ==========================================================
# Modelos mínimos
# ==========================================================
@dataclass(frozen=True)
class ParametrosCableado:
    vac: float
    fases: int
    fp: float
    dist_dc_m: float
    dist_ac_m: float
    vdrop_obj_dc_pct: float
    vdrop_obj_ac_pct: float
    incluye_neutro_ac: bool
    otros_ccc: int
    t_min_c: float


@dataclass(frozen=True)
class PanelDC:
    pmax_w: float
    vmp_v: float
    voc_v: float
    imp_a: float
    isc_a: float


@dataclass(frozen=True)
class InversorAC:
    pac_kw: float
    vac_nom_v: float
    fases: int
    fp: float


# ==========================================================
# NEC helpers (cortos)
# ==========================================================
def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _vdrop_pct(vdrop_v: float, vbase_v: float) -> float:
    return 100.0 * float(vdrop_v) / max(float(vbase_v), 1e-9)


def _iac(pac_kw: float, vac: float, fases: int, fp: float) -> float:
    p_w = float(pac_kw) * 1000.0
    vac = max(float(vac), 1e-9)
    fp = _clamp(fp, 0.8, 1.0)
    if int(fases) == 3:
        return p_w / (math.sqrt(3) * vac * fp)
    return p_w / (vac * fp)


# ==========================================================
# Resistencias DC aproximadas (Cu, 75°C) [ohm/km]
# Nota: suficiente para vdrop preliminar. Luego lo afinamos con tabla NEC completa.
# ==========================================================
_AWG_OHM_KM_CU_75C: Dict[str, float] = {
    "14": 10.2,
    "12": 6.4,
    "10": 4.0,
    "8":  2.5,
    "6":  1.6,
    "4":  1.0,
    "3":  0.79,
    "2":  0.62,
    "1":  0.49,
    "1/0": 0.39,
    "2/0": 0.31,
    "3/0": 0.25,
    "4/0": 0.20,
}


# ==========================================================
# Ampacidades base Cu THHN/THWN-2 (75°C) — simplificado NEC
# Nota: luego lo expandimos; esto permite decisiones correctas en 1F/3F típicos.
# ==========================================================
_AWG_AMP_CU_75C: Dict[str, int] = {
    "14": 20,
    "12": 25,
    "10": 35,
    "8":  50,
    "6":  65,
    "4":  85,
    "3":  100,
    "2":  115,
    "1":  130,
    "1/0": 150,
    "2/0": 175,
    "3/0": 200,
    "4/0": 230,
}


def _nec_ccc_total(base_ccc: int, incluye_neutro: bool, otros_ccc: int) -> int:
    # CCC = current-carrying conductors
    n = int(base_ccc) + int(otros_ccc)
    if incluye_neutro:
        n += 1
    return max(1, n)


def _factor_ajuste_ccc(nec_ccc: int) -> float:
    # NEC 310.15(C)(1) (aprox estándar)
    if nec_ccc <= 3:
        return 1.00
    if nec_ccc <= 6:
        return 0.80
    if nec_ccc <= 9:
        return 0.70
    if nec_ccc <= 20:
        return 0.50
    return 0.45


def _factor_temp_75c(t_amb_c: float) -> float:
    # NEC 310.15(B)(1) correction factors (aprox) para 75°C
    # Si luego quieres exactitud de tabla, lo hacemos; por ahora conservador.
    t = float(t_amb_c)
    if t <= 30:
        return 1.00
    if t <= 35:
        return 0.94
    if t <= 40:
        return 0.88
    if t <= 45:
        return 0.82
    if t <= 50:
        return 0.75
    if t <= 55:
        return 0.67
    if t <= 60:
        return 0.58
    return 0.50


def _ampacidad_ajustada(awg: str, t_amb_c: float, ccc: int) -> float:
    base = float(_AWG_AMP_CU_75C[awg])
    return base * _factor_temp_75c(t_amb_c) * _factor_ajuste_ccc(ccc)


def _escoger_awg_por_corriente(idisenio_a: float, t_amb_c: float, ccc: int) -> str:
    # pick mínimo AWG cuyo ampacity adjusted >= idiseño
    for awg in _AWG_AMP_CU_75C.keys():
        if _ampacidad_ajustada(awg, t_amb_c, ccc) >= float(idisenio_a) - 1e-9:
            return awg
    return "4/0"


def _vdrop_dc_2hilo(i_a: float, dist_m: float, awg: str) -> float:
    # Vdrop = I * R_total; ida y vuelta => 2*L
    ohm_km = float(_AWG_OHM_KM_CU_75C.get(awg, 999.0))
    r = ohm_km * (2.0 * float(dist_m) / 1000.0)
    return float(i_a) * r


def _vdrop_ac_1f_2hilo(i_a: float, dist_m: float, awg: str) -> float:
    # aproximación igual a DC (sin reactancia)
    return _vdrop_dc_2hilo(i_a, dist_m, awg)


def _vdrop_ac_3f(i_a: float, dist_m: float, awg: str) -> float:
    # aproximación 3Φ: Vdrop ≈ √3 I R L
    ohm_km = float(_AWG_OHM_KM_CU_75C.get(awg, 999.0))
    r = ohm_km * (float(dist_m) / 1000.0)
    return math.sqrt(3) * float(i_a) * r


# ==========================================================
# Protecciones NEC (referencial robusto)
# ==========================================================
def _idc_diseno_nec(isc_a: float, n_strings_total: int) -> float:
    # NEC 690.8: Imax = 1.25 * Isc * Ns; y conductores/OC PD pueden ir a 1.25 adicional
    # diseño conductor conservador: 1.56 * Isc * Ns
    return 1.56 * float(isc_a) * max(1, int(n_strings_total))


def _iac_diseno_nec(iac: float) -> float:
    # salida inversor: típicamente 125% para conductor/ocpd
    return 1.25 * float(iac)


def _breaker_estandar_a(i_diseno: float) -> int:
    # próximo tamaño estándar simple (NO lista completa NEC, pero suficiente)
    pasos = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 125, 150, 175, 200]
    for p in pasos:
        if p >= i_diseno - 1e-9:
            return p
    return int(math.ceil(i_diseno / 10.0) * 10)


# ==========================================================
# API pública
# ==========================================================
def calcular_paquete_nec_2023(
    *,
    panel: PanelDC,
    inversor: InversorAC,
    strings_auto: Dict[str, Any],
    params: ParametrosCableado,
    t_amb_c: float = 30.0,
) -> Dict[str, Any]:
    """
    Recibe:
      - panel STC
      - inversor AC
      - strings_auto: salida de nucleo/sizing.py (strings_auto resumido) o recomendar_string()
      - params: distancias, objetivos vdrop, etc
    Retorna:
      - texto_ui: listas para UI
      - datos_pdf: dict para reporte
      - checks: warnings/errores
      - sizing: corrientes/cables/protecciones
    """
    checks: List[str] = []

    n_strings_total = int(strings_auto.get("n_strings_total", 0) or 0)
    n_paneles_string = int(strings_auto.get("n_paneles_string", 0) or 0)
    strings_por_mppt = int(strings_auto.get("strings_por_mppt", 0) or 0)

    if n_strings_total <= 0 or n_paneles_string <= 0:
        return {"ok": False, "checks": ["No hay strings_auto válido (n_strings_total/n_paneles_string)."]}

    # ===== Corrientes base =====
    idc_dis = _idc_diseno_nec(panel.isc_a, n_strings_total)
    iac_nom = _iac(inversor.pac_kw, params.vac, params.fases, params.fp)
    iac_dis = _iac_diseno_nec(iac_nom)

    # ===== CCC y factores =====
    ccc_ac = _nec_ccc_total(2 if params.fases == 1 else 3, params.incluye_neutro_ac, params.otros_ccc)
    fac_ccc = _factor_ajuste_ccc(ccc_ac)
    fac_tmp = _factor_temp_75c(t_amb_c)

    # ===== Selección conductores =====
    awg_dc = _escoger_awg_por_corriente(idc_dis, t_amb_c, ccc=2)  # DC 2 conductores CCC
    awg_ac = _escoger_awg_por_corriente(iac_dis, t_amb_c, ccc=ccc_ac)

    # ===== Caída de voltaje =====
    vdrop_dc_v = _vdrop_dc_2hilo(idc_dis, params.dist_dc_m, awg_dc)
    vdrop_dc_pct = _vdrop_pct(vdrop_dc_v, max(panel.vmp_v * n_paneles_string, params.vac))

    if params.fases == 3:
        vdrop_ac_v = _vdrop_ac_3f(iac_dis, params.dist_ac_m, awg_ac)
    else:
        vdrop_ac_v = _vdrop_ac_1f_2hilo(iac_dis, params.dist_ac_m, awg_ac)
    vdrop_ac_pct = _vdrop_pct(vdrop_ac_v, params.vac)

    if vdrop_dc_pct > float(params.vdrop_obj_dc_pct) + 1e-9:
        checks.append(f"⚠️ Vdrop DC {vdrop_dc_pct:.2f}% > objetivo {params.vdrop_obj_dc_pct:.2f}% (ajustar calibre o ruta).")
    if vdrop_ac_pct > float(params.vdrop_obj_ac_pct) + 1e-9:
        checks.append(f"⚠️ Vdrop AC {vdrop_ac_pct:.2f}% > objetivo {params.vdrop_obj_ac_pct:.2f}% (ajustar calibre o ruta).")

    # ===== Protecciones =====
    breaker_ac_a = _breaker_estandar_a(iac_dis)
    fusible_string_a = _breaker_estandar_a(1.56 * panel.isc_a)  # referencial por string

    # ===== UI texto =====
    ui_strings = [
        f"Auto-stringing: {n_paneles_string} módulos en serie por string; {n_strings_total} strings totales; {strings_por_mppt} strings/MPPT.",
        f"DC diseño (NEC): Idc≈{idc_dis:.1f} A (1.56×Isc×Nstrings).",
        f"AC nominal: Iac≈{iac_nom:.1f} A | diseño (125%): {iac_dis:.1f} A.",
    ]
    ui_cables = [
        f"Conductor DC sugerido: {awg_dc} AWG Cu PV/USE-2 (ajustado por T={t_amb_c:.0f}°C).",
        f"Vdrop DC: {vdrop_dc_pct:.2f}% (dist {params.dist_dc_m:.1f} m).",
        f"Conductor AC sugerido: {awg_ac} AWG Cu THHN/THWN-2 (CCC={ccc_ac}, facT={fac_tmp:.2f}, facCCC={fac_ccc:.2f}).",
        f"Vdrop AC: {vdrop_ac_pct:.2f}% (dist {params.dist_ac_m:.1f} m).",
    ]
    ui_prot = [
        f"Breaker AC sugerido: {breaker_ac_a} A (125% Iac).",
        f"Fusible string (referencial): {fusible_string_a} A (1.56×Isc por string).",
        "SPD DC: Tipo 2 (recomendado) cerca del inversor/combiner (según arquitectura).",
        "SPD AC: Tipo 2 en tablero principal / salida inversor.",
        "Nota: validar contra datasheet del inversor (OCPD, backfeed, terminales 75°C).",
    ]

    texto_ui = {
        "strings": ui_strings,
        "cableado": ui_cables + ui_prot,
        "checks": checks + list(strings_auto.get("warnings") or []) + list(strings_auto.get("errores") or []),
        "disclaimer": (
            "Cálculo referencial NEC 2023. Calibre final sujeto a: temperatura real, "
            "agrupamiento, método de instalación, terminales 75°C, fill de tubería, y normativa aplicable."
        ),
    }

    sizing = {
        "idc_diseno_a": float(idc_dis),
        "iac_nom_a": float(iac_nom),
        "iac_diseno_a": float(iac_dis),
        "awg_dc": awg_dc,
        "awg_ac": awg_ac,
        "vdrop_dc_pct": float(vdrop_dc_pct),
        "vdrop_ac_pct": float(vdrop_ac_pct),
        "breaker_ac_a": int(breaker_ac_a),
        "fusible_string_a": int(fusible_string_a),
        "ccc_ac": int(ccc_ac),
        "factor_ccc": float(fac_ccc),
        "factor_temp": float(fac_tmp),
    }

    datos_pdf = {
        "strings": {"n_paneles_string": n_paneles_string, "n_strings_total": n_strings_total, "strings_por_mppt": strings_por_mppt},
        "corrientes": sizing,
        "cableado": {"dist_dc_m": float(params.dist_dc_m), "dist_ac_m": float(params.dist_ac_m)},
        "vdrop": {"dc_pct": float(vdrop_dc_pct), "ac_pct": float(vdrop_ac_pct)},
        "protecciones": {"breaker_ac_a": int(breaker_ac_a), "fusible_string_a": int(fusible_string_a)},
    }

    ok = True
    return {"ok": ok, "texto_ui": texto_ui, "sizing": sizing, "datos_pdf": datos_pdf}

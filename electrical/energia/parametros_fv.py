from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


# ==========================================================
# MODELO DE SALIDA
# ==========================================================

@dataclass(frozen=True)
class ParametrosFV:

    hsp: float

    prod_base_kwh_kwp_mes: float

    factores_fv_12m: List[float]

    azimut_deg: float

    inclinacion_deg: float

    tipo_superficie: str

    perdidas_sistema_pct: float
    sombras_pct: float

    azimut_a_deg: Optional[float] = None
    azimut_b_deg: Optional[float] = None
    reparto_pct_a: Optional[float] = None


# ==========================================================
# HELPERS INTERNOS
# ==========================================================

def _to_float(x: Any, field: str) -> float:

    try:
        return float(x)
    except Exception:
        raise ValueError(f"Valor inválido para {field}")


def _clamp(x: float, lo: float, hi: float, field: str) -> float:

    if x < lo or x > hi:
        raise ValueError(f"{field} fuera de rango ({lo}-{hi})")

    return x


def _pct_to_factor(pct: float) -> float:

    return 1.0 - pct / 100.0


def _tipo_superficie_code(sfv: dict) -> str:

    code = str(sfv.get("tipo_superficie_code") or "").strip().lower()

    if code in ("plano", "dos_aguas"):
        return code

    label = str(sfv.get("tipo_superficie") or "").strip()

    if label == "Techo dos aguas":
        return "dos_aguas"

    if label:
        return "plano"

    raise ValueError("tipo_superficie no definido")


# ==========================================================
# API PUBLICA — DOMINIO ENERGIA
# ==========================================================

def construir_parametros_fv(sfv: dict) -> ParametrosFV:

    if not isinstance(sfv, dict):
        raise ValueError("Sistema FV inválido (no es dict)")

    # =========================
    # HSP
    # =========================

    if "hsp" not in sfv and "hsp_kwh_m2_d" not in sfv:
        raise ValueError("HSP no definido en sistema FV")

    hsp_raw = sfv.get("hsp", sfv.get("hsp_kwh_m2_d"))

    hsp = _clamp(
        _to_float(hsp_raw, "hsp"),
        0.5,
        9.0,
        "hsp",
    )

    # =========================
    # Pérdidas
    # =========================

    perdidas_pct = _clamp(
        _to_float(sfv.get("perdidas_sistema_pct", 15.0), "perdidas_sistema_pct"),
        0.0,
        60.0,
        "perdidas_sistema_pct",
    )

    sombras_pct = _clamp(
        _to_float(sfv.get("sombras_pct", 0.0), "sombras_pct"),
        0.0,
        80.0,
        "sombras_pct",
    )

    # =========================
    # Geometría
    # =========================

    tipo = _tipo_superficie_code(sfv)

    inclinacion_deg = _clamp(
        _to_float(sfv.get("inclinacion_deg", 15.0), "inclinacion_deg"),
        0.0,
        60.0,
        "inclinacion_deg",
    )

    azimut_deg = _clamp(
        _to_float(sfv.get("azimut_deg", 180.0), "azimut_deg"),
        0.0,
        359.9,
        "azimut_deg",
    )

    azimut_a_deg: Optional[float] = None
    azimut_b_deg: Optional[float] = None
    reparto_pct_a: Optional[float] = None

    if tipo == "dos_aguas":

        azimut_a_deg = _clamp(
            _to_float(sfv.get("azimut_a_deg", azimut_deg), "azimut_a_deg"),
            0.0,
            359.9,
            "azimut_a_deg",
        )

        azimut_b_deg = _clamp(
            _to_float(
                sfv.get("azimut_b_deg", (azimut_a_deg + 180.0) % 360.0),
                "azimut_b_deg",
            ),
            0.0,
            359.9,
            "azimut_b_deg",
        )

        reparto_pct_a = _clamp(
            _to_float(sfv.get("reparto_pct_a", 50.0), "reparto_pct_a"),
            0.0,
            100.0,
            "reparto_pct_a",
        )

        azimut_deg = float(azimut_a_deg)

    # =========================
    # Modelo energético base
    # =========================

    pr = _pct_to_factor(perdidas_pct) * _pct_to_factor(sombras_pct)

    pr = max(0.1, min(1.0, pr))

    prod_base_kwh_kwp_mes = hsp * 30.0 * pr

    # =========================
    # Factores mensuales
    # =========================

    factores_in = sfv.get("factores_fv_12m") or sfv.get("factores_12m")

    if factores_in is not None:

        if not isinstance(factores_in, list) or len(factores_in) != 12:
            raise ValueError("factores_fv_12m debe tener 12 valores")

        factores: List[float] = [
            _clamp(_to_float(v, "factor_mensual"), 0.3, 1.7, "factor_mensual")
            for v in factores_in
        ]

    else:

        factores = [1.0] * 12

    return ParametrosFV(

        hsp=float(hsp),

        prod_base_kwh_kwp_mes=float(prod_base_kwh_kwp_mes),

        factores_fv_12m=factores,

        azimut_deg=float(azimut_deg),

        inclinacion_deg=float(inclinacion_deg),

        tipo_superficie=tipo,

        perdidas_sistema_pct=float(perdidas_pct),

        sombras_pct=float(sombras_pct),

        azimut_a_deg=azimut_a_deg,
        azimut_b_deg=azimut_b_deg,
        reparto_pct_a=reparto_pct_a,
    )


# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# ParametrosFV
#
# Campos:
#
# hsp : float
# prod_base_kwh_kwp_mes : float
# factores_fv_12m : list[float]
# azimut_deg : float
# inclinacion_deg : float
# tipo_superficie : str
# perdidas_sistema_pct : float
# sombras_pct : float
#
# azimut_a_deg : Optional[float]
# azimut_b_deg : Optional[float]
# reparto_pct_a : Optional[float]
#
# Descripción:
# Parámetros normalizados del sistema FV para el dominio energía.
#
# Consumido por:
# energia.orquestador_energia
#
# ==========================================================

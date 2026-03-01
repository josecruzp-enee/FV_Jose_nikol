from __future__ import annotations

from typing import Dict, Any, List


# ==========================================================
# Constantes energéticas base
# ==========================================================

DIAS_MES: List[int] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# ==========================================================
# Modelo HSP (Honduras conservador)
# ==========================================================

def hsp_honduras_conservador_12m() -> List[float]:
    """
    Modelo mensual conservador Honduras.
    Fuente simplificada para preview y estimaciones rápidas.
    """
    return [5.1, 5.4, 5.8, 5.6, 5.0, 4.5, 4.3, 4.4, 4.1, 4.0, 4.4, 4.7]


# ==========================================================
# Normalización Sistema FV (UI → dominio)
# ==========================================================

def normalizar_sistema_fv(sf: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza campos esperados por el motor energético.
    No modifica el dict original.
    """

    sf = dict(sf)

    # -------------------------
    # HSP normalizada
    # -------------------------
    hsp = sf.get("hsp")
    if hsp is None:
        hsp = float(sf.get("hsp_kwh_m2_d", 5.2))

    sf["hsp"] = float(hsp)
    sf["hsp_kwh_m2_d"] = float(sf["hsp"])

    # -------------------------
    # Tipo superficie
    # -------------------------
    label = str(sf.get("tipo_superficie", "")).strip()

    sf["tipo_superficie_code"] = (
        "dos_aguas" if label == "Techo dos aguas" else "plano"
    )

    # Compatibilidad: motor espera azimut único
    if sf.get("tipo_superficie") == "Techo dos aguas":
        sf["azimut_deg"] = int(
            sf.get("azimut_a_deg", sf.get("azimut_deg", 180))
        )

    return sf


# ==========================================================
# Preview energético (modelo simplificado UI)
# ==========================================================

def preview_generacion_anual(sf: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modelo simplificado de generación anual para preview UI.
    NO reemplaza simulación energética completa.
    """

    sf = normalizar_sistema_fv(sf)

    kwp = float(sf.get("kwp_preview", 5.0))
    perd = float(sf.get("perdidas_sistema_pct", 15.0))
    sombras = float(sf.get("sombras_pct", 0.0))

    # PR simplificado
    pr = (1.0 - perd / 100.0) * (1.0 - sombras / 100.0)
    pr = max(0.10, min(1.00, pr))

    # HSP mensual
    if bool(sf.get("hsp_override", False)):
        hsp_12m = [float(sf.get("hsp_kwh_m2_d", 5.2))] * 12
    else:
        hsp_12m = hsp_honduras_conservador_12m()

    # Generación mensual
    gen_mes = [
        kwp * h * pr * d
        for h, d in zip(hsp_12m, DIAS_MES)
    ]

    gen_dia = [
        (g / d) if d else 0.0
        for g, d in zip(gen_mes, DIAS_MES)
    ]

    return {
        "gen_mes": gen_mes,
        "gen_dia_prom": gen_dia,
        "total_kwh_anual": sum(gen_mes),
        "pr": pr,
        "hsp_12m": hsp_12m,
    }

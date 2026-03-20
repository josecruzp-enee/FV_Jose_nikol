from __future__ import annotations

"""
TRAMO CONDUCTOR — FV ENGINE
===========================

Motor de decisión final del conductor.

Integra:

    ✔ Corriente (corrientes)
    ✔ Ampacidad (NEC)
    ✔ Caída de tensión (VD)

Este módulo responde:

    "¿Qué conductor cumple TODO?"

"""

from dataclasses import dataclass
from typing import Optional

from .tablas_conductores import tabla_base_conductores
from .factores_nec import ampacidad_ajustada_nec
from .caida_voltaje import caida_tension_pct, ajustar_calibre_por_vd


# ==========================================================
# RESULTADO TIPADO
# ==========================================================

@dataclass(frozen=True)
class ResultadoConductor:

    nombre: str

    # Entrada relevante
    i_diseno_a: float
    v_base_v: float
    l_m: float

    # Resultado conductor
    calibre: str
    material: str

    # Ampacidad
    ampacidad_base_a: float
    ampacidad_ajustada_a: float

    # Factores
    fac_temp: float
    fac_ccc: float

    # Caída de tensión
    vd_pct: float
    vd_obj_pct: float

    # Evaluación
    cumple_ampacidad: bool
    cumple_vd: bool
    cumple: bool

    # Extras
    r_ohm_km: float
    agotado_vd: bool


# ==========================================================
# MOTOR
# ==========================================================

def tramo_conductor(
    *,
    nombre: str,
    i_diseno_a: float,
    v_base_v: float,
    l_m: float,
    vd_obj_pct: float,
    material: str = "Cu",
    n_hilos: int = 2,
    t_amb_c: float = 30.0,
    ccc: int = 2,
    aplicar_derating: bool = True,
) -> ResultadoConductor:

    tabla = list(tabla_base_conductores(material))

    # ------------------------------------------------------
    # 1 Selección por ampacidad
    # ------------------------------------------------------

    for t in tabla:

        amp_base = float(t["amp_a"])

        amp_adj, f_t, f_c = ampacidad_ajustada_nec(
            amp_base,
            t_amb_c,
            ccc,
            aplicar=aplicar_derating,
        )

        if i_diseno_a <= amp_adj:
            awg = t["awg"]
            break
    else:
        awg = tabla[-1]["awg"]

    # ------------------------------------------------------
    # 2 Ajuste por VD
    # ------------------------------------------------------

    awg = ajustar_calibre_por_vd(
        tabla,
        awg=awg,
        i_a=i_diseno_a,
        v_v=v_base_v,
        l_m=l_m,
        vd_obj_pct=vd_obj_pct,
        n_hilos=n_hilos,
    )

    # ------------------------------------------------------
    # 3 Resultado final
    # ------------------------------------------------------

    fila = next(t for t in tabla if t["awg"] == awg)

    amp_base = float(fila["amp_a"])
    r = float(fila["r_ohm_km"])

    amp_adj, f_t, f_c = ampacidad_ajustada_nec(
        amp_base,
        t_amb_c,
        ccc,
        aplicar=aplicar_derating,
    )

    vd = caida_tension_pct(
        v=v_base_v,
        i=i_diseno_a,
        l_m=l_m,
        r_ohm_km=r,
        n_hilos=n_hilos,
    )

    cumple_amp = amp_adj >= i_diseno_a
    cumple_vd = vd <= vd_obj_pct

    return ResultadoConductor(

        nombre=nombre,

        i_diseno_a=i_diseno_a,
        v_base_v=v_base_v,
        l_m=l_m,

        calibre=str(awg),
        material=material,

        ampacidad_base_a=amp_base,
        ampacidad_ajustada_a=amp_adj,

        fac_temp=f_t,
        fac_ccc=f_c,

        vd_pct=vd,
        vd_obj_pct=vd_obj_pct,

        cumple_ampacidad=cumple_amp,
        cumple_vd=cumple_vd,
        cumple=(cumple_amp and cumple_vd),

        r_ohm_km=r,
        agotado_vd=(awg == tabla[-1]["awg"] and not cumple_vd),
    )

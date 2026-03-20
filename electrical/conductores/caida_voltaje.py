from __future__ import annotations

"""
MOTOR FÍSICO DE CAÍDA DE VOLTAJE — FV ENGINE
===========================================

🔷 PROPÓSITO
----------------------------------------------------------
Calcular la caída de tensión en conductores eléctricos
usando modelo resistivo puro.

----------------------------------------------------------
🔷 RESPONSABILIDADES
----------------------------------------------------------

✔ Cálculo de caída de tensión (%)
✔ Lectura de resistencia del conductor
✔ Ajuste de calibre por criterio de VD

----------------------------------------------------------
🔷 NO HACE
----------------------------------------------------------

✘ No calcula ampacidad
✘ No aplica factores NEC
✘ No selecciona calibre inicial

----------------------------------------------------------
🔷 FILOSOFÍA
----------------------------------------------------------

Este módulo responde:

    "¿Este conductor cumple caída de tensión?"

No decide ingeniería completa.
"""

from typing import Dict, List


# ==========================================================
# CAÍDA DE TENSIÓN
# ==========================================================

def caida_tension_pct(
    *,
    v: float,
    i: float,
    l_m: float,
    r_ohm_km: float,
    n_hilos: float = 2.0,
) -> float:
    """
    🔷 ENTRADAS

    v:
        → voltaje del circuito [V]

    i:
        → corriente del circuito [A]

    l_m:
        → longitud del tramo [m]

    r_ohm_km:
        → resistencia del conductor [ohm/km]

    n_hilos:
        → factor de camino eléctrico

        típicos:
            DC / monofásico → 2
            trifásico → 1.732

    ----------------------------------------------------------

    🔷 SALIDA

    vd_pct:
        → caída de tensión [%]
    """

    try:
        v = float(v)
        i = float(i)
        l_m = float(l_m)
        r_ohm_km = float(r_ohm_km)
        n_hilos = float(n_hilos)
    except Exception:
        return 0.0

    if n_hilos <= 0:
        n_hilos = 1.0

    if v <= 0 or i <= 0 or l_m <= 0 or r_ohm_km <= 0:
        return 0.0

    r_total = r_ohm_km * (l_m / 1000.0) * n_hilos

    vd_pct = 100.0 * (i * r_total) / v

    return vd_pct


# ==========================================================
# RESISTENCIA DESDE TABLA
# ==========================================================

def resistencia_de_tabla(
    tabla: List[Dict[str, float]],
    awg: str,
) -> float:
    """
    🔷 ENTRADAS

    tabla:
        → lista de conductores (AWG, resistencia)

    awg:
        → calibre buscado

    ----------------------------------------------------------

    🔷 SALIDA

    r_ohm_km:
        → resistencia del conductor

    Si no existe → 0.0
    """

    a = str(awg)

    for t in tabla:

        if str(t.get("awg")) == a:

            try:
                return float(t.get("r_ohm_km", 0.0))
            except Exception:
                return 0.0

    return 0.0


# ==========================================================
# AJUSTE DE CALIBRE POR VD
# ==========================================================

def ajustar_calibre_por_vd(
    tabla: List[Dict[str, float]],
    *,
    awg: str,
    i_a: float,
    v_v: float,
    l_m: float,
    vd_obj_pct: float,
    n_hilos: float = 2.0,
) -> str:
    """
    🔷 ENTRADAS

    tabla:
        → lista ordenada de conductores (menor → mayor)

    awg:
        → calibre inicial

    i_a:
        → corriente del circuito [A]

    v_v:
        → voltaje del circuito [V]

    l_m:
        → longitud del tramo [m]

    vd_obj_pct:
        → caída máxima permitida [%]

    n_hilos:
        → camino eléctrico

    ----------------------------------------------------------

    🔷 PROCESO

    Itera desde el calibre inicial hasta encontrar uno que cumpla:

        VD <= VD_objetivo

    ----------------------------------------------------------

    🔷 SALIDA

    awg_resultado:
        → calibre mínimo que cumple VD
    """

    try:
        i_a = float(i_a)
        v_v = float(v_v)
        l_m = float(l_m)
        vd_obj_pct = float(vd_obj_pct)
        n_hilos = float(n_hilos)
    except Exception:
        return str(awg)

    awg = str(awg)

    idx0 = next(
        (k for k, t in enumerate(tabla) if str(t.get("awg")) == awg),
        None,
    )

    if idx0 is None:
        idx0 = 0

    idx = idx0

    while idx < len(tabla):

        try:
            r = float(tabla[idx].get("r_ohm_km", 0.0))
        except Exception:
            r = 0.0

        vd = caida_tension_pct(
            v=v_v,
            i=i_a,
            l_m=l_m,
            r_ohm_km=r,
            n_hilos=n_hilos,
        )

        if vd <= vd_obj_pct:
            return str(tabla[idx].get("awg"))

        idx += 1

    return str(tabla[-1].get("awg"))


# ==========================================================
# RESUMEN DE VARIABLES DE SALIDA
# ==========================================================

"""
SALIDAS DEL MÓDULO
==================

1. caida_tension_pct(...)
--------------------------------

vd_pct:
    → caída de tensión [%]

Uso:
    validar calidad del diseño

----------------------------------------------------------

2. resistencia_de_tabla(...)
--------------------------------

r_ohm_km:
    → resistencia del conductor [ohm/km]

Uso:
    entrada para cálculo de VD

----------------------------------------------------------

3. ajustar_calibre_por_vd(...)
--------------------------------

awg_resultado:
    → calibre mínimo que cumple VD objetivo

Uso:
    ajuste fino de conductor después de ampacidad

----------------------------------------------------------

REGLA DE INGENIERÍA
----------------------------------------------------------

Este módulo NO decide calibre final.

Solo responde:

    "¿Este calibre cumple caída de tensión?"

La decisión final ocurre en:

    tramo_conductor
"""

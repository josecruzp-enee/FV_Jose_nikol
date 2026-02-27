"""
protecciones.py — FV Engine

Subdominio protecciones (OCPD).

Responsabilidad:
- Seleccionar tamaños estándar de OCPD (breaker/fuse) a partir de corrientes de diseño.
- Reglas mínimas para FV (string fusing cuando aplica).
- Entregar un shape estable para UI/PDF/orquestador.

Notas:
- Este módulo NO calcula corrientes. Recibe corrientes ya definidas por el orquestador/corrientes.
- Este módulo NO dimensiona conductores.
- Regla básica usada aquí: OCPD >= I_diseño, con I_diseño = I_nom * factor.
- String fusing: se activa típicamente cuando hay ≥3 strings en paralelo (combiner).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence


# Tamaños OCPD estándar (puedes extender sin tocar lógica).
TAMANOS_OCPD_STD: Sequence[int] = (
    15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200
)

# Referencias (dejadas como texto; tu motor final puede mapearlas a NEC exacto)
REFERENCIAS = [
    "NEC (reglas FV) — OCPD basado en corriente de diseño (criterio práctico).",
    "Recomendación práctica: usar tamaños estándar comerciales (siguiente tamaño ≥ I_diseño).",
    "String fusing: normalmente requerido con ≥3 strings en paralelo (combiner).",
]


def siguiente_ocpd(i_a: float, *, tabla: Sequence[int] = TAMANOS_OCPD_STD) -> int:
    """Devuelve el siguiente tamaño estándar >= i_a."""
    x = float(i_a)
    for s in tabla:
        if x <= float(s):
            return int(s)
    return int(tabla[-1])


def ocpd_desde_corriente(
    *,
    i_nom_a: float,
    factor: float = 1.25,
    tabla: Sequence[int] = TAMANOS_OCPD_STD,
) -> Dict[str, float | int]:
    """
    Calcula corriente de diseño y selecciona OCPD estándar.

    Returns:
      - i_nom_a
      - factor
      - i_diseno_a
      - tamano_a
    """
    i_nom = float(i_nom_a)
    f = float(factor)
    i_dis = i_nom * f
    return {
        "i_nom_a": round(i_nom, 3),
        "factor": round(f, 4),
        "i_diseno_a": round(i_dis, 3),
        "tamano_a": int(siguiente_ocpd(i_dis, tabla=tabla)),
    }


def fusible_string_fv(
    *,
    n_strings_paralelo: int,
    isc_mod_a: float,
    has_combiner: Optional[bool] = None,
    factor: float = 1.25,
    tabla: Sequence[int] = TAMANOS_OCPD_STD,
) -> Dict[str, Any]:
    """
    Reglas mínimas de fusible por string (FV).

    Criterio práctico:
      - si hay combiner o >=3 strings en paralelo, normalmente se requiere protección por string.
      - i_min ≈ factor * Isc_módulo (simplificado; luego puedes migrar a regla NEC exacta).

    Returns:
      - requerido: bool
      - i_min_a (si requerido)
      - tamano_a (si requerido)
      - nota
    """
    ns = max(0, int(n_strings_paralelo))
    requerido = bool(has_combiner) if has_combiner is not None else (ns >= 3)

    if not requerido:
        return {
            "requerido": False,
            "nota": "No requerido por criterio práctico (sin combiner o <3 strings en paralelo).",
        }

    if ns < 3:
        # Si el usuario fuerza has_combiner=True pero ns<3, igual dejamos trazabilidad.
        return {
            "requerido": True,
            "i_min_a": round(float(isc_mod_a) * float(factor), 3),
            "tamano_a": int(siguiente_ocpd(float(isc_mod_a) * float(factor), tabla=tabla)),
            "nota": "Combiner indicado; revisar si realmente hay strings en paralelo.",
        }

    i_min = float(isc_mod_a) * float(factor)
    return {
        "requerido": True,
        "i_min_a": round(i_min, 3),
        "tamano_a": int(siguiente_ocpd(i_min, tabla=tabla)),
        "nota": "Criterio práctico: ≥3 strings en paralelo requiere protección por string.",
    }


def dimensionar_protecciones_fv(
    *,
    iac_nom_a: float,
    n_strings_paralelo: int,
    isc_mod_a: float,
    has_combiner: Optional[bool] = None,
    factor_ac: float = 1.25,
    factor_dc: float = 1.25,
) -> Dict[str, Any]:
    """
    Orquestador simple de protecciones FV (solo OCPD por ahora).

    Entradas:
      - iac_nom_a: corriente nominal AC (del inversor o calculada)
      - n_strings_paralelo: cantidad de strings en paralelo en el punto donde podría haber combiner
      - isc_mod_a: Isc del módulo (o Isc_string si ese es tu criterio de entrada)
      - has_combiner: si hay combiner real
      - factor_ac: multiplicador para corriente de diseño AC
      - factor_dc: multiplicador para corriente base DC (string fuse)

    Salida (shape estable):
      - ok
      - ac: {breaker: {...}}
      - dc: {fusible_string: {...}}
      - referencias
    """
    ac = {"breaker": ocpd_desde_corriente(i_nom_a=float(iac_nom_a), factor=float(factor_ac))}
    dc = {
        "fusible_string": fusible_string_fv(
            n_strings_paralelo=int(n_strings_paralelo),
            isc_mod_a=float(isc_mod_a),
            has_combiner=has_combiner,
            factor=float(factor_dc),
        )
    }

    return {
        "ok": True,
        "ac": ac,
        "dc": dc,
        "referencias": list(REFERENCIAS),
    }


__all__ = [
    "TAMANOS_OCPD_STD",
    "siguiente_ocpd",
    "ocpd_desde_corriente",
    "fusible_string_fv",
    "dimensionar_protecciones_fv",
]

from __future__ import annotations

"""
PROTECCIONES FV — DOMINIO
"""

from dataclasses import dataclass
from typing import List

from electrical.conductores.corrientes import ResultadoCorrientes

from electrical.protecciones.resultado_protecciones import (
    ResultadoProtecciones,
    OCPDResultado,
    FusibleStringResultado,
)


# ==========================================================
# ENTRADA
# ==========================================================

@dataclass(frozen=True)
class EntradaProtecciones:
    corrientes: ResultadoCorrientes
    n_strings: int
    paneles=paneles


# ==========================================================
# TABLA NEC
# ==========================================================

TAMANOS_OCPD_STD = [
    15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 110, 125,
    150, 175, 200, 225, 250, 300,
    350, 400, 450, 500, 600
]


def seleccionar_ocpd(i_diseno: float) -> int:

    if i_diseno <= 0:
        raise ValueError("Corriente inválida para OCPD")

    for size in TAMANOS_OCPD_STD:
        if i_diseno <= size:
            return size

    raise ValueError("Corriente fuera de rango NEC 240.6")


# ==========================================================
# HELPERS
# ==========================================================

def _ocpd(i: float, norma: str) -> OCPDResultado:
    size = seleccionar_ocpd(i)
    return OCPDResultado(
        i_diseno_a=round(i, 3),
        tamano_a=size,
        norma=norma
    )


def _fusible_string(n_strings: int, i: float) -> FusibleStringResultado:

    if n_strings < 3:
        return FusibleStringResultado(
            requerido=False,
            i_diseno_a=None,
            tamano_a=None,
            norma=None,
            nota="No requerido (<3 strings)"
        )

    size = seleccionar_ocpd(i)

    return FusibleStringResultado(
        requerido=True,
        i_diseno_a=round(i, 3),
        tamano_a=size,
        norma="NEC 690.9",
        nota=None
    )


# ==========================================================
# 🔥 MPPT
# ==========================================================

def _ocpd_mppt(corrientes: ResultadoCorrientes) -> List[OCPDResultado]:

    resultado = []

    for mppt in getattr(corrientes, "mppt_detalle", []):
        resultado.append(
            _ocpd(
                mppt.i_diseno_a,
                "NEC 690.9 (MPPT)"
            )
        )

    return resultado


# ==========================================================
# 🔥 NUEVO: FUSIBLE POR MPPT
# ==========================================================

def _fusible_por_mppt(corrientes: ResultadoCorrientes, paneles) -> List[FusibleStringResultado]:

    resultado = []

    strings = getattr(paneles, "strings", [])

    # agrupar por zona
    grupos = {}

    for s in strings:
        zona = getattr(s, "zona", 0)
        grupos.setdefault(zona, []).append(s)

    for zona, grupo in grupos.items():

        n_strings = len(grupo)

        if n_strings < 3:
            resultado.append(
                FusibleStringResultado(
                    requerido=False,
                    i_diseno_a=None,
                    tamano_a=None,
                    norma=None,
                    nota="No requerido (<3 strings en MPPT)"
                )
            )
            continue

        isc = grupo[0].isc_string_a
        i_diseno = isc * 1.56  # NEC

        size = seleccionar_ocpd(i_diseno)

        resultado.append(
            FusibleStringResultado(
                requerido=True,
                i_diseno_a=round(i_diseno, 3),
                tamano_a=size,
                norma="NEC 690.9 (string)",
                nota=None
            )
        )

    return resultado


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def calcular_protecciones(
    entrada: EntradaProtecciones
) -> ResultadoProtecciones:

    errores: list[str] = []
    warnings: list[str] = []

    try:
        corr = entrada.corrientes

        return ResultadoProtecciones(
            ok=True,
            errores=[],
            warnings=warnings,

            # -----------------------------
            # AC
            # -----------------------------
            ocpd_ac=_ocpd(
                corr.ac.i_diseno_a,
                "NEC 690.8 / 210.20(A)"
            ),

            # -----------------------------
            # DC GLOBAL (LEGACY)
            # 👉 NO usar en diseño real
            # -----------------------------
            ocpd_dc_array=OCPDResultado(
                i_diseno_a=0.0,
                tamano_a=0,
                norma="NO APLICA (MPPT independientes)"
            ),

            # -----------------------------
            # STRING (LEGACY)
            # -----------------------------
            fusible_string=_fusible_string(
                entrada.n_strings,
                corr.string.i_diseno_a
            ),

            # -----------------------------
            # MPPT
            # -----------------------------
            mppt=_ocpd_mppt(corr),

            # -----------------------------
            # 🔥 NUEVO
            # -----------------------------
            fusible_mppt=_fusible_por_mppt(
                corr,
                entrada.paneles
            )
        )

    except Exception as e:

        errores.append(str(e))

        return ResultadoProtecciones(
            ok=False,
            errores=errores,
            warnings=warnings,

            ocpd_ac=OCPDResultado(0.0, 0, ""),

            ocpd_dc_array=OCPDResultado(0.0, 0, ""),

            fusible_string=FusibleStringResultado(
                False, None, None, None, "error"
            ),

            mppt=[],

            fusible_mppt=[]  # 🔥 clave
        )

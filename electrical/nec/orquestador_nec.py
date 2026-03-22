from __future__ import annotations

"""
ADAPTADOR NEC — FV ENGINE (CORRECTO)

Rol:
    Adaptador tipado entre:
        core → electrical

NO usa dict
NO usa .get()
NO calcula nada

Solo transforma estructuras
"""

from dataclasses import dataclass
from typing import List

from core.dominio.contrato import ResultadoSizing

from electrical.ingenieria_electrica import (
    ejecutar_ingenieria_electrica,
    ResultadoElectrico,
)

# ==========================================================
# CONTRATOS INTERNOS
# ==========================================================

@dataclass(frozen=True)
class StringData:
    imp_string_a: float
    isc_string_a: float
    vmp_string_v: float


@dataclass(frozen=True)
class EntradaStrings:
    strings: List[StringData]


@dataclass(frozen=True)
class DatosInversor:
    kw_ac: float
    v_ac_nom_v: float
    fases: int
    fp: float


@dataclass(frozen=True)
class ParametrosConductores:
    vdc: float
    vac: float
    l_dc: float
    l_ac: float
    vd_dc: float
    vd_ac: float


@dataclass(frozen=True)
class EntradaNEC:
    strings: EntradaStrings
    inversor: DatosInversor
    n_strings: int
    params_conductores: ParametrosConductores


@dataclass(frozen=True)
class ResultadoNEC:
    entrada: EntradaNEC
    resultado: ResultadoElectrico


# ==========================================================
# EXTRACCIÓN DE STRINGS (TIPADA)
# ==========================================================

def _extraer_strings(strings) -> EntradaStrings:

    if hasattr(strings, "strings"):
        lista = strings.strings
    elif isinstance(strings, list):
        lista = strings
    else:
        raise ValueError("Formato de strings inválido")

    resultado: List[StringData] = []

    for s in lista:

        if hasattr(s, "imp_string_a"):
            resultado.append(
                StringData(
                    imp_string_a=s.imp_string_a,
                    isc_string_a=s.isc_string_a,
                    vmp_string_v=s.vmp_string_v,
                )
            )
        else:
            raise ValueError("String sin atributos válidos")

    return EntradaStrings(strings=resultado)


# ==========================================================
# BASE ELÉCTRICA
# ==========================================================

def _leer_base_electrica(p):

    if not hasattr(p, "electrico"):
        raise ValueError("Proyecto sin datos eléctricos")

    base = p.electrico

    return base.vac, base.fases, base.fp


# ==========================================================
# CONSTRUCCIÓN DE ENTRADA
# ==========================================================

def _construir_entrada_nec(
    p,
    sizing: ResultadoSizing,
    strings
) -> EntradaNEC:

    entrada_strings = _extraer_strings(strings)

    vac, fases, fp = _leer_base_electrica(p)

    if not entrada_strings.strings:
        raise ValueError("No hay strings disponibles")

    s0 = entrada_strings.strings[0]

    params = ParametrosConductores(
        vdc=s0.vmp_string_v,
        vac=vac,
        l_dc=10.0,      # ⚠️ luego parametrizar
        l_ac=10.0,
        vd_dc=2.0,
        vd_ac=2.0,
    )

    return EntradaNEC(
        strings=entrada_strings,
        inversor=DatosInversor(
            kw_ac=sizing.kw_ac,
            v_ac_nom_v=vac,
            fases=fases,
            fp=fp,
        ),
        n_strings=len(entrada_strings.strings),
        params_conductores=params,
    )


# ==========================================================
# ORQUESTADOR NEC
# ==========================================================

def ejecutar_nec(
    p,
    sizing: ResultadoSizing,
    strings
) -> ResultadoNEC:

    entrada = _construir_entrada_nec(
        p,
        sizing,
        strings
    )

    resultado = ejecutar_ingenieria_electrica(
        datos_strings=entrada.strings,
        datos_inversor=entrada.inversor,
        n_strings=entrada.n_strings,
        params_conductores=entrada.params_conductores,
    )

    return ResultadoNEC(
        entrada=entrada,
        resultado=resultado
    )

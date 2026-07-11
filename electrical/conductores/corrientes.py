from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional
import math

from electrical.paneles.resultado_paneles import ResultadoPaneles


# ==========================================================
# MODELOS
# ==========================================================

@dataclass(frozen=True)
class NivelCorriente:
    i_operacion_a: float
    i_diseno_a: float


@dataclass(frozen=True)
class ResultadoCorrientes:
    ok: bool

    panel: NivelCorriente
    string: NivelCorriente
    mppt: NivelCorriente
    dc_total: NivelCorriente
    ac_inversor: NivelCorriente
    ac_total: NivelCorriente
    ac: NivelCorriente

    mppt_detalle: List[NivelCorriente]
    strings_detalle: List
    inversores_detalle: List[NivelCorriente]

    errores: List[str]
    warnings: List[str]

    # =========================
    # RESULTADO CORRECTO
    # =========================
    @staticmethod
    def build(
        panel: NivelCorriente,
        string: NivelCorriente,
        mppt: NivelCorriente,
        dc_total: NivelCorriente,
        ac_inversor: NivelCorriente,
        ac_total: NivelCorriente,
        ac: NivelCorriente,
        mppt_detalle: Optional[List[NivelCorriente]] = None,
        strings_detalle: Optional[List] = None,
        inversores_detalle: Optional[List[NivelCorriente]] = None,
        warnings: Optional[List[str]] = None,
    ) -> "ResultadoCorrientes":

        return ResultadoCorrientes(
            ok=True,
            panel=panel,
            string=string,
            mppt=mppt,
            dc_total=dc_total,
            ac_inversor=ac_inversor,
            ac_total=ac_total,
            ac=ac,
            mppt_detalle=mppt_detalle or [],
            strings_detalle=strings_detalle or [],
            inversores_detalle=inversores_detalle or [],
            errores=[],
            warnings=warnings or [],
        )

    # =========================
    # RESULTADO CON ERROR
    # =========================
    @staticmethod
    def error(msg: str) -> "ResultadoCorrientes":

        cero = NivelCorriente(
            i_operacion_a=0.0,
            i_diseno_a=0.0,
        )

        return ResultadoCorrientes(
            ok=False,
            panel=cero,
            string=cero,
            mppt=cero,
            dc_total=cero,
            ac_inversor=cero,
            ac_total=cero,
            ac=cero,
            mppt_detalle=[],
            strings_detalle=[],
            inversores_detalle=[],
            errores=[msg],
            warnings=[],
        )


# ==========================================================
# DATOS DE ENTRADA
# ==========================================================

@dataclass(frozen=True)
class CorrientesInput:
    paneles: ResultadoPaneles

    # Potencia AC TOTAL del sistema, no potencia unitaria.
    kw_ac: float

    # Tensión AC línea-línea o tensión del circuito evaluado.
    vac: float

    # Valores admitidos: 1 o 3.
    fases: int

    fp: float
    n_inversores: int = 1

    factor_dc: float = 1.25
    factor_ac: float = 1.25


# ==========================================================
# VALIDACIONES
# ==========================================================

def _validar_entrada(
    inp: CorrientesInput,
) -> Optional[str]:

    if inp is None:
        return "CorrientesInput no fue proporcionado"

    if inp.paneles is None:
        return "El resultado de paneles no está disponible"

    if float(inp.kw_ac or 0.0) <= 0:
        return "kw_ac debe ser mayor que cero"

    if float(inp.vac or 0.0) <= 0:
        return "vac debe ser mayor que cero"

    if int(inp.fases or 0) not in (1, 3):
        return "fases debe ser 1 o 3"

    if float(inp.fp or 0.0) <= 0:
        return "El factor de potencia debe ser mayor que cero"

    if float(inp.fp or 0.0) > 1:
        return "El factor de potencia no puede ser mayor que 1"

    if int(inp.n_inversores or 0) <= 0:
        return "n_inversores debe ser mayor que cero"

    if float(inp.factor_dc or 0.0) <= 0:
        return "factor_dc debe ser mayor que cero"

    if float(inp.factor_ac or 0.0) <= 0:
        return "factor_ac debe ser mayor que cero"

    return None


def _leer_corriente_string(
    string,
    campo: str,
) -> float:

    valor = float(
        getattr(string, campo, 0.0) or 0.0
    )

    if valor <= 0:
        raise ValueError(
            f"El string no contiene un valor válido para '{campo}'"
        )

    return valor


# ==========================================================
# AGRUPACIÓN DE STRINGS POR INVERSOR Y MPPT
# ==========================================================

def _agrupar_por_mppt(strings):

    grupos = defaultdict(list)

    for string in strings:

        inversor = getattr(
            string,
            "inversor",
            None,
        )

        mppt = getattr(
            string,
            "mppt",
            None,
        )

        if inversor is None:
            raise ValueError(
                "Se encontró un string sin número de inversor"
            )

        if mppt is None:
            raise ValueError(
                "Se encontró un string sin número de MPPT"
            )

        grupos[(inversor, mppt)].append(string)

    return grupos


# ==========================================================
# CORRIENTE DEL PANEL Y DEL STRING
# ==========================================================

def _calcular_corriente_panel_y_string(
    string_referencia,
    factor_dc: float,
) -> tuple[NivelCorriente, NivelCorriente]:

    imp_a = _leer_corriente_string(
        string_referencia,
        "imp_string_a",
    )

    isc_a = _leer_corriente_string(
        string_referencia,
        "isc_string_a",
    )

    # ------------------------------------------------------
    # PANEL
    # ------------------------------------------------------
    # La corriente de operación corresponde a Imp.
    # La corriente base de diseño/protección corresponde a Isc.
    #
    # En una conexión serie:
    # - Imp del string = Imp del módulo.
    # - Isc del string = Isc del módulo.
    # ------------------------------------------------------

    panel = NivelCorriente(
        i_operacion_a=imp_a,
        i_diseno_a=isc_a * factor_dc,
    )

    # ------------------------------------------------------
    # STRING
    # ------------------------------------------------------

    string = NivelCorriente(
        i_operacion_a=imp_a,
        i_diseno_a=isc_a * factor_dc,
    )

    return panel, string


# ==========================================================
# CORRIENTES POR MPPT
# ==========================================================

def _calcular_corrientes_mppt(
    strings,
    factor_dc: float,
) -> List[NivelCorriente]:

    grupos = _agrupar_por_mppt(strings)
    detalle = []

    print("\n🔹 CÁLCULO MPPT")

    for (inversor_id, mppt_id), grupo in grupos.items():

        i_operacion_a = sum(
            _leer_corriente_string(
                string,
                "imp_string_a",
            )
            for string in grupo
        )

        isc_total_a = sum(
            _leer_corriente_string(
                string,
                "isc_string_a",
            )
            for string in grupo
        )

        i_diseno_a = isc_total_a * factor_dc

        print(
            f"INV {inversor_id} / MPPT {mppt_id}:"
        )
        print(
            "  strings:",
            len(grupo),
        )
        print(
            "  I operación:",
            i_operacion_a,
        )
        print(
            "  I diseño:",
            i_diseno_a,
        )

        detalle.append(
            NivelCorriente(
                i_operacion_a=i_operacion_a,
                i_diseno_a=i_diseno_a,
            )
        )

    return detalle


# ==========================================================
# CORRIENTE DC TOTAL
# ==========================================================

def _calcular_corriente_dc_total(
    mppt_detalle: List[NivelCorriente],
) -> NivelCorriente:

    return NivelCorriente(
        i_operacion_a=sum(
            mppt.i_operacion_a
            for mppt in mppt_detalle
        ),
        i_diseno_a=sum(
            mppt.i_diseno_a
            for mppt in mppt_detalle
        ),
    )


# ==========================================================
# CORRIENTES AC
# ==========================================================

def _calcular_corrientes_ac(
    *,
    kw_ac_total: float,
    vac: float,
    fases: int,
    fp: float,
    factor_ac: float,
    n_inversores: int,
) -> tuple[
    NivelCorriente,
    NivelCorriente,
    List[NivelCorriente],
]:

    potencia_total_w = kw_ac_total * 1000.0

    # ------------------------------------------------------
    # CORRIENTE TOTAL DEL SISTEMA
    # ------------------------------------------------------

    if fases == 3:

        i_operacion_total_a = (
            potencia_total_w
            / (
                math.sqrt(3)
                * vac
                * fp
            )
        )

    else:

        i_operacion_total_a = (
            potencia_total_w
            / (
                vac
                * fp
            )
        )

    i_diseno_total_a = (
        i_operacion_total_a
        * factor_ac
    )

    ac_total = NivelCorriente(
        i_operacion_a=i_operacion_total_a,
        i_diseno_a=i_diseno_total_a,
    )

    # ------------------------------------------------------
    # CORRIENTE POR INVERSOR
    # ------------------------------------------------------
    # Esta división es válida porque kw_ac_total representa
    # la potencia AC total y se asume que los inversores son
    # iguales y comparten la potencia uniformemente.
    # ------------------------------------------------------

    i_operacion_inversor_a = (
        i_operacion_total_a
        / n_inversores
    )

    i_diseno_inversor_a = (
        i_diseno_total_a
        / n_inversores
    )

    ac_inversor = NivelCorriente(
        i_operacion_a=i_operacion_inversor_a,
        i_diseno_a=i_diseno_inversor_a,
    )

    inversores_detalle = [
        NivelCorriente(
            i_operacion_a=i_operacion_inversor_a,
            i_diseno_a=i_diseno_inversor_a,
        )
        for _ in range(n_inversores)
    ]

    return (
        ac_total,
        ac_inversor,
        inversores_detalle,
    )


# ==========================================================
# MOTOR PRINCIPAL
# ==========================================================

def calcular_corrientes(
    inp: CorrientesInput,
) -> ResultadoCorrientes:

    print("\n########################################")
    print("🔥 DEBUG CORRIENTES INICIO")
    print("########################################")

    error_entrada = _validar_entrada(inp)

    if error_entrada:
        return ResultadoCorrientes.error(
            error_entrada
        )

    paneles = inp.paneles
    array = getattr(
        paneles,
        "array",
        None,
    )

    strings = (
        getattr(
            paneles,
            "strings",
            [],
        )
        or []
    )

    if array is None:
        return ResultadoCorrientes.error(
            "No existe información del arreglo FV"
        )

    print(
        "Total strings:",
        len(strings),
    )

    print(
        "n_strings_total:",
        getattr(
            array,
            "n_strings_total",
            "N/A",
        ),
    )

    # ------------------------------------------------------
    # VALIDACIONES DEL ARREGLO
    # ------------------------------------------------------

    if not strings:
        return ResultadoCorrientes.error(
            "No hay strings definidos"
        )

    n_strings_total = int(
        getattr(
            array,
            "n_strings_total",
            0,
        )
        or 0
    )

    if n_strings_total <= 0:
        return ResultadoCorrientes.error(
            "n_strings_total inválido"
        )

    factor_dc = float(
        inp.factor_dc
    )

    factor_ac = float(
        inp.factor_ac
    )

    n_inversores = int(
        inp.n_inversores
    )

    # ------------------------------------------------------
    # PANEL Y STRING
    # ------------------------------------------------------

    try:
        panel, string = (
            _calcular_corriente_panel_y_string(
                strings[0],
                factor_dc,
            )
        )

    except (TypeError, ValueError) as exc:
        return ResultadoCorrientes.error(
            str(exc)
        )

    print("\n🔹 PANEL")
    print(
        "I operación (Imp):",
        panel.i_operacion_a,
    )
    print(
        "I diseño (Isc × factor DC):",
        panel.i_diseno_a,
    )

    print("\n🔹 STRING")
    print(
        "I operación (Imp):",
        string.i_operacion_a,
    )
    print(
        "I diseño (Isc × factor DC):",
        string.i_diseno_a,
    )

    # ------------------------------------------------------
    # MPPT
    # ------------------------------------------------------

    try:
        mppt_detalle = (
            _calcular_corrientes_mppt(
                strings,
                factor_dc,
            )
        )

    except (TypeError, ValueError) as exc:
        return ResultadoCorrientes.error(
            str(exc)
        )

    mppt = (
        max(
            mppt_detalle,
            key=lambda nivel: nivel.i_diseno_a,
        )
        if mppt_detalle
        else NivelCorriente(
            i_operacion_a=0.0,
            i_diseno_a=0.0,
        )
    )

    print(
        "\nLEN mppt_detalle:",
        len(mppt_detalle),
    )

    # ------------------------------------------------------
    # DC TOTAL
    # ------------------------------------------------------

    dc_total = _calcular_corriente_dc_total(
        mppt_detalle
    )

    print("\n🔹 DC TOTAL")
    print(
        "I operación:",
        dc_total.i_operacion_a,
    )
    print(
        "I diseño:",
        dc_total.i_diseno_a,
    )

    # ------------------------------------------------------
    # AC
    # ------------------------------------------------------

    ac_total, ac_inversor, inversores_detalle = (
        _calcular_corrientes_ac(
            kw_ac_total=float(inp.kw_ac),
            vac=float(inp.vac),
            fases=int(inp.fases),
            fp=float(inp.fp),
            factor_ac=factor_ac,
            n_inversores=n_inversores,
        )
    )

    print("\n🔹 AC TOTAL")
    print(
        "I operación:",
        ac_total.i_operacion_a,
    )
    print(
        "I diseño:",
        ac_total.i_diseno_a,
    )

    print("\n🔹 AC POR INVERSOR")
    print(
        "I operación:",
        ac_inversor.i_operacion_a,
    )
    print(
        "I diseño:",
        ac_inversor.i_diseno_a,
    )

    print("\n########################################")
    print("🔥 DEBUG CORRIENTES FIN")
    print("########################################\n")

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

    return ResultadoCorrientes.build(
        panel=panel,
        string=string,
        mppt=mppt,
        dc_total=dc_total,
        ac_inversor=ac_inversor,
        ac_total=ac_total,
        ac=ac_total,
        mppt_detalle=mppt_detalle,
        strings_detalle=strings,
        inversores_detalle=inversores_detalle,
    )


# ==========================================================
# RESUMEN TÉCNICO DEL MÓDULO
# ==========================================================
#
# Este módulo calcula las corrientes eléctricas principales.
#
# Corrientes DC:
# - Operación del panel: Imp.
# - Diseño del panel: Isc × factor_dc.
# - Operación del string: Imp.
# - Diseño del string: Isc × factor_dc.
# - MPPT: suma de corrientes de strings conectados en paralelo.
#
# Corrientes AC:
# - kw_ac representa la potencia AC total del sistema.
# - Una fase:
#       I = P / (V × FP)
# - Tres fases:
#       I = P / (√3 × V × FP)
# - La corriente por inversor se obtiene dividiendo la corriente
#   total entre n_inversores, bajo el supuesto de inversores iguales.
#
# Este módulo no valida si el modelo de inversor es compatible
# con la tensión, las fases o el esquema de conexión del cliente.
# Esa validación corresponde al selector técnico de inversores.
#
# Este módulo tampoco selecciona calibres ni protecciones.
# Solo entrega las corrientes necesarias para dimensionarlos.
# ==========================================================

# ==========================================================
# RESUMEN TÉCNICO DEL MÓDULO
# ==========================================================
#
# Este módulo calcula las corrientes eléctricas principales del sistema FV.
#
# Entradas principales:
# - paneles: resultado del dimensionamiento de paneles y strings.
# - kw_ac: potencia AC total del sistema.
# - vac: voltaje AC del sistema.
# - fases: 1 o 3.
# - fp: factor de potencia.
# - n_inversores: cantidad de inversores.
# - factor_dc: factor de diseño DC, normalmente 1.25.
# - factor_ac: factor de diseño AC, normalmente 1.25.
#
# Salidas principales:
# - panel: corriente de un panel.
# - string: corriente de un string.
# - mppt: MPPT crítico, es decir, el de mayor corriente de diseño.
# - dc_total: suma de todos los MPPT.
# - ac_inversor: corriente AC de diseño por cada inversor.
# - ac_total / ac: corriente AC total del sistema.
# - mppt_detalle: lista de corrientes por cada MPPT real.
# - inversores_detalle: lista de corrientes AC individuales por inversor.
#
# Criterio importante:
# - Los strings en paralelo dentro de un mismo MPPT suman corriente.
# - Cada MPPT se calcula agrupando por (inversor, mppt).
# - La corriente AC total se divide entre n_inversores para obtener ac_inversor.
# - inversores_detalle permite dimensionar conductores y protecciones
#   separados para cada salida de inversor.
#
# Este módulo NO selecciona calibres, protecciones ni canalizaciones.
# Solo calcula corrientes. El dimensionamiento de conductores debe hacerse
# en el módulo de conductores usando mppt_detalle e inversores_detalle.
# ==========================================================

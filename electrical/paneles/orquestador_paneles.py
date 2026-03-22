from __future__ import annotations

"""
ORQUESTADOR DEL DOMINIO PANELES — FV ENGINE

Coordina:

    EntradaPaneles
        ↓
    validaciones
        ↓
    dimensionado
        ↓
    cálculo de strings
        ↓
    ResultadoPaneles

REGLA:
    - NO dict
    - NO get
    - NO lógica eléctrica compleja
    - SOLO orquestación
"""

from dataclasses import dataclass
from typing import List

from .entrada_panel import EntradaPaneles
from .dimensionado_paneles import dimensionar_paneles
from .calculo_de_strings import calcular_strings_fv

from .validacion_strings import (
    validar_panel,
    validar_inversor,
    validar_parametros_generales,
)

from .resultado_paneles import (
    ResultadoPaneles,
    ArrayFV,
    StringFV,
    RecomendacionStrings,
)


# =========================================================
# META TIPADA
# =========================================================

@dataclass(frozen=True)
class MetaPaneles:
    n_paneles_total: int
    pdc_kw: float
    n_inversores: int


# =========================================================
# HELPERS
# =========================================================

def _resultado_error(errores: List[str], warnings: List[str]) -> ResultadoPaneles:

    return ResultadoPaneles(
        ok=False,
        topologia="desconocida",
        array=ArrayFV(
            potencia_dc_w=0.0,
            vdc_nom=0.0,
            idc_nom=0.0,
            voc_frio_array_v=0.0,
            n_strings_total=0,
            n_paneles_total=0,
            strings_por_mppt=0,
            n_mppt=0,
            p_panel_w=0.0,
            isc_total=0.0,
        ),
        recomendacion=RecomendacionStrings(
            n_series=0,
            n_strings_total=0,
            strings_por_mppt=0,
            vmp_string_v=0.0,
            vmp_stc_string_v=0.0,
            voc_frio_string_v=0.0,
        ),
        strings=[],
        warnings=warnings,
        errores=errores,
        meta=MetaPaneles(0, 0.0, 0),
    )


# =========================================================
# ORQUESTADOR PRINCIPAL
# =========================================================

def ejecutar_paneles(entrada: EntradaPaneles) -> ResultadoPaneles:

    errores: List[str] = []
    warnings: List[str] = []

    panel = entrada.panel
    inversor = entrada.inversor

    # ======================================================
    # VALIDACIONES
    # ======================================================

    val = validar_panel(panel)
    errores += val.errores
    warnings += val.warnings

    val = validar_inversor(inversor)
    errores += val.errores
    warnings += val.warnings

    val = validar_parametros_generales(
        entrada.n_paneles_total or 0,
        entrada.t_min_c,
        entrada.t_oper_c,
    )
    errores += val.errores
    warnings += val.warnings

    if errores:
        return _resultado_error(errores, warnings)

    # ======================================================
    # DIMENSIONADO
    # ======================================================

    dim = dimensionar_paneles(entrada)

    if not dim.ok:
        return _resultado_error(dim.errores, warnings)

    if dim.n_paneles <= 0:
        return _resultado_error(["Número de paneles inválido"], warnings)

    # ======================================================
    # STRINGS
    # ======================================================

    n_inversores = max(1, int(entrada.n_inversores or 1))

    strings_res = calcular_strings_fv(
        n_paneles_total=dim.n_paneles,
        panel=panel,
        inversor=inversor,
        n_inversores=n_inversores,
        t_min_c=float(entrada.t_min_c),
        t_oper_c=entrada.t_oper_c,
        dos_aguas=entrada.dos_aguas,
        objetivo_dc_ac=entrada.objetivo_dc_ac,
        pdc_kw_objetivo=entrada.pdc_kw_objetivo,
    )

    warnings += strings_res.warnings

    if not strings_res.ok:
        return _resultado_error(strings_res.errores, warnings)

    # ======================================================
    # ARRAY FV (AGREGACIÓN)
    # ======================================================

    n_strings_total = strings_res.recomendacion.n_strings_total

    idc_nom = panel.imp_a * n_strings_total
    isc_total = panel.isc_a * n_strings_total

    strings_por_mppt = (
        n_strings_total // inversor.n_mppt
        if inversor.n_mppt > 0 else 0
    )

    array = ArrayFV(
        potencia_dc_w=dim.pdc_kw * 1000.0,
        vdc_nom=strings_res.recomendacion.vmp_string_v,
        idc_nom=idc_nom,
        voc_frio_array_v=strings_res.recomendacion.voc_string_v,
        n_strings_total=n_strings_total,
        n_paneles_total=dim.n_paneles,
        strings_por_mppt=strings_por_mppt,
        n_mppt=inversor.n_mppt,
        p_panel_w=panel.pmax_w,
        isc_total=isc_total,
    )

    # ======================================================
    # RECOMENDACION
    # ======================================================

    recomendacion = RecomendacionStrings(
        n_series=strings_res.recomendacion.n_series,
        n_strings_total=n_strings_total,
        strings_por_mppt=strings_por_mppt,
        vmp_string_v=strings_res.recomendacion.vmp_string_v,
        vmp_stc_string_v=strings_res.recomendacion.vmp_string_v,
        voc_frio_string_v=strings_res.recomendacion.voc_string_v,
    )

    # ======================================================
    # STRINGS → DOMAIN OBJECT
    # ======================================================

    strings_obj = [
        StringFV(
            mppt=s.mppt,
            n_series=s.n_series,
            vmp_string_v=s.vmp_string_v,
            voc_frio_string_v=s.voc_frio_string_v,
            imp_string_a=s.imp_string_a,
            isc_string_a=s.isc_string_a,
            i_mppt_a=s.imp_string_a,
            isc_mppt_a=s.isc_string_a,
            imax_pv_a=0.0,
            idesign_cont_a=0.0,
        )
        for s in strings_res.strings
    ]

    # ======================================================
    # META
    # ======================================================

    meta = MetaPaneles(
        n_paneles_total=dim.n_paneles,
        pdc_kw=dim.pdc_kw,
        n_inversores=n_inversores,
    )

    # ======================================================
    # SALIDA FINAL
    # ======================================================

    return ResultadoPaneles(
        ok=True,
        topologia="string-centralizado",
        array=array,
        recomendacion=recomendacion,
        strings=strings_obj,
        warnings=warnings,
        errores=[],
        meta=meta,
    )

# ==========================================================
# SALIDAS DEL ARCHIVO
# ==========================================================
#
# FUNCIÓN PRINCIPAL:
# ----------------------------------------------------------
# ejecutar_paneles(entrada: EntradaPaneles)
#
#
# ----------------------------------------------------------
# ENTRADA (CONTRATO)
# ----------------------------------------------------------
#
# EntradaPaneles:
#
#   panel: PanelSpec
#       → características eléctricas del módulo FV
#           - pmax_w
#           - vmp_v
#           - voc_v
#           - imp_a
#           - isc_a
#
#   inversor: InversorSpec
#       → restricciones eléctricas del sistema
#           - kw_ac
#           - vdc_max_v
#           - mppt_min_v
#           - mppt_max_v
#           - n_mppt
#
#   n_paneles_total: Optional[int]
#       → número de paneles (modo manual)
#
#   pdc_kw_objetivo: Optional[float]
#       → potencia objetivo (modo automático)
#
#   n_inversores: Optional[int]
#       → cantidad de inversores
#
#   t_min_c: float
#       → temperatura mínima (Voc frío)
#
#   t_oper_c: Optional[float]
#       → temperatura de operación
#
#   dos_aguas: bool
#       → configuración física
#
#   objetivo_dc_ac: Optional[float]
#       → ratio DC/AC
#
#
# ----------------------------------------------------------
# PROCESO (FLUJO INTERNO)
# ----------------------------------------------------------
#
# 1. VALIDACIÓN
#       - validar_panel
#       - validar_inversor
#       - validar_parametros_generales
#
# 2. DIMENSIONADO
#       - cálculo de número de paneles
#       - cálculo de potencia DC
#
# 3. CÁLCULO DE STRINGS
#       - número de módulos en serie
#       - número de strings
#       - voltajes (Vmp, Voc frío)
#       - corrientes por string
#
# 4. CONSTRUCCIÓN DEL ARRAY FV
#       - agregación del sistema completo
#
# 5. CONSTRUCCIÓN DE OBJETOS DE DOMINIO
#       - ArrayFV
#       - StringFV
#       - RecomendacionStrings
#
# 6. SALIDA FINAL
#
#
# ----------------------------------------------------------
# VARIABLES CALCULADAS (CLAVE)
# ----------------------------------------------------------
#
# dim.n_paneles
#       → número total de paneles
#
# dim.pdc_kw
#       → potencia DC instalada
#
# strings_res.recomendacion.n_strings_total
#       → número total de strings
#
# idc_nom
#       → corriente DC nominal del generador
#
# isc_total
#       → corriente máxima DC (corto circuito)
#
# strings_por_mppt
#       → distribución promedio por MPPT
#
#
# ----------------------------------------------------------
# SALIDA
# ----------------------------------------------------------
#
# ResultadoPaneles:
#
#   ok: bool
#       → estado del cálculo
#
#   array: ArrayFV
#       → modelo agregado del sistema:
#           - potencia_dc_w
#           - vdc_nom
#           - idc_nom
#           - voc_frio_array_v
#           - n_strings_total
#           - n_paneles_total
#           - strings_por_mppt
#           - n_mppt
#           - isc_total
#
#   recomendacion: RecomendacionStrings
#       → configuración óptima:
#           - n_series
#           - n_strings_total
#           - strings_por_mppt
#
#   strings: List[StringFV]
#       → detalle por string
#
#   warnings: List[str]
#       → advertencias técnicas
#
#   errores: List[str]
#       → errores críticos
#
#   meta: MetaPaneles
#       → datos de trazabilidad:
#           - n_paneles_total
#           - pdc_kw
#           - n_inversores
#
#
# ----------------------------------------------------------
# UBICACIÓN EN LA ARQUITECTURA
# ----------------------------------------------------------
#
# Carpeta:
#   electrical/paneles/
#
# Rol:
#   Orquestador del dominio paneles
#
#
# ----------------------------------------------------------
# FLUJO GLOBAL DEL SISTEMA
# ----------------------------------------------------------
#
# EntradaPaneles
#       ↓
# ejecutar_paneles  ← ESTE MÓDULO
#       ↓
# ResultadoPaneles
#       ↓
# Corrientes
#       ↓
# Conductores
#       ↓
# Protecciones (NEC)
#
#
# ----------------------------------------------------------
# PRINCIPIOS
# ----------------------------------------------------------
#
# ✔ NO usa dict
# ✔ SOLO usa dataclass
# ✔ NO calcula NEC
# ✔ NO calcula corrientes
# ✔ NO calcula energía
#
# SOLO:
#   → define el generador FV
#
#
# ----------------------------------------------------------
# CONSUMIDO POR
# ----------------------------------------------------------
#
# core.aplicacion.orquestador_estudio
#
#
# ----------------------------------------------------------
# NOTA DE DISEÑO
# ----------------------------------------------------------
#
# Este módulo define la base eléctrica del sistema FV.
#
# Todo el sistema depende de este resultado.
#
# Si este módulo es correcto:
#   → todo el engine será consistente
#
# ==========================================================

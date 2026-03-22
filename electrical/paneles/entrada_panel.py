from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO PANELES (FV ENGINE)
================================================

🔷 PROPÓSITO
----------------------------------------------------------
Definir de forma estricta y tipada el problema eléctrico
del sistema fotovoltaico en el dominio de paneles.

Este objeto representa:

    "las condiciones iniciales del sistema FV"

NO realiza cálculos.
NO transforma datos.
NO contiene lógica.

----------------------------------------------------------
🔷 PRINCIPIO FUNDAMENTAL
----------------------------------------------------------

EntradaPaneles  = definición del problema
ResultadoPaneles = solución eléctrica

Nunca se mezclan.
Nunca se mutan.
Nunca se recalculan fuera del dominio.

----------------------------------------------------------
🔷 CONSUMIDO POR
----------------------------------------------------------

electrical.paneles.orquestador_paneles

Ese módulo:
    → valida entradas
    → dimensiona sistema
    → calcula strings
    → construye ResultadoPaneles
"""

from dataclasses import dataclass
from typing import Optional


# =========================================================
# ENTRADA DEL DOMINIO PANELES
# =========================================================

@dataclass(frozen=True)
class EntradaPaneles:

    # =====================================================
    # ESPECIFICACIÓN DEL MÓDULO FV
    # =====================================================

    panel: any
    """
    Datos eléctricos del panel fotovoltaico (unidad).

    Debe incluir:
        pmax_w   → potencia nominal [W]
        vmp_v    → voltaje en MPPT [V]
        voc_v    → voltaje en circuito abierto [V]
        imp_a    → corriente en MPPT [A]
        isc_a    → corriente de cortocircuito [A]

    Define:
        → comportamiento eléctrico base del sistema
        → voltajes y corrientes de strings
    """

    # =====================================================
    # ESPECIFICACIÓN DEL INVERSOR
    # =====================================================

    inversor: any
    """
    Restricciones eléctricas del inversor (lado DC y AC).

    Debe incluir:
        kw_ac         → potencia nominal AC [kW]
        vmppt_min_v   → voltaje mínimo MPPT [V]
        vmppt_max_v   → voltaje máximo MPPT [V]
        vdc_max_v     → voltaje DC máximo permitido [V]
        n_mppt        → número de MPPT

    Define:
        → límites de diseño de strings
        → validaciones eléctricas
        → distribución en MPPT
    """

    # =====================================================
    # CONFIGURACIÓN DEL SISTEMA
    # =====================================================

    n_paneles_total: Optional[int] = None
    """
    Número total de paneles del sistema.

    Reglas:
        - Si se define → modo manual
        - Si None → dimensionamiento automático

    Impacto:
        → potencia total del sistema
        → número de strings
    """

    n_inversores: Optional[int] = None
    """
    Número de inversores del sistema.

    Impacto:
        → distribución de strings
        → potencia por inversor
    """

    # =====================================================
    # CONDICIONES TÉRMICAS
    # =====================================================

    t_min_c: float = 25.0
    """
    Temperatura mínima ambiente [°C]

    Uso:
        → cálculo de Voc en frío

    Regla:
        ↓ temperatura → ↑ voltaje

    Impacto:
        → validación contra vdc_max del inversor
    """

    t_oper_c: float = 55.0
    """
    Temperatura de operación del módulo [°C]

    Uso:
        → condiciones reales de operación
        → ajuste térmico secundario
    """

    # =====================================================
    # CONFIGURACIÓN FÍSICA
    # =====================================================

    dos_aguas: bool = False
    """
    Configuración del arreglo FV.

    True:
        → dos orientaciones (posible división de strings)

    False:
        → sistema uniforme

    Nota:
        No afecta cálculos eléctricos directos,
        pero sí la distribución de strings.
    """

    # =====================================================
    # OBJETIVO DE DISEÑO
    # =====================================================

    objetivo_dc_ac: Optional[float] = None
    """
    Relación DC/AC objetivo.

    Ejemplo:
        1.2 → 20% sobre dimensionamiento DC

    Uso:
        → dimensionamiento automático
        → optimización producción vs clipping
    """

    pdc_kw_objetivo: Optional[float] = None
    """
    Potencia DC objetivo del sistema [kW]

    Reglas:
        - Si se define → prioridad directa
        - Si no → se calcula vía DC/AC

    Uso:
        → dimensionamiento directo del sistema
    """


# =========================================================
# SALIDAS DEL DOMINIO (DOCUMENTACIÓN)
# =========================================================
#
# EntradaPaneles NO genera salida directamente.
#
# Alimenta el flujo que produce:
#
#   ResultadoPaneles
#
# Ubicación:
#   electrical/paneles/resultado_paneles.py
#
# ---------------------------------------------------------
# RESULTADO ESPERADO
# ---------------------------------------------------------
#
# ResultadoPaneles contiene:
#
#   ARRAY (fuente principal del sistema)
#       potencia_dc_w
#       vdc_nom
#       idc_nom
#       isc_total
#       n_strings_total
#
#   STRINGS (detalle eléctrico)
#       vmp_string_v
#       isc_string_a
#       imp_string_a
#
#   RECOMENDACIÓN
#       configuración óptima del sistema
#
# ---------------------------------------------------------
# FLUJO COMPLETO
# ---------------------------------------------------------
#
# EntradaPaneles
#       ↓
# dimensionado_paneles
#       ↓
# calculo_de_strings
#       ↓
# distribución MPPT
#       ↓
# ResultadoPaneles
#
# ---------------------------------------------------------
# PRINCIPIO FINAL
# ---------------------------------------------------------
#
# EntradaPaneles  = problema
# ResultadoPaneles = solución
#
# No se mezclan.
# No se recalculan.
# No se transforman fuera del dominio.
#
# =========================================================

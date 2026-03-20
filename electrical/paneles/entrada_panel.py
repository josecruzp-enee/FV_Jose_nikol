from __future__ import annotations

"""
CONTRATO DE ENTRADA — DOMINIO PANELES (FV ENGINE)
================================================

🔷 QUÉ ES ESTE ARCHIVO
----------------------------------------------------------
Este archivo define el CONTRATO DE ENTRADA del dominio paneles.

Es decir:
    → aquí se define TODO lo que entra al dominio
    → NO se calcula nada aquí
    → NO se transforma nada aquí

Este objeto representa:
    "las condiciones iniciales del problema eléctrico FV"

----------------------------------------------------------
🔷 QUÉ ENTRA (SEMÁNTICA GENERAL)
----------------------------------------------------------

Este contrato recibe información de:

1. PANEL (comportamiento eléctrico base)
    - define voltajes y corrientes unitarias

2. INVERSOR (restricciones del sistema)
    - define límites de operación DC

3. CONFIGURACIÓN
    - tamaño del sistema (manual o automático)

4. CONDICIONES TÉRMICAS
    - afectan principalmente voltajes (Voc frío)

5. OBJETIVO DE DISEÑO
    - define cómo dimensionar (DC/AC o potencia objetivo)

----------------------------------------------------------
🔷 CÓMO SE USA
----------------------------------------------------------

Este objeto es consumido por:

    electrical.paneles.orquestador_paneles

Ese módulo:
    - dimensiona paneles
    - calcula strings
    - distribuye MPPT

----------------------------------------------------------
🔷 QUÉ NO HACE
----------------------------------------------------------

Este objeto NO:

    - calcula energía
    - calcula pérdidas
    - calcula NEC
    - calcula corrientes totales

Solo define el problema.

----------------------------------------------------------
🔷 PRINCIPIO CLAVE
----------------------------------------------------------

EntradaPaneles = definición del problema
ResultadoPaneles = solución eléctrica

Nunca se mezclan.
Nunca se mutan.
"""

from dataclasses import dataclass
from typing import Optional


# =========================================================
# ENTRADA DEL DOMINIO PANELES
# =========================================================

@dataclass(frozen=True)
class EntradaPaneles:

    # -----------------------------------------------------
    # ESPECIFICACIÓN DEL MÓDULO FV
    # -----------------------------------------------------

    panel: any
    """
    Datos eléctricos del panel fotovoltaico.

    Representa el comportamiento UNITARIO del sistema.

    Debe incluir:
        p_w     → potencia del panel [W]
        vmp_v   → voltaje en operación [V]
        voc_v   → voltaje en circuito abierto [V]
        imp_a   → corriente en MPPT [A]
        isc_a   → corriente de corto circuito [A]

    Este bloque define:
        → voltajes de string
        → corrientes DC
        → potencia total del sistema
    """


    # -----------------------------------------------------
    # ESPECIFICACIÓN DEL INVERSOR
    # -----------------------------------------------------

    inversor: any
    """
    Límites eléctricos del inversor (lado DC).

    Debe incluir:
        kw_ac         → potencia AC nominal [kW]
        vmppt_min_v   → voltaje mínimo MPPT [V]
        vmppt_max_v   → voltaje máximo MPPT [V]
        vdc_max_v     → voltaje DC máximo permitido [V]
        n_mppt        → número de MPPT

    Este bloque define:
        → límites de diseño de strings
        → validaciones eléctricas
        → distribución en MPPT
    """


    # -----------------------------------------------------
    # CONFIGURACIÓN DEL SISTEMA
    # -----------------------------------------------------

    n_paneles_total: Optional[int] = None
    """
    Número total de paneles del sistema.

    Reglas:
        - Si viene definido → se respeta (modo manual)
        - Si es None → se calcula automáticamente

    Impacto:
        → define número de strings
        → define potencia total del sistema
    """


    n_inversores: Optional[int] = None
    """
    Número de inversores en el sistema.

    Impacto:
        → divide la potencia total
        → afecta distribución de strings
    """


    # -----------------------------------------------------
    # CONDICIONES TÉRMICAS
    # -----------------------------------------------------

    t_min_c: float = 25.0
    """
    Temperatura mínima ambiente [°C].

    Uso:
        → cálculo de Voc en frío

    Regla física:
        ↓ temperatura → ↑ voltaje

    Impacto:
        → validación contra vdc_max del inversor
    """


    t_oper_c: float = 55.0
    """
    Temperatura de operación del módulo [°C].

    Uso:
        → estimación de condiciones reales
        → ajuste térmico (secundario en este dominio)
    """


    # -----------------------------------------------------
    # CONFIGURACIÓN FÍSICA
    # -----------------------------------------------------

    dos_aguas: bool = False
    """
    Configuración del techo.

    True:
        → dos orientaciones (posible división de strings)

    False:
        → sistema uniforme

    Nota:
        No afecta cálculos eléctricos directos,
        pero sí la distribución de strings.
    """


    # -----------------------------------------------------
    # OBJETIVO DE DISEÑO
    # -----------------------------------------------------

    objetivo_dc_ac: Optional[float] = None
    """
    Relación DC/AC deseada.

    Ejemplo:
        1.2 → 20% más potencia DC que AC

    Uso:
        → dimensionamiento automático del sistema
        → optimización de producción vs clipping
    """


    pdc_kw_objetivo: Optional[float] = None
    """
    Potencia DC objetivo del sistema [kW].

    Reglas:
        - Si viene → define directamente el tamaño
        - Si no → se calcula usando DC/AC

    Uso:
        → dimensionamiento directo del sistema
    """


# =========================================================
# SALIDA DEL DOMINIO (DOCUMENTACIÓN DE FRONTERA)
# =========================================================

"""
🔷 QUÉ SALE DE ESTE DOMINIO
----------------------------------------------------------

Este contrato NO genera salida directamente,
pero alimenta al flujo que produce:

    ResultadoPaneles

Ubicación:
    electrical.paneles.resultado_paneles

----------------------------------------------------------

🔷 RESULTADO ESPERADO (SEMÁNTICA)
----------------------------------------------------------

ResultadoPaneles contiene:

1. ARRAY (fuente principal del sistema)
    - potencia_dc_w   → potencia total DC
    - vdc_nom         → voltaje del sistema
    - idc_nom         → corriente total DC 🔥
    - n_strings_total → número de strings

2. STRINGS (detalle eléctrico)
    - vmp_string_v
    - isc_string_a
    - idesign_cont_a

3. RECOMENDACIÓN
    - configuración óptima del sistema

----------------------------------------------------------

🔷 REGLA CRÍTICA DEL SISTEMA
----------------------------------------------------------

ResultadoPaneles es:

    → la ÚNICA fuente de verdad para NEC
    → la base de todos los cálculos eléctricos posteriores

----------------------------------------------------------

🔷 FLUJO COMPLETO
----------------------------------------------------------

EntradaPaneles
    ↓
dimensionado_paneles
    ↓
calculo_de_strings
    ↓
configuración MPPT
    ↓
ResultadoPaneles

----------------------------------------------------------

🔷 PRINCIPIO FINAL
----------------------------------------------------------

EntradaPaneles  = define el problema
ResultadoPaneles = define la solución

No se mezclan.
No se recalculan.
No se transforman fuera del dominio.
"""

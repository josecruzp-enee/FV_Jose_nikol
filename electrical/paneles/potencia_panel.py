"""
MODELO DE POTENCIA DEL PANEL FV — FV Engine

Dominio: paneles / energía

Responsabilidad
---------------
Calcular el comportamiento eléctrico del módulo fotovoltaico
en condiciones reales de operación.

Este módulo ajusta:

• potencia máxima del módulo
• voltaje en punto de máxima potencia (Vmp)
• voltaje en circuito abierto (Voc)

en función de:

• irradiancia incidente (POA)
• temperatura de celda
• coeficientes térmicos del panel

Modelo utilizado
----------------
Modelo simplificado basado en coeficientes térmicos.
"""
"""
RELACIÓN DEL MÓDULO EN EL MOTOR FV — FV Engine

Este módulo calcula el comportamiento eléctrico de un módulo
fotovoltaico bajo condiciones reales de operación.

Recibe información de:

    modelo_termico.py
        → temperatura de celda del módulo

    modelo_clima / irradiancia_poa
        → irradiancia incidente en el plano del generador (POA)

    catálogo de paneles
        → parámetros eléctricos del módulo en STC
           (Pmax, Vmp, Voc y coeficientes térmicos)

Entrega resultados a:

    potencia_string.py
        → cálculo del comportamiento eléctrico del string FV
           (paneles conectados en serie)

Rol en el flujo energético del sistema:

    clima / irradiancia
            ↓
    modelo_termico
            ↓
    potencia_panel
            ↓
    potencia_string
            ↓
    potencia_arreglo
            ↓
    producción energética del sistema FV

Este módulo representa el nivel físico más bajo del modelo
energético del generador fotovoltaico.
"""


from dataclasses import dataclass


# ==========================================================
# MODELOS DE DATOS
# ==========================================================

@dataclass
class PotenciaPanelInput:
    """
    Parámetros de entrada del modelo del panel
    """

    irradiancia_poa_wm2: float
    temperatura_celda_c: float

    pmax_stc_w: float
    vmp_stc_v: float
    voc_stc_v: float

    coef_pmax_pct_per_c: float
    coef_voc_pct_per_c: float
    coef_vmp_pct_per_c: float


@dataclass
class PotenciaPanelResultado:
    """
    Resultado del comportamiento del panel
    """

    pmp_w: float
    vmp_v: float
    voc_v: float


# ==========================================================
# MOTOR DEL PANEL
# ==========================================================

def calcular_potencia_panel(inp: PotenciaPanelInput) -> PotenciaPanelResultado:
    """
    Calcula potencia y voltajes del panel bajo condiciones
    reales de irradiancia y temperatura.
    """

    poa = inp.irradiancia_poa_wm2
    t_cell = inp.temperatura_celda_c

    # ------------------------------------------------------
    # Sin irradiancia no hay generación
    # ------------------------------------------------------

    if poa <= 0:
        return PotenciaPanelResultado(
            pmp_w=0.0,
            vmp_v=0.0,
            voc_v=0.0
        )

    # ------------------------------------------------------
    # irradiancia relativa respecto a STC
    # ------------------------------------------------------

    g_rel = poa / 1000

    # diferencia de temperatura respecto a STC
    delta_t = t_cell - 25

    # ------------------------------------------------------
    # ajuste de potencia
    # ------------------------------------------------------

    pmp = (
        inp.pmax_stc_w
        * g_rel
        * (1 + inp.coef_pmax_pct_per_c * delta_t)
    )

    # ------------------------------------------------------
    # ajuste de voltaje MPP
    # ------------------------------------------------------

    vmp = (
        inp.vmp_stc_v
        * (1 + inp.coef_vmp_pct_per_c * delta_t)
    )

    # ------------------------------------------------------
    # ajuste de Voc
    # ------------------------------------------------------

    voc = (
        inp.voc_stc_v
        * (1 + inp.coef_voc_pct_per_c * delta_t)
    )

    return PotenciaPanelResultado(
        pmp_w=pmp,
        vmp_v=vmp,
        voc_v=voc
    )

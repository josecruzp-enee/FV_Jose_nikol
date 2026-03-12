from __future__ import annotations

"""
ADAPTADORES UI → CORE
FV Engine

Este módulo implementa los adaptadores que traducen los datos
capturados por la interfaz de usuario (WizardCtx / SessionState)
hacia los modelos de dominio utilizados por el motor FV.

FRONTERA DEL MÓDULO
-------------------

Entrada:
    WizardCtx (estado de la UI)

Salida:
    Datosproyecto (modelo del core)

RESPONSABILIDAD
---------------

Este módulo NO realiza cálculos.

Solo transforma estructuras de datos:

    UI  →  Core

La UI nunca debe construir directamente los modelos del core.
Siempre debe pasar por este adaptador.

Esto mantiene:

    separación de capas
    estabilidad de contratos
    arquitectura limpia
"""

from typing import List

from core.dominio.modelo import Datosproyecto


# ==========================================================
# Adaptador principal
# ==========================================================

def datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    """
    Traduce WizardCtx → Datosproyecto.

    La UI captura datos en diferentes secciones del wizard:

        datos_cliente
        consumo
        sistema_fv

    Este adaptador los convierte en el modelo de entrada
    que espera el motor del sistema FV.

    Parámetros
    ----------
    ctx :
        Objeto de estado del wizard (UI)

    Retorna
    -------
    Datosproyecto
        Modelo de entrada del motor FV
    """

    # ------------------------------------------------------
    # Secciones del wizard
    # ------------------------------------------------------

    dc = ctx.datos_cliente
    c = ctx.consumo
    s = ctx.sistema_fv

    # ------------------------------------------------------
    # Consumo mensual
    # ------------------------------------------------------

    consumo_12m: List[float] = [float(x) for x in c.get("kwh_12m", [0] * 12)]

    # ------------------------------------------------------
    # Producción base FV
    # ------------------------------------------------------

    prod_base = float(s.get("produccion_base", 145.0))

    # factores de ajuste mensual FV
    factores = [float(x) for x in s.get("factores_fv_12m", [1.0] * 12)]

    # ------------------------------------------------------
    # Cobertura objetivo
    # ------------------------------------------------------

    cobertura = float(s.get("offset_pct", 80.0)) / 100.0

    # ------------------------------------------------------
    # Construcción del modelo de dominio
    # ------------------------------------------------------

    datos = Datosproyecto(

        # ===============================
        # Información cliente
        # ===============================

        cliente=str(dc.get("cliente", "")).strip(),
        ubicacion=str(dc.get("ubicacion", "")).strip(),

        # ===============================
        # Consumo energético
        # ===============================

        consumo_12m=consumo_12m,
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0.0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0.0)),

        # ===============================
        # Producción solar
        # ===============================

        prod_base_kwh_kwp_mes=prod_base,
        factores_fv_12m=factores,
        cobertura_objetivo=cobertura,

        # ===============================
        # Parámetros financieros
        # ===============================

        costo_usd_kwp=float(s.get("costo_usd_kwp", 1200.0)),
        tcambio=float(s.get("tcambio", 27.0)),

        tasa_anual=float(s.get("tasa_anual", 0.08)),
        plazo_anios=int(s.get("plazo_anios", 10)),
        porcentaje_financiado=float(s.get("porcentaje_financiado", 1.0)),

        om_anual_pct=float(s.get("om_anual_pct", 0.01)),
    )

    return datos

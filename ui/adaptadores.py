from __future__ import annotations

"""
ADAPTADORES UI → CORE
FV Engine

Este módulo implementa los adaptadores que traducen los datos
capturados por la interfaz de usuario (WizardCtx / SessionState)
hacia los modelos de dominio utilizados por el motor FV.
"""

from typing import Dict, List

from core.dominio.modelo import Datosproyecto


# ==========================================================
# Adaptador principal
# ==========================================================

def datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    """
    Traduce WizardCtx → Datosproyecto.

    Este módulo NO calcula.
    Solo transforma datos UI → Core.
    """

    # ------------------------------------------------------
    # Secciones del wizard
    # ------------------------------------------------------

    dc = getattr(ctx, "datos_cliente", {}) or {}
    c = getattr(ctx, "consumo", {}) or {}
    s = getattr(ctx, "sistema_fv", {}) or {}

    equipos = getattr(ctx, "equipos", {}) or {}
    electrico = getattr(ctx, "electrico", {}) or {}

    # ------------------------------------------------------
    # Consumo mensual
    # ------------------------------------------------------

    consumo_12m: List[float] = [
        float(x)
        for x in c.get("kwh_12m", [0.0] * 12)
    ]

    # ------------------------------------------------------
    # Producción base FV
    # ------------------------------------------------------

    prod_base = float(s.get("produccion_base", 145.0))

    factores = [
        float(x)
        for x in s.get("factores_fv_12m", [1.0] * 12)
    ]

    # ------------------------------------------------------
    # Cobertura objetivo
    # ------------------------------------------------------

    cobertura = float(s.get("offset_pct", 80.0)) / 100.0

    # ------------------------------------------------------
    # Ubicación
    # ------------------------------------------------------

    lat = float(
        dc.get(
            "lat",
            dc.get("latitud", 0.0),
        )
    )

    lon = float(
        dc.get(
            "lon",
            dc.get("longitud", 0.0),
        )
    )

    # ------------------------------------------------------
    # Perfil horario técnico de consumo
    # ------------------------------------------------------

    perfil_kw_24h: Dict[int, float] = {
        int(hora): float(kw)
        for hora, kw in getattr(ctx, "perfil_kw_24h", {}).items()
    }

    consumo_horario_24h_kwh: Dict[int, float] = {
        int(hora): float(kwh)
        for hora, kwh in getattr(ctx, "consumo_horario_24h_kwh", {}).items()
    }

    resumen_perfil_consumo: Dict[str, float] = {
        str(k): float(v)
        for k, v in getattr(ctx, "resumen_perfil_consumo", {}).items()
    }

    # ------------------------------------------------------
    # Construcción del modelo de dominio
    # ------------------------------------------------------

    datos = Datosproyecto(

        # ===============================
        # Información cliente
        # ===============================

        cliente=str(dc.get("cliente", "")).strip(),
        ubicacion=str(dc.get("ubicacion", "")).strip(),

        lat=lat,
        lon=lon,

        # ===============================
        # Consumo energético
        # ===============================

        consumo_12m=consumo_12m,
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0.0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0.0)),

        perfil_kw_24h=perfil_kw_24h,
        consumo_horario_24h_kwh=consumo_horario_24h_kwh,
        resumen_perfil_consumo=resumen_perfil_consumo,

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

        # ===============================
        # Diccionarios controlados pipeline
        # ===============================

        sistema_fv=dict(s),
        equipos=dict(equipos),
        electrico=dict(electrico),
    )

    return datos

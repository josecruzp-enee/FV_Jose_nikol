# ui/adaptadores.py
from __future__ import annotations
from typing import List

from core.modelo import Datosproyecto


def datosproyecto_desde_ctx(ctx) -> Datosproyecto:
    """
    Traduce WizardCtx -> Datosproyecto (core).
    app.py no debe mapear campos uno por uno.
    """
    dc = ctx.datos_cliente
    c = ctx.consumo
    s = ctx.sistema_fv

    consumo_12m: List[float] = [float(x) for x in c["kwh_12m"]]

    # Producción mensual por kWp: base * factor_mes
    prod_base = float(s.get("produccion_base", 145.0))
    factores = [float(x) for x in s.get("factores_fv_12m", [1.0] * 12)]

    # Si tu core espera "factores_fv_12m" como factores (no kWh/kWp), se queda así.
    # Si tu core espera factores, perfecto.
    # Si tu core espera ya ajustado, te lo ajusto en el siguiente paso (no adivino hoy).
    cobertura = float(s.get("offset_pct", 80.0)) / 100.0

    # OJO: aquí solo pasamos lo que tu Datosproyecto exige hoy
    return Datosproyecto(
        cliente=str(dc.get("cliente", "")).strip(),
        ubicacion=str(dc.get("ubicacion", "")).strip(),
        consumo_12m=consumo_12m,
        tarifa_energia=float(c.get("tarifa_energia_L_kwh", 0.0)),
        cargos_fijos=float(c.get("cargos_fijos_L_mes", 0.0)),
        prod_base_kwh_kwp_mes=prod_base,
        factores_fv_12m=factores,
        cobertura_objetivo=cobertura,

        # Finanza: si aún no está en wizard, pon defaults temporales (los subimos al paso finanzas luego)
        costo_usd_kwp=1200.0,
        tcambio=27.0,
        tasa_anual=0.08,
        plazo_anios=10,
        porcentaje_financiado=1.0,
        om_anual_pct=0.01,
    )

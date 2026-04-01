from core.dominio.modelo import Datosproyecto


def construir_datos_proyecto(ctx):

    # ======================================================
    # BASE
    # ======================================================
    p = Datosproyecto(
        cliente=getattr(ctx, "cliente", ""),
        ubicacion=getattr(ctx, "ubicacion", ""),
        lat=float(getattr(ctx, "lat", 0)),
        lon=float(getattr(ctx, "lon", 0)),

        consumo_12m=getattr(ctx, "consumo_12m", [0]*12),

        tarifa_energia=float(getattr(ctx, "tarifa_energia", 0)),
        cargos_fijos=float(getattr(ctx, "cargos_fijos", 0)),

        prod_base_kwh_kwp_mes=getattr(ctx, "prod_base_kwh_kwp_mes", [0]*12),
        factores_fv_12m=getattr(ctx, "factores_fv_12m", [1]*12),

        cobertura_objetivo=float(getattr(ctx, "cobertura_objetivo", 1.0)),

        costo_usd_kwp=float(getattr(ctx, "costo_usd_kwp", 1000)),
        tcambio=float(getattr(ctx, "tcambio", 24.5)),
        tasa_anual=float(getattr(ctx, "tasa_anual", 0.1)),
        plazo_anios=int(getattr(ctx, "plazo_anios", 10)),
        porcentaje_financiado=float(getattr(ctx, "porcentaje_financiado", 0)),
    )

    # ======================================================
    # ELÉCTRICO
    # ======================================================
    e = getattr(ctx, "electrico", {}) or {}

    p.electrico = {
        "vac": float(e.get("vac", 240)),
        "fases": int(e.get("fases", 1)),
        "fp": float(e.get("fp", 1.0)),
        "dist_dc_m": float(e.get("dist_dc_m", 0)),
        "dist_ac_m": float(e.get("dist_ac_m", 0)),
    }

    # ======================================================
    # EQUIPOS
    # ======================================================
    eq = getattr(ctx, "equipos", None)

    if not eq:
        raise ValueError("ctx.equipos no definido")

    p.equipos = eq

    # ======================================================
    # SISTEMA FV (🔥 NORMALIZACIÓN CRÍTICA)
    # ======================================================
    sf = getattr(ctx, "sistema_fv", {}) or {}
    sizing_input = sf.get("sizing_input", {}) or {}

    modo = sizing_input.get("modo") or sf.get("modo")
    valor = sizing_input.get("valor") or sf.get("valor")

    p.sistema_fv = {
        "modo": modo,
        "valor": valor,
        "zonas": sf.get("zonas", []),
    }

    return p

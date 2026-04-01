from core.dominio.modelo import Datosproyecto


def construir_datos_proyecto(ctx):

    # ======================================================
    # BASE
    # ======================================================
    p = Datosproyecto(
        cliente=str(getattr(ctx, "cliente", "") or ""),
        ubicacion=str(getattr(ctx, "ubicacion", "") or ""),

        lat=float(getattr(ctx, "lat", 0) or 0),
        lon=float(getattr(ctx, "lon", 0) or 0),

        # 🔥 mantener None si no viene
        consumo_12m=getattr(ctx, "consumo_12m", None),

        tarifa_energia=float(getattr(ctx, "tarifa_energia", 0) or 0),
        cargos_fijos=float(getattr(ctx, "cargos_fijos", 0) or 0),

        # 🔥 mantener None si no viene
        prod_base_kwh_kwp_mes=getattr(ctx, "prod_base_kwh_kwp_mes", None),

        factores_fv_12m=getattr(ctx, "factores_fv_12m", [1] * 12),

        cobertura_objetivo=float(getattr(ctx, "cobertura_objetivo", 1.0) or 1.0),

        costo_usd_kwp=float(getattr(ctx, "costo_usd_kwp", 1000) or 1000),
        tcambio=float(getattr(ctx, "tcambio", 24.5) or 24.5),

        tasa_anual=float(getattr(ctx, "tasa_anual", 0.1) or 0.1),
        plazo_anios=int(getattr(ctx, "plazo_anios", 10) or 10),
        porcentaje_financiado=float(getattr(ctx, "porcentaje_financiado", 0) or 0),
    )

    # ======================================================
    # ELÉCTRICO
    # ======================================================
    e = getattr(ctx, "electrico", {}) or {}

    if not isinstance(e, dict):
        e = {}

    p.electrico = {
        "vac": float(e.get("vac", 240) or 240),
        "fases": int(e.get("fases", 1) or 1),
        "fp": float(e.get("fp", 1.0) or 1.0),
        "dist_dc_m": float(e.get("dist_dc_m", 0) or 0),
        "dist_ac_m": float(e.get("dist_ac_m", 0) or 0),
    }

    # ======================================================
    # EQUIPOS
    # ======================================================
    eq = getattr(ctx, "equipos", None)

    if not isinstance(eq, dict) or not eq:
        raise ValueError("ctx.equipos inválido o no definido")

    panel_id = eq.get("panel_id")
    inversor_id = eq.get("inversor_id")

    if not panel_id:
        raise ValueError("panel_id no definido en equipos")

    if not inversor_id:
        raise ValueError("inversor_id no definido en equipos")

    p.equipos = {
        "panel_id": panel_id,
        "inversor_id": inversor_id,
        "sobredimension_dc_ac": eq.get("sobredimension_dc_ac"),
        "tension_sistema": eq.get("tension_sistema"),
    }

    # ======================================================
    # SISTEMA FV
    # ======================================================
    sf = getattr(ctx, "sistema_fv", {}) or {}

    if not isinstance(sf, dict):
        sf = {}

    sizing_input = sf.get("sizing_input", {}) or {}

    # ----------------------
    # modo
    # ----------------------
    modo = sizing_input.get("modo") or sf.get("modo")

    if not modo:
        raise ValueError("sistema_fv.modo no definido")

    # ----------------------
    # valor
    # ----------------------
    valor = sizing_input.get("valor")
    if valor is None:
        valor = sf.get("valor")

    # ----------------------
    # zonas
    # ----------------------
    zonas = sf.get("zonas") or []

    if not isinstance(zonas, list):
        zonas = []

    zonas_limpias = []

    for z in zonas:
        if not isinstance(z, dict):
            continue

        zonas_limpias.append({
            "nombre": z.get("nombre", ""),
            "modo": z.get("modo", "paneles"),
            "n_paneles": z.get("n_paneles"),
            "area": z.get("area"),
            "azimut": z.get("azimut"),
            "inclinacion": z.get("inclinacion"),
        })

    p.sistema_fv = {
        "modo": modo,
        "valor": valor,
        "zonas": zonas_limpias,
    }

    # ======================================================
    # VALIDACIÓN FINAL
    # ======================================================
    p.validar_minimo()

    return p

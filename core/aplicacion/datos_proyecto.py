from core.dominio.modelo import Datosproyecto


def construir_datos_proyecto(ctx):

    # ======================================================
    # BASE
    # ======================================================
    p = Datosproyecto(
        dc = getattr(ctx, "datos_cliente", {}) or {}
        cliente = str(dc.get("cliente", "") or "")
        ubicacion = str(dc.get("ubicacion", "") or "")

        lat=float(getattr(ctx, "lat", 0) or 0),
        lon=float(getattr(ctx, "lon", 0) or 0),

        consumo_12m=getattr(ctx, "consumo_12m", None),

        tarifa_energia=float(getattr(ctx, "tarifa_energia", 0) or 0),
        cargos_fijos=float(getattr(ctx, "cargos_fijos", 0) or 0),

        prod_base_kwh_kwp_mes=getattr(ctx, "prod_base_kwh_kwp_mes", None),
        factores_fv_12m=getattr(ctx, "factores_fv_12m", None),

        cobertura_objetivo=float(getattr(ctx, "cobertura_objetivo", 1.0) or 1.0),

        costo_usd_kwp=float(getattr(ctx, "costo_usd_kwp", 1000) or 1000),
        tcambio=float(getattr(ctx, "tcambio", 24.5) or 24.5),

        tasa_anual=float(getattr(ctx, "tasa_anual", 0.1) or 0.1),
        plazo_anios=int(getattr(ctx, "plazo_anios", 10) or 10),
        porcentaje_financiado=float(getattr(ctx, "porcentaje_financiado", 0) or 0),
    )

    # ======================================================
    # DEBUG (solo temporal)
    # ======================================================
    MODO_DEBUG = True

    if MODO_DEBUG:
        if not p.consumo_12m or not isinstance(p.consumo_12m, list):
            p.consumo_12m = [10000.0] * 12

        if not p.prod_base_kwh_kwp_mes:
            p.prod_base_kwh_kwp_mes = [120.0] * 12

        if not p.factores_fv_12m:
            p.factores_fv_12m = [1.0] * 12

    # ======================================================
    # NORMALIZACIÓN
    # ======================================================
    p.consumo_12m = [float(x or 0) for x in p.consumo_12m]
    p.prod_base_kwh_kwp_mes = [float(x or 0) for x in p.prod_base_kwh_kwp_mes]
    p.factores_fv_12m = [float(x or 1) for x in p.factores_fv_12m]

    # ======================================================
    # 🔴 ELÉCTRICO (RÍGIDO)
    # ======================================================
    e = getattr(ctx, "electrico", None)

    if not isinstance(e, dict):
        raise ValueError("electrico inválido o no definido")

    required = ["vac", "fases", "fp", "dist_dc_m", "dist_ac_m"]

    for k in required:
        if e.get(k) is None:
            raise ValueError(f"electrico.{k} es obligatorio")

    p.electrico = {
        "vac": float(e["vac"]),
        "fases": int(e["fases"]),
        "fp": float(e["fp"]),
        "dist_dc_m": float(e["dist_dc_m"]),
        "dist_ac_m": float(e["dist_ac_m"]),
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
        "panel_id": str(panel_id),
        "inversor_id": str(inversor_id),
        "sobredimension_dc_ac": float(eq.get("sobredimension_dc_ac") or 1.2),
        "tension_sistema": eq.get("tension_sistema"),
    }

    # ======================================================
    # SISTEMA FV
    # ======================================================
    sf = getattr(ctx, "sistema_fv", {}) or {}

    if not isinstance(sf, dict):
        raise ValueError("sistema_fv inválido")

    sizing_input = sf.get("sizing_input", {}) or {}

    modo = sizing_input.get("modo") or sf.get("modo")

    if not modo:
        raise ValueError("sistema_fv.modo no definido")

    valor = sizing_input.get("valor")
    if valor is None:
        valor = sf.get("valor")

    zonas = sf.get("zonas") or []

    if not isinstance(zonas, list):
        raise ValueError("zonas inválidas")

    zonas_limpias = []

    for i, z in enumerate(zonas):

        if not isinstance(z, dict):
            continue

        n_paneles = z.get("n_paneles")
        area = z.get("area")

        if (n_paneles is None or n_paneles <= 0) and (area is None or area <= 0):
            raise ValueError(f"Zona {i+1}: sin paneles ni área válida")

        zonas_limpias.append({
            "nombre": str(z.get("nombre", f"Zona {i+1}")),
            "modo": str(z.get("modo", "paneles")),
            "n_paneles": int(n_paneles) if n_paneles else None,
            "area": area,
            "azimut": float(z.get("azimut", 180)),
            "inclinacion": float(z.get("inclinacion", 15)),
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

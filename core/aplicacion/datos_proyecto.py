from core.dominio.modelo import Datosproyecto


# ======================================================
# HELPERS GENERALES
# ======================================================

def _get(obj, campo, default=None):
    return getattr(obj, campo, default)


def _as_float(valor, default=0.0) -> float:
    try:
        return float(valor if valor is not None else default)
    except Exception:
        return float(default)


def _as_int(valor, default=0) -> int:
    try:
        return int(valor if valor is not None else default)
    except Exception:
        return int(default)


def _as_dict(valor, default=None) -> dict:
    if isinstance(valor, dict):
        return valor
    return default or {}


def _as_list(valor, default=None) -> list:
    if isinstance(valor, list):
        return valor
    return default or []


# ======================================================
# DATOS CLIENTE
# ======================================================

def _leer_datos_cliente(ctx) -> dict:
    dc = _as_dict(_get(ctx, "datos_cliente", {}))

    return {
        "cliente": str(dc.get("cliente", "") or ""),
        "ubicacion": str(dc.get("ubicacion", "") or ""),
    }


# ======================================================
# CONSUMO
# ======================================================

def _leer_consumo(ctx) -> dict:
    return {
        "consumo_12m": _as_list(_get(ctx, "consumo_12m", [0] * 12), [0] * 12),
        "tarifa_energia": _as_float(_get(ctx, "tarifa_energia", 0), 0),
        "cargos_fijos": _as_float(_get(ctx, "cargos_fijos", 0), 0),
        "perfil_kw_24h": _as_dict(_get(ctx, "perfil_kw_24h", {})),
        "consumo_horario_24h_kwh": _as_dict(
            _get(ctx, "consumo_horario_24h_kwh", {})
        ),
        "resumen_perfil_consumo": _as_dict(
            _get(ctx, "resumen_perfil_consumo", {})
        ),
    }


# ======================================================
# FINANCIAMIENTO
# ======================================================

def _leer_financiamiento(ctx) -> dict:
    """
    Perfil financiero por defecto:
    Crédito PyME Invierta Prendario.

    Mantiene compatibilidad:
    si ctx trae valores, se respetan.
    si no trae valores, usa el banco por defecto.
    """

    tasa_anual = _as_float(_get(ctx, "tasa_anual", 0.195), 0.195)
    plazo_anios = _as_int(_get(ctx, "plazo_anios", 7), 7)
    porcentaje_financiado = _as_float(
        _get(ctx, "porcentaje_financiado", 0.90),
        0.90,
    )

    prima_pct = _as_float(
        _get(ctx, "prima_pct", max(0.0, 1.0 - porcentaje_financiado)),
        max(0.0, 1.0 - porcentaje_financiado),
    )

    cat = _as_float(_get(ctx, "cat", 0.2196), 0.2196)

    return {
        "nombre_financiamiento": str(
            _get(ctx, "nombre_financiamiento", "Crédito PyME Invierta Prendario")
            or "Crédito PyME Invierta Prendario"
        ),
        "entidad_financiera": str(
            _get(ctx, "entidad_financiera", "Banco") or "Banco"
        ),
        "tasa_anual": tasa_anual,
        "plazo_anios": plazo_anios,
        "plazo_meses": plazo_anios * 12,
        "porcentaje_financiado": porcentaje_financiado,
        "prima_pct": prima_pct,
        "cat": cat,
    }


# ======================================================
# BASE DEL PROYECTO
# ======================================================

def _crear_datos_base(ctx, cliente_data: dict, consumo_data: dict, fin_data: dict):
    return Datosproyecto(
        cliente=cliente_data["cliente"],
        ubicacion=cliente_data["ubicacion"],

        lat=_as_float(_get(ctx, "lat", 0), 0),
        lon=_as_float(_get(ctx, "lon", 0), 0),

        consumo_12m=consumo_data["consumo_12m"],

        tarifa_energia=consumo_data["tarifa_energia"],
        cargos_fijos=consumo_data["cargos_fijos"],
        perfil_kw_24h=consumo_data["perfil_kw_24h"],
        consumo_horario_24h_kwh=consumo_data["consumo_horario_24h_kwh"],
        resumen_perfil_consumo=consumo_data["resumen_perfil_consumo"],

        prod_base_kwh_kwp_mes=_get(ctx, "prod_base_kwh_kwp_mes", None),
        factores_fv_12m=_get(ctx, "factores_fv_12m", None),

        cobertura_objetivo=_as_float(_get(ctx, "cobertura_objetivo", 1.0), 1.0),

        costo_usd_kwp=_as_float(_get(ctx, "costo_usd_kwp", 1200), 1200),
        tcambio=_as_float(_get(ctx, "tcambio", 26.75), 26.75),

        tasa_anual=fin_data["tasa_anual"],
        plazo_anios=fin_data["plazo_anios"],
        porcentaje_financiado=fin_data["porcentaje_financiado"],
    )


# ======================================================
# APLICAR FINANCIAMIENTO EXTRA
# ======================================================

def _aplicar_financiamiento_extra(p, fin_data: dict):
    """
    Agrega campos nuevos sin romper Datosproyecto.
    Si el dataclass no los declara, Python normalmente permite atributos dinámicos
    salvo que use slots.
    """

    try:
        p.nombre_financiamiento = fin_data["nombre_financiamiento"]
    except Exception:
        pass

    try:
        p.entidad_financiera = fin_data["entidad_financiera"]
    except Exception:
        pass

    try:
        p.prima_pct = fin_data["prima_pct"]
    except Exception:
        pass

    try:
        p.cat = fin_data["cat"]
    except Exception:
        pass

    try:
        p.plazo_meses = fin_data["plazo_meses"]
    except Exception:
        pass

    return p


# ======================================================
# DEBUG TEMPORAL
# ======================================================

def _aplicar_debug_temporal(p):
    MODO_DEBUG = True

    if not MODO_DEBUG:
        return p

    if not p.consumo_12m or not isinstance(p.consumo_12m, list):
        p.consumo_12m = [10000.0] * 12

    if not p.prod_base_kwh_kwp_mes:
        p.prod_base_kwh_kwp_mes = 120.0

    if not p.factores_fv_12m:
        p.factores_fv_12m = [1.0] * 12

    return p


# ======================================================
# NORMALIZACIÓN
# ======================================================

def _normalizar_datos_base(p):
    p.consumo_12m = [float(x or 0) for x in p.consumo_12m]

    if isinstance(p.prod_base_kwh_kwp_mes, list):
        p.prod_base_kwh_kwp_mes = float(
            sum(p.prod_base_kwh_kwp_mes) / len(p.prod_base_kwh_kwp_mes)
        )
    else:
        p.prod_base_kwh_kwp_mes = float(p.prod_base_kwh_kwp_mes or 0)

    p.factores_fv_12m = [float(x or 1) for x in p.factores_fv_12m]

    return p


# ======================================================
# ELÉCTRICO
# ======================================================

def _aplicar_electrico(ctx, p):
    e = _get(ctx, "electrico", None)

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

    return p


# ======================================================
# EQUIPOS
# ======================================================

def _aplicar_equipos(ctx, p):
    eq = _get(ctx, "equipos", None)

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

    return p


# ======================================================
# ZONAS FV
# ======================================================

def _limpiar_zonas(zonas: list) -> list:
    if not isinstance(zonas, list):
        raise ValueError("zonas inválidas")

    zonas_limpias = []

    for i, z in enumerate(zonas):
        if not isinstance(z, dict):
            continue

        n_paneles = z.get("n_paneles")
        area = z.get("area")

        if (n_paneles is None or n_paneles <= 0) and (area is None or area <= 0):
            raise ValueError(f"Zona {i + 1}: sin paneles ni área válida")

        zonas_limpias.append({
            "nombre": str(z.get("nombre", f"Zona {i + 1}")),
            "modo": str(z.get("modo", "paneles")),
            "n_paneles": int(n_paneles) if n_paneles else None,
            "area": area,
            "azimut": float(z.get("azimut", 180)),
            "inclinacion": float(z.get("inclinacion", 15)),
        })

    return zonas_limpias


# ======================================================
# SISTEMA FV
# ======================================================

def _aplicar_sistema_fv(ctx, p):
    sf = _as_dict(_get(ctx, "sistema_fv", {}))

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
    zonas_limpias = _limpiar_zonas(zonas)

    p.sistema_fv = {
        "modo": modo,
        "valor": valor,
        "zonas": zonas_limpias,
        "bateria": sf.get("bateria", {}),
    }

    return p


# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================

def construir_datos_proyecto(ctx):

    cliente_data = _leer_datos_cliente(ctx)
    consumo_data = _leer_consumo(ctx)
    fin_data = _leer_financiamiento(ctx)

    p = _crear_datos_base(
        ctx=ctx,
        cliente_data=cliente_data,
        consumo_data=consumo_data,
        fin_data=fin_data,
    )

    p = _aplicar_financiamiento_extra(p, fin_data)
    p = _aplicar_debug_temporal(p)
    p = _normalizar_datos_base(p)

    p = _aplicar_electrico(ctx, p)
    p = _aplicar_equipos(ctx, p)
    p = _aplicar_sistema_fv(ctx, p)

    p.validar_minimo()

    return p

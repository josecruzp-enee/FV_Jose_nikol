from typing import Dict, Any, Optional
from itertools import product
from electrical.catalogos.catalogos_yaml import (
    get_inversor,
    ids_inversores,
)


# ======================================================
# 🔥 NUEVO: SUGERENCIAS DE CONFIGURACIÓN
# ======================================================
def sugerir_configuraciones_inversor(pdc_kw, dc_ac_obj, max_inv=4):

    catalogo = []

    for iid in ids_inversores():
        inv = get_inversor(iid)
        if inv and inv.kw_ac > 0:
            catalogo.append({
                "id": iid,
                "kw": float(inv.kw_ac)
            })

    soluciones = []

    pac_obj = pdc_kw / dc_ac_obj

    for n in range(1, max_inv + 1):

        for combo in product(catalogo, repeat=n):

            pac_total = sum(inv["kw"] for inv in combo)

            if pac_total <= 0:
                continue

            dc_ac = pdc_kw / pac_total

            if 1.1 <= dc_ac <= 1.3:

                soluciones.append({
                    "config": combo,
                    "pac_total": pac_total,
                    "dc_ac": round(dc_ac, 2),
                    "error": abs(pac_total - pac_obj)
                })

    soluciones.sort(key=lambda x: x["error"])

    return soluciones[:5]


def formatear_configuracion(config):

    conteo = {}

    for inv in config:
        key = (inv["id"], inv["kw"])
        conteo[key] = conteo.get(key, 0) + 1

    partes = []

    for (iid, kw), cantidad in conteo.items():
        partes.append(f"{cantidad}×{kw} kW")

    return " + ".join(partes)

from math import ceil

# ======================================================
# CÁLCULO DE CANTIDAD DE INVERSORES
# ======================================================
def calcular_cantidad_inversores(
    pdc_kw: float,
    pac_inversor_kw: float,
    dc_ac_obj: float,
) -> Dict[str, float]:
    """
    Calcula número de inversores necesarios.

    Retorna:
        n_inversores
        kw_ac
        kw_ac_total
        ratio_real
        kw_ac_obj
    """

    if pac_inversor_kw <= 0:
        raise ValueError("pac_inversor_kw inválido")

    # Potencia AC objetivo
    kw_ac_obj = pdc_kw / dc_ac_obj

    # Número de inversores (siempre entero hacia arriba)
    n_inversores = ceil(kw_ac_obj / pac_inversor_kw)

    # Potencia total instalada
    kw_ac_total = n_inversores * pac_inversor_kw

    # Ratio real DC/AC
    ratio_real = pdc_kw / kw_ac_total if kw_ac_total > 0 else 0

    return {
        "n_inversores": n_inversores,
        "kw_ac": pac_inversor_kw,
        "kw_ac_total": kw_ac_total,
        "ratio_real": ratio_real,
        "kw_ac_obj": kw_ac_obj,
    }

# ======================================================
# API PRINCIPAL
# ======================================================

# ======================================================
# VALIDACIONES
# ======================================================

def validar_entradas_inversor(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
) -> None:
    """
    Valida entradas principales del prediseño de inversores.
    """

    if pdc_kw <= 0:
        raise ValueError("pdc_kw inválido")

    if dc_ac_obj <= 0:
        raise ValueError("dc_ac_obj inválido")


# ======================================================
# INVERSOR FORZADO
# ======================================================

def resolver_inversor_forzado(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id_forzado: str,
) -> Optional[Dict[str, Any]]:
    """
    Resuelve el caso en que el usuario o el flujo envía un inversor específico.

    Mantiene la lógica actual:
    - Si el inversor existe, calcula cantidad por DC/AC objetivo.
    - Si no existe, devuelve None para permitir fallback automático.
    """

    inv = get_inversor(inversor_id_forzado)

    if inv is None:
        print(
            f"[WARN] Inversor '{inversor_id_forzado}' no encontrado. "
            "Usando selección automática."
        )
        return None

    pac = float(inv.kw_ac)

    calc = calcular_cantidad_inversores(
        pdc_kw=pdc_kw,
        pac_inversor_kw=pac,
        dc_ac_obj=dc_ac_obj,
    )

    return {
        "inversor_id": inversor_id_forzado,
        **calc,
        "sugerencias": [],
    }


# ======================================================
# SELECCIÓN AUTOMÁTICA ACTUAL
# ======================================================

def resolver_inversor_automatico_actual(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
) -> Optional[Dict[str, Any]]:
    """
    Ejecuta la selección automática actual.

    Mantiene la lógica existente:
    - Recorre el catálogo.
    - Calcula cantidad por DC/AC objetivo.
    - Selecciona la alternativa con menor potencia AC total.
    """

    mejor_total = None
    mejor_resultado = None
    mejor_id = None

    for iid in ids_inversores():

        inv = get_inversor(iid)

        if inv is None:
            continue

        pac = float(inv.kw_ac)

        if pac <= 0:
            continue

        calc = calcular_cantidad_inversores(
            pdc_kw=pdc_kw,
            pac_inversor_kw=pac,
            dc_ac_obj=dc_ac_obj,
        )

        pac_total = calc["kw_ac_total"]

        if mejor_total is None or pac_total < mejor_total:
            mejor_total = pac_total
            mejor_resultado = calc
            mejor_id = iid

    if mejor_resultado is None:
        return None

    return {
        "inversor_id": mejor_id,
        **mejor_resultado,
    }


# ======================================================
# SUGERENCIAS FORMATEADAS
# ======================================================

def construir_sugerencias_inversor(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
) -> list[Dict[str, Any]]:
    """
    Genera sugerencias de configuración para UI.
    """

    sugerencias = sugerir_configuraciones_inversor(
        pdc_kw,
        dc_ac_obj,
    )

    return [
        {
            "descripcion": formatear_configuracion(s["config"]),
            "pac_total": s["pac_total"],
            "dc_ac": s["dc_ac"],
        }
        for s in sugerencias
    ]


# ======================================================
# API PRINCIPAL
# ======================================================

def ejecutar_inversor_desde_sizing(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id_forzado: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Orquesta el prediseño de inversores desde sizing.

    Mantiene el comportamiento actual.
    No optimiza todavía por ventana DC/AC.
    """

    validar_entradas_inversor(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    if inversor_id_forzado:

        resultado_forzado = resolver_inversor_forzado(
            pdc_kw=pdc_kw,
            dc_ac_obj=dc_ac_obj,
            inversor_id_forzado=inversor_id_forzado,
        )

        if resultado_forzado is not None:
            return resultado_forzado

    resultado_automatico = resolver_inversor_automatico_actual(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    if resultado_automatico is None:
        print("[WARN] No se encontró ningún inversor válido")

        return {
            "inversor_id": None,
            "kw_ac_total": 0,
            "n_inversores": 0,
            "dc_ac": 0,
            "sugerencias": [],
        }

    sugerencias_fmt = construir_sugerencias_inversor(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    return {
        **resultado_automatico,
        "sugerencias": sugerencias_fmt,
    }

from typing import Dict, Any, Optional
from itertools import product
from math import ceil

from electrical.catalogos.catalogos_yaml import (
    get_inversor,
    ids_inversores,
)


# ======================================================
# CATÁLOGO AUXILIAR
# ======================================================

def obtener_catalogo_inversores() -> list[Dict[str, Any]]:
    catalogo = []

    for iid in ids_inversores():
        inv = get_inversor(iid)

        if inv is None:
            continue

        pac = float(inv.kw_ac)

        if pac <= 0:
            continue

        catalogo.append({
            "id": iid,
            "kw": pac,
        })

    return catalogo


# ======================================================
# FORMATO
# ======================================================

def formatear_configuracion(config) -> str:
    conteo = {}

    for inv in config:
        key = (inv["id"], inv["kw"])
        conteo[key] = conteo.get(key, 0) + 1

    partes = []

    for (iid, kw), cantidad in conteo.items():
        partes.append(f"{cantidad}×{kw:.1f} kW")

    return " + ".join(partes)


# ======================================================
# VALIDACIONES
# ======================================================

def validar_entradas_inversor(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
) -> None:

    if pdc_kw <= 0:
        raise ValueError("pdc_kw inválido")

    if dc_ac_obj <= 0:
        raise ValueError("dc_ac_obj inválido")


# ======================================================
# CÁLCULO BASE
# ======================================================

def calcular_cantidad_inversores(
    pdc_kw: float,
    pac_inversor_kw: float,
    dc_ac_obj: float,
) -> Dict[str, float]:

    if pac_inversor_kw <= 0:
        raise ValueError("pac_inversor_kw inválido")

    kw_ac_obj = pdc_kw / dc_ac_obj
    n_inversores = ceil(kw_ac_obj / pac_inversor_kw)
    kw_ac_total = n_inversores * pac_inversor_kw
    ratio_real = pdc_kw / kw_ac_total if kw_ac_total > 0 else 0

    return {
        "n_inversores": n_inversores,
        "kw_ac": pac_inversor_kw,
        "kw_ac_total": kw_ac_total,
        "ratio_real": ratio_real,
        "kw_ac_obj": kw_ac_obj,
    }


# ======================================================
# EVALUACIÓN DE OPCIÓN
# ======================================================

def evaluar_opcion_inversor(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id: str,
    pac_inversor_kw: float,
    tolerancia_dc_ac: float = 0.15,
) -> Dict[str, Any]:

    calc = calcular_cantidad_inversores(
        pdc_kw=pdc_kw,
        pac_inversor_kw=pac_inversor_kw,
        dc_ac_obj=dc_ac_obj,
    )

    ratio_real = float(calc["ratio_real"])
    n_inversores = int(calc["n_inversores"])
    kw_ac_total = float(calc["kw_ac_total"])

    desviacion = abs(ratio_real - dc_ac_obj)

    dc_ac_min = max(0.01, dc_ac_obj - tolerancia_dc_ac)
    dc_ac_max = dc_ac_obj + tolerancia_dc_ac

    dentro_rango = dc_ac_min <= ratio_real <= dc_ac_max

    if dentro_rango:
        estado = "ACEPTABLE"
        motivo = "DC/AC dentro del rango permitido."
        penalizacion_rango = 0
    elif ratio_real > dc_ac_max:
        estado = "NO RECOMENDADO"
        motivo = "DC/AC alto; posible sobredimensionamiento DC o clipping."
        penalizacion_rango = 1
    else:
        estado = "NO RECOMENDADO"
        motivo = "DC/AC bajo; inversor sobredimensionado respecto al arreglo."
        penalizacion_rango = 1

    score = (
        penalizacion_rango,
        desviacion,
        n_inversores,
        kw_ac_total,
    )

    return {
        "inversor_id": inversor_id,
        "configuracion": f"{n_inversores}×{pac_inversor_kw:.1f} kW",
        "n_inversores": n_inversores,
        "kw_ac": pac_inversor_kw,
        "kw_ac_total": kw_ac_total,
        "dc_ac_real": ratio_real,
        "ratio_real": ratio_real,
        "kw_ac_obj": calc["kw_ac_obj"],
        "desviacion_dc_ac": desviacion,
        "estado": estado,
        "motivo": motivo,
        "score": score,
    }


# ======================================================
# TABLA COMPARATIVA
# ======================================================

def generar_tabla_comparativa_inversores(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    tolerancia_dc_ac: float = 0.15,
) -> list[Dict[str, Any]]:

    catalogo = obtener_catalogo_inversores()
    tabla = []

    dc_ac_min = max(0.01, dc_ac_obj - tolerancia_dc_ac)
    dc_ac_max = dc_ac_obj + tolerancia_dc_ac

    for inv in catalogo:

        pac = float(inv["kw"])
        n_base = ceil((pdc_kw / dc_ac_obj) / pac)

        candidatos_n = sorted(set([
            max(1, n_base - 1),
            n_base,
            n_base + 1,
        ]))

        for n in candidatos_n:

            kw_ac_total = n * pac
            ratio_real = pdc_kw / kw_ac_total if kw_ac_total > 0 else 0
            desviacion = abs(ratio_real - dc_ac_obj)

            dentro_rango = dc_ac_min <= ratio_real <= dc_ac_max

            if dentro_rango:
                estado = "ACEPTABLE"
                motivo = "DC/AC dentro del rango permitido."
                penalizacion_rango = 0
            elif ratio_real > dc_ac_max:
                estado = "NO RECOMENDADO"
                motivo = "DC/AC alto; posible clipping."
                penalizacion_rango = 1
            else:
                estado = "NO RECOMENDADO"
                motivo = "DC/AC bajo; inversor sobredimensionado respecto al arreglo."
                penalizacion_rango = 1

            tabla.append({
                "inversor_id": inv["id"],
                "configuracion": f"{n}×{pac:.1f} kW",
                "n_inversores": n,
                "kw_ac": pac,
                "kw_ac_total": kw_ac_total,
                "dc_ac_real": ratio_real,
                "ratio_real": ratio_real,
                "kw_ac_obj": pdc_kw / dc_ac_obj,
                "desviacion_dc_ac": desviacion,
                "estado": estado,
                "motivo": motivo,
                "score": (
                    penalizacion_rango,
                    desviacion,
                    n,
                    kw_ac_total,
                ),
            })

    tabla.sort(key=lambda x: x["score"])

    # eliminar duplicados
    unicos = []
    vistos = set()

    for fila in tabla:
        key = (fila["inversor_id"], fila["n_inversores"], fila["kw_ac_total"])

        if key in vistos:
            continue

        vistos.add(key)
        unicos.append(fila)

    for i, fila in enumerate(unicos, 1):
        fila["opcion"] = i

        if i == 1 and fila["estado"] == "ACEPTABLE":
            fila["estado"] = "ÓPTIMO"
            fila["motivo"] = (
                "Mejor opción evaluada: DC/AC dentro del rango permitido "
                "y configuración técnicamente razonable."
            )

        fila.pop("score", None)

    return unicos[:10]

def obtener_opcion_optima(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
) -> Optional[Dict[str, Any]]:

    tabla = generar_tabla_comparativa_inversores(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    if not tabla:
        return None

    return tabla[0]


# ======================================================
# SUGERENCIAS DE CONFIGURACIÓN
# ======================================================

def sugerir_configuraciones_inversor(
    pdc_kw,
    dc_ac_obj,
    max_inv=4,
    tolerancia_dc_ac=0.15,
):

    catalogo = obtener_catalogo_inversores()
    soluciones = []

    pac_obj = pdc_kw / dc_ac_obj

    dc_ac_min = max(0.01, dc_ac_obj - tolerancia_dc_ac)
    dc_ac_max = dc_ac_obj + tolerancia_dc_ac

    for n in range(1, max_inv + 1):

        for combo in product(catalogo, repeat=n):

            pac_total = sum(inv["kw"] for inv in combo)

            if pac_total <= 0:
                continue

            dc_ac = pdc_kw / pac_total

            if not (dc_ac_min <= dc_ac <= dc_ac_max):
                continue

            soluciones.append({
                "config": combo,
                "pac_total": pac_total,
                "dc_ac": round(dc_ac, 2),
                "error": abs(pac_total - pac_obj),
                "n_inversores": n,
            })

    soluciones.sort(
        key=lambda x: (
            abs(x["dc_ac"] - dc_ac_obj),
            x["n_inversores"],
            x["pac_total"],
            x["error"],
        )
    )

    return soluciones[:5]


def construir_sugerencias_inversor(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
) -> list[Dict[str, Any]]:

    sugerencias = sugerir_configuraciones_inversor(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    return [
        {
            "descripcion": formatear_configuracion(s["config"]),
            "pac_total": s["pac_total"],
            "dc_ac": s["dc_ac"],
            "n_inversores": s["n_inversores"],
        }
        for s in sugerencias
    ]

def comparar_opciones_economica_conservadora(
    *,
    pdc_kw: float,
) -> Dict[str, Any]:

    economicas = sugerir_configuraciones_inversor(
        pdc_kw=pdc_kw,
        dc_ac_obj=1.30,
        max_inv=10,
        tolerancia_dc_ac=0.02,
    )

    conservadoras = sugerir_configuraciones_inversor(
        pdc_kw=pdc_kw,
        dc_ac_obj=1.15,
        max_inv=10,
        tolerancia_dc_ac=0.08,
    )

    economica = economicas[0] if economicas else None
    conservadora = conservadoras[0] if conservadoras else None

    return {
        "economica": {
            "descripcion": formatear_configuracion(economica["config"]),
            "kw_ac_total": economica["pac_total"],
            "dc_ac": economica["dc_ac"],
            "n_inversores": economica["n_inversores"],
            "criterio": "Menor CAPEX; acepta mayor clipping.",
        } if economica else None,

        "conservadora": {
            "descripcion": formatear_configuracion(conservadora["config"]),
            "kw_ac_total": conservadora["pac_total"],
            "dc_ac": conservadora["dc_ac"],
            "n_inversores": conservadora["n_inversores"],
            "criterio": "Mayor CAPEX; menor clipping.",
        } if conservadora else None,
    }
    
# ======================================================
# SELECCIÓN AUTOMÁTICA
# ======================================================

def resolver_inversor_automatico_actual(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
) -> Optional[Dict[str, Any]]:

    comparacion = comparar_opciones_economica_conservadora(
        pdc_kw=pdc_kw,
    )

    economica = comparacion.get("economica")

    if economica is not None:
        return {
            "inversor_id": None,
            "configuracion": economica["descripcion"],
            "n_inversores": economica["n_inversores"],
            "kw_ac": 0.0,
            "kw_ac_total": economica["kw_ac_total"],
            "ratio_real": economica["dc_ac"],
            "kw_ac_obj": pdc_kw / dc_ac_obj,
            "seleccion_forzada": False,
            "advertencia": None,
            "alternativa_recomendada": comparacion.get("conservadora"),
            "comparacion_inversores": comparacion,
            "configuracion_mixta": True,
        }

    optimo = obtener_opcion_optima(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    if optimo is None:
        return None

    return {
        "inversor_id": optimo["inversor_id"],
        "configuracion": optimo["configuracion"],
        "n_inversores": optimo["n_inversores"],
        "kw_ac": optimo["kw_ac"],
        "kw_ac_total": optimo["kw_ac_total"],
        "ratio_real": optimo["ratio_real"],
        "kw_ac_obj": optimo["kw_ac_obj"],
        "seleccion_forzada": False,
        "advertencia": None,
        "alternativa_recomendada": None,
        "comparacion_inversores": comparacion,
        "configuracion_mixta": False,
    }

# ======================================================
# ADVERTENCIA PARA INVERSOR FORZADO
# ======================================================

def construir_advertencia_inversor_forzado(
    *,
    resultado_forzado: Dict[str, Any],
    alternativa_optima: Optional[Dict[str, Any]],
) -> tuple[Optional[str], Optional[Dict[str, Any]]]:

    if alternativa_optima is None:
        return None, None

    id_forzado = resultado_forzado.get("inversor_id")
    id_optimo = alternativa_optima.get("inversor_id")

    if id_forzado == id_optimo:
        return None, None

    n_forzado = int(resultado_forzado.get("n_inversores", 0))
    n_optimo = int(alternativa_optima.get("n_inversores", 0))

    kw_forzado = float(resultado_forzado.get("kw_ac_total", 0))
    kw_optimo = float(alternativa_optima.get("kw_ac_total", 0))

    mejor_por_simplicidad = (
        n_optimo > 0
        and n_forzado > n_optimo
        and kw_optimo <= kw_forzado
    )

    if not mejor_por_simplicidad:
        return None, None

    alternativa = {
        "inversor_id": alternativa_optima["inversor_id"],
        "configuracion": alternativa_optima["configuracion"],
        "n_inversores": alternativa_optima["n_inversores"],
        "kw_ac": alternativa_optima["kw_ac"],
        "kw_ac_total": alternativa_optima["kw_ac_total"],
        "ratio_real": alternativa_optima["ratio_real"],
        "estado": alternativa_optima["estado"],
        "motivo": alternativa_optima["motivo"],
    }

    advertencia = (
        f"La selección manual requiere {n_forzado} inversores "
        f"para {kw_forzado:.2f} kW AC. "
        f"La opción óptima es {alternativa_optima['configuracion']} "
        f"con {kw_optimo:.2f} kW AC total."
    )

    return advertencia, alternativa


# ======================================================
# INVERSOR FORZADO
# ======================================================

def resolver_inversor_forzado(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id_forzado: str,
) -> Optional[Dict[str, Any]]:

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

    resultado_forzado = {
        "inversor_id": inversor_id_forzado,
        **calc,
        "seleccion_forzada": True,
    }

    alternativa_optima = obtener_opcion_optima(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    advertencia, alternativa = construir_advertencia_inversor_forzado(
        resultado_forzado=resultado_forzado,
        alternativa_optima=alternativa_optima,
    )

    sugerencias_fmt = construir_sugerencias_inversor(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    tabla_comparativa = generar_tabla_comparativa_inversores(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    return {
        **resultado_forzado,
        "sugerencias": sugerencias_fmt,
        "comparativa_inversores": tabla_comparativa,
        "advertencia": advertencia,
        "alternativa_recomendada": alternativa,
    }


# ======================================================
# API PRINCIPAL
# ======================================================

def ejecutar_inversor_desde_sizing(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    inversor_id_forzado: Optional[str] = None,
) -> Dict[str, Any]:

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

    tabla_comparativa = generar_tabla_comparativa_inversores(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    sugerencias_fmt = construir_sugerencias_inversor(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    if resultado_automatico is None:
        print("[WARN] No se encontró ningún inversor válido")

        return {
            "inversor_id": None,
            "kw_ac_total": 0,
            "n_inversores": 0,
            "kw_ac": 0,
            "ratio_real": 0,
            "kw_ac_obj": 0,
            "seleccion_forzada": False,
            "advertencia": None,
            "alternativa_recomendada": None,
            "sugerencias": [],
            "comparativa_inversores": [],
        }

    return {
        **resultado_automatico,
        "sugerencias": sugerencias_fmt,
        "comparativa_inversores": [],
        "comparacion_inversores": {},
        "configuracion_mixta": False,
    }


# ======================================================
# NOTA DE MANTENIMIENTO
# ======================================================
# Este módulo ahora:
# 1. Respeta la selección manual del usuario.
# 2. Genera una tabla comparativa de inversores.
# 3. Marca una opción como ÓPTIMO.
# 4. En modo automático usa la opción óptima.
# 5. En modo manual advierte si existe una opción más simple.

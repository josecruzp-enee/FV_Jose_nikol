from typing import Dict, Any, Optional
from itertools import combinations_with_replacement
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

        pac = float(getattr(inv, "kw_ac", 0.0) or 0.0)

        if pac <= 0:
            continue

        catalogo.append({
            "id": iid,
            "kw": pac,
        })

    catalogo.sort(key=lambda x: x["kw"])
    return catalogo


# ======================================================
# FORMATO
# ======================================================

def formatear_configuracion(config) -> str:
    conteo = {}

    for inv in config:
        key = (inv["id"], float(inv["kw"]))
        conteo[key] = conteo.get(key, 0) + 1

    partes = []

    for (iid, kw), cantidad in sorted(
        conteo.items(),
        key=lambda x: x[0][1],
        reverse=True,
    ):
        partes.append(f"{cantidad}×{kw:.1f} kW")

    return " + ".join(partes)


def _id_representativo(config) -> Optional[str]:
    if not config:
        return None

    mayor = max(config, key=lambda x: float(x["kw"]))
    return mayor["id"]


def _kw_representativo(config) -> float:
    if not config:
        return 0.0

    mayor = max(config, key=lambda x: float(x["kw"]))
    return float(mayor["kw"])


def _componentes_config(config) -> list[Dict[str, Any]]:
    conteo = {}

    for inv in config:
        key = (inv["id"], float(inv["kw"]))
        conteo[key] = conteo.get(key, 0) + 1

    componentes = []

    for (iid, kw), cantidad in sorted(
        conteo.items(),
        key=lambda x: x[0][1],
        reverse=True,
    ):
        componentes.append({
            "inversor_id": iid,
            "kw_ac": kw,
            "cantidad": cantidad,
            "kw_ac_total": kw * cantidad,
        })

    return componentes


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
# EVALUACIÓN
# ======================================================

def _clasificar_dc_ac(
    *,
    ratio_real: float,
    dc_ac_obj: float,
    tolerancia_dc_ac: float,
) -> tuple[str, str, int]:

    dc_ac_min = 1.10
    dc_ac_max = 1.30

    if dc_ac_min <= ratio_real <= dc_ac_max:
        return (
            "ACEPTABLE",
            "DC/AC dentro del rango permitido.",
            0,
        )

    if ratio_real > dc_ac_max:
        return (
            "NO RECOMENDADO",
            "DC/AC mayor que 1.30; posible clipping excesivo.",
            1,
        )

    return (
        "NO RECOMENDADO",
        "DC/AC menor que 1.10; inversor sobredimensionado.",
        1,
    )

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

    estado, motivo, penalizacion_rango = _clasificar_dc_ac(
        ratio_real=ratio_real,
        dc_ac_obj=dc_ac_obj,
        tolerancia_dc_ac=tolerancia_dc_ac,
    )

    score = (
        penalizacion_rango,
        n_inversores,
        kw_ac_total,
        desviacion,
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
        "configuracion_mixta": False,
        "componentes": [{
            "inversor_id": inversor_id,
            "kw_ac": pac_inversor_kw,
            "cantidad": n_inversores,
            "kw_ac_total": kw_ac_total,
        }],
    }


def evaluar_configuracion_mixta(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    config,
    tolerancia_dc_ac: float = 0.15,
) -> Dict[str, Any]:

    kw_ac_total = sum(float(inv["kw"]) for inv in config)
    n_inversores = len(config)

    ratio_real = pdc_kw / kw_ac_total if kw_ac_total > 0 else 0.0
    desviacion = abs(ratio_real - dc_ac_obj)

    estado, motivo, penalizacion_rango = _clasificar_dc_ac(
        ratio_real=ratio_real,
        dc_ac_obj=dc_ac_obj,
        tolerancia_dc_ac=tolerancia_dc_ac,
    )

    # Preferencia:
    # 1. Dentro de rango.
    # 2. Menor cantidad de inversores.
    # 3. Menor kW AC total.
    # 4. DC/AC más cercano al objetivo.
    score = (
        penalizacion_rango,
        n_inversores,
        kw_ac_total,
        desviacion,
    )

    return {
        "inversor_id": _id_representativo(config),
        "configuracion": formatear_configuracion(config),
        "n_inversores": n_inversores,
        "kw_ac": _kw_representativo(config),
        "kw_ac_total": kw_ac_total,
        "dc_ac_real": ratio_real,
        "ratio_real": ratio_real,
        "kw_ac_obj": pdc_kw / dc_ac_obj,
        "desviacion_dc_ac": desviacion,
        "estado": estado,
        "motivo": motivo,
        "score": score,
        "configuracion_mixta": len(_componentes_config(config)) > 1,
        "componentes": _componentes_config(config),
    }


# ======================================================
# TABLA COMPARATIVA
# ======================================================

def generar_tabla_comparativa_inversores(
    *,
    pdc_kw: float,
    dc_ac_obj: float,
    tolerancia_dc_ac: float = 0.15,
    max_inv: int = 10,
) -> list[Dict[str, Any]]:

    catalogo = obtener_catalogo_inversores()
    tabla = []

    if not catalogo:
        return []

    # ==================================================
    # 1. OPCIONES DE UN SOLO MODELO
    # ==================================================
    for inv in catalogo:

        pac = float(inv["kw"])
        n_base = ceil((pdc_kw / dc_ac_obj) / pac)

        candidatos_n = sorted(set([
            max(1, n_base - 1),
            n_base,
            n_base + 1,
        ]))

        for n in candidatos_n:

            if n > max_inv:
                continue

            config = [inv] * n

            fila = evaluar_configuracion_mixta(
                pdc_kw=pdc_kw,
                dc_ac_obj=dc_ac_obj,
                config=config,
                tolerancia_dc_ac=tolerancia_dc_ac,
            )

            fila["configuracion_mixta"] = False
            tabla.append(fila)

    # ==================================================
    # 2. OPCIONES MIXTAS
    # ==================================================
    for n in range(2, max_inv + 1):

        for combo in combinations_with_replacement(catalogo, n):

            fila = evaluar_configuracion_mixta(
                pdc_kw=pdc_kw,
                dc_ac_obj=dc_ac_obj,
                config=combo,
                tolerancia_dc_ac=tolerancia_dc_ac,
            )

            # No metas opciones absurdas muy lejos del rango.
            # Las no recomendadas cercanas sí se dejan para diagnóstico.
            if fila["estado"] == "NO RECOMENDADO":
                if fila["desviacion_dc_ac"] > tolerancia_dc_ac * 2:
                    continue

            tabla.append(fila)

    tabla.sort(key=lambda x: x["score"])

    # ==================================================
    # 3. ELIMINAR DUPLICADOS
    # ==================================================
    unicos = []
    vistos = set()

    for fila in tabla:
        componentes = tuple(
            sorted(
                (
                    c["inversor_id"],
                    round(float(c["kw_ac"]), 4),
                    int(c["cantidad"]),
                )
                for c in fila.get("componentes", [])
            )
        )

        key = (
            componentes,
            round(float(fila["kw_ac_total"]), 4),
            round(float(fila["ratio_real"]), 4),
        )

        if key in vistos:
            continue

        vistos.add(key)
        unicos.append(fila)

    # ==================================================
    # 4. NUMERAR Y MARCAR ÓPTIMO
    # ==================================================
    for i, fila in enumerate(unicos, 1):
        fila["opcion"] = i

        if i == 1 and fila["estado"] == "ACEPTABLE":
            fila["estado"] = "ÓPTIMO"
            fila["motivo"] = (
                "Mejor opción evaluada: DC/AC dentro del rango permitido, "
                "menor cantidad de inversores y menor potencia AC total."
            )

        fila.pop("score", None)

    return unicos[:20]


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

    for fila in tabla:
        if fila.get("estado") in ("ÓPTIMO", "ACEPTABLE"):
            return fila

    return tabla[0]


# ======================================================
# SUGERENCIAS
# ======================================================

def sugerir_configuraciones_inversor(
    pdc_kw,
    dc_ac_obj,
    max_inv=10,
    tolerancia_dc_ac=0.15,
):

    tabla = generar_tabla_comparativa_inversores(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
        tolerancia_dc_ac=tolerancia_dc_ac,
        max_inv=max_inv,
    )

    soluciones = []

    for fila in tabla:
        if fila.get("estado") not in ("ÓPTIMO", "ACEPTABLE"):
            continue

        soluciones.append({
            "config": fila.get("componentes", []),
            "descripcion": fila["configuracion"],
            "pac_total": fila["kw_ac_total"],
            "dc_ac": round(float(fila["ratio_real"]), 2),
            "error": abs(float(fila["kw_ac_total"]) - (pdc_kw / dc_ac_obj)),
            "n_inversores": fila["n_inversores"],
            "configuracion_mixta": fila.get("configuracion_mixta", False),
        })

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
            "descripcion": s["descripcion"],
            "pac_total": s["pac_total"],
            "dc_ac": s["dc_ac"],
            "n_inversores": s["n_inversores"],
            "configuracion_mixta": s.get("configuracion_mixta", False),
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
            "descripcion": economica["descripcion"],
            "kw_ac_total": economica["pac_total"],
            "dc_ac": economica["dc_ac"],
            "n_inversores": economica["n_inversores"],
            "criterio": "Menor CAPEX; acepta mayor DC/AC.",
            "configuracion_mixta": economica.get("configuracion_mixta", False),
        } if economica else None,

        "conservadora": {
            "descripcion": conservadora["descripcion"],
            "kw_ac_total": conservadora["pac_total"],
            "dc_ac": conservadora["dc_ac"],
            "n_inversores": conservadora["n_inversores"],
            "criterio": "Mayor CAPEX; menor clipping.",
            "configuracion_mixta": conservadora.get("configuracion_mixta", False),
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

    optimo = obtener_opcion_optima(
        pdc_kw=pdc_kw,
        dc_ac_obj=dc_ac_obj,
    )

    if optimo is None:
        return None

    comparacion = comparar_opciones_economica_conservadora(
        pdc_kw=pdc_kw,
    )

    return {
        "inversor_id": optimo["inversor_id"],
        "configuracion": optimo["configuracion"],
        "n_inversores": optimo["n_inversores"],
        "kw_ac": optimo["kw_ac"],
        "kw_ac_total": optimo["kw_ac_total"],
        "ratio_real": optimo["ratio_real"],
        "dc_ac_real": optimo["ratio_real"],
        "kw_ac_obj": optimo["kw_ac_obj"],
        "seleccion_forzada": False,
        "advertencia": None,
        "alternativa_recomendada": comparacion.get("conservadora"),
        "comparacion_inversores": comparacion,
        "configuracion_mixta": optimo.get("configuracion_mixta", False),
        "componentes": optimo.get("componentes", []),
        "estado": optimo.get("estado"),
        "motivo": optimo.get("motivo"),
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

    n_forzado = int(resultado_forzado.get("n_inversores", 0))
    n_optimo = int(alternativa_optima.get("n_inversores", 0))

    kw_forzado = float(resultado_forzado.get("kw_ac_total", 0))
    kw_optimo = float(alternativa_optima.get("kw_ac_total", 0))

    ratio_forzado = float(resultado_forzado.get("ratio_real", 0))
    ratio_optimo = float(alternativa_optima.get("ratio_real", 0))

    misma_opcion = (
        id_forzado == id_optimo
        and n_forzado == n_optimo
        and abs(kw_forzado - kw_optimo) < 0.001
    )

    if misma_opcion:
        return None, None

    mejor_por_simplicidad = (
        n_optimo > 0
        and n_forzado > n_optimo
    )

    mejor_por_potencia = (
        kw_optimo > 0
        and kw_forzado > 0
        and kw_optimo < kw_forzado
    )

    mejor_por_ratio = (
        abs(ratio_optimo - 1.20) < abs(ratio_forzado - 1.20)
    )

    if not (
        mejor_por_simplicidad
        or mejor_por_potencia
        or mejor_por_ratio
    ):
        return None, None

    alternativa = {
        "inversor_id": alternativa_optima["inversor_id"],
        "configuracion": alternativa_optima["configuracion"],
        "n_inversores": alternativa_optima["n_inversores"],
        "kw_ac": alternativa_optima["kw_ac"],
        "kw_ac_total": alternativa_optima["kw_ac_total"],
        "ratio_real": alternativa_optima["ratio_real"],
        "estado": alternativa_optima.get("estado"),
        "motivo": alternativa_optima.get("motivo"),
        "configuracion_mixta": alternativa_optima.get("configuracion_mixta", False),
        "componentes": alternativa_optima.get("componentes", []),
    }

    advertencia = (
        f"La selección manual requiere {n_forzado} inversores "
        f"para {kw_forzado:.2f} kW AC total. "
        f"La opción automática recomendada es {alternativa_optima['configuracion']} "
        f"con {kw_optimo:.2f} kW AC total y DC/AC "
        f"{float(alternativa_optima['ratio_real']):.2f}."
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

    pac = float(getattr(inv, "kw_ac", 0.0) or 0.0)

    if pac <= 0:
        print(
            f"[WARN] Inversor '{inversor_id_forzado}' tiene kw_ac inválido. "
            "Usando selección automática."
        )
        return None

    calc = calcular_cantidad_inversores(
        pdc_kw=pdc_kw,
        pac_inversor_kw=pac,
        dc_ac_obj=dc_ac_obj,
    )

    resultado_forzado = {
        "inversor_id": inversor_id_forzado,
        "configuracion": f"{int(calc['n_inversores'])}×{pac:.1f} kW",
        **calc,
        "dc_ac_real": calc["ratio_real"],
        "seleccion_forzada": True,
        "configuracion_mixta": False,
        "componentes": [{
            "inversor_id": inversor_id_forzado,
            "kw_ac": pac,
            "cantidad": int(calc["n_inversores"]),
            "kw_ac_total": float(calc["kw_ac_total"]),
        }],
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
            "dc_ac_real": 0,
            "kw_ac_obj": 0,
            "seleccion_forzada": False,
            "advertencia": None,
            "alternativa_recomendada": None,
            "sugerencias": [],
            "comparativa_inversores": [],
            "comparacion_inversores": {},
            "configuracion_mixta": False,
            "componentes": [],
        }

    return {
        **resultado_automatico,
        "sugerencias": sugerencias_fmt,
        "comparativa_inversores": tabla_comparativa,
    }


# ======================================================
# NOTA DE MANTENIMIENTO
# ======================================================
# Este módulo:
# 1. Respeta la selección manual del usuario.
# 2. Genera tabla comparativa con opciones simples y mixtas.
# 3. Evita devolver kw_ac = 0 en configuraciones mixtas.
# 4. Devuelve un inversor representativo para no romper el contrato actual.
# 5. Mantiene las llaves usadas por el sizing:
#    inversor_id, kw_ac, kw_ac_total, n_inversores,
#    ratio_real, comparativa_inversores, advertencia,
#    alternativa_recomendada.

# ======================================================
# NOTA DE MANTENIMIENTO
# ======================================================
# Este módulo ahora:
# 1. Respeta la selección manual del usuario.
# 2. Genera una tabla comparativa de inversores.
# 3. Marca una opción como ÓPTIMO.
# 4. En modo automático usa la opción óptima.
# 5. En modo manual advierte si existe una opción más simple.

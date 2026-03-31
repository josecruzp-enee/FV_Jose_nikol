from dataclasses import replace
from typing import List, Dict, Any

from core.aplicacion.dependencias import DependenciasEstudio
from core.dominio.resultado_proyecto import ResultadoProyecto
from electrical.paneles.entrada_panel import EntradaPaneles
from electrical.paneles.resultado_paneles import ResultadoPaneles

# ======================================================
# EJECUTAR ESTUDIO COMPLETO
# ======================================================
def ejecutar_estudio(datos: Any, deps: DependenciasEstudio) -> ResultadoProyecto:
    """
    Orquesta todo el flujo del proyecto FV:
    1. Sizing
    2. Paneles (manual/multizona)
    3. Energía
    4. Electrical
    5. Finanzas
    Devuelve ResultadoProyecto completo
    """
    # -------------------------------
    # 1️⃣ SIZING
    # -------------------------------
    sizing = deps.sizing.ejecutar(datos)
    if not getattr(sizing, "ok", True):
        return ResultadoProyecto(
            sizing=sizing,
            strings=None,
            energia=None,
            electrical=None,
            financiero=None
        )

    # -------------------------------
    # 2️⃣ PANEL
    # -------------------------------
    entrada_paneles = construir_entrada_paneles(datos, sizing)
    
    # Validación de entrada
    if entrada_paneles.modo == "multizona":
        if not entrada_paneles.zonas or any(z.n_paneles <= 0 for z in entrada_paneles.zonas):
            raise ValueError("Modo multizona inválido: todas las zonas deben tener n_paneles > 0")
    else:
        if entrada_paneles.n_paneles_total is None or entrada_paneles.n_paneles_total <= 0:
            raise ValueError("n_paneles_total inválido")

    paneles = _ejecutar_paneles(entrada_paneles, deps, datos)

    # -------------------------------
    # 3️⃣ ENERGÍA
    # -------------------------------
    energia = deps.energia.ejecutar(datos, sizing, paneles)

    # -------------------------------
    # 4️⃣ ELECTRICAL
    # -------------------------------
    electrical = deps.electrical.ejecutar(
        entrada_paneles=entrada_paneles,
        sizing=sizing,
        paneles=paneles,
        energia=energia
    )

    # -------------------------------
    # 5️⃣ FINANZAS
    # -------------------------------
    financiero = deps.finanzas.ejecutar(datos, sizing, paneles, energia, electrical)

    # -------------------------------
    # RESULTADO FINAL
    # -------------------------------
    return ResultadoProyecto(
        sizing=sizing,
        strings=paneles,
        energia=energia,
        electrical=electrical,
        financiero=financiero
    )


# ======================================================
# EJECUTAR PANEL
# ======================================================
def _ejecutar_paneles(entrada_paneles: EntradaPaneles, deps, datos) -> ResultadoPaneles:
    if entrada_paneles.modo == "multizona":
        if not entrada_paneles.zonas or len(entrada_paneles.zonas) == 0:
            raise ValueError("Modo multizona pero no hay zonas definidas")
        for i, z in enumerate(entrada_paneles.zonas, 1):
            if getattr(z, "n_paneles", 0) <= 0:
                raise ValueError(f"Zona {i} tiene n_paneles <= 0")
    else:
        if entrada_paneles.n_paneles_total is None or entrada_paneles.n_paneles_total <= 0:
            raise ValueError("n_paneles_total inválido")

    resultados: List[ResultadoPaneles] = []

    if entrada_paneles.modo == "multizona":
        for zona in entrada_paneles.zonas:
            entrada_zona = replace(
                entrada_paneles,
                modo="manual",
                n_paneles_total=zona.n_paneles,
                zonas=None
            )
            resultado_zona = deps.paneles.ejecutar(entrada_zona)
            if resultado_zona is None:
                raise ValueError("Paneles devolvió None en una zona")
            resultados.append(resultado_zona)
    else:
        resultado = deps.paneles.ejecutar(entrada_paneles)
        if resultado is None:
            raise ValueError("Paneles devolvió None")
        resultados.append(resultado)

    resultado_final = _consolidar_paneles(resultados)
    return resultado_final


# ======================================================
# CLONAR ENTRADA PARA ZONA
# ======================================================
def _clonar_entrada_para_zona(entrada, n_paneles):
    return replace(
        entrada,
        n_paneles_total=int(n_paneles or 0),
        modo="manual",
        zonas=None
    )


# ======================================================
# CONSOLIDAR PANEL
# ======================================================
def _consolidar_paneles(resultados: List[ResultadoPaneles]) -> ResultadoPaneles:
    if not resultados:
        return None

    base = resultados[0]
    strings = []

    for i, r in enumerate(resultados, 1):
        for j, s in enumerate(r.strings, 1):
            s_new = replace(s)
            object.__setattr__(s_new, "zona", i)
            object.__setattr__(s_new, "id_string", f"Z{i}_S{j}")
            strings.append(s_new)

    total_strings = len(strings)
    total_paneles = sum(getattr(s, "n_paneles", 0) for s in strings)
    mppt_detectados = set(getattr(s, "mppt", None) for s in strings)

    array_new = replace(
        base.array,
        n_strings_total=total_strings,
        n_paneles_total=total_paneles,
        n_mppt=len(mppt_detectados),
        vdc_nom=max(getattr(s, "vmp_string_v", 0) for s in strings),
        isc_total=sum(getattr(s, "isc_string_a", 0) for s in strings)
    )

    resultado = replace(
        base,
        strings=strings,
        array=array_new
    )

    return resultado

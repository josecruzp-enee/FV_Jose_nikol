from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


DIAS_MES = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


# ==========================================================
# HELPERS GENERALES
# ==========================================================

def _leer(obj: Any, campo: str, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


def _mkdir_charts(out_dir: str | None) -> Path:
    base = Path(out_dir) if out_dir else Path("salidas") / "charts"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _lista_float(valores, n: int, default: float = 0.0) -> List[float]:
    salida = []

    if valores is None:
        return [default] * n

    if isinstance(valores, dict):
        for i in range(n):
            salida.append(float(valores.get(i, valores.get(str(i), default)) or default))
        return salida

    if isinstance(valores, list):
        for x in valores[:n]:
            try:
                salida.append(float(x or default))
            except Exception:
                salida.append(default)

    while len(salida) < n:
        salida.append(default)

    return salida


# ==========================================================
# ENERGÍA
# ==========================================================

def _extraer_energia_12m(lista) -> List[float]:
    if not lista:
        return [0.0] * 12

    if isinstance(lista[0], (int, float)):
        return [float(x or 0.0) for x in lista[:12]]

    if isinstance(lista[0], dict):
        for key in ("energia_kwh", "energia", "valor"):
            if key in lista[0]:
                return [float(item.get(key, 0.0) or 0.0) for item in lista[:12]]

    return [0.0] * 12


def _extraer_energia_resultado(res):
    return _leer(res, "energia", None)


def _extraer_energia_mensual(energia) -> List[float]:
    if energia is None:
        return [0.0] * 12

    energia_raw = list(_leer(energia, "energia_util_12m", []) or [])
    return _extraer_energia_12m(energia_raw)


def _extraer_energia_horaria(energia) -> List[float]:
    if energia is None:
        return []

    return list(_leer(energia, "energia_horaria_kwh", []) or [])


def _promedio_fv_24h(energia_horaria_kwh: List[float]) -> List[float]:
    if not energia_horaria_kwh:
        energia_horaria_kwh = [0.0] * 8760

    suma = [0.0] * 24
    conteo = [0] * 24

    for idx, valor in enumerate(energia_horaria_kwh):
        hora = (idx - 6) % 24
        suma[hora] += float(valor or 0.0)
        conteo[hora] += 1

    return [suma[h] / conteo[h] if conteo[h] else 0.0 for h in range(24)]


# ==========================================================
# PROYECTO / DEMANDA
# ==========================================================

def _extraer_proyecto(res, proyecto=None):
    if proyecto is not None:
        return proyecto

    return _leer(res, "proyecto", None)


def _extraer_consumo_24h(proyecto) -> Dict:
    if proyecto is None:
        return {}

    return _leer(proyecto, "consumo_horario_24h_kwh", {}) or {}


def _demanda_24h_desde_dict(consumo_horario_24h_kwh: dict) -> List[float]:
    return [
        float(
            consumo_horario_24h_kwh.get(
                h,
                consumo_horario_24h_kwh.get(str(h), 0.0),
            ) or 0.0
        )
        for h in range(24)
    ]


# ==========================================================
# BATERÍA
# ==========================================================

def _extraer_bateria_directa(res, energia):
    bateria = _leer(res, "bateria", None)

    if bateria is None and energia is not None:
        bateria = _leer(energia, "bateria", None)

    return bateria


def _extraer_bateria_desde_financiero(res):
    financiero = _leer(res, "financiero", None)

    if financiero is None:
        return None

    bateria_optima = _leer(financiero, "bateria_optima", None)

    if bateria_optima is None:
        return None

    return _leer(bateria_optima, "resultado_bateria", None)


def _resolver_bateria(res, energia):
    bateria = _extraer_bateria_directa(res, energia)

    if bateria is not None:
        return bateria

    return _extraer_bateria_desde_financiero(res)


def _extraer_tabla_24h_bateria(resultado_bateria):
    return (
        _leer(resultado_bateria, "tabla_24h", None)
        or _leer(resultado_bateria, "tabla_horaria", None)
        or _leer(resultado_bateria, "detalle_24h", None)
    )


def _serie_24_desde_tabla(tabla, campos: List[str]) -> Optional[List[float]]:
    if not isinstance(tabla, list):
        return None

    salida = []

    for fila in tabla[:24]:
        if not isinstance(fila, dict):
            salida.append(0.0)
            continue

        valor = 0.0

        for campo in campos:
            if campo in fila:
                try:
                    valor = float(fila.get(campo) or 0.0)
                except Exception:
                    valor = 0.0
                break

        salida.append(valor)

    while len(salida) < 24:
        salida.append(0.0)

    return salida


def _serie_24_desde_atributos(obj, campos: List[str]) -> Optional[List[float]]:
    for campo in campos:
        valor = _leer(obj, campo, None)

        if valor is not None:
            return _lista_float(valor, 24, 0.0)

    return None


def _extraer_resultado_bateria(bateria):
    if bateria is None:
        return None

    return (
        _leer(bateria, "resultado_bateria", None)
        or _leer(bateria, "bateria", None)
        or _leer(bateria, "resultado", None)
        or bateria
    )


def _extraer_red_con_bateria(resultado_bateria, tabla_24h):
    campos_attr = [
        "compra_red_con_bateria_24h",
        "red_con_bateria_24h",
        "demanda_red_con_bateria_24h",
        "compra_red_24h_kwh",
        "energia_red_24h_kwh",
    ]

    campos_tabla = [
        "compra_red_con_bateria_kwh",
        "red_con_bateria_kwh",
        "demanda_red_con_bateria_kwh",
        "compra_red_kwh",
        "red_kwh",
    ]

    return (
        _serie_24_desde_atributos(resultado_bateria, campos_attr)
        or _serie_24_desde_tabla(tabla_24h, campos_tabla)
    )


def _extraer_descarga_bateria(resultado_bateria, tabla_24h):
    campos_attr = [
        "descarga_bateria_24h",
        "descarga_24h_kwh",
        "energia_descargada_24h",
        "bateria_descarga_24h_kwh",
    ]

    campos_tabla = [
        "descarga_kwh",
        "descarga_bateria_kwh",
        "energia_descargada_kwh",
        "energia_entregada_kwh",
        "bateria_a_carga_kwh",
    ]

    return (
        _serie_24_desde_atributos(resultado_bateria, campos_attr)
        or _serie_24_desde_tabla(tabla_24h, campos_tabla)
    )


def _extraer_carga_bateria(resultado_bateria, tabla_24h):
    campos_attr = [
        "carga_bateria_24h",
        "carga_24h_kwh",
        "energia_cargada_24h",
        "bateria_carga_24h_kwh",
    ]

    campos_tabla = [
        "carga_kwh",
        "carga_bateria_kwh",
        "energia_cargada_kwh",
        "fv_a_bateria_kwh",
    ]

    return (
        _serie_24_desde_atributos(resultado_bateria, campos_attr)
        or _serie_24_desde_tabla(tabla_24h, campos_tabla)
    )


def _extraer_soc_bateria(resultado_bateria, tabla_24h):
    campos_attr = [
        "soc_24h_pct",
        "soc_pct_24h",
        "soc_24h",
        "estado_carga_24h_pct",
    ]

    campos_tabla = [
        "soc_pct",
        "soc",
        "soc_bateria_pct",
        "estado_carga_pct",
    ]

    return (
        _serie_24_desde_atributos(resultado_bateria, campos_attr)
        or _serie_24_desde_tabla(tabla_24h, campos_tabla)
    )


def _extraer_series_bateria(bateria) -> dict:
    resultado_bateria = _extraer_resultado_bateria(bateria)
    tabla_24h = _extraer_tabla_24h_bateria(resultado_bateria)

    return {
        "demanda": _serie_24_desde_atributos(
            resultado_bateria,
            ["demanda_24h_kwh"],
        ),
        "fv": _serie_24_desde_atributos(
            resultado_bateria,
            ["fv_24h_kwh"],
        ),
        "red_sin_bateria": _serie_24_desde_atributos(
            resultado_bateria,
            ["compra_red_sin_bateria_24h"],
        ),
        "red_con_bateria": _extraer_red_con_bateria(resultado_bateria, tabla_24h),
        "descarga": _extraer_descarga_bateria(resultado_bateria, tabla_24h),
        "carga": _extraer_carga_bateria(resultado_bateria, tabla_24h),
        "soc": _extraer_soc_bateria(resultado_bateria, tabla_24h),
    }


# ==========================================================
# CÁLCULOS DEMANDA VS FV
# ==========================================================

def _calcular_red_sin_bateria(demanda: List[float], fv: List[float]) -> List[float]:
    return [max(d - f, 0.0) for d, f in zip(demanda, fv)]


def _calcular_autoconsumo(demanda: List[float], fv: List[float]) -> List[float]:
    return [min(d, f) for d, f in zip(demanda, fv)]


def _calcular_excedente(demanda: List[float], fv: List[float]) -> List[float]:
    return [max(f - d, 0.0) for d, f in zip(demanda, fv)]


def _calcular_red_con_bateria_si_falta(
    red_sin_bateria: List[float],
    red_con_bateria,
    descarga,
):
    if red_con_bateria is not None:
        return red_con_bateria

    if descarga is None:
        return None

    return [
        max(red - desc, 0.0)
        for red, desc in zip(red_sin_bateria, descarga)
    ]


def _resumen_demanda_fv(
    demanda: List[float],
    fv: List[float],
    autoconsumo: List[float],
    excedente: List[float],
    red_sin_bateria: List[float],
    red_con_bateria=None,
    descarga=None,
    carga=None,
    soc=None,
) -> str:
    energia_demanda = sum(demanda)
    energia_fv = sum(fv)
    energia_autoconsumo = sum(autoconsumo)
    energia_excedente = sum(excedente)
    energia_red = sum(red_sin_bateria)

    cobertura_directa = (
        energia_autoconsumo / energia_demanda * 100
        if energia_demanda > 0
        else 0.0
    )

    reduccion_red = (
        (1 - energia_red / energia_demanda) * 100
        if energia_demanda > 0
        else 0.0
    )

    texto = (
        f"Demanda diaria promedio: {energia_demanda:.1f} kWh\n"
        f"Generación FV promedio: {energia_fv:.1f} kWh\n"
        f"Autoconsumo promedio: {energia_autoconsumo:.1f} kWh\n"
        f"Compra de red promedio: {energia_red:.1f} kWh\n"
        f"Excedente FV promedio: {energia_excedente:.1f} kWh\n"
        f"Cobertura directa: {cobertura_directa:.1f}%\n"
        f"Reducción compra red: {reduccion_red:.1f}%"
    )

    if red_con_bateria is not None:
        energia_red_bateria = sum(red_con_bateria)

        reduccion_red_bateria = (
            (1 - energia_red_bateria / energia_demanda) * 100
            if energia_demanda > 0
            else 0.0
        )

        texto += (
            f"\nRed con batería: {energia_red_bateria:.1f} kWh"
            f"\nReducción con batería: {reduccion_red_bateria:.1f}%"
        )

    if descarga is not None:
        texto += f"\nDescarga batería: {sum(descarga):.1f} kWh"

    if carga is not None:
        texto += f"\nCarga batería: {sum(carga):.1f} kWh"

    if soc is not None:
        texto += f"\nSOC mín/máx: {min(soc):.0f}% / {max(soc):.0f}%"

    return texto


# ==========================================================
# GRÁFICAS BÁSICAS
# ==========================================================

def _guardar_figura(fig, path: Path):
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _chart_mensual(meses: List[str], energia: List[float], path: Path):
    fig, ax = plt.subplots()
    ax.bar(meses, energia)
    ax.set_title("Generación FV mensual")
    ax.set_ylabel("Energía (kWh)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True)
    _guardar_figura(fig, path)


def _chart_diaria(meses: List[str], energia: List[float], path: Path):
    fig, ax = plt.subplots()
    ax.bar(meses, energia)
    ax.set_title("Energía diaria promedio")
    ax.set_ylabel("kWh/día")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True)
    _guardar_figura(fig, path)


def _chart_potencia_horaria(energia_horaria_kwh: List[float], path: Path):
    potencia_promedio = _promedio_fv_24h(energia_horaria_kwh)
    horas = list(range(24))

    fig, ax = plt.subplots()
    ax.plot(horas, potencia_promedio, marker="o")
    ax.set_title("Perfil horario de potencia FV")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Potencia (kW)")
    ax.set_xticks(range(24))
    ax.grid(True)
    _guardar_figura(fig, path)


def _chart_energia_horaria(energia_horaria_kwh: List[float], path: Path):
    energia_promedio = _promedio_fv_24h(energia_horaria_kwh)
    horas = list(range(24))

    fig, ax = plt.subplots()
    ax.bar(horas, energia_promedio)
    ax.set_title("Energía generada por hora")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Energía (kWh)")
    ax.set_xticks(range(24))
    ax.grid(True)
    _guardar_figura(fig, path)


def _chart_anual(energia_anual: float, path: Path):
    fig, ax = plt.subplots()
    ax.bar(["Anual"], [energia_anual])
    ax.set_title("Generación FV anual")
    ax.set_ylabel("Energía (kWh)")
    _guardar_figura(fig, path)


# ==========================================================
# GRÁFICA DEMANDA VS FV
# ==========================================================

def _dibujar_area_fv(ax, horas_np, demanda_np, fv_np, red_np):
    ax.fill_between(
        horas_np,
        red_np,
        demanda_np,
        where=demanda_np > red_np,
        interpolate=True,
        color="green",
        alpha=0.16,
        label="Demanda reducida por FV",
        zorder=1,
    )

    ax.fill_between(
        horas_np,
        demanda_np,
        fv_np,
        where=fv_np > demanda_np,
        interpolate=True,
        color="orange",
        alpha=0.25,
        label="Excedente FV",
        zorder=2,
    )


def _dibujar_lineas_base(ax, horas_np, demanda_np, fv_np, red_np):
    ax.plot(
        horas_np,
        demanda_np,
        marker="o",
        linewidth=2,
        color="blue",
        label="Demanda original",
        zorder=5,
    )

    ax.plot(
        horas_np,
        fv_np,
        marker="o",
        linewidth=2,
        color="green",
        label="Generación FV",
        zorder=6,
    )

    ax.plot(
        horas_np,
        red_np,
        marker="o",
        linewidth=2,
        linestyle="--",
        color="red",
        label="Demanda neta desde red",
        zorder=7,
    )


def _dibujar_bateria(ax, horas_np, red_np, red_con_bateria):
    if red_con_bateria is None:
        return

    import numpy as np

    red_bat_np = np.array(red_con_bateria, dtype=float)

    if np.allclose(red_bat_np, red_np, rtol=0.0, atol=1e-9):
        return

    ax.fill_between(
        horas_np,
        red_bat_np,
        red_np,
        where=red_np > red_bat_np,
        interpolate=True,
        color="purple",
        alpha=0.18,
        label="Reducción por batería",
        zorder=3,
    )

    ax.plot(
        horas_np,
        red_bat_np,
        marker="o",
        linewidth=2,
        linestyle="-.",
        color="purple",
        label="Demanda neta con batería",
        zorder=8,
    )


def _dibujar_soc(ax, horas_np, soc):
    if soc is None or sum(soc) <= 0:
        return None

    ax_soc = ax.twinx()

    ax_soc.plot(
        horas_np,
        soc,
        color="black",
        linewidth=2.2,
        linestyle=":",
        label="SOC batería (%)",
        zorder=9,
    )

    ax_soc.set_ylabel("SOC batería (%)")
    ax_soc.set_ylim(0, 100)

    return ax_soc


def _dibujar_caja_resumen(ax, texto: str):
    ax.text(
        0.02,
        0.97,
        texto,
        transform=ax.transAxes,
        fontsize=8,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            edgecolor="gray",
            alpha=0.80,
        ),
        zorder=10,
    )


def _configurar_ejes_demanda(ax):
    ax.set_title("Demanda del cliente vs generación FV y almacenamiento")
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Energía promedio horaria (kWh)")
    ax.set_xticks(range(24))
    ax.grid(True, alpha=0.35)


def _configurar_leyenda(ax, ax_soc=None):
    if ax_soc is not None:
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax_soc.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8)
    else:
        ax.legend(loc="upper right", fontsize=8)


def _chart_demanda_vs_fv_horaria(
    consumo_horario_24h_kwh: dict,
    energia_horaria_kwh: List[float],
    path: Path,
    bateria=None,
):
    import numpy as np

    horas = list(range(24))

    series_bateria = _extraer_series_bateria(bateria)

    demanda = (
        series_bateria.get("demanda")
        or _demanda_24h_desde_dict(consumo_horario_24h_kwh)
    )
    fv = (
        series_bateria.get("fv")
        or _promedio_fv_24h(energia_horaria_kwh or [0.0] * 8760)
    )
    # Se recalcula desde las mismas series usadas en la gráfica.
    # Así siempre se cumple:
    # demanda = autoconsumo + compra de red.
    red_sin_bateria = _calcular_red_sin_bateria(demanda, fv)
    autoconsumo = _calcular_autoconsumo(demanda, fv)
    excedente = _calcular_excedente(demanda, fv)

    red_con_bateria = series_bateria.get("red_con_bateria")
    descarga = series_bateria.get("descarga")
    carga = series_bateria.get("carga")
    soc = series_bateria.get("soc")

    red_con_bateria = _calcular_red_con_bateria_si_falta(
        red_sin_bateria,
        red_con_bateria,
        descarga,
    )

    bateria_activa = (
        red_con_bateria is not None
        and any(
            abs(a - b) > 1e-9
            for a, b in zip(red_sin_bateria, red_con_bateria)
        )
    )

    if not bateria_activa:
        red_con_bateria = None
        descarga = None
        carga = None
        soc = None

    horas_np = np.array(horas, dtype=float)
    demanda_np = np.array(demanda, dtype=float)
    fv_np = np.array(fv, dtype=float)
    red_np = np.array(red_sin_bateria, dtype=float)

    fig, ax = plt.subplots(figsize=(11, 5.8))

    _dibujar_area_fv(ax, horas_np, demanda_np, fv_np, red_np)
    _dibujar_lineas_base(ax, horas_np, demanda_np, fv_np, red_np)
    _dibujar_bateria(ax, horas_np, red_np, red_con_bateria)

    ax_soc = _dibujar_soc(ax, horas_np, soc)

    texto = _resumen_demanda_fv(
        demanda=demanda,
        fv=fv,
        autoconsumo=autoconsumo,
        excedente=excedente,
        red_sin_bateria=red_sin_bateria,
        red_con_bateria=red_con_bateria,
        descarga=descarga,
        carga=carga,
        soc=soc,
    )

    _dibujar_caja_resumen(ax, texto)
    _configurar_ejes_demanda(ax)
    _configurar_leyenda(ax, ax_soc)

    _guardar_figura(fig, path)


# ==========================================================
# GENERACIÓN DE CHARTS
# ==========================================================

def _generar_chart_mensual(base: Path, paths: dict, energia_mensual: List[float]):
    p = base / "fv_energia_mensual.png"
    _chart_mensual(MESES, energia_mensual, p)
    paths["chart_energia_mensual"] = str(p)


def _generar_chart_diario(base: Path, paths: dict, energia_mensual: List[float]):
    energia_diaria = [
        e / d if d else 0.0
        for e, d in zip(energia_mensual, DIAS_MES)
    ]

    p = base / "fv_energia_diaria.png"
    _chart_diaria(MESES, energia_diaria, p)
    paths["chart_energia_diaria"] = str(p)


def _generar_charts_horarios(base: Path, paths: dict, energia_horaria: List[float]):
    p_potencia = base / "fv_potencia_horaria.png"
    _chart_potencia_horaria(energia_horaria, p_potencia)
    paths["chart_potencia_horaria"] = str(p_potencia)

    p_energia = base / "fv_energia_horaria.png"
    _chart_energia_horaria(energia_horaria, p_energia)
    paths["chart_energia_horaria"] = str(p_energia)


def _generar_chart_demanda_vs_fv(
    base: Path,
    paths: dict,
    proyecto,
    energia_horaria: List[float],
    bateria=None,
):
    consumo_horario_24h_kwh = _extraer_consumo_24h(proyecto)

    p = base / "demanda_vs_fv_horaria.png"

    _chart_demanda_vs_fv_horaria(
        consumo_horario_24h_kwh,
        energia_horaria,
        p,
        bateria=bateria,
    )

    paths["chart_demanda_vs_fv_horaria"] = str(p)


def _generar_chart_anual(base: Path, paths: dict, energia_mensual: List[float]):
    energia_anual = sum(energia_mensual)

    p = base / "fv_energia_anual.png"
    _chart_anual(energia_anual, p)
    paths["chart_anual"] = str(p)


def generar_charts(
    res,
    out_dir=None,
    vista_resultados=None,
    proyecto=None,
):
    base = _mkdir_charts(out_dir)

    energia = _extraer_energia_resultado(res)
    bateria = _resolver_bateria(res, energia)
    proyecto = _extraer_proyecto(res, proyecto)

    energia_mensual = _extraer_energia_mensual(energia)
    energia_horaria = _extraer_energia_horaria(energia)

    paths = {}

    _generar_chart_mensual(base, paths, energia_mensual)
    _generar_chart_diario(base, paths, energia_mensual)
    _generar_charts_horarios(base, paths, energia_horaria)

    _generar_chart_demanda_vs_fv(
        base=base,
        paths=paths,
        proyecto=proyecto,
        energia_horaria=energia_horaria,
        bateria=bateria,
    )

    _generar_chart_anual(base, paths, energia_mensual)

    return paths

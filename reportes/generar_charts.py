from __future__ import annotations

from pathlib import Path
from typing import List

import math
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


# ==========================================================
# CONFIG
# ==========================================================

DIAS_MES = [31,28,31,30,31,30,31,31,30,31,30,31]


# ==========================================================
# CREAR CARPETA
# ==========================================================

def _mkdir_charts(out_dir: str | None) -> Path:
    base = Path(out_dir) if out_dir else Path("salidas") / "charts"
    base.mkdir(parents=True, exist_ok=True)
    return base


# ==========================================================
# LEER POTENCIA DC
# ==========================================================

def _leer_pdc_kw(res):

    sizing = res.get("sizing") if isinstance(res, dict) else getattr(res, "sizing", None)

    if not sizing:
        return 0.0

    # objeto
    kwp = getattr(sizing, "kwp_dc", None)
    if kwp:
        return float(kwp)

    # dict
    if isinstance(sizing, dict):

        kwp = sizing.get("kwp_recomendado")
        if kwp:
            return float(kwp)

        pdc_w = sizing.get("potencia_dc_w")
        if pdc_w:
            return float(pdc_w) / 1000.0

    return 0.0


# ==========================================================
# HELPERS ENERGÍA
# ==========================================================

def _extraer_energia(lista):

    if not lista:
        return [0] * 12

    if isinstance(lista[0], (int, float)):
        return lista

    if isinstance(lista[0], dict):
        for key in ("energia_kwh", "energia", "valor"):
            if key in lista[0]:
                return [item.get(key, 0) for item in lista]

    return [0] * 12


# ==========================================================
# GRÁFICAS
# ==========================================================

def _chart_mensual(meses: List[str], energia: List[float], path: Path):

    plt.figure()
    plt.bar(meses, energia)

    plt.title("Generación FV mensual")
    plt.ylabel("Energía (kWh)")
    plt.xticks(rotation=45)
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _chart_diaria(meses: List[str], energia: List[float], path: Path):

    plt.figure()
    plt.bar(meses, energia)

    plt.title("Energía diaria promedio")
    plt.ylabel("kWh/día")
    plt.xticks(rotation=45)
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _chart_potencia_horaria(
    energia_horaria_kwh: List[float],
    path: Path
):

    if not energia_horaria_kwh:
        energia_horaria_kwh = [0.0] * 8760

    horas = list(range(24))

    suma = [0.0] * 24
    conteo = [0] * 24

    for idx, valor in enumerate(energia_horaria_kwh):

        hora = (idx - 6) % 24

        suma[hora] += float(valor)
        conteo[hora] += 1

    potencia_promedio = []

    for h in horas:

        if conteo[h] == 0:
            potencia_promedio.append(0.0)
        else:
            potencia_promedio.append(
                suma[h] / conteo[h]
            )

    plt.figure()
    plt.plot(
        horas,
        potencia_promedio,
        marker="o"
    )

    plt.title("Perfil horario de potencia FV")
    plt.xlabel("Hora")
    plt.ylabel("Potencia (kW)")
    plt.xticks(range(24))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def _chart_demanda_vs_fv_horaria(
    consumo_horario_24h_kwh: dict,
    energia_horaria_kwh: List[float],
    path: Path,
    bateria=None,
):
    """
    Grafica demanda original, generación FV, demanda neta desde red
    y, si existe batería, demanda neta desde red con batería.

    Colores:
    - Azul: demanda original.
    - Verde: generación FV / reducción por FV.
    - Rojo: demanda neta desde red sin batería.
    - Morado: demanda neta desde red con batería.
    - Naranja/beige: excedente FV.
    """

    import numpy as np
    import matplotlib.pyplot as plt

    if not energia_horaria_kwh:
        energia_horaria_kwh = [0.0] * 8760

    horas = list(range(24))

    demanda = [
        float(consumo_horario_24h_kwh.get(h, 0.0) or 0.0)
        for h in horas
    ]

    suma_fv = [0.0] * 24
    conteo = [0] * 24

    for idx, valor in enumerate(energia_horaria_kwh):
        hora = (idx - 6) % 24
        suma_fv[hora] += float(valor or 0.0)
        conteo[hora] += 1

    fv_promedio = [
        suma_fv[h] / conteo[h] if conteo[h] else 0.0
        for h in horas
    ]

    autoconsumo = [
        min(d, f)
        for d, f in zip(demanda, fv_promedio)
    ]

    excedente = [
        max(f - d, 0.0)
        for d, f in zip(demanda, fv_promedio)
    ]

    demanda_neta_red = [
        max(d - f, 0.0)
        for d, f in zip(demanda, fv_promedio)
    ]

    # ======================================================
    # BATERÍA, SI EXISTE
    # ======================================================
    red_con_bateria = None
    descarga_bateria = None
    carga_bateria = None
    soc_bateria = None

    if bateria is not None and getattr(bateria, "ok", False):
        red_con_bateria = getattr(
            bateria,
            "compra_red_con_bateria_24h",
            None
        )

        descarga_bateria = getattr(
            bateria,
            "descarga_bateria_24h",
            None
        )

        carga_bateria = getattr(
            bateria,
            "carga_bateria_24h",
            None
        )

        soc_bateria = getattr(
            bateria,
            "soc_24h_pct",
            None
        )

        if red_con_bateria:
            red_con_bateria = [
                float(x or 0.0)
                for x in list(red_con_bateria)[:24]
            ]

            if len(red_con_bateria) < 24:
                red_con_bateria += [0.0] * (24 - len(red_con_bateria))
        else:
            red_con_bateria = None

    energia_demanda = sum(demanda)
    energia_fv = sum(fv_promedio)
    energia_autoconsumo = sum(autoconsumo)
    energia_excedente = sum(excedente)
    energia_red = sum(demanda_neta_red)

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

    energia_red_bateria = None
    reduccion_red_bateria = None

    if red_con_bateria is not None:
        energia_red_bateria = sum(red_con_bateria)

        reduccion_red_bateria = (
            (1 - energia_red_bateria / energia_demanda) * 100
            if energia_demanda > 0
            else 0.0
        )

    horas_np = np.array(horas, dtype=float)
    demanda_np = np.array(demanda, dtype=float)
    fv_np = np.array(fv_promedio, dtype=float)
    red_np = np.array(demanda_neta_red, dtype=float)

    plt.figure(figsize=(11, 5.5))
    ax = plt.gca()

    # ======================================================
    # ÁREA DE REDUCCIÓN POR FV
    # ======================================================
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

    # ======================================================
    # ÁREA DE EXCEDENTE FV
    # ======================================================
    ax.fill_between(
        horas_np,
        demanda_np,
        fv_np,
        where=fv_np > demanda_np,
        interpolate=True,
        color="orange",
        alpha=0.28,
        label="Excedente FV",
        zorder=2,
    )

    # ======================================================
    # ÁREA DE DESCARGA DE BATERÍA
    # ======================================================
    if red_con_bateria is not None:
        red_bat_np = np.array(red_con_bateria, dtype=float)

        ax.fill_between(
            horas_np,
            red_bat_np,
            red_np,
            where=red_np > red_bat_np,
            interpolate=True,
            color="purple",
            alpha=0.18,
            label="Reducción adicional por batería",
            zorder=3,
        )

    # ======================================================
    # CURVA DEMANDA ORIGINAL
    # ======================================================
    ax.plot(
        horas_np,
        demanda_np,
        marker="o",
        linewidth=2,
        color="blue",
        label="Demanda original",
        zorder=5,
    )

    # ======================================================
    # CURVA GENERACIÓN FV
    # ======================================================
    ax.plot(
        horas_np,
        fv_np,
        marker="o",
        linewidth=2,
        color="green",
        label="Generación FV",
        zorder=6,
    )

    # ======================================================
    # CURVA DEMANDA NETA DESDE RED SIN BATERÍA
    # ======================================================
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

    # ======================================================
    # CURVA DEMANDA NETA DESDE RED CON BATERÍA
    # ======================================================
    if red_con_bateria is not None:
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

    texto = (
        f"Demanda diaria: {energia_demanda:.1f} kWh\n"
        f"Generación FV: {energia_fv:.1f} kWh\n"
        f"Autoconsumo: {energia_autoconsumo:.1f} kWh\n"
        f"Energía desde red: {energia_red:.1f} kWh\n"
        f"Excedente FV: {energia_excedente:.1f} kWh\n"
        f"Cobertura directa: {cobertura_directa:.1f}%\n"
        f"Reducción compra red: {reduccion_red:.1f}%"
    )

    if energia_red_bateria is not None:
        texto += (
            f"\nRed con batería: {energia_red_bateria:.1f} kWh"
            f"\nReducción con batería: {reduccion_red_bateria:.1f}%"
        )

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

    ax.set_title("Reducción de demanda por generación fotovoltaica")
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Energía promedio horaria (kWh)")
    ax.set_xticks(range(24))
    ax.grid(True, alpha=0.35)
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()



def _chart_energia_horaria(
    energia_horaria_kwh: List[float],
    path: Path
):

    if not energia_horaria_kwh:
        energia_horaria_kwh = [0.0] * 8760

    horas = list(range(24))

    suma = [0.0] * 24
    conteo = [0] * 24

    for idx, valor in enumerate(energia_horaria_kwh):

        hora = (idx - 6) % 24

        suma[hora] += float(valor)
        conteo[hora] += 1

    energia_promedio = []

    for h in horas:

        if conteo[h] == 0:
            energia_promedio.append(0.0)
        else:
            energia_promedio.append(
                suma[h] / conteo[h]
            )

    plt.figure()
    plt.bar(
        horas,
        energia_promedio
    )

    plt.title("Energía generada por hora")
    plt.xlabel("Hora")
    plt.ylabel("Energía (kWh)")
    plt.xticks(range(24))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

def _chart_anual(energia_anual: float, path: Path):

    plt.figure()
    plt.bar(["Anual"], [energia_anual])

    plt.title("Generación FV anual")
    plt.ylabel("Energía (kWh)")

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()



# ==========================================================
# GENERADOR PRINCIPAL (LIMPIO)
# ==========================================================

def generar_charts(
    res,
    out_dir=None,
    vista_resultados=None,
    proyecto=None,
):

    base = _mkdir_charts(out_dir)

    # ======================================================
    # DATOS ENERGÍA (NO SE CALCULA AQUÍ)
    # ======================================================

    energia = (
        res.get("energia")
        if isinstance(res, dict)
        else getattr(res, "energia", None)
    )

    if energia:
        energia_raw = list(
            getattr(energia, "energia_util_12m", [])
        )
        energia_mensual = _extraer_energia(energia_raw)
    else:
        energia_mensual = [0] * 12

    meses = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    energia_anual = sum(energia_mensual)

    paths = {}

    # ======================================================
    # GRÁFICAS
    # ======================================================

    p1 = base / "fv_energia_mensual.png"
    _chart_mensual(meses, energia_mensual, p1)
    paths["chart_energia_mensual"] = str(p1)

    energia_diaria = [
        e / d if d else 0
        for e, d in zip(energia_mensual, DIAS_MES)
    ]

    p2 = base / "fv_energia_diaria.png"
    _chart_diaria(meses, energia_diaria, p2)
    paths["chart_energia_diaria"] = str(p2)

    # ======================================================
    # SERIE HORARIA REAL 8760
    # ======================================================

    energia_horaria = []

    if energia:
        energia_horaria = list(
            getattr(
                energia,
                "energia_horaria_kwh",
                []
            )
        )

    p3 = base / "fv_potencia_horaria.png"
    _chart_potencia_horaria(
        energia_horaria,
        p3
    )
    paths["chart_potencia_horaria"] = str(p3)

    p4 = base / "fv_energia_horaria.png"
    _chart_energia_horaria(
        energia_horaria,
        p4
    )
    paths["chart_energia_horaria"] = str(p4)

    # ======================================================
    # DEMANDA CLIENTE VS GENERACIÓN FV
    # ======================================================

    consumo_horario_24h_kwh = {}

    if proyecto is None:
        proyecto = (
            res.get("proyecto")
            if isinstance(res, dict)
            else getattr(res, "proyecto", None)
        )

    if proyecto:
        consumo_horario_24h_kwh = getattr(
            proyecto,
            "consumo_horario_24h_kwh",
            {}
        ) or {}

    p6 = base / "demanda_vs_fv_horaria.png"

    _chart_demanda_vs_fv_horaria(
        consumo_horario_24h_kwh,
        energia_horaria,
        p6,
    )

    paths["chart_demanda_vs_fv_horaria"] = str(p6)

    # anual
    p5 = base / "fv_energia_anual.png"
    _chart_anual(energia_anual, p5)
    paths["chart_anual"] = str(p5)

    return paths

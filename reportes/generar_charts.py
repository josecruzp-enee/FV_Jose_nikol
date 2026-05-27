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
):
    """
    Grafica demanda promedio horaria del cliente vs generación FV promedio horaria.
    """

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

    plt.figure(figsize=(10, 5))

    plt.plot(horas, demanda, marker="o", label="Demanda cliente")
    plt.plot(horas, fv_promedio, marker="o", label="Generación FV")

    plt.title("Demanda del cliente vs Generación FV")
    plt.xlabel("Hora")
    plt.ylabel("kWh por hora / kW promedio")
    plt.xticks(range(24))
    plt.grid(True)
    plt.legend()

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
# DEMANDA VS FV
# ==========================================================
def _chart_demanda_vs_fv_horaria(
    consumo_horario_24h_kwh: dict,
    energia_horaria_kwh: List[float],
    path: Path,
):
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

    plt.figure(figsize=(10, 5))
    plt.plot(horas, demanda, marker="o", label="Demanda cliente")
    plt.plot(horas, fv_promedio, marker="o", label="Generación FV")

    plt.title("Demanda del cliente vs Generación FV")
    plt.xlabel("Hora")
    plt.ylabel("kWh por hora / kW promedio")
    plt.xticks(range(24))
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
# ==========================================================
# GENERADOR PRINCIPAL (LIMPIO)
# ==========================================================

def generar_charts(
    res,
    out_dir=None,
    vista_resultados=None
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

    # mensual
    p1 = base / "fv_energia_mensual.png"
    _chart_mensual(meses, energia_mensual, p1)
    paths["chart_energia_mensual"] = str(p1)

    # diaria
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

    # potencia horaria real desde 8760
    p3 = base / "fv_potencia_horaria.png"
    _chart_potencia_horaria(
        energia_horaria,
        p3
    )
    paths["chart_potencia_horaria"] = str(p3)

    # energía horaria real desde 8760
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

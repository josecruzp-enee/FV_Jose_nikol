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
    Gráfica de demanda vs FV con batería.

    Muestra:
    - Demanda original
    - Generación FV
    - Demanda neta desde red sin batería
    - Demanda neta desde red con batería
    - SOC batería (%) si existe
    """

    import numpy as np
    import matplotlib.pyplot as plt

    def _leer(obj, nombres, default=None):
        if obj is None:
            return default

        for nombre in nombres:
            if isinstance(obj, dict) and nombre in obj:
                return obj.get(nombre)

            valor = getattr(obj, nombre, None)
            if valor is not None:
                return valor

        return default

    def _lista_24(valores):
        if valores is None:
            return None

        if isinstance(valores, dict):
            return [
                float(valores.get(h, valores.get(str(h), 0.0)) or 0.0)
                for h in range(24)
            ]

        if isinstance(valores, list):
            salida = []

            for x in valores[:24]:
                try:
                    salida.append(float(x or 0.0))
                except Exception:
                    salida.append(0.0)

            if len(salida) < 24:
                salida += [0.0] * (24 - len(salida))

            return salida

        return None

    def _tabla_24(tabla, nombres):
        if not isinstance(tabla, list):
            return None

        salida = []

        for fila in tabla[:24]:
            if not isinstance(fila, dict):
                salida.append(0.0)
                continue

            valor = 0.0

            for nombre in nombres:
                if nombre in fila:
                    try:
                        valor = float(fila.get(nombre) or 0.0)
                    except Exception:
                        valor = 0.0
                    break

            salida.append(valor)

        if len(salida) < 24:
            salida += [0.0] * (24 - len(salida))

        return salida

    if not energia_horaria_kwh:
        energia_horaria_kwh = [0.0] * 8760

    horas = list(range(24))

    demanda = [
        float(
            consumo_horario_24h_kwh.get(
                h,
                consumo_horario_24h_kwh.get(str(h), 0.0)
            ) or 0.0
        )
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
    # LECTURA FLEXIBLE DE BATERÍA
    # ======================================================

    resultado_bateria = _leer(
        bateria,
        ["resultado_bateria", "bateria", "resultado"],
        bateria,
    )

    tabla_24h = _leer(
        resultado_bateria,
        ["tabla_24h", "tabla_horaria", "detalle_24h"],
        None,
    )

    red_con_bateria = _lista_24(
        _leer(
            resultado_bateria,
            [
                "compra_red_con_bateria_24h",
                "red_con_bateria_24h",
                "demanda_red_con_bateria_24h",
                "compra_red_24h_kwh",
                "energia_red_24h_kwh",
            ],
            None,
        )
    )

    descarga_bateria = _lista_24(
        _leer(
            resultado_bateria,
            [
                "descarga_bateria_24h",
                "descarga_24h_kwh",
                "energia_descargada_24h",
                "bateria_descarga_24h_kwh",
            ],
            None,
        )
    )

    carga_bateria = _lista_24(
        _leer(
            resultado_bateria,
            [
                "carga_bateria_24h",
                "carga_24h_kwh",
                "energia_cargada_24h",
                "bateria_carga_24h_kwh",
            ],
            None,
        )
    )

    soc_bateria = _lista_24(
        _leer(
            resultado_bateria,
            [
                "soc_24h_pct",
                "soc_pct_24h",
                "soc_24h",
                "estado_carga_24h_pct",
            ],
            None,
        )
    )

    if red_con_bateria is None:
        red_con_bateria = _tabla_24(
            tabla_24h,
            [
                "compra_red_con_bateria_kwh",
                "red_con_bateria_kwh",
                "demanda_red_con_bateria_kwh",
                "compra_red_kwh",
                "red_kwh",
            ],
        )

    if descarga_bateria is None:
        descarga_bateria = _tabla_24(
            tabla_24h,
            [
                "descarga_kwh",
                "descarga_bateria_kwh",
                "energia_descargada_kwh",
                "energia_entregada_kwh",
                "bateria_a_carga_kwh",
            ],
        )

    if carga_bateria is None:
        carga_bateria = _tabla_24(
            tabla_24h,
            [
                "carga_kwh",
                "carga_bateria_kwh",
                "energia_cargada_kwh",
                "fv_a_bateria_kwh",
            ],
        )

    if soc_bateria is None:
        soc_bateria = _tabla_24(
            tabla_24h,
            [
                "soc_pct",
                "soc",
                "soc_bateria_pct",
                "estado_carga_pct",
            ],
        )

    # Si no viene red con batería, se estima con la descarga.
    if red_con_bateria is None and descarga_bateria is not None:
        red_con_bateria = [
            max(red - desc, 0.0)
            for red, desc in zip(demanda_neta_red, descarga_bateria)
        ]

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

    energia_descarga_bateria = (
        sum(descarga_bateria)
        if descarga_bateria is not None
        else 0.0
    )

    energia_carga_bateria = (
        sum(carga_bateria)
        if carga_bateria is not None
        else 0.0
    )

    horas_np = np.array(horas, dtype=float)
    demanda_np = np.array(demanda, dtype=float)
    fv_np = np.array(fv_promedio, dtype=float)
    red_np = np.array(demanda_neta_red, dtype=float)

    plt.figure(figsize=(11, 5.8))
    ax = plt.gca()

    ax_soc = None

    if soc_bateria is not None and sum(soc_bateria) > 0:
        ax_soc = ax.twinx()

    # ======================================================
    # ÁREAS
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
    # CURVAS PRINCIPALES
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

    # ======================================================
    # SOC EN EJE SECUNDARIO
    # ======================================================

    if ax_soc is not None:
        ax_soc.plot(
            horas_np,
            soc_bateria,
            color="black",
            linewidth=2.2,
            linestyle=":",
            label="SOC batería (%)",
            zorder=9,
        )

        ax_soc.set_ylabel("SOC batería (%)")
        ax_soc.set_ylim(0, 100)

    # ======================================================
    # TEXTO RESUMEN
    # ======================================================

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
            f"\nDescarga batería: {energia_descarga_bateria:.1f} kWh"
            f"\nCarga batería: {energia_carga_bateria:.1f} kWh"
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

    ax.set_title("Demanda del cliente vs generación FV con batería")
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Energía promedio horaria (kWh)")
    ax.set_xticks(range(24))
    ax.grid(True, alpha=0.35)

    if ax_soc is not None:
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax_soc.get_legend_handles_labels()

        ax.legend(
            h1 + h2,
            l1 + l2,
            loc="upper right",
            fontsize=8,
        )
    else:
        ax.legend(
            loc="upper right",
            fontsize=8,
        )

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
    # DATOS ENERGÍA
    # ======================================================
    energia = (
        res.get("energia")
        if isinstance(res, dict)
        else getattr(res, "energia", None)
    )

    bateria = (
        res.get("bateria")
        if isinstance(res, dict)
        else getattr(res, "bateria", None)
    )

    if energia:
        energia_raw = list(getattr(energia, "energia_util_12m", []))
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
    # GRÁFICAS MENSUALES / DIARIAS
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
    # SERIE HORARIA 8760
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
    _chart_potencia_horaria(energia_horaria, p3)
    paths["chart_potencia_horaria"] = str(p3)

    p4 = base / "fv_energia_horaria.png"
    _chart_energia_horaria(energia_horaria, p4)
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
        if isinstance(proyecto, dict):
            consumo_horario_24h_kwh = (
                proyecto.get("consumo_horario_24h_kwh", {})
                or {}
            )
        else:
            consumo_horario_24h_kwh = (
                getattr(proyecto, "consumo_horario_24h_kwh", {})
                or {}
            )

    p6 = base / "demanda_vs_fv_horaria.png"

    _chart_demanda_vs_fv_horaria(
        consumo_horario_24h_kwh,
        energia_horaria,
        p6,
        bateria=bateria,
    )

    paths["chart_demanda_vs_fv_horaria"] = str(p6)

    # ======================================================
    # GRÁFICA ANUAL
    # ======================================================
    p5 = base / "fv_energia_anual.png"
    _chart_anual(energia_anual, p5)
    paths["chart_anual"] = str(p5)

    return paths

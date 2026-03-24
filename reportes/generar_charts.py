from __future__ import annotations

from pathlib import Path
from typing import List

import math
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

# ✅ fallback seguro (elimina dependencia rota)
DIAS_MES = [31,28,31,30,31,30,31,31,30,31,30,31]

from reportes.generar_string_fv import generar_string_fv


# ==========================================================
# Crear carpeta charts
# ==========================================================

def _mkdir_charts(out_dir: str | None) -> Path:

    base = Path(out_dir) if out_dir else Path("salidas") / "charts"
    base.mkdir(parents=True, exist_ok=True)

    return base


# ==========================================================
# Extraer potencia DC desde ResultadoProyecto
# ==========================================================

def _leer_pdc_kw(res):

    sizing = res.get("sizing") if isinstance(res, dict) else getattr(res, "sizing", None)

    if not sizing:
        return 0.0

    kwp = getattr(sizing, "kwp_dc", None)
    if kwp:
        return float(kwp)

    if isinstance(sizing, dict):
        kwp = sizing.get("kwp_recomendado")
        if kwp:
            return float(kwp)

        pdc_w = sizing.get("potencia_dc_w")
        if pdc_w:
            return float(pdc_w) / 1000.0

    return 0.0


# ==========================================================
# Gráfica energía mensual
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


# ==========================================================
# Gráfica energía diaria promedio
# ==========================================================

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


# ==========================================================
# Perfil horario de potencia
# ==========================================================

def _chart_potencia_horaria(pdc_kw: float, path: Path):

    horas = list(range(24))
    potencia = []

    PR = 0.82

    for h in horas:

        if 6 <= h <= 18:
            angulo = (h - 6) / 12 * math.pi
            irr_rel = math.sin(angulo)
        else:
            irr_rel = 0

        p = pdc_kw * irr_rel * PR
        potencia.append(p)

    plt.figure()
    plt.plot(horas, potencia, marker="o")

    plt.title("Perfil horario de potencia FV")
    plt.xlabel("Hora")
    plt.ylabel("Potencia (kW)")
    plt.xticks(range(24))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


# ==========================================================
# Energía horaria
# ==========================================================

def _chart_energia_horaria(pdc_kw: float, path: Path):

    horas = list(range(24))
    energia = []

    PR = 0.82

    for h in horas:

        if 6 <= h <= 18:
            angulo = (h - 6) / 12 * math.pi
            irr_rel = math.sin(angulo)
        else:
            irr_rel = 0

        e = pdc_kw * irr_rel * PR
        energia.append(e)

    plt.figure()
    plt.bar(horas, energia)

    plt.title("Energía generada por hora")
    plt.xlabel("Hora")
    plt.ylabel("Energía (kWh)")
    plt.xticks(range(24))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


# ==========================================================
# Energía anual
# ==========================================================

def _chart_anual(energia_anual: float, path: Path):

    plt.figure()
    plt.bar(["Anual"], [energia_anual])

    plt.title("Generación FV anual")
    plt.ylabel("Energía (kWh)")

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


# ==========================================================
# GENERADOR PRINCIPAL
# ==========================================================

def generar_charts(
    res,
    out_dir=None,
    vista_resultados=None
):

    base = _mkdir_charts(out_dir)

    # ==========================================================
    # 🔥 AUTO-EJECUTAR MOTOR ENERGÉTICO SI NO EXISTE
    # ==========================================================

    energia = None

    if isinstance(res, dict):
        energia = res.get("energia")
    else:
        energia = getattr(res, "energia", None)

    if not energia:
        try:
            from energy.orquestador_energia import ejecutar_modelo_energetico

            if isinstance(res, dict):
                energia_calc = ejecutar_modelo_energetico(res)
                res["energia"] = energia_calc
                energia = energia_calc
            else:
                energia_calc = ejecutar_modelo_energetico(res)
                setattr(res, "energia", energia_calc)
                energia = energia_calc

            print("✅ Motor energético ejecutado correctamente")

        except Exception as e:
            print("⚠️ No se pudo ejecutar motor energético:", e)
            energia = None

    # ==========================================================
    # 🧠 FUNCIÓN ROBUSTA PARA EXTRAER ENERGÍA
    # ==========================================================

    def _extraer_energia(lista):
        if not lista:
            return [0] * 12

        # Caso 1: lista de números
        if isinstance(lista[0], (int, float)):
            return lista

        # Caso 2: lista de dicts
        if isinstance(lista[0], dict):
            for key in ("energia_kwh", "energia", "valor"):
                if key in lista[0]:
                    return [item.get(key, 0) for item in lista]

        # fallback seguro
        return [0] * 12

    # ==========================================================
    # Procesamiento energía
    # ==========================================================

    if energia:
        energia_raw = list(getattr(energia, "energia_util_12m", []))
        energia_mensual = _extraer_energia(energia_raw)
    else:
        energia_mensual = [0] * 12

    meses = [
        "Ene","Feb","Mar","Abr","May","Jun",
        "Jul","Ago","Sep","Oct","Nov","Dic"
    ]

    energia_anual = sum(energia_mensual)

    paths = {}

    # ==========================================================
    # 📊 GRÁFICAS
    # ==========================================================

    # mensual
    p1 = base / "fv_energia_mensual.png"
    _chart_mensual(meses, energia_mensual, p1)
    paths["chart_energia_mensual"] = str(p1)

    # diaria
    energia_diaria = [
        e/d if d else 0 for e, d in zip(energia_mensual, DIAS_MES)
    ]

    p2 = base / "fv_energia_diaria.png"
    _chart_diaria(meses, energia_diaria, p2)
    paths["chart_energia_diaria"] = str(p2)

    # potencia
    pdc_kw = _leer_pdc_kw(res)

    p3 = base / "fv_potencia_horaria.png"
    _chart_potencia_horaria(pdc_kw, p3)
    paths["chart_potencia_horaria"] = str(p3)

    # energía horaria
    p4 = base / "fv_energia_horaria.png"
    _chart_energia_horaria(pdc_kw, p4)
    paths["chart_energia_horaria"] = str(p4)

    # anual
    p5 = base / "fv_energia_anual.png"
    _chart_anual(energia_anual, p5)
    paths["chart_anual"] = str(p5)

    # ==========================================================
    # 🔌 STRING FV
    # ==========================================================

    try:
        strings_block = res.get("strings") if isinstance(res, dict) else getattr(res, "strings", None)
        strings = getattr(strings_block, "strings", []) if strings_block else []

        if strings:
            n_series = getattr(strings[0], "n_series", None)

            if n_series:
                p6 = base / "string_fv.png"

                generar_string_fv(
                    n_series,
                    p6,
                    n_strings=len(strings)
                )

                paths["string_fv"] = str(p6)

    except Exception as e:
        print("Error generando diagrama string FV:", e)

    return paths

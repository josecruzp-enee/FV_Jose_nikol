from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any

import matplotlib.pyplot as plt

from electrical.energia.irradiancia import (
    hsp_12m_base,
    hsp_a_perfil_horario,
    DIAS_MES
)


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

    sizing = (res or {}).get("sizing") or {}

    # 1️⃣ kwp directo
    kwp = sizing.get("kwp_dc")
    if kwp:
        return float(kwp)

    # 2️⃣ kwp recomendado
    kwp = sizing.get("kwp_recomendado")
    if kwp:
        return float(kwp)

    # 3️⃣ potencia en watts
    pdc_w = sizing.get("potencia_dc_w")
    if pdc_w:
        return float(pdc_w) / 1000.0

    return 0.0

# ==========================================================
# Gráfica mensual
# ==========================================================

def _chart_mensual(meses: List[str], energia: List[float], path: Path):

    plt.figure()

    plt.plot(meses, energia, marker="o")

    plt.title("Generación FV mensual")
    plt.ylabel("kWh")
    plt.xticks(rotation=45)
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


# ==========================================================
# Gráfica diaria promedio
# ==========================================================

def _chart_horaria(pdc_kw: float, hsp_dia: float, path: Path):

    horas = list(range(24))
    potencia = []

    PR = 0.82

    for h in horas:

        if 6 <= h <= 18:
            angulo = (h - 6) / 12 * math.pi
            irradiancia_rel = math.sin(angulo)
        else:
            irradiancia_rel = 0

        p = pdc_kw * irradiancia_rel * PR
        potencia.append(p)

    plt.figure()
    plt.plot(horas, potencia, marker="o")

    plt.title("Perfil horario de generación FV")
    plt.xlabel("Hora")
    plt.ylabel("Potencia (kW)")
    plt.xticks(range(24))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

# ==========================================================
# Gráfica horaria
# ==========================================================

def _chart_horaria(pdc_kw: float, hsp_dia: float, path: Path):

    perfil = hsp_a_perfil_horario(hsp_dia)

    horas = list(range(24))
    potencia = []

    PR = 0.82

    for irr in perfil:

        # convertir energía horaria a fracción del día solar
        if hsp_dia > 0:
            fraccion = irr / hsp_dia
        else:
            fraccion = 0

        p = pdc_kw * fraccion * PR

        potencia.append(p)

    plt.figure()

    plt.plot(horas, potencia, marker="o")

    plt.title("Perfil horario de generación FV")
    plt.xlabel("Hora")
    plt.ylabel("Potencia (kW)")
    plt.xticks(range(0,24))
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

# ==========================================================
# Gráfica anual
# ==========================================================

def _chart_anual(energia_anual: float, path: Path):

    plt.figure()

    plt.bar(["Anual"], [energia_anual])

    plt.title("Generación FV anual")
    plt.ylabel("kWh")

    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


# ==========================================================
# GENERADOR PRINCIPAL
# ==========================================================

def generar_charts(
    res: Any,
    out_dir: str | None = None,
    vista_resultados: Dict | None = None
) -> Dict[str, str]:

    base = _mkdir_charts(out_dir)

    pdc_kw = _leer_pdc_kw(res)
    import streamlit as st

    st.write("DEBUG ResultadoProyecto:", res)
    st.write("DEBUG PDC KW:", pdc_kw)
    meses = [
        "Ene","Feb","Mar","Abr","May","Jun",
        "Jul","Ago","Sep","Oct","Nov","Dic"
    ]

    hsp = hsp_12m_base()

    energia_mensual = []
    energia_diaria = []

    for hsp_mes, dias in zip(hsp, DIAS_MES):

        e_mes = pdc_kw * hsp_mes * dias

        energia_mensual.append(e_mes)
        energia_diaria.append(e_mes / dias)

    energia_anual = sum(energia_mensual)

    paths = {}

    # mensual
    p1 = base / "fv_chart_mensual.png"
    _chart_mensual(meses, energia_mensual, p1)
    paths["chart_mensual"] = str(p1)

    # diaria
    p2 = base / "fv_chart_diaria.png"
    _chart_diaria(meses, energia_diaria, p2)
    paths["chart_diaria"] = str(p2)

    # horaria
    p3 = base / "fv_chart_horaria.png"
    _chart_horaria(pdc_kw, max(hsp), p3)
    paths["chart_horaria"] = str(p3)

    # anual
    p4 = base / "fv_chart_anual.png"
    _chart_anual(energia_anual, p4)
    paths["chart_anual"] = str(p4)

    return paths

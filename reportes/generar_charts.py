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

def _leer_pdc_kw(res) -> float:

    try:

        # ResultadoProyecto como dict
        if isinstance(res, dict):

            # ruta nueva
            if "tecnico" in res:
                sistema = res["tecnico"].get("sistema", {})
                if "potencia_dc_kw" in sistema:
                    return float(sistema["potencia_dc_kw"])

            # ruta sizing
            sizing = res.get("sizing", {})
            if "potencia_dc_w" in sizing:
                return float(sizing["potencia_dc_w"]) / 1000

        # ResultadoProyecto como dataclass
        else:

            if hasattr(res, "tecnico"):
                sistema = getattr(res.tecnico, "sistema", None)
                if sistema and hasattr(sistema, "potencia_dc_kw"):
                    return float(sistema.potencia_dc_kw)

            if hasattr(res, "sizing"):
                sizing = res.sizing
                if hasattr(sizing, "potencia_dc_w"):
                    return float(sizing.potencia_dc_w) / 1000

    except Exception:
        pass

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

def _chart_diaria(meses: List[str], energia: List[float], path: Path):

    plt.figure()

    plt.bar(meses, energia)

    plt.title("Generación FV diaria promedio")
    plt.ylabel("kWh/día")
    plt.xticks(rotation=45)
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

    for irr in perfil:

        if hsp_dia > 0:
            p = pdc_kw * (irr / hsp_dia)
        else:
            p = 0

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

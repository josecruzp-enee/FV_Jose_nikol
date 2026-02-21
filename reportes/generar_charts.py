# reportes/generar_charts.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt


# -------------------------
# Helpers básicos
# -------------------------
def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def _dias_mes_default() -> List[int]:
    # Aproximación estable (no bisiesto); suficiente para promedios.
    return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _meses_default() -> List[str]:
    return ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _resolver_tabla_12m(
    tabla_12m: Union[List[Dict[str, Any]], Dict[str, Any], None]
) -> List[Dict[str, Any]]:
    """
    Normaliza entradas:
    - Si viene lista: ok
    - Si viene dict (resultado completo): intenta dict["tabla_12m"]
    - Si viene None: []
    """
    if tabla_12m is None:
        return []
    if isinstance(tabla_12m, list):
        return [r for r in tabla_12m if isinstance(r, dict)]
    if isinstance(tabla_12m, dict):
        t = tabla_12m.get("tabla_12m")
        if isinstance(t, list):
            return [r for r in t if isinstance(r, dict)]
    return []


def _mkdir_charts(out_dir: Optional[str]) -> Path:
    # Default estable: salidas/charts
    base = Path(out_dir) if out_dir else Path("salidas") / "charts"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _plot_line(meses: List[str], ys: List[List[float]], labels: List[str], out_path: Path) -> None:
    plt.figure()
    for y, lab in zip(ys, labels):
        plt.plot(meses, y, marker="o", label=lab)
    plt.xticks(rotation=90)
    if any(labels):
        plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_bar(meses: List[str], y: List[float], out_path: Path) -> None:
    plt.figure()
    plt.bar(meses, y)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _fv_aprox_desde_panel_sizing(res: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construye generación FV aproximada usando:
      res["sizing"]["pdc_kw"] (o kwp_dc)
      res["sizing"]["panel_sizing"]["hsp_12m"]
      res["sizing"]["panel_sizing"]["pr"]
      res["sizing"]["panel_sizing"]["meta"]["dias_mes"] (opcional)

    Devuelve:
      {
        "meses": [str]*12,
        "fv_kwh": [float]*12,
        "fv_kwh_dia": [float]*12,
      }
    """
    sizing = (res or {}).get("sizing") or {}
    if not isinstance(sizing, dict):
        return {}

    # Potencia DC (kW)
    pdc_kw = _as_float(sizing.get("pdc_kw"), 0.0)
    if pdc_kw <= 0:
        pdc_kw = _as_float(sizing.get("kwp_dc"), 0.0)
    if pdc_kw <= 0:
        return {}

    panel_sizing = sizing.get("panel_sizing") or {}
    if not isinstance(panel_sizing, dict):
        return {}

    hsp_12m = panel_sizing.get("hsp_12m")
    if not (isinstance(hsp_12m, list) and len(hsp_12m) == 12):
        return {}

    pr = _as_float(panel_sizing.get("pr"), 0.0)
    if pr <= 0:
        return {}

    meta = panel_sizing.get("meta") or {}
    dias = meta.get("dias_mes") if isinstance(meta, dict) else None
    if not (isinstance(dias, list) and len(dias) == 12):
        dias = _dias_mes_default()

    meses = _meses_default()

    fv_kwh: List[float] = []
    fv_kwh_dia: List[float] = []
    for hsp, d in zip(hsp_12m, dias):
        d_i = int(d) if int(d) > 0 else 30
        e_mes = pdc_kw * _as_float(hsp, 0.0) * pr * float(d_i)
        fv_kwh.append(float(e_mes))
        fv_kwh_dia.append(float(e_mes / float(d_i)))

    return {"meses": meses, "fv_kwh": fv_kwh, "fv_kwh_dia": fv_kwh_dia}


def generar_charts(
    tabla_12m: Union[List[Dict[str, Any]], Dict[str, Any], None],
    out_dir: Optional[str] = None,
    vista_resultados: bool = False,
    **kwargs: Any,
) -> Dict[str, str]:
    """
    Genera PNGs:
      - fv_chart_energia.png (factura_base vs pago_enee) (solo si hay tabla_12m real)
      - fv_chart_neto.png (ahorro) (solo si hay tabla_12m real)
      - fv_chart_generacion.png o fv_chart_generacion_aprox.png (fv_kwh mensual)
      - fv_chart_generacion_diaria_aprox.png (kWh/día promedio por mes, solo en modo aprox)

    Compatibilidad:
    - Acepta vista_resultados (aunque no se use)
    - Acepta **kwargs (tolerante a flags nuevos)
    - Si por error le pasas el 'resultado' completo (dict), extrae dict["tabla_12m"]
      y además puede usar dict["sizing"]["panel_sizing"] como fallback.
    """
    tabla = _resolver_tabla_12m(tabla_12m)
    res_dict: Dict[str, Any] = tabla_12m if isinstance(tabla_12m, dict) else {}

    base = _mkdir_charts(out_dir)
    paths_out: Dict[str, str] = {}

    # -------------------------
    # Caso A: tenemos tabla_12m real
    # -------------------------
    if tabla:
        meses = [str(r.get("mes", i + 1)) for i, r in enumerate(tabla)]
        factura_base = [float(r.get("factura_base_L", 0.0)) for r in tabla]
        pago_enee = [float(r.get("pago_enee_L", 0.0)) for r in tabla]
        ahorro = [float(r.get("ahorro_L", 0.0)) for r in tabla]
        fv_kwh = [float(r.get("fv_kwh", 0.0)) for r in tabla]

        p1 = base / "fv_chart_energia.png"
        _plot_line(meses, [factura_base, pago_enee], ["Factura base", "Pago ENEE"], p1)
        paths_out["chart_energia"] = str(p1)

        p2 = base / "fv_chart_neto.png"
        _plot_bar(meses, ahorro, p2)
        paths_out["chart_neto"] = str(p2)

        p3 = base / "fv_chart_generacion.png"
        _plot_line(meses, [fv_kwh], ["FV kWh"], p3)
        paths_out["chart_generacion"] = str(p3)

        return paths_out

    # -------------------------
    # Caso B: fallback aproximado (sin tabla_12m)
    # -------------------------
    if not res_dict:
        return {}

    aprox = _fv_aprox_desde_panel_sizing(res_dict)
    if not aprox:
        return {}

    meses = aprox["meses"]
    fv_kwh = aprox["fv_kwh"]
    fv_kwh_dia = aprox["fv_kwh_dia"]

    p3 = base / "fv_chart_generacion_aprox.png"
    _plot_line(meses, [fv_kwh], ["FV kWh (aprox)"], p3)
    paths_out["chart_generacion"] = str(p3)

    p4 = base / "fv_chart_generacion_diaria_aprox.png"
    _plot_bar(meses, fv_kwh_dia, p4)
    paths_out["chart_generacion_diaria"] = str(p4)

    return paths_out

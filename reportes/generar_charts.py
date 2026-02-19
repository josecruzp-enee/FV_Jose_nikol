# reportes/generar_charts.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt


def _resolver_tabla_12m(
    tabla_12m: Union[List[Dict[str, Any]], Dict[str, Any], None]
) -> List[Dict[str, Any]]:
    """
    Normaliza entradas:
    - Si viene lista: ok
    - Si viene dict (resultado completo): intenta resultado["tabla_12m"]
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


def _plot_line(meses: List[str], ys: List[float], labels: List[str], out_path: Path) -> None:
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


def generar_charts(
    tabla_12m: Union[List[Dict[str, Any]], Dict[str, Any], None],
    out_dir: Optional[str] = None,
    vista_resultados: bool = False,
    **kwargs: Any,
) -> Dict[str, str]:
    """
    Genera 3 PNG:
      - fv_chart_energia.png (factura_base vs pago_enee)
      - fv_chart_neto.png (ahorro)
      - fv_chart_generacion.png (fv_kwh)

    Compatibilidad:
    - Acepta vista_resultados (aunque no se use)
    - Acepta **kwargs (tolerante a flags nuevos)
    - Si por error le pasas el 'resultado' completo (dict), extrae resultado["tabla_12m"]
    """
    tabla = _resolver_tabla_12m(tabla_12m)
    if not tabla:
        return {}

    base = _mkdir_charts(out_dir)

    meses = [str(r.get("mes", i + 1)) for i, r in enumerate(tabla)]
    factura_base = [float(r.get("factura_base_L", 0.0)) for r in tabla]
    pago_enee = [float(r.get("pago_enee_L", 0.0)) for r in tabla]
    ahorro = [float(r.get("ahorro_L", 0.0)) for r in tabla]
    fv_kwh = [float(r.get("fv_kwh", 0.0)) for r in tabla]

    p1 = base / "fv_chart_energia.png"
    _plot_line(meses, [factura_base, pago_enee], ["Factura base", "Pago ENEE"], p1)

    p2 = base / "fv_chart_neto.png"
    _plot_bar(meses, ahorro, p2)

    p3 = base / "fv_chart_generacion.png"
    _plot_line(meses, [fv_kwh], ["FV kWh"], p3)

    return {
        "chart_energia": str(p1),
        "chart_neto": str(p2),
        "chart_generacion": str(p3),
    }

# reportes/imagenes.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def construir_paths_salida(base_dir: str | Path) -> Dict[str, str]:
    """
    Contrato único de carpetas/paths para artefactos.
    """
    base = Path(base_dir)
    _ensure_dir(base)

    charts_dir = _ensure_dir(base / "charts")
    return {
        "out_dir": str(base),
        "charts_dir": str(charts_dir),
        "layout_paneles": str(base / "layout_paneles.png"),
        # opcional: logo, portada, etc.
        # "logo": str(base / "logo.png"),
    }


def _as_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return int(default)
        return int(float(x))
    except Exception:
        return int(default)


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def _inferir_n_paneles(res: Dict[str, Any]) -> int:
    """
    Inferencia tolerante para layout (NO ingeniería).
    Orden:
      1) sizing.n_paneles
      2) sizing.n_paneles_string (si alguien lo usa así)
      3) res.n_paneles
      4) heuristic: kwp_dc y panel_wp si están
    """
    sizing = (res or {}).get("sizing") or {}
    if isinstance(sizing, dict):
        n = _as_int(sizing.get("n_paneles"), 0)
        if n > 0:
            return n

        n = _as_int(sizing.get("n_paneles_string"), 0)
        if n > 0:
            return n

    n = _as_int((res or {}).get("n_paneles"), 0)
    if n > 0:
        return n

    # Heurística SOLO para layout: n_paneles ≈ kwp_dc*1000/panel_wp
    kwp = None
    if isinstance(sizing, dict):
        kwp = sizing.get("kwp_dc") or sizing.get("kwp_recomendado")
    if kwp is None:
        kwp = (res or {}).get("kwp_dc")

    kwp = _as_float(kwp, 0.0)
    if kwp <= 0:
        return 0

    # panel_wp: si existe en sizing/equipos, úsalo; si no, usa 550 como default visual
    panel_wp = None
    if isinstance(sizing, dict):
        panel_wp = sizing.get("panel_wp")
    if panel_wp is None:
        panel_wp = (res or {}).get("panel_wp")
    panel_wp = _as_float(panel_wp, 550.0)
    if panel_wp <= 0:
        panel_wp = 550.0

    return max(0, int(round((kwp * 1000.0) / panel_wp)))


def generar_artefactos(
    *,
    res: Dict[str, Any],
    out_dir: str | Path,
    vista_resultados: Optional[Dict[str, Any]] = None,
    dos_aguas: bool = True,
    max_cols: int = 7,
    gap_cumbrera_m: float = 0.35,
) -> Dict[str, str]:
    """
    Genera todos los artefactos gráficos y devuelve 'paths' listos para el PDF.
    No depende de Streamlit.
    """
    from reportes.generar_charts import generar_charts
    from reportes.generar_layout_paneles import generar_layout_paneles

    paths = construir_paths_salida(out_dir)

    # --- charts
    tabla_12m = (res or {}).get("tabla_12m")
    if tabla_12m:
        charts = generar_charts(
            tabla_12m,
            paths["charts_dir"],
            vista_resultados=vista_resultados or {},
        )
        for k, v in (charts or {}).items():
            paths[k] = str(v)

    # --- layout paneles (tolerante)
    n_paneles = _inferir_n_paneles(res)
    if n_paneles > 0:
        generar_layout_paneles(
            n_paneles=n_paneles,
            out_path=paths["layout_paneles"],
            max_cols=max_cols,
            dos_aguas=bool(dos_aguas),
            gap_cumbrera_m=float(gap_cumbrera_m),
        )

    return paths

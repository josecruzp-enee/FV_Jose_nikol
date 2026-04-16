# reportes/imagenes.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


# =========================================================
# BASE PATHS
# =========================================================

def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def construir_paths_salida(base_dir: str | Path) -> Dict[str, str]:
    """
    Contrato único de rutas de salida para artefactos.
    """
    base = Path(base_dir)
    _ensure_dir(base)

    charts_dir = _ensure_dir(base / "charts")

    return {
        "out_dir": str(base),
        "charts_dir": str(charts_dir),
        "layout_paneles": str(base / "layout_paneles.png"),
    }


# =========================================================
# HELPERS NUMÉRICOS
# =========================================================

def _as_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x)) if x is not None else int(default)
    except Exception:
        return int(default)


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else float(default)
    except Exception:
        return float(default)


# =========================================================
# INFERENCIA DE PANELES (SOLO VISUAL)
# =========================================================

def inferir_n_paneles(res: Any) -> int:
    """
    Inferencia tolerante para layout (NO ingeniería).
    """

    # --- sizing
    sizing = res.get("sizing") if isinstance(res, dict) else getattr(res, "sizing", None)

    # --- objeto
    if sizing and not isinstance(sizing, dict):

        n = _as_int(getattr(sizing, "n_paneles", 0))
        if n > 0:
            return n

        n = _as_int(getattr(sizing, "n_paneles_string", 0))
        if n > 0:
            return n

    # --- dict
    if isinstance(sizing, dict):

        n = _as_int(sizing.get("n_paneles"), 0)
        if n > 0:
            return n

        n = _as_int(sizing.get("n_paneles_string"), 0)
        if n > 0:
            return n

    # --- fallback
    n = _as_int(res.get("n_paneles") if isinstance(res, dict) else getattr(res, "n_paneles", 0))
    if n > 0:
        return n

    # --- heurística por potencia
    kwp = None

    if isinstance(sizing, dict):
        kwp = sizing.get("kwp_dc") or sizing.get("kwp_recomendado")
    else:
        kwp = getattr(sizing, "kwp_dc", None) or getattr(sizing, "kwp_recomendado", None)

    if kwp is None:
        kwp = res.get("kwp_dc") if isinstance(res, dict) else getattr(res, "kwp_dc", None)

    kwp = _as_float(kwp, 0.0)
    if kwp <= 0:
        return 0

    panel_wp = None

    if isinstance(sizing, dict):
        panel_wp = sizing.get("panel_wp")
    else:
        panel_wp = getattr(sizing, "panel_wp", None)

    if panel_wp is None:
        panel_wp = res.get("panel_wp") if isinstance(res, dict) else getattr(res, "panel_wp", None)

    panel_wp = _as_float(panel_wp, 550.0)
    if panel_wp <= 0:
        panel_wp = 550.0

    return max(0, int(round((kwp * 1000.0) / panel_wp)))


# =========================================================
# PIPELINE DE ARTEFACTOS (LIMPIO)
# =========================================================

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
    Genera artefactos gráficos del proyecto FV.

    ✔ charts → generar_charts
    ✔ layout → generar_layout_paneles
    ✔ paths unificados
    """

    from reportes.generar_charts import generar_charts
    from reportes.generar_layout_paneles import generar_layout_paneles

    # --- paths base
    paths = construir_paths_salida(out_dir)

    # =====================================================
    # CHARTS (motor único)
    # =====================================================

    charts = generar_charts(
        res,
        paths["charts_dir"],
        vista_resultados=vista_resultados or {},
    )

    if charts:
        paths.update({k: str(v) for k, v in charts.items()})

    # =====================================================
    # LAYOUT DE PANELES
    # =====================================================

    n_paneles = inferir_n_paneles(res)

    if n_paneles > 0:
        generar_layout_paneles(
            n_paneles=n_paneles,
            out_path=paths["layout_paneles"],
            max_cols=max_cols,
            dos_aguas=bool(dos_aguas),
            gap_cumbrera_m=float(gap_cumbrera_m),
        )

    return paths

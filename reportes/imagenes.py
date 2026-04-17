# reportes/imagenes.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


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

    sizing = res.get("sizing") if isinstance(res, dict) else getattr(res, "sizing", None)

    if sizing and not isinstance(sizing, dict):
        n = _as_int(getattr(sizing, "n_paneles", 0))
        if n > 0:
            return n

        n = _as_int(getattr(sizing, "n_paneles_string", 0))
        if n > 0:
            return n

    if isinstance(sizing, dict):
        n = _as_int(sizing.get("n_paneles"), 0)
        if n > 0:
            return n

        n = _as_int(sizing.get("n_paneles_string"), 0)
        if n > 0:
            return n

    n = _as_int(res.get("n_paneles") if isinstance(res, dict) else getattr(res, "n_paneles", 0))
    if n > 0:
        return n

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
# GENERADOR STRING FV (IMAGEN)
# =========================================================

def generar_string_fv_imagen(strings, out_path):

    if not strings:
        return None

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    grupos = {}
    for s in strings:
        inv = getattr(s, "inversor", 1)
        mppt = getattr(s, "mppt", 1)
        grupos.setdefault((inv, mppt), []).append(s)

    fig, ax = plt.subplots(figsize=(14, 6))

    panel_w, panel_h, gap = 0.45, 0.9, 0.12
    X_MPPT = 8
    X_INV = 12

    y_base = 2
    conexiones = {}

    for (inv, mppt), grupo in grupos.items():

        s = grupo[0]
        n = s.n_series
        y = y_base

        for i in range(n):
            x = i * (panel_w + gap)

            ax.add_patch(Rectangle(
                (x, y),
                panel_w,
                panel_h,
                edgecolor="black",
                facecolor="#1e293b"
            ))

            if i < n - 1:
                ax.plot(
                    [x + panel_w, x + panel_w + gap],
                    [y + panel_h/2]*2,
                    color="black"
                )

        x_end = n * (panel_w + gap)

        y_pos = y + 0.65
        y_neg = y + 0.35

        ax.plot([x_end, X_MPPT], [y_pos, y_pos], "r", lw=2)
        ax.plot([x_end, X_MPPT], [y_neg, y_neg], "k", lw=2)

        conexiones.setdefault(inv, []).append((y_pos, y_neg))

        y_base -= 2.5

    for inv, pts in conexiones.items():
        for (y_pos, y_neg) in pts:
            ax.plot([X_MPPT, X_INV], [y_pos, y_pos], "r", lw=2)
            ax.plot([X_MPPT, X_INV], [y_neg, y_neg], "k", lw=2)
            ax.plot(X_INV, y_pos, "ro")
            ax.plot(X_INV, y_neg, "ko")

    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

    return str(out_path)


# =========================================================
# PIPELINE DE ARTEFACTOS
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

    from reportes.generar_charts import generar_charts
    from reportes.generar_layout_paneles import generar_layout_paneles

    paths = construir_paths_salida(out_dir)

    # =========================
    # CHARTS
    # =========================
    charts = generar_charts(
        res,
        paths["charts_dir"],
        vista_resultados=vista_resultados or {},
    )

    if charts:
        paths.update({k: str(v) for k, v in charts.items()})

    # =========================
    # LAYOUT PANELES
    # =========================
    n_paneles = inferir_n_paneles(res)

    if n_paneles > 0:
        generar_layout_paneles(
            n_paneles=n_paneles,
            out_path=paths["layout_paneles"],
            max_cols=max_cols,
            dos_aguas=bool(dos_aguas),
            gap_cumbrera_m=float(gap_cumbrera_m),
        )

    # =========================
    # STRING FV (NUEVO)
    # =========================
    strings = getattr(res, "strings", None)

    if strings:
        path_string = Path(paths["out_dir"]) / "string_fv.png"

        generar_string_fv_imagen(strings, path_string)

        paths["string_fv"] = str(path_string)

    return paths

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
# INFERENCIA DE PANELES
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

    return 0


# =========================================================
# PIPELINE
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
    # LAYOUT
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

    # =====================================================
    # STRING FV (INTEGRADO COMPLETO)
    # =====================================================
    try:
        strings = getattr(res, "strings", None)

        if strings:

            path_string = (Path(paths["out_dir"]) / "string_fv.png").resolve()
            path_string.parent.mkdir(parents=True, exist_ok=True)

            # ===== DIBUJO =====
            grupos = {}
            for s in strings:
                inv = getattr(s, "inversor", 1)
                mppt = getattr(s, "mppt", 1)
                grupos.setdefault((inv, mppt), []).append(s)

            fig, ax = plt.subplots(figsize=(12, 5))

            panel_w, panel_h, gap = 0.5, 1.0, 0.15
            X_MPPT, X_INV = 7.5, 10.5

            y_base = 2.0
            conexiones = []

            for (inv, mppt), grupo in sorted(grupos.items()):
                s = grupo[0]
                n = int(getattr(s, "n_series", 0) or 0)

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
                            [y + panel_h / 2]*2,
                            color="black"
                        )

                x_end = n * (panel_w + gap)

                y_pos = y + 0.7
                y_neg = y + 0.3

                ax.plot([x_end, X_MPPT], [y_pos, y_pos], "r", lw=2)
                ax.plot([x_end, X_MPPT], [y_neg, y_neg], "k", lw=2)

                conexiones.append((y_pos, y_neg))

                y_base -= 2.2

            for (y_pos, y_neg) in conexiones:
                ax.plot([X_MPPT, X_INV], [y_pos, y_pos], "r", lw=2)
                ax.plot([X_MPPT, X_INV], [y_neg, y_neg], "k", lw=2)
                ax.plot(X_INV, y_pos, "ro")
                ax.plot(X_INV, y_neg, "ko")

            ax.axis("off")
            plt.tight_layout()
            plt.savefig(path_string, dpi=200, bbox_inches="tight")
            plt.close()

            if path_string.exists():
                paths["string_fv"] = str(path_string)
            else:
                print("❌ No se creó string_fv.png")

    except Exception as e:
        print("❌ ERROR STRING FV:", e)

    return paths

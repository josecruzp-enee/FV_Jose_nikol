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
# PIPELINE PRINCIPAL
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

    # =====================================================
    # CHARTS
    # =====================================================
    charts = generar_charts(
        res,
        paths["charts_dir"],
        vista_resultados=vista_resultados or {},
    )

    if charts:
        paths.update({k: str(v) for k, v in charts.items()})

    # =====================================================
    # LAYOUT PANELES
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

    # =====================================================
    # STRING FV (ALINEADO)
    # =====================================================
    try:
        strings = res.get("strings") if isinstance(res, dict) else getattr(res, "strings", None)

        if not strings:
            print("❌ No hay strings en res")
        else:
            print(f"✔ Strings detectados: {len(strings)}")

            path_string = (Path(paths["out_dir"]) / "string_fv.png").resolve()
            path_string.parent.mkdir(parents=True, exist_ok=True)

            # ---------- AGRUPAR ----------
            grupos = {}
            for s in strings:
                inv = getattr(s, "inversor", 1)
                mppt = getattr(s, "mppt", 1)
                grupos.setdefault((inv, mppt), []).append(s)

            # ---------- CONFIG ----------
            panel_w = 0.5
            panel_h = 1.0
            gap = 0.15

            X_PANEL = 0
            X_MPPT = 8
            X_INV = 12

            fig, ax = plt.subplots(figsize=(14, 6))

            y_base = 0
            conexiones = {}

            # ---------- STRINGS ----------
            for (inv, mppt), grupo in sorted(grupos.items()):
                s = grupo[0]
                n = int(getattr(s, "n_series", 0) or 0)

                y = y_base

                for i in range(n):
                    x = X_PANEL + i * (panel_w + gap)

                    ax.add_patch(Rectangle(
                        (x, y),
                        panel_w,
                        panel_h,
                        edgecolor="#0B2E4A",
                        facecolor="#1F2A37"
                    ))

                    if i < n - 1:
                        ax.plot(
                            [x + panel_w, x + panel_w + gap],
                            [y + panel_h/2, y + panel_h/2],
                            color="black"
                        )

                x_end = X_PANEL + n * (panel_w + gap)

                y_pos = y + panel_h * 0.7
                y_neg = y + panel_h * 0.3

                ax.plot([x_end, X_MPPT], [y_pos, y_pos], "r", lw=2)
                ax.plot([x_end, X_MPPT], [y_neg, y_neg], "k", lw=2)

                ax.plot(X_MPPT, y_pos, "ro")
                ax.plot(X_MPPT, y_neg, "ko")

                ax.text(X_MPPT, y + panel_h + 0.3, f"MPPT {mppt}", ha="center")

                conexiones.setdefault(inv, []).append((y_pos, y_neg))

                y_base -= 2.5

            # ---------- INVERSOR ----------
            for inv, pts in conexiones.items():
                y_vals = [yy for (yp, yn) in pts for yy in (yp, yn)]
                y_mid = sum(y_vals) / len(y_vals)

                ax.add_patch(Rectangle(
                    (X_INV, y_mid - 1),
                    2,
                    2,
                    edgecolor="black",
                    facecolor="#eeeeee"
                ))

                ax.text(X_INV + 1, y_mid, f"INV {inv}", ha="center")

                for (y_pos, y_neg) in pts:
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

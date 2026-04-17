# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# =========================================================
# CONFIGURACIÓN VISUAL
# =========================================================

COLOR_PANEL = "#1F3A5F"
COLOR_BORDE = "#0B2E4A"
COLOR_FONDO = "#FFFFFF"


# =========================================================
# GRID DE PANELES
# =========================================================

def _dibujar_grid(n, cols, rows, x0, y0, w, h, gap, start_num=1):

    patches = []
    labels = []

    num = start_num

    for r in range(rows):
        for c in range(cols):

            if num >= start_num + n:
                break

            x = x0 + c * (w + gap)
            y = y0 + r * (h + gap)

            rect = Rectangle(
                (x, y),
                w,
                h,
                facecolor=COLOR_PANEL,
                edgecolor=COLOR_BORDE,
                linewidth=0.8
            )

            patches.append(rect)
            labels.append((x + w/2, y + h/2, str(num)))

            num += 1

    return patches, labels, num


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================

def generar_layout_paneles(
    n_paneles: int,
    out_path: str | Path,
    max_cols: int = 7,
    panel_w: float = 1.1,
    panel_h: float = 2.2,
    gap: float = 0.08,
    dos_aguas: bool = True,
    gap_cumbrera_m: float = 0.35,
):

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_facecolor(COLOR_FONDO)

    # =====================================================
    # CASO 1: UNA SOLA AGUA
    # =====================================================

    if not dos_aguas:

        cols = min(max_cols, n_paneles)
        rows = math.ceil(n_paneles / cols)

        patches, labels, _ = _dibujar_grid(
            n_paneles, cols, rows,
            0, 0,
            panel_w, panel_h,
            gap
        )

        for p in patches:
            ax.add_patch(p)

        for x, y, txt in labels:
            ax.text(x, y, txt, color="white", ha="center", va="center", fontsize=6)

        W = cols * (panel_w + gap)
        H = rows * (panel_h + gap)

    # =====================================================
    # CASO 2: DOS AGUAS (ARRIBA / ABAJO)
    # =====================================================

    else:

        n_arriba = (n_paneles + 1) // 2
        n_abajo = n_paneles // 2

        cols = min(max_cols, max(n_arriba, n_abajo))

        rows_arriba = math.ceil(n_arriba / cols)
        rows_abajo = math.ceil(n_abajo / cols)

        # alturas
        H_arriba = rows_arriba * (panel_h + gap)
        H_abajo = rows_abajo * (panel_h + gap)

        # ancho total
        W = cols * (panel_w + gap)

        # altura total
        H = H_arriba + gap_cumbrera_m + H_abajo

        off_x = 0
        off_y = 0

        # =================================================
        # ABAJO
        # =================================================
        patches_abajo, labels_abajo, next_num = _dibujar_grid(
            n_abajo,
            cols,
            rows_abajo,
            off_x,
            off_y,
            panel_w,
            panel_h,
            gap,
            start_num=1
        )

        # =================================================
        # ARRIBA
        # =================================================
        y_arriba = off_y + H_abajo + gap_cumbrera_m

        patches_arriba, labels_arriba, _ = _dibujar_grid(
            n_arriba,
            cols,
            rows_arriba,
            off_x,
            y_arriba,
            panel_w,
            panel_h,
            gap,
            start_num=next_num
        )

        # =================================================
        # DIBUJAR
        # =================================================
        for p in patches_abajo + patches_arriba:
            ax.add_patch(p)

        for x, y, txt in labels_abajo + labels_arriba:
            ax.text(x, y, txt, color="white", ha="center", va="center", fontsize=6)

        # =================================================
        # CUMBRERA (HORIZONTAL)
        # =================================================
        y_c = off_y + H_abajo

        ax.add_patch(Rectangle(
            (off_x, y_c),
            W,
            gap_cumbrera_m,
            linewidth=0.0,
            facecolor="#DDDDDD"
        ))

    # =====================================================
    # AJUSTES FINALES
    # =====================================================

    ax.set_xlim(-0.2, W + 0.2)
    ax.set_ylim(-0.2, H + 0.2)

    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return str(out_path)

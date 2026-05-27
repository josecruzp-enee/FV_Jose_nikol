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
COLOR_CUMBRERA = "#DDDDDD"


# =========================================================
# UTILIDADES
# =========================================================

def _normalizar_modo(modo_sistema) -> str:
    if modo_sistema is None:
        return ""

    return str(modo_sistema).strip().lower()


def _es_modo_por_zonas(modo_sistema=None, zonas=None) -> bool:
    modo = _normalizar_modo(modo_sistema)
    zonas = zonas or []

    return (
        modo in ["multizona", "por_zonas", "zonas", "por zonas"]
        or len(zonas) > 0
    )


def _validar_entrada(
    n_paneles: int,
    max_cols: int,
    panel_w: float,
    panel_h: float,
    gap: float,
    gap_cumbrera_m: float,
) -> None:

    if n_paneles <= 0:
        raise ValueError("n_paneles debe ser mayor que cero.")

    if max_cols <= 0:
        raise ValueError("max_cols debe ser mayor que cero.")

    if panel_w <= 0:
        raise ValueError("panel_w debe ser mayor que cero.")

    if panel_h <= 0:
        raise ValueError("panel_h debe ser mayor que cero.")

    if gap < 0:
        raise ValueError("gap no puede ser negativo.")

    if gap_cumbrera_m < 0:
        raise ValueError("gap_cumbrera_m no puede ser negativo.")


# =========================================================
# GRID DE PANELES
# =========================================================

def _dibujar_grid(
    n,
    cols,
    rows,
    x0,
    y0,
    w,
    h,
    gap,
    start_num=1,
):

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
                linewidth=0.8,
            )

            patches.append(rect)
            labels.append((x + w / 2, y + h / 2, str(num)))

            num += 1

    return patches, labels, num


def _agregar_paneles(ax, patches, labels):

    for p in patches:
        ax.add_patch(p)

    for x, y, txt in labels:
        ax.text(
            x,
            y,
            txt,
            color="white",
            ha="center",
            va="center",
            fontsize=6,
        )


# =========================================================
# LAYOUT UNA AGUA / RECTANGULAR
# =========================================================

def _generar_layout_rectangular(
    ax,
    n_paneles: int,
    max_cols: int,
    panel_w: float,
    panel_h: float,
    gap: float,
):

    cols = min(max_cols, n_paneles)
    rows = math.ceil(n_paneles / cols)

    patches, labels, _ = _dibujar_grid(
        n=n_paneles,
        cols=cols,
        rows=rows,
        x0=0,
        y0=0,
        w=panel_w,
        h=panel_h,
        gap=gap,
        start_num=1,
    )

    _agregar_paneles(ax, patches, labels)

    ancho_total = cols * panel_w + max(cols - 1, 0) * gap
    alto_total = rows * panel_h + max(rows - 1, 0) * gap

    return ancho_total, alto_total


# =========================================================
# LAYOUT DOS AGUAS
# =========================================================

def _generar_layout_dos_aguas(
    ax,
    n_paneles: int,
    max_cols: int,
    panel_w: float,
    panel_h: float,
    gap: float,
    gap_cumbrera_m: float,
):

    n_arriba = (n_paneles + 1) // 2
    n_abajo = n_paneles // 2

    cols = min(max_cols, max(n_arriba, n_abajo))

    rows_arriba = math.ceil(n_arriba / cols)
    rows_abajo = math.ceil(n_abajo / cols)

    ancho_total = cols * panel_w + max(cols - 1, 0) * gap

    alto_abajo = rows_abajo * panel_h + max(rows_abajo - 1, 0) * gap
    alto_arriba = rows_arriba * panel_h + max(rows_arriba - 1, 0) * gap

    alto_total = alto_abajo + gap_cumbrera_m + alto_arriba

    # =====================================================
    # ABAJO
    # =====================================================

    patches_abajo, labels_abajo, next_num = _dibujar_grid(
        n=n_abajo,
        cols=cols,
        rows=rows_abajo,
        x0=0,
        y0=0,
        w=panel_w,
        h=panel_h,
        gap=gap,
        start_num=1,
    )

    # =====================================================
    # ARRIBA
    # =====================================================

    y_arriba = alto_abajo + gap_cumbrera_m

    patches_arriba, labels_arriba, _ = _dibujar_grid(
        n=n_arriba,
        cols=cols,
        rows=rows_arriba,
        x0=0,
        y0=y_arriba,
        w=panel_w,
        h=panel_h,
        gap=gap,
        start_num=next_num,
    )

    _agregar_paneles(
        ax,
        patches_abajo + patches_arriba,
        labels_abajo + labels_arriba,
    )

    # =====================================================
    # CUMBRERA
    # =====================================================

    ax.add_patch(
        Rectangle(
            (0, alto_abajo),
            ancho_total,
            gap_cumbrera_m,
            linewidth=0.0,
            facecolor=COLOR_CUMBRERA,
        )
    )

    return ancho_total, alto_total


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
    modo_sistema: str | None = None,
    zonas: list | None = None,
):

    """
    Genera una imagen PNG del layout de paneles FV.

    Criterio:
    - Si el sistema NO está en modo por zonas, fuerza layout rectangular.
    - Si el sistema está en modo por zonas/multizona, permite layout dos aguas.
    - No modifica cálculos eléctricos, strings ni optimización.
    """

    _validar_entrada(
        n_paneles=n_paneles,
        max_cols=max_cols,
        panel_w=panel_w,
        panel_h=panel_h,
        gap=gap,
        gap_cumbrera_m=gap_cumbrera_m,
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    es_por_zonas = _es_modo_por_zonas(
        modo_sistema=modo_sistema,
        zonas=zonas,
    )

    if not es_por_zonas:
        dos_aguas = False

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_facecolor(COLOR_FONDO)

    if dos_aguas:
        ancho_total, alto_total = _generar_layout_dos_aguas(
            ax=ax,
            n_paneles=n_paneles,
            max_cols=max_cols,
            panel_w=panel_w,
            panel_h=panel_h,
            gap=gap,
            gap_cumbrera_m=gap_cumbrera_m,
        )
    else:
        ancho_total, alto_total = _generar_layout_rectangular(
            ax=ax,
            n_paneles=n_paneles,
            max_cols=max_cols,
            panel_w=panel_w,
            panel_h=panel_h,
            gap=gap,
        )

    ax.set_xlim(-0.2, ancho_total + 0.2)
    ax.set_ylim(-0.2, alto_total + 0.2)

    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    return str(out_path)

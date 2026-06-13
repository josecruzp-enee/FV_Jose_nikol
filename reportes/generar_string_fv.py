# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


COLOR_PANEL = "#1F2A37"
COLOR_BORDE_PANEL = "#0B2E4A"
COLOR_INV = "#EEEEEE"
COLOR_BORDE_INV = "#222222"


def generar_string_fv(strings, out_path, *_, **__):
    """
    Genera diagrama gráfico de strings FV.

    Mantiene compatibilidad:
    - recibe lista strings
    - usa atributos existentes: inversor, mppt, n_series
    - guarda imagen en out_path
    """

    if not strings:
        raise ValueError("Lista vacía")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ==============================
    # ORDENAR STRINGS
    # ==============================
    strings_ordenados = sorted(
        strings,
        key=lambda s: (
            int(getattr(s, "inversor", 1) or 1),
            int(getattr(s, "mppt", 1) or 1),
            int(getattr(s, "string_id", getattr(s, "id", 0)) or 0),
        )
    )

    # ==============================
    # CONFIG VISUAL
    # ==============================
    X_PANEL = 0.0
    X_MPPT = 8.2
    X_INV = 12.0

    panel_w = 0.36
    panel_h = 0.72
    gap = 0.10

    dy_string = 1.25
    dy_inv_extra = 0.45

    fig_h = max(5.5, len(strings_ordenados) * 0.55)
    fig, ax = plt.subplots(figsize=(14, fig_h))

    conexiones_por_inv = {}
    y_actual = 0.0

    # ==============================
    # DIBUJAR STRINGS
    # ==============================
    for idx, s in enumerate(strings_ordenados, start=1):

        inv = int(getattr(s, "inversor", 1) or 1)
        mppt = int(getattr(s, "mppt", 1) or 1)
        n = int(getattr(s, "n_series", 0) or 0)

        if n <= 0:
            continue

        # separación extra cuando cambia de inversor
        if idx > 1:
            inv_prev = int(getattr(strings_ordenados[idx - 2], "inversor", 1) or 1)
            if inv != inv_prev:
                y_actual -= dy_inv_extra

        y = -y_actual

        # etiqueta string
        ax.text(
            X_PANEL - 0.25,
            y + panel_h / 2,
            f"S{idx}",
            ha="right",
            va="center",
            fontsize=7,
            weight="bold",
        )

        # paneles en serie
        for i in range(n):
            x = X_PANEL + i * (panel_w + gap)

            ax.add_patch(
                Rectangle(
                    (x, y),
                    panel_w,
                    panel_h,
                    edgecolor=COLOR_BORDE_PANEL,
                    facecolor=COLOR_PANEL,
                    linewidth=0.8,
                )
            )

            if i < n - 1:
                ax.plot(
                    [x + panel_w, x + panel_w + gap],
                    [y + panel_h / 2, y + panel_h / 2],
                    color="black",
                    lw=0.8,
                )

        x_end = X_PANEL + n * (panel_w + gap)

        y_pos = y + panel_h * 0.68
        y_neg = y + panel_h * 0.32

        # cables DC
        ax.plot([x_end, X_MPPT], [y_pos, y_pos], color="red", lw=1.8)
        ax.plot([x_end, X_MPPT], [y_neg, y_neg], color="black", lw=1.8)

        # bornes MPPT
        ax.plot(X_MPPT, y_pos, "o", color="red", markersize=4)
        ax.plot(X_MPPT, y_neg, "o", color="black", markersize=4)

        ax.text(
            X_MPPT,
            y + panel_h + 0.18,
            f"MPPT {mppt}",
            ha="center",
            va="bottom",
            fontsize=7,
        )

        conexiones_por_inv.setdefault(inv, []).append(
            {
                "mppt": mppt,
                "y_pos": y_pos,
                "y_neg": y_neg,
                "y_mid": y + panel_h / 2,
            }
        )

        y_actual += dy_string

    # ==============================
    # DIBUJAR INVERSORES
    # ==============================
    for inv, pts in sorted(conexiones_por_inv.items()):

        y_vals = [p["y_mid"] for p in pts]
        y_top = max(y_vals) + 0.55
        y_bottom = min(y_vals) - 0.55

        inv_h = max(0.95, y_top - y_bottom)

        ax.add_patch(
            Rectangle(
                (X_INV, y_bottom),
                1.85,
                inv_h,
                edgecolor=COLOR_BORDE_INV,
                facecolor=COLOR_INV,
                linewidth=1.0,
            )
        )

        ax.text(
            X_INV + 0.925,
            (y_top + y_bottom) / 2,
            f"INV {inv}",
            ha="center",
            va="center",
            fontsize=8,
        )

        # líneas hacia inversor
        for p in pts:
            y_pos = p["y_pos"]
            y_neg = p["y_neg"]

            ax.plot([X_MPPT, X_INV], [y_pos, y_pos], color="red", lw=1.8)
            ax.plot([X_MPPT, X_INV], [y_neg, y_neg], color="black", lw=1.8)

            ax.plot(X_INV, y_pos, "o", color="red", markersize=4)
            ax.plot(X_INV, y_neg, "o", color="black", markersize=4)

    # ==============================
    # LEYENDA SIMPLE
    # ==============================
    y_min = min([p["y_neg"] for pts in conexiones_por_inv.values() for p in pts]) - 0.75

    ax.text(
        X_PANEL,
        y_min,
        "Rojo: conductor positivo (+)    Negro: conductor negativo (-)",
        ha="left",
        va="top",
        fontsize=8,
    )

    # ==============================
    # FINAL
    # ==============================
    ax.set_xlim(-0.8, X_INV + 2.4)
    ax.set_ylim(y_min - 0.6, 1.35)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=220, bbox_inches="tight", pad_inches=0.10)
    plt.close()

    return str(out_path)

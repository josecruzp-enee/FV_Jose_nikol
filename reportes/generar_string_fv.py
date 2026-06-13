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

    Compatible con atributos:
    - inversor
    - mppt
    - n_series
    """

    if not strings:
        raise ValueError("Lista vacía")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    strings_ordenados = sorted(
        strings,
        key=lambda s: (
            int(getattr(s, "inversor", 1) or 1),
            int(getattr(s, "mppt", 1) or 1),
            int(getattr(s, "string_id", getattr(s, "id", 0)) or 0),
        ),
    )

    # ==============================
    # CONFIG VISUAL
    # ==============================
    X_LABEL = -0.55
    X_PANEL = 0.0
    X_MPPT = 8.0
    X_INV = 11.8

    panel_w = 0.36
    panel_h = 0.72
    gap = 0.10

    y_step = 1.05
    y_gap_inv = 0.55

    fig_h = max(5.4, len(strings_ordenados) * 0.55)
    fig, ax = plt.subplots(figsize=(14, fig_h))

    conexiones = []
    y_actual = 0.0
    inv_anterior = None

    # ==============================
    # DIBUJAR STRINGS
    # ==============================
    for idx, s in enumerate(strings_ordenados, start=1):

        inv = int(getattr(s, "inversor", 1) or 1)
        mppt = int(getattr(s, "mppt", 1) or 1)
        n = int(getattr(s, "n_series", 0) or 0)

        if n <= 0:
            continue

        if inv_anterior is not None and inv != inv_anterior:
            y_actual -= y_gap_inv

        y = y_actual

        ax.text(
            X_LABEL,
            y + panel_h / 2,
            f"STR-{idx:02d}",
            ha="right",
            va="center",
            fontsize=7,
            weight="bold",
        )

        for i in range(n):
            x = X_PANEL + i * (panel_w + gap)

            ax.add_patch(
                Rectangle(
                    (x, y),
                    panel_w,
                    panel_h,
                    edgecolor=COLOR_BORDE_PANEL,
                    facecolor=COLOR_PANEL,
                    linewidth=0.75,
                )
            )

            if i < n - 1:
                ax.plot(
                    [x + panel_w, x + panel_w + gap],
                    [y + panel_h / 2, y + panel_h / 2],
                    color="black",
                    lw=0.7,
                )

        x_end = X_PANEL + n * (panel_w + gap)

        y_pos = y + panel_h * 0.66
        y_neg = y + panel_h * 0.34
        y_mid = y + panel_h / 2

        ax.plot([x_end, X_INV], [y_pos, y_pos], color="red", lw=1.7)
        ax.plot([x_end, X_INV], [y_neg, y_neg], color="black", lw=1.7)

        # Nodo MPPT
        ax.plot(X_MPPT, y_pos, "o", color="red", markersize=3.8)
        ax.plot(X_MPPT, y_neg, "o", color="black", markersize=3.8)

        # Etiqueta MPPT centrada entre los dos conductores
        ax.text(
            X_MPPT,
            y_mid,
            f"MPPT {mppt}",
            ha="center",
            va="center",
            fontsize=6.5,
            bbox=dict(
                boxstyle="round,pad=0.15",
                facecolor="white",
                edgecolor="none",
                alpha=0.9,
            ),
        )

        conexiones.append(
            {
                "inv": inv,
                "mppt": mppt,
                "y_pos": y_pos,
                "y_neg": y_neg,
                "y_mid": y_mid,
            }
        )

        y_actual -= y_step
        inv_anterior = inv

    # ==============================
    # DIBUJAR INVERSORES INDEPENDIENTES
    # ==============================
    for c in conexiones:
        inv = c["inv"]
        y_mid = c["y_mid"]

        inv_w = 1.75
        inv_h = 0.78
        y_inv = y_mid - inv_h / 2

        ax.add_patch(
            Rectangle(
                (X_INV, y_inv),
                inv_w,
                inv_h,
                edgecolor=COLOR_BORDE_INV,
                facecolor=COLOR_INV,
                linewidth=0.9,
            )
        )

        ax.text(
            X_INV + inv_w / 2,
            y_mid,
            f"INV {inv}",
            ha="center",
            va="center",
            fontsize=7.5,
        )

        ax.plot(X_INV, c["y_pos"], "o", color="red", markersize=3.8)
        ax.plot(X_INV, c["y_neg"], "o", color="black", markersize=3.8)

    # ==============================
    # LEYENDA
    # ==============================
    if conexiones:
        y_min = min(c["y_neg"] for c in conexiones) - 0.75
    else:
        y_min = -1.0

    ax.text(
        X_PANEL,
        y_min,
        "Rojo: conductor positivo (+)     Negro: conductor negativo (-)",
        ha="left",
        va="top",
        fontsize=8,
    )

    # ==============================
    # FINAL
    # ==============================
    ax.set_xlim(-1.0, X_INV + 2.2)
    ax.set_ylim(y_min - 0.4, 1.2)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=220, bbox_inches="tight", pad_inches=0.10)
    plt.close()

    return str(out_path)

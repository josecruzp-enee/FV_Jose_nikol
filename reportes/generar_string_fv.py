# -*- coding: utf-8 -*-
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar_string_fv(strings, out_path, *_, **__):

    if not strings:
        raise ValueError("Lista vacía")

    # ==============================
    # AGRUPAR POR MPPT
    # ==============================
    grupos = {}
    for s in strings:
        inv = getattr(s, "inversor", 1)
        mppt = getattr(s, "mppt", 1)
        grupos.setdefault((inv, mppt), []).append(s)

    # ==============================
    # LAYOUT (FIJO)
    # ==============================
    X_PANEL = 0
    X_STRING = 6
    X_MPPT = 9
    X_INV = 13

    panel_w = 0.45
    panel_h = 0.9
    gap = 0.12

    fig, ax = plt.subplots(figsize=(16, 8))

    # ==============================
    # TÍTULO
    # ==============================
    ax.text(7.5, 3.8,
            "CONFIGURACIÓN DEL GENERADOR FOTOVOLTAICO (TOPOLOGÍA REAL)",
            ha="center", fontsize=14, fontweight="bold")

    # ==============================
    # SECCIONES (LÍNEAS GUÍA)
    # ==============================
    for x in [X_STRING - 0.5, X_MPPT - 0.5, X_INV - 0.5]:
        ax.plot([x, x], [-4, 4], linestyle="--", linewidth=1, color="#9aa5b1")

    ax.text(1.5, 3, "STRING FV\n(MÓDULOS EN SERIE)", ha="center", fontsize=10)
    ax.text(7, 3, "SALIDA DC\nDEL STRING", ha="center", fontsize=10)
    ax.text(10, 3, "ENTRADA MPPT\n(DC)", ha="center", fontsize=10)
    ax.text(14.5, 3, "INVERSOR", ha="center", fontsize=10)

    y_base = 2
    conexiones = {}

    # ==============================
    # DIBUJAR STRINGS
    # ==============================
    for (inv, mppt), grupo in sorted(grupos.items()):

        s = grupo[0]
        n = s.n_series

        y = y_base

        # texto string
        ax.text(-0.5, y + 0.3,
                f"STRING {mppt}\n{n} MÓDULOS",
                ha="right", fontsize=9)

        # ==========================
        # PANELES
        # ==========================
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
                    [y + panel_h / 2] * 2,
                    color="black",
                    linewidth=1
                )

        x_end = X_PANEL + n * (panel_w + gap)

        y_pos = y + 0.7
        y_neg = y + 0.25

        # ==========================
        # CABLES STRING → MPPT
        # ==========================
        ax.plot([x_end, X_MPPT], [y_pos, y_pos], color="red", linewidth=2)
        ax.plot([x_end, X_MPPT], [y_neg, y_neg], color="black", linewidth=2)

        # terminal MPPT
        ax.add_patch(Rectangle((X_MPPT - 0.2, y_pos - 0.1), 0.4, 0.4,
                               edgecolor="red", facecolor="white"))
        ax.text(X_MPPT, y_pos + 0.05, "+", ha="center", color="red")

        ax.add_patch(Rectangle((X_MPPT - 0.2, y_neg - 0.1), 0.4, 0.4,
                               edgecolor="black", facecolor="white"))
        ax.text(X_MPPT, y_neg + 0.05, "–", ha="center")

        ax.text(X_MPPT, y + 1.1, f"MPPT {mppt}", ha="center", fontsize=9)

        conexiones.setdefault(inv, []).append((y_pos, y_neg))

        y_base -= 2.5

    # ==============================
    # INVERSOR
    # ==============================
    for inv, pts in conexiones.items():

        y_vals = [y for p in pts for y in p]
        y_mid = sum(y_vals) / len(y_vals)

        ax.add_patch(Rectangle(
            (X_INV, y_mid - 1.5),
            2.5,
            3,
            edgecolor="black",
            facecolor="#eeeeee",
            linewidth=1.5
        ))

        ax.text(X_INV + 1.25, y_mid,
                f"INVERSOR {inv}",
                ha="center", va="center", fontsize=10)

        # conexiones
        for (y_pos, y_neg) in pts:

            ax.plot([X_MPPT + 0.2, X_INV], [y_pos, y_pos],
                    color="red", linewidth=2)
            ax.plot([X_MPPT + 0.2, X_INV], [y_neg, y_neg],
                    color="black", linewidth=2)

            ax.plot(X_INV, y_pos, "ro")
            ax.plot(X_INV, y_neg, "ko")

    # ==============================
    # FINAL
    # ==============================
    ax.set_xlim(-1, 17)
    ax.set_ylim(-4, 4)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

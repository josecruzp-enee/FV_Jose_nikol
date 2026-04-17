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
    # CONFIG
    # ==============================
    X_PANEL = 0
    X_MPPT = 9
    X_INV = 13

    panel_w = 0.45
    panel_h = 0.9
    gap = 0.12

    fig, ax = plt.subplots(figsize=(16, 8))

    # ==============================
    # SECCIONES
    # ==============================
    for x in [X_MPPT - 0.5, X_INV - 0.5]:
        ax.plot([x, x], [-4, 4], linestyle="--", linewidth=0.8, color="#cbd5e1")

    y_base = 2
    conexiones = {}

    # ==============================
    # STRINGS
    # ==============================
    for (inv, mppt), grupo in sorted(grupos.items()):

        s = grupo[0]
        n = s.n_series
        y = y_base

        ax.text(-0.5, y + 0.3,
                f"STRING {mppt}\n{n} MÓDULOS",
                ha="right", fontsize=9)

        # paneles
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
                    [y + panel_h / 2]*2,
                    color="#2b2b2b",
                    linewidth=1
                )

        x_end = X_PANEL + n * (panel_w + gap)

        # separación + y -
        y_pos = y + 0.65
        y_neg = y + 0.35

        # cables a MPPT
        ax.plot([x_end, X_MPPT], [y_pos, y_pos], "r", lw=2)
        ax.plot([x_end, X_MPPT], [y_neg, y_neg], "k", lw=2)

        # bornes MPPT
        ax.plot(X_MPPT, y_pos, "ro")
        ax.plot(X_MPPT, y_neg, "ko")

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

        # conexiones escalonadas
        for i, (y_pos, y_neg) in enumerate(pts):

            x_mid = X_INV - 0.8
            offset = 0.5 + i * 0.3

            # positivo
            ax.plot([X_MPPT, x_mid], [y_pos, y_pos], "r", lw=2)
            ax.plot([x_mid, x_mid], [y_pos, y_pos - offset], "r", lw=2)
            ax.plot([x_mid, X_INV], [y_pos - offset, y_pos - offset], "r", lw=2)
            ax.plot(X_INV, y_pos - offset, "ro")

            # negativo
            ax.plot([X_MPPT, x_mid], [y_neg, y_neg], "k", lw=2)
            ax.plot([x_mid, x_mid], [y_neg, y_neg - offset], "k", lw=2)
            ax.plot([x_mid, X_INV], [y_neg - offset, y_neg - offset], "k", lw=2)
            ax.plot(X_INV, y_neg - offset, "ko")

    # ==============================
    # FINAL
    # ==============================
    ax.set_xlim(-1, 17)
    ax.set_ylim(-4, 4)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

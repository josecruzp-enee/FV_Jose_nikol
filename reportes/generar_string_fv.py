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
        key = (getattr(s, "inversor", 1), getattr(s, "mppt", 1))
        grupos.setdefault(key, []).append(s)

    # ==============================
    # CONFIG
    # ==============================
    X_PANEL = 0
    X_MPPT = 8
    X_INV = 12

    panel_w = 0.4
    panel_h = 0.8
    gap = 0.1

    fig, ax = plt.subplots(figsize=(14, 6))

    y_base = 2
    conexiones = {}

    # ==============================
    # DIBUJAR STRINGS
    # ==============================
    for (inv, mppt), grupo in sorted(grupos.items()):

        s = grupo[0]
        n = s.n_series
        y = y_base

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
                    [y + panel_h/2]*2,
                    color="black"
                )

        x_end = X_PANEL + n * (panel_w + gap)

        # polos
        y_pos = y + 0.6
        y_neg = y + 0.3

        # cables hacia MPPT
        ax.plot([x_end, X_MPPT], [y_pos, y_pos], "r", lw=2)
        ax.plot([x_end, X_MPPT], [y_neg, y_neg], "k", lw=2)

        # bornes MPPT
        ax.plot(X_MPPT, y_pos, "ro")
        ax.plot(X_MPPT, y_neg, "ko")

        ax.text(X_MPPT, y + 1, f"MPPT {mppt}", ha="center")

        conexiones.setdefault(inv, []).append((y_pos, y_neg))

        y_base -= 2

    # ==============================
    # INVERSOR
    # ==============================
    for inv, pts in conexiones.items():

        y_vals = [y for p in pts for y in p]
        y_mid = sum(y_vals) / len(y_vals)

        # caja inversor
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

    # ==============================
    # FINAL
    # ==============================
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

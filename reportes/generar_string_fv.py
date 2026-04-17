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
    # POSICIONES FIJAS (CLAVE)
    # ==============================
    X_PANEL = 0
    X_STRING_END = 6
    X_MPPT = 8
    X_INV = 12

    panel_w = 0.4
    panel_h = 0.8
    gap = 0.1

    fig, ax = plt.subplots(figsize=(14, 6))

    y_base = 0
    conexiones = {}

    # ==============================
    # DIBUJAR STRINGS
    # ==============================
    for (inv, mppt), grupo in sorted(grupos.items()):

        y = y_base

        for s in grupo:

            n = s.n_series

            # PANEL
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

            # PUNTO DE SALIDA (REAL)
            y_pos = y + 0.55
            y_neg = y + 0.25

            # terminal string
            ax.plot(X_STRING_END, y_pos, "ro")
            ax.plot(X_STRING_END, y_neg, "ko")

            # cable hasta MPPT
            ax.plot([X_STRING_END, X_MPPT], [y_pos, y_pos], "r", lw=2)
            ax.plot([X_STRING_END, X_MPPT], [y_neg, y_neg], "k", lw=2)

        # ==============================
        # MPPT (BORNE REAL)
        # ==============================
        ax.plot(X_MPPT, y_pos, "ro")
        ax.plot(X_MPPT, y_neg, "ko")

        ax.text(X_MPPT, y + 0.8, f"MPPT {mppt}", ha="center")

        conexiones.setdefault(inv, []).append((y_pos, y_neg))

        y_base -= 2

    # ==============================
    # INVERSOR (BORNERA REAL)
    # ==============================
    for inv, pts in conexiones.items():

        y_vals = [y for p in pts for y in p]
        y_mid = sum(y_vals) / len(y_vals)

        # caja
        ax.add_patch(Rectangle(
            (X_INV, y_mid - 1),
            2,
            2,
            edgecolor="black",
            facecolor="#eeeeee"
        ))

        ax.text(X_INV + 1, y_mid, f"INV {inv}", ha="center", va="center")

        # entradas
        for (y_pos, y_neg) in pts:

            # terminal inversor
            ax.plot(X_INV, y_pos, "ro")
            ax.plot(X_INV, y_neg, "ko")

            # conexión limpia horizontal
            ax.plot([X_MPPT, X_INV], [y_pos, y_pos], "r", lw=2)
            ax.plot([X_MPPT, X_INV], [y_neg, y_neg], "k", lw=2)

    # ==============================
    # FINAL
    # ==============================
    ax.set_title("Configuración FV (Topología Correcta)")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

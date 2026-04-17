# -*- coding: utf-8 -*-
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar_string_fv(strings, out_path, *_, **__):

    if not strings:
        raise ValueError("Lista vacía")

    # =====================================================
    # AGRUPAR POR MPPT
    # =====================================================
    grupos = {}

    for s in strings:
        key = (getattr(s, "inversor", 1), getattr(s, "mppt", 1))
        grupos.setdefault(key, []).append(s)

    # =====================================================
    # CONFIGURACIÓN DE COLUMNAS (CLAVE)
    # =====================================================
    X_PANELES = 0
    X_SALIDA = 6
    X_MPPT   = 8
    X_INV    = 11

    panel_w = 0.4
    panel_h = 0.8
    gap = 0.1

    fig, ax = plt.subplots(figsize=(14, 6))

    y_base = 0
    conexiones_inv = {}

    # =====================================================
    # DIBUJAR STRINGS
    # =====================================================
    for (inv, mppt), grupo in sorted(grupos.items()):

        y_string = y_base

        for s in grupo:

            n = s.n_series

            # -------------------------
            # PANELES
            # -------------------------
            for i in range(n):
                x = X_PANELES + i * (panel_w + gap)

                ax.add_patch(Rectangle(
                    (x, y_string),
                    panel_w,
                    panel_h,
                    edgecolor="#0B2E4A",
                    facecolor="#1F2A37"
                ))

                if i < n - 1:
                    ax.plot(
                        [x + panel_w, x + panel_w + gap],
                        [y_string + panel_h/2]*2,
                        color="black"
                    )

            x_end = X_PANELES + n * (panel_w + gap)

            # -------------------------
            # SALIDA (+ y -)
            # -------------------------
            y_pos = y_string + 0.55
            y_neg = y_string + 0.25

            ax.plot([x_end, X_SALIDA], [y_pos, y_pos], color="red", lw=2)
            ax.plot([x_end, X_SALIDA], [y_neg, y_neg], color="black", lw=2)

        # -------------------------
        # MPPT
        # -------------------------
        ax.text(X_MPPT, y_string + 0.5, f"MPPT {mppt}", fontsize=10)

        # línea hacia MPPT
        ax.plot([X_SALIDA, X_MPPT], [y_pos, y_pos], color="red", lw=2)
        ax.plot([X_SALIDA, X_MPPT], [y_neg, y_neg], color="black", lw=2)

        conexiones_inv.setdefault(inv, []).append((y_pos, y_neg))

        y_base -= 2

    # =====================================================
    # INVERSOR
    # =====================================================
    for inv, puntos in conexiones_inv.items():

        y_vals = [y for p in puntos for y in p]
        y_mid = sum(y_vals)/len(y_vals)

        # caja inversor
        ax.add_patch(Rectangle(
            (X_INV, y_mid - 1),
            2,
            2,
            edgecolor="black",
            facecolor="#eeeeee"
        ))

        ax.text(X_INV + 1, y_mid, f"INV {inv}", ha="center", va="center")

        # conexiones
        for (y_pos, y_neg) in puntos:

            ax.plot([X_MPPT, X_INV], [y_pos, y_pos], color="red", lw=2)
            ax.plot([X_MPPT, X_INV], [y_neg, y_neg], color="black", lw=2)

            ax.plot(X_INV, y_pos, "ro")
            ax.plot(X_INV, y_neg, "ko")

    # =====================================================
    # FINAL
    # =====================================================
    ax.set_title("Configuración FV (Topología Correcta)")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

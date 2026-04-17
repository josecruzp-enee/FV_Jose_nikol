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
    # CONFIGURACIÓN VISUAL
    # ==============================
    panel_w = 0.5
    panel_h = 1.0
    gap = 0.15

    X_PANEL = 0
    X_STRING = 7
    X_MPPT = 9
    X_INV = 13

    fig, ax = plt.subplots(figsize=(16, 6))

    y_base = 0
    conexiones = {}

    # ==============================
    # DIBUJAR STRINGS
    # ==============================
    for (inv, mppt), grupo in sorted(grupos.items()):

        for idx, s in enumerate(grupo):

            n = s.n_series
            y = y_base - idx * 2.5

            y_pos = y + 0.7
            y_neg = y + 0.3

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
                    facecolor="#1F2A37",
                    linewidth=1
                ))

                # conexión serie
                if i < n - 1:
                    ax.plot(
                        [x + panel_w, x + panel_w + gap],
                        [y + panel_h/2, y + panel_h/2],
                        color="black",
                        linewidth=1
                    )

            x_end = X_PANEL + n * (panel_w + gap)

            # ==========================
            # SALIDA DEL STRING (+ / -)
            # ==========================
            ax.plot([x_end, X_STRING], [y_pos, y_pos], color="red", linewidth=2)
            ax.plot([x_end, X_STRING], [y_neg, y_neg], color="black", linewidth=2)

            # terminal
            ax.plot(X_STRING, y_pos, "ro")
            ax.plot(X_STRING, y_neg, "ko")

        # ==============================
        # MPPT
        # ==============================
        y_mppt_pos = y_pos
        y_mppt_neg = y_neg

        ax.plot(X_MPPT, y_mppt_pos, "ro")
        ax.plot(X_MPPT, y_mppt_neg, "ko")

        ax.text(X_MPPT, y_mppt_pos + 0.6, f"MPPT {mppt}", ha="center")

        conexiones.setdefault(inv, []).append((y_mppt_pos, y_mppt_neg))

        y_base -= 4

    # ==============================
    # INVERSOR
    # ==============================
    for inv, pts in conexiones.items():

        y_vals = [y for p in pts for y in p]
        y_mid = sum(y_vals) / len(y_vals)

        # caja inversor
        ax.add_patch(Rectangle(
            (X_INV, y_mid - 1.2),
            2.5,
            2.4,
            edgecolor="black",
            facecolor="#eeeeee",
            linewidth=1.5
        ))

        ax.text(X_INV + 1.25, y_mid, f"INV {inv}", ha="center", va="center", fontsize=10)

        # ==============================
        # CONEXIONES LIMPIAS (SIN CRUCES)
        # ==============================
        for (y_pos, y_neg) in pts:

            # + (rojo)
            ax.plot([X_MPPT, X_INV], [y_pos, y_pos], color="red", linewidth=2)
            ax.plot(X_INV, y_pos, "ro")

            # - (negro)
            ax.plot([X_MPPT, X_INV], [y_neg, y_neg], color="black", linewidth=2)
            ax.plot(X_INV, y_neg, "ko")

    # ==============================
    # FINAL
    # ==============================
    ax.set_title("Configuración FV (Topología Profesional)")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

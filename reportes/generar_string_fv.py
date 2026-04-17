# -*- coding: utf-8 -*-
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch


def generar_string_fv(strings, out_path):

    # =========================
    # CONFIGURACIÓN BASE
    # =========================
    fig, ax = plt.subplots(figsize=(18, 10))

    # posiciones horizontales (como tu lámina)
    X_PANEL = 0
    X_SALIDA = 6
    X_MPPT = 9
    X_INV = 13

    panel_w = 0.4
    panel_h = 0.8
    gap = 0.1

    # =========================
    # TÍTULO
    # =========================
    ax.text(8, 5,
        "CONFIGURACIÓN DEL GENERADOR FOTOVOLTAICO (TOPOLOGÍA REAL)",
        ha="center", fontsize=16, fontweight="bold")

    # =========================
    # SECCIONES
    # =========================
    for x in [X_SALIDA-0.5, X_MPPT-0.5, X_INV-0.5]:
        ax.plot([x, x], [-5, 5], "--", color="#94a3b8")

    ax.text(2, 4, "STRING FV\n(MÓDULOS EN SERIE)", ha="center", fontsize=11)
    ax.text(7, 4, "SALIDA DC\nDEL STRING", ha="center", fontsize=11)
    ax.text(10, 4, "ENTRADA MPPT\n(DC)", ha="center", fontsize=11)
    ax.text(14.5, 4, "INVERSOR", ha="center", fontsize=11)

    # =========================
    # FUNCION DIBUJO STRING
    # =========================
    def dibujar_string(y, n_mod, label):

        ax.text(-0.5, y+0.3, f"{label}\n{n_mod} MÓDULOS",
                ha="right", fontsize=10)

        # módulos
        for i in range(n_mod):
            x = X_PANEL + i * (panel_w + gap)

            ax.add_patch(Rectangle(
                (x, y),
                panel_w,
                panel_h,
                edgecolor="#1e293b",
                facecolor="#1e293b"
            ))

            if i < n_mod - 1:
                ax.plot(
                    [x + panel_w, x + panel_w + gap],
                    [y + panel_h/2]*2,
                    color="#64748b"
                )

        x_end = X_PANEL + n_mod * (panel_w + gap)

        y_pos = y + 0.6
        y_neg = y + 0.25

        # cables
        ax.plot([x_end, X_MPPT], [y_pos, y_pos], color="red", lw=2)
        ax.plot([x_end, X_MPPT], [y_neg, y_neg], color="black", lw=2)

        return y_pos, y_neg

    # =========================
    # STRINGS
    # =========================
    y1 = 2
    y2 = -1.5

    pos1, neg1 = dibujar_string(y1, 10, "STRING 1")
    pos2, neg2 = dibujar_string(y2, 8, "STRING 2")

    # =========================
    # MPPT
    # =========================
    def dibujar_mppt(x, y_pos, y_neg, label):

        ax.text(x, y_pos+0.7, label, ha="center", fontsize=10)

        # + 
        ax.add_patch(Rectangle(
            (x-0.2, y_pos-0.2),
            0.4, 0.4,
            edgecolor="red", facecolor="white", linewidth=1.5
        ))
        ax.text(x, y_pos, "+", ha="center", color="red")

        # -
        ax.add_patch(Rectangle(
            (x-0.2, y_neg-0.2),
            0.4, 0.4,
            edgecolor="black", facecolor="white", linewidth=1.5
        ))
        ax.text(x, y_neg, "–", ha="center")

    dibujar_mppt(X_MPPT, pos1, neg1, "MPPT 1")
    dibujar_mppt(X_MPPT, pos2, neg2, "MPPT 2")

    # =========================
    # INVERSOR
    # =========================
    inv_y = 0.3

    ax.add_patch(FancyBboxPatch(
        (X_INV, inv_y-2),
        3,
        4,
        boxstyle="round,pad=0.3",
        edgecolor="#1e293b",
        facecolor="#eeeeee",
        linewidth=1.5
    ))

    ax.text(X_INV+1.5, inv_y+1.5, "INVERSOR 1", ha="center", fontsize=11)

    # conexiones finales
    def conectar(y_pos, y_neg):

        ax.plot([X_MPPT+0.2, X_INV], [y_pos, y_pos], "r", lw=2)
        ax.plot([X_MPPT+0.2, X_INV], [y_neg, y_neg], "k", lw=2)

        ax.plot(X_INV, y_pos, "ro")
        ax.plot(X_INV, y_neg, "ko")

    conectar(pos1, neg1)
    conectar(pos2, neg2)

    # =========================
    # LEYENDA
    # =========================
    ax.text(-0.5, -4.5, "LEYENDA", fontsize=11, fontweight="bold")

    ax.add_patch(Rectangle((-0.5, -5.2), 0.4, 0.4, color="#1e293b"))
    ax.text(0, -5, "Módulo Fotovoltaico", fontsize=9)

    ax.plot([2,3], [-5,-5], color="red", lw=2)
    ax.text(3.2, -5, "Conductor Positivo (+)", fontsize=9)

    ax.plot([2,3], [-5.5,-5.5], color="black", lw=2)
    ax.text(3.2, -5.5, "Conductor Negativo (-)", fontsize=9)

    # =========================
    # NOTA
    # =========================
    ax.text(12, -4,
        "NOTA:\nCada MPPT trabaja de forma independiente.\nNo existe conexión entre MPPT.",
        fontsize=9)

    # =========================
    # FINAL
    # =========================
    ax.set_xlim(-1, 18)
    ax.set_ylim(-6, 6)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()

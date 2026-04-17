from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar_string_fv(strings, out_path, *_, **__):

    if not strings:
        raise ValueError("Lista de strings vacía")

    # =====================================================
    # AGRUPAR POR (INVERSOR, MPPT)
    # =====================================================
    grupos = {}

    for s in strings:
        inv = getattr(s, "inversor", 1)
        mppt = getattr(s, "mppt", 1)

        grupos.setdefault((inv, mppt), []).append(s)

    # =====================================================
    # PARÁMETROS
    # =====================================================
    panel_w = 0.5
    panel_h = 1.0
    gap = 0.2
    v_gap = 2.0

    fig = plt.figure(figsize=(14, 4 + len(grupos)))
    ax = fig.add_subplot(111)

    y_global = 0
    conexiones_inv = {}

    # =====================================================
    # DIBUJAR STRINGS
    # =====================================================
    for (inv, mppt), grupo in sorted(grupos.items()):

        y_strings = []

        for idx, s in enumerate(grupo):

            n_series = s.n_series
            y_offset = y_global - idx * v_gap
            y_center = y_offset + panel_h / 2
            y_strings.append(y_center)

            # -------------------------------
            # MÓDULOS EN SERIE
            # -------------------------------
            for i in range(n_series):

                x = i * (panel_w + gap)

                rect = Rectangle(
                    (x, y_offset),
                    panel_w,
                    panel_h,
                    edgecolor="#0B2E4A",
                    facecolor="#1F2A37",
                    linewidth=1
                )
                ax.add_patch(rect)

                if i < n_series - 1:
                    ax.plot(
                        [x + panel_w, x + panel_w + gap],
                        [y_center, y_center],
                        color="black",
                        linewidth=1
                    )

            width = n_series * panel_w + (n_series - 1) * gap

            # -------------------------------
            # SALIDA DEL STRING (+ y -)
            # -------------------------------
            ax.plot([width, width + 0.8], [y_center, y_center], color="red", linewidth=2)
            ax.plot([width, width + 0.8], [y_center - 0.15, y_center - 0.15], color="black", linewidth=2)

        # =====================================================
        # MPPT
        # =====================================================
        x_mppt = width + 0.8

        if len(grupo) == 1:
            # 🔥 CASO REAL: 1 STRING → 1 MPPT
            y_mppt = y_strings[0]

        else:
            # 🔥 SOLO SI HAY PARALELO
            y_min = min(y_strings)
            y_max = max(y_strings)

            # bus vertical
            ax.plot([x_mppt, x_mppt], [y_min, y_max], color="red", linewidth=3)

            y_mppt = (y_min + y_max) / 2

        # salida MPPT
        ax.plot([x_mppt, x_mppt + 1], [y_mppt, y_mppt], color="red", linewidth=2)
        ax.plot([x_mppt, x_mppt + 1], [y_mppt - 0.15, y_mppt - 0.15], color="black", linewidth=2)

        conexiones_inv.setdefault(inv, []).append((x_mppt + 1, y_mppt))

        # etiqueta MPPT
        ax.text(
            x_mppt,
            y_mppt + 0.4,
            f"MPPT {mppt}",
            ha="center",
            fontsize=8
        )

        y_global -= (len(grupo) * v_gap + 1)

    # =====================================================
    # INVERSOR (GEOMETRÍA LIMPIA)
    # =====================================================
    for inv, puntos in conexiones_inv.items():

        # ordenar de arriba hacia abajo
        puntos = sorted(puntos, key=lambda x: -x[1])

        x_inv = max(p[0] for p in puntos) + 2.0

        y_vals = [p[1] for p in puntos]
        y_top = max(y_vals)
        y_bottom = min(y_vals)
        y_inv = (y_top + y_bottom) / 2

        # -------------------------------
        # INVERSOR
        # -------------------------------
        rect = Rectangle(
            (x_inv, y_inv - 0.8),
            1.8,
            1.6,
            edgecolor="black",
            facecolor="#eeeeee",
            linewidth=1.5
        )
        ax.add_patch(rect)

        ax.text(
            x_inv + 0.9,
            y_inv,
            f"INV {inv}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold"
        )

        # -------------------------------
        # CONEXIONES DIRECTAS (SIN CRUCES)
        # -------------------------------
        for (x, y) in puntos:

            # positivo
            ax.plot([x, x_inv], [y, y], color="red", linewidth=2)

            # negativo
            ax.plot([x, x_inv], [y - 0.15, y - 0.15], color="black", linewidth=2)

            # bornes
            ax.plot(x_inv, y, "o", color="red", markersize=5)
            ax.plot(x_inv, y - 0.15, "o", color="black", markersize=5)

            ax.text(x_inv + 0.1, y, "+", fontsize=8)
            ax.text(x_inv + 0.1, y - 0.15, "–", fontsize=8)

    # =====================================================
    # FINAL
    # =====================================================
    ax.set_title("Configuración del Generador Fotovoltaico (Topología Real)")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=200, bbox_inches="tight")
    plt.close()

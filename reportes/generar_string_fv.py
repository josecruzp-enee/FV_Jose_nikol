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
    # STRINGS
    # =====================================================
    for (inv, mppt) in sorted(grupos.keys()):

        grupo = grupos[(inv, mppt)]
        y_strings = []

        for idx, s in enumerate(grupo):

            n_series = s.n_series
            y_offset = y_global - idx * v_gap
            y_center = y_offset + panel_h / 2
            y_strings.append(y_center)

            # módulos
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

            # 🔴 POSITIVO
            ax.plot([width, width + 0.8], [y_center, y_center], color="red", linewidth=2)

            # ⚫ NEGATIVO
            ax.plot([width, width + 0.8], [y_center - 0.25, y_center - 0.25], color="black", linewidth=2)

        # =====================================================
        # MPPT (PARALELO SI APLICA)
        # =====================================================
        x_mppt = width + 0.8

        if len(grupo) > 1:
            y_min = min(y_strings)
            y_max = max(y_strings)

            # buses
            ax.plot([x_mppt, x_mppt], [y_min, y_max], color="red", linewidth=3)
            ax.plot([x_mppt, x_mppt], [y_min - 0.25, y_max - 0.25], color="black", linewidth=3)

            y_mppt = (y_min + y_max) / 2
        else:
            y_mppt = y_strings[0]

        # salida MPPT (+ y -)
        ax.plot([x_mppt, x_mppt + 1], [y_mppt, y_mppt], color="red", linewidth=2)
        ax.plot([x_mppt, x_mppt + 1], [y_mppt - 0.25, y_mppt - 0.25], color="black", linewidth=2)

        conexiones_inv.setdefault(inv, []).append((x_mppt + 1, y_mppt))

        # etiqueta
        ax.text(x_mppt, y_mppt + 0.5, f"MPPT {mppt}", ha="center", fontsize=8)

        y_global -= (len(grupo) * v_gap + 1)

    # =====================================================
    # INVERSORES
    # =====================================================
    for inv, puntos in conexiones_inv.items():

        x_inv = max(p[0] for p in puntos) + 1.5
        y_vals = [p[1] for p in puntos]

        y_min = min(y_vals)
        y_max = max(y_vals)
        y_inv = (y_min + y_max) / 2

        # inversor
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

        # =====================================================
        # ENTRADAS MPPT (+ y - SEPARADAS)
        # =====================================================
        n = len(puntos)

        for i, (x, y) in enumerate(puntos):

            y_entry = y_inv + ((i - (n - 1) / 2) * 0.5)

            # positivo
            ax.plot([x, x_inv], [y, y], color="red", linewidth=2)
            ax.plot([x_inv, x_inv], [y, y_entry], color="red", linewidth=2)
            ax.plot([x_inv, x_inv + 0.2], [y_entry, y_entry], color="red", linewidth=2)

            # negativo
            y_neg = y - 0.25
            y_entry_neg = y_entry - 0.25

            ax.plot([x, x_inv], [y_neg, y_neg], color="black", linewidth=2)
            ax.plot([x_inv, x_inv], [y_neg, y_entry_neg], color="black", linewidth=2)
            ax.plot([x_inv, x_inv + 0.2], [y_entry_neg, y_entry_neg], color="black", linewidth=2)

            # símbolos
            ax.text(x_inv + 0.25, y_entry, "+", color="red", fontsize=9)
            ax.text(x_inv + 0.25, y_entry_neg, "–", color="black", fontsize=9)

    # =====================================================
    # FINAL
    # =====================================================
    ax.set_title("Configuración del Generador Fotovoltaico (Topología Real)")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=200, bbox_inches="tight")
    plt.close()

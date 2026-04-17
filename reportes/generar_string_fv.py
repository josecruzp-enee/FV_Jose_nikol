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
        # MPPT (PARALELO SOLO SI APLICA)
        # =====================================================
        x_mppt = width + 0.8

        if len(grupo) > 1:
            y_min = min(y_strings)
            y_max = max(y_strings)

            # buses + y -
            ax.plot([x_mppt, x_mppt], [y_min, y_max], color="red", linewidth=3)
            ax.plot([x_mppt, x_mppt], [y_min - 0.25, y_max - 0.25], color="black", linewidth=3)

            y_mppt = (y_min + y_max) / 2
        else:
            y_mppt = y_strings[0]

        # salida MPPT (+ y -)
        ax.plot([x_mppt, x_mppt + 1], [y_mppt, y_mppt], color="red", linewidth=2)
        ax.plot([x_mppt, x_mppt + 1], [y_mppt - 0.25, y_mppt - 0.25], color="black", linewidth=2)

        # 🔥 GUARDAR + Y -
        conexiones_inv.setdefault(inv, []).append({
            "x": x_mppt + 1,
            "y_pos": y_mppt,
            "y_neg": y_mppt - 0.25
        })

        # etiqueta
        ax.text(
            x_mppt,
            y_mppt + 0.5,
            f"MPPT {mppt}",
            ha="center",
            fontsize=8
        )

        y_global -= (len(grupo) * v_gap + 1)

    # =====================================================
    # INVERSORES
    # =====================================================
    for inv, puntos in conexiones_inv.items():

        x_inv = max(p["x"] for p in puntos) + 1.5
        y_vals = [p["y_pos"] for p in puntos]

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
        # ENTRADAS MPPT (SEPARADAS)
        # =====================================================
        n = len(puntos)

        for i, p in enumerate(puntos):

            x = p["x"]
            y_pos = p["y_pos"]
            y_neg = p["y_neg"]

            y_entry = y_inv + ((i - (n - 1) / 2) * 0.5)
            y_entry_neg = y_entry - 0.25

            # positivo
            ax.plot([x, x_inv], [y_pos, y_pos], color="red", linewidth=2)
            ax.plot([x_inv, x_inv], [y_pos, y_entry], color="red", linewidth=2)
            ax.plot([x_inv, x_inv + 0.25], [y_entry, y_entry], color="red", linewidth=2)

            # negativo
            ax.plot([x, x_inv], [y_neg, y_neg], color="black", linewidth=2)
            ax.plot([x_inv, x_inv], [y_neg, y_entry_neg], color="black", linewidth=2)
            ax.plot([x_inv, x_inv + 0.25], [y_entry_neg, y_entry_neg], color="black", linewidth=2)

            # bornes
            ax.plot(x_inv + 0.3, y_entry, marker='o', color='red', markersize=4)
            ax.plot(x_inv + 0.3, y_entry_neg, marker='o', color='black', markersize=4)

            ax.text(x_inv + 0.4, y_entry, "+", color="red", fontsize=9)
            ax.text(x_inv + 0.4, y_entry_neg, "–", color="black", fontsize=9)

    # =====================================================
    # FINAL
    # =====================================================
    ax.set_title("Configuración del Generador Fotovoltaico (Topología Real)")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=200, bbox_inches="tight")
    plt.close()

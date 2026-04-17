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

        key = (inv, mppt)
        grupos.setdefault(key, []).append(s)

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

            # salida string
            ax.plot(
                [width, width + 0.8],
                [y_center, y_center],
                color="red",
                linewidth=2
            )

        # =====================================================
        # MPPT (PARALELO SOLO SI APLICA)
        # =====================================================
        x_mppt = width + 0.8

        if len(grupo) > 1:
            y_min = min(y_strings)
            y_max = max(y_strings)

            # bus vertical (paralelo real)
            ax.plot(
                [x_mppt, x_mppt],
                [y_min, y_max],
                color="red",
                linewidth=3
            )

            y_mppt = (y_min + y_max) / 2
        else:
            y_mppt = y_strings[0]

        # salida MPPT
        ax.plot(
            [x_mppt, x_mppt + 1],
            [y_mppt, y_mppt],
            color="red",
            linewidth=2
        )

        conexiones_inv.setdefault(inv, []).append((x_mppt + 1, y_mppt))

        # etiqueta
        ax.text(
            x_mppt,
            y_mppt + 0.4,
            f"MPPT {mppt}",
            ha="center",
            fontsize=8
        )

        y_global -= (len(grupo) * v_gap + 1)

    # =====================================================
    # INVERSORES (ENTRADAS SEPARADAS ✔)
    # =====================================================
    for inv, puntos in conexiones_inv.items():

        x_inv = max(p[0] for p in puntos) + 1.5
        y_vals = [p[1] for p in puntos]

        y_min = min(y_vals)
        y_max = max(y_vals)
        y_inv = (y_min + y_max) / 2

        # inversor
        rect = Rectangle(
            (x_inv, y_inv - 0.6),
            1.5,
            1.2,
            edgecolor="black",
            facecolor="#eeeeee",
            linewidth=1.5
        )
        ax.add_patch(rect)

        ax.text(
            x_inv + 0.75,
            y_inv,
            f"INV {inv}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold"
        )

        # 🔥 CLAVE: entradas independientes (NO unión)
        for (x, y) in puntos:
            ax.plot(
                [x, x_inv],
                [y, y],   # ← AQUÍ ESTÁ LA CORRECCIÓN REAL
                color="red",
                linewidth=2
            )

    # =====================================================
    # FINAL
    # =====================================================
    ax.set_title("Configuración del Generador Fotovoltaico (Topología Real)")
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(str(out_path), dpi=200, bbox_inches="tight")
    plt.close()

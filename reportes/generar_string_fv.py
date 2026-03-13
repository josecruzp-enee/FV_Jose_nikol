from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar_string_fv(
    n_series: int,
    out_path,
    *,
    n_strings: int = 1
):

    panel_w = 0.5
    panel_h = 1.0
    gap = 0.2
    v_gap = 1.8

    width = n_series * (panel_w + gap)

    fig = plt.figure(figsize=(12, 3 + n_strings))
    ax = fig.add_subplot(111)

    # ============================
    # Dibujar strings
    # ============================

    for s in range(n_strings):

        y_offset = -s * v_gap

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

            # conexión serie
            if i < n_series - 1:

                x1 = x + panel_w
                x2 = x + panel_w + gap

                ax.plot(
                    [x1, x2],
                    [y_offset + panel_h / 2, y_offset + panel_h / 2],
                    color="black",
                    linewidth=1
                )

        # línea hacia bus
        ax.plot(
            [width, width + 1],
            [y_offset + panel_h / 2, y_offset + panel_h / 2],
            color="red",
            linewidth=2
        )

    # ============================
    # Bus DC
    # ============================

    bus_x = width + 1

    ax.plot(
        [bus_x, bus_x],
        [panel_h / 2, -(n_strings - 1) * v_gap + panel_h / 2],
        color="red",
        linewidth=3
    )

    # ============================
    # Inversor
    # ============================

    inv_x = bus_x + 1.5
    inv_y = -(n_strings - 1) * v_gap / 2

    rect = Rectangle(
        (inv_x, inv_y),
        1.2,
        1.2,
        edgecolor="black",
        facecolor="#eeeeee"
    )

    ax.add_patch(rect)

    ax.text(
        inv_x + 0.6,
        inv_y + 0.6,
        "INV",
        ha="center",
        va="center",
        fontsize=10
    )

    # conexión bus → inversor

    ax.plot(
        [bus_x, inv_x],
        [inv_y + 0.6, inv_y + 0.6],
        color="red",
        linewidth=2
    )

    # ============================
    # Texto
    # ============================

    ax.set_title(
        f"Configuración del String Fotovoltaico\n"
        f"{n_series} módulos por string • {n_strings} strings en paralelo",
        fontsize=12
    )

    # ============================
    # Ajustes
    # ============================

    ax.axis("off")

    ax.set_xlim(-0.5, inv_x + 2)
    ax.set_ylim(-(n_strings) * v_gap, 2)

    plt.tight_layout()

    plt.savefig(out_path, dpi=200, bbox_inches="tight")

    plt.close()

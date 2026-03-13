# reportes/generar_string_fv.py
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar_string_fv(
    n_series: int,
    out_path,
    *,
    n_strings: int = 1,
    panel_w: float = 0.6,
    panel_h: float = 1.2,
    gap: float = 0.25,
    titulo: str = "Configuración del String Fotovoltaico"
):
    """
    Dibuja:
      - 1 string si n_strings == 1
      - 2 strings en paralelo (representativos) si n_strings >= 2
    """

    n_series = int(n_series)
    n_strings = int(n_strings)

    if n_series <= 0:
        raise ValueError("n_series debe ser > 0")

    # tamaño del canvas
    width = n_series * (panel_w + gap)
    height = panel_h * (2 if n_strings >= 2 else 1) + 2

    fig = plt.figure(figsize=(10, 3 if n_strings == 1 else 4), dpi=170)
    ax = fig.add_subplot(111)

    ax.set_title(titulo)
    ax.set_aspect("equal")

    ax.set_xlim(-0.5, width + 0.5)
    ax.set_ylim(-0.5, height)

    # posiciones Y de los strings
    y_top = panel_h + 0.9
    y_bottom = 0.6

    def draw_string(y):

        for i in range(n_series):

            x = i * (panel_w + gap)

            # panel
            ax.add_patch(
                Rectangle(
                    (x, y),
                    panel_w,
                    panel_h,
                    linewidth=0.8,
                    edgecolor="#0B2E4A",
                    facecolor="#1F2A37",
                )
            )

            # polaridad
            ax.text(x + panel_w * 0.25, y - 0.12, "+", color="red", fontsize=8, ha="center")
            ax.text(x + panel_w * 0.75, y - 0.12, "-", color="black", fontsize=8, ha="center")

            # conexión serie
            if i < n_series - 1:
                x2 = x + panel_w
                x3 = (i + 1) * (panel_w + gap)

                ax.plot(
                    [x2, x3],
                    [y + panel_h / 2, y + panel_h / 2],
                    color="black",
                    linewidth=1.2
                )

    # === dibujar strings ===

    if n_strings == 1:

        draw_string(y_bottom)

        ax.text(
            width / 2,
            y_bottom + panel_h + 0.4,
            f"{n_series} módulos conectados en serie",
            ha="center",
            fontsize=10
        )

    else:

        draw_string(y_top)
        draw_string(y_bottom)

        # bus paralelo
        x_bus = width + 0.1

        ax.plot(
            [x_bus, x_bus],
            [y_bottom + panel_h / 2, y_top + panel_h / 2],
            color="black",
            linewidth=1.5
        )

        ax.text(
            width / 2,
            y_top + panel_h + 0.4,
            f"{n_series} módulos por string · {n_strings} strings en paralelo",
            ha="center",
            fontsize=10
        )

    ax.axis("off")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

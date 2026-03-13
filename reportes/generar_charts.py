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
):

    width = n_series * (panel_w + gap)

    fig = plt.figure(figsize=(10, 3 if n_strings == 1 else 4), dpi=170)
    ax = fig.add_subplot(111)

    ax.set_title("Configuración del String Fotovoltaico")

    ax.set_xlim(-0.5, width + 1)
    ax.set_ylim(-0.5, 3)

    def draw_string(y):

        for i in range(n_series):

            x = i * (panel_w + gap)

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

            ax.text(x + panel_w * 0.25, y - 0.12, "+", color="red", fontsize=8, ha="center")
            ax.text(x + panel_w * 0.75, y - 0.12, "-", color="black", fontsize=8, ha="center")

            if i < n_series - 1:
                x2 = x + panel_w
                x3 = (i + 1) * (panel_w + gap)

                ax.plot(
                    [x2, x3],
                    [y + panel_h / 2, y + panel_h / 2],
                    color="black",
                    linewidth=1.2
                )

    # ===== 1 string =====
    if n_strings == 1:

        draw_string(0.8)

        ax.text(
            width / 2,
            2.2,
            f"String FV representativo\n{n_series} módulos conectados en serie",
            ha="center",
            fontsize=10
        )

    # ===== paralelo =====
    else:

        y1 = 1.6
        y2 = 0.4

        draw_string(y1)
        draw_string(y2)

        x_bus = width + 0.15

        ax.plot([x_bus, x_bus], [y2 + panel_h / 2, y1 + panel_h / 2], linewidth=2)

        ax.text(
            width / 2,
            2.6,
            f"{n_series} módulos por string · {n_strings} strings en paralelo",
            ha="center",
            fontsize=10
        )

    ax.axis("off")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

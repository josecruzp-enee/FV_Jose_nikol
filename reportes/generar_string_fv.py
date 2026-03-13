# reportes/generar_string_fv.py

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar_string_fv(
    n_series: int,
    out_path: str,
    *,
    panel_w: float = 1.2,
    panel_h: float = 2.2,
    gap: float = 0.35,
    titulo: str = "String FV representativo"
):

    n = int(n_series)
    if n <= 0:
        raise ValueError("n_series debe ser > 0")

    W = n * panel_w + (n - 1) * gap
    H = panel_h + 1.2

    fig = plt.figure(figsize=(10, 3), dpi=170)
    ax = fig.add_subplot(111)

    ax.set_title(titulo)
    ax.set_aspect("equal")

    ax.set_xlim(-0.5, W + 0.5)
    ax.set_ylim(-0.5, H)

    y = 0.6

    for i in range(n):

        x = i * (panel_w + gap)

        # panel (igual estilo que layout)
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
        ax.text(
            x + panel_w * 0.25,
            y - 0.15,
            "+",
            fontsize=10,
            color="red",
            ha="center"
        )

        ax.text(
            x + panel_w * 0.75,
            y - 0.15,
            "−",
            fontsize=10,
            color="black",
            ha="center"
        )

        # cable serie
        if i < n - 1:
            x2 = x + panel_w
            x3 = (i + 1) * (panel_w + gap)

            ax.plot(
                [x2, x3],
                [y + panel_h / 2, y + panel_h / 2],
                color="black",
                linewidth=1.4
            )

    ax.text(
        W / 2,
        panel_h + 0.9,
        f"{n} módulos conectados en serie",
        ha="center",
        fontsize=10
    )

    ax.axis("off")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")

    plt.close(fig)

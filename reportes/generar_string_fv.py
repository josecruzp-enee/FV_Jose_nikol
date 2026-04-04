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

    # ============================
    # VALIDACIÓN
    # ============================
    if n_series <= 0 or n_strings <= 0:
        raise ValueError("n_series y n_strings deben ser mayores a 0")

    # ============================
    # PARÁMETROS
    # ============================

    panel_w = 0.5
    panel_h = 1.0

    gap = 0.2
    v_gap = 1.8

    # 🔥 FIX 1: ancho correcto
    width = n_series * panel_w + (n_series - 1) * gap

    fig = plt.figure(figsize=(12, 3 + n_strings * 0.6))
    ax = fig.add_subplot(111)

    y_strings = []

    # ============================
    # DIBUJO STRINGS
    # ============================

    for s in range(n_strings):

        y_offset = -s * v_gap
        y_center = y_offset + panel_h / 2
        y_strings.append(y_center)

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
                    [y_center, y_center],
                    color="black",
                    linewidth=1
                )

        # conexión string → bus
        ax.plot(
            [width, width + 1],
            [y_center, y_center],
            color="red",
            linewidth=2
        )

    # ============================
    # BUS DC
    # ============================

    bus_x = width + 1

    y_min = min(y_strings)
    y_max = max(y_strings)

    # 🔥 FIX 2: evitar colapso con 1 string
    if n_strings == 1:
        y_min -= 0.5
        y_max += 0.5

    ax.plot(
        [bus_x, bus_x],
        [y_min, y_max],
        color="red",
        linewidth=3
    )

    # ============================
    # INVERSOR
    # ============================

    inv_x = bus_x + 1.5
    y_mid = (y_min + y_max) / 2
    inv_y = y_mid - 0.6

    rect = Rectangle(
        (inv_x, inv_y),
        1.2,
        1.2,
        edgecolor="black",
        facecolor="#eeeeee",
        linewidth=1.5
    )

    ax.add_patch(rect)

    ax.text(
        inv_x + 0.6,
        inv_y + 0.6,
        "INV",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold"
    )

    # conexión bus → inversor
    ax.plot(
        [bus_x, inv_x],
        [y_mid, y_mid],
        color="red",
        linewidth=2
    )

    # ============================
    # TEXTO
    # ============================

    ax.set_title(
        f"Configuración del Generador Fotovoltaico\n"
        f"{n_series} módulos por string • {n_strings} strings en paralelo",
        fontsize=12
    )

    # ============================
    # AJUSTES
    # ============================

    ax.axis("off")

    ax.set_xlim(-0.5, inv_x + 2)
    ax.set_ylim(y_min - 1, y_max + 1.5)

    plt.tight_layout()

    # 🔥 FIX 3: asegurar guardado correcto
    plt.savefig(str(out_path), dpi=200, bbox_inches="tight")

    plt.close()

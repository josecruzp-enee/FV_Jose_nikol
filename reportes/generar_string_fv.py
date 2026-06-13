# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


COLOR_PANEL = "#1F2A37"
COLOR_BORDE_PANEL = "#0B2E4A"
COLOR_INV = "#EEEEEE"
COLOR_MPPT = "#FFFFFF"
COLOR_BORDE = "#222222"


def generar_string_fv(strings, out_path, *_, **__):
    """
    Diagrama de strings FV con inversores y MPPT visibles.

    Compatible con:
    - s.inversor
    - s.mppt
    - s.n_series
    """

    if not strings:
        raise ValueError("Lista vacía")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    strings_ordenados = sorted(
        strings,
        key=lambda s: (
            int(getattr(s, "inversor", 1) or 1),
            int(getattr(s, "mppt", 1) or 1),
            int(getattr(s, "string_id", getattr(s, "id", 0)) or 0),
        ),
    )

    # Agrupar por inversor
    grupos_inv = {}
    for idx, s in enumerate(strings_ordenados, start=1):
        inv = int(getattr(s, "inversor", 1) or 1)
        mppt = int(getattr(s, "mppt", 1) or 1)
        n_series = int(getattr(s, "n_series", 0) or 0)

        grupos_inv.setdefault(inv, []).append({
            "idx": idx,
            "mppt": mppt,
            "n_series": n_series,
        })

    # Configuración visual
    X_LABEL = -0.75
    X_PANEL = 0.0
    X_INV = 11.4

    panel_w = 0.34
    panel_h = 0.66
    gap = 0.09

    inv_w = 2.55
    mppt_w = 1.10
    mppt_h = 0.42

    y_step = 0.95
    y_gap_inv = 0.70

    total_strings = len(strings_ordenados)
    fig_h = max(5.8, total_strings * 0.62)

    fig, ax = plt.subplots(figsize=(14, fig_h))

    y_actual = 0.0
    conexiones = []

    # Resumen superior
    n_inversores = len(grupos_inv)
    n_mppt = len(set((inv, item["mppt"]) for inv, items in grupos_inv.items() for item in items))

    ax.text(
        X_PANEL,
        1.10,
        f"{total_strings} strings FV  |  {n_inversores} inversores  |  {n_mppt} MPPT utilizados",
        ha="left",
        va="bottom",
        fontsize=8.5,
        weight="bold",
    )

    # Dibujar por inversor
    for inv, items in sorted(grupos_inv.items()):

        y_inicio_inv = y_actual
        y_centros = []

        for item in items:
            idx = item["idx"]
            mppt = item["mppt"]
            n = item["n_series"]

            if n <= 0:
                continue

            y = y_actual
            y_mid = y + panel_h / 2
            y_pos = y + panel_h * 0.66
            y_neg = y + panel_h * 0.34

            y_centros.append(y_mid)

            # Etiqueta string
            ax.text(
                X_LABEL,
                y_mid,
                f"STR-{idx:02d}",
                ha="right",
                va="center",
                fontsize=7,
                weight="bold",
            )

            # Paneles
            for i in range(n):
                x = X_PANEL + i * (panel_w + gap)

                ax.add_patch(
                    Rectangle(
                        (x, y),
                        panel_w,
                        panel_h,
                        edgecolor=COLOR_BORDE_PANEL,
                        facecolor=COLOR_PANEL,
                        linewidth=0.75,
                    )
                )

                if i < n - 1:
                    ax.plot(
                        [x + panel_w, x + panel_w + gap],
                        [y_mid, y_mid],
                        color="black",
                        lw=0.7,
                    )

            x_end = X_PANEL + n * (panel_w + gap)

            conexiones.append({
                "inv": inv,
                "mppt": mppt,
                "x_end": x_end,
                "y_pos": y_pos,
                "y_neg": y_neg,
                "y_mid": y_mid,
            })

            y_actual -= y_step

        if not y_centros:
            continue

        y_top = max(y_centros) + 0.55
        y_bottom = min(y_centros) - 0.55
        inv_h = y_top - y_bottom

        # Caja inversor principal
        ax.add_patch(
            Rectangle(
                (X_INV, y_bottom),
                inv_w,
                inv_h,
                edgecolor=COLOR_BORDE,
                facecolor=COLOR_INV,
                linewidth=1.0,
            )
        )

        ax.text(
            X_INV + inv_w - 0.35,
            (y_top + y_bottom) / 2,
            f"INV {inv}",
            ha="center",
            va="center",
            fontsize=8,
            weight="bold",
            rotation=90 if inv_h > 1.2 else 0,
        )

        # MPPT dentro del inversor
        items_inv = [c for c in conexiones if c["inv"] == inv]

        for c in items_inv:
            mppt_x = X_INV + 0.18
            mppt_y = c["y_mid"] - mppt_h / 2

            ax.add_patch(
                Rectangle(
                    (mppt_x, mppt_y),
                    mppt_w,
                    mppt_h,
                    edgecolor="#555555",
                    facecolor=COLOR_MPPT,
                    linewidth=0.75,
                )
            )

            ax.text(
                mppt_x + mppt_w / 2,
                c["y_mid"],
                f"MPPT {c['mppt']}",
                ha="center",
                va="center",
                fontsize=6.6,
            )

            # Conductores hasta el MPPT
            ax.plot(
                [c["x_end"], mppt_x],
                [c["y_pos"], c["y_pos"]],
                color="red",
                lw=1.7,
            )
            ax.plot(
                [c["x_end"], mppt_x],
                [c["y_neg"], c["y_neg"]],
                color="black",
                lw=1.7,
            )

            # Bornes en MPPT
            ax.plot(mppt_x, c["y_pos"], "o", color="red", markersize=3.5)
            ax.plot(mppt_x, c["y_neg"], "o", color="black", markersize=3.5)

        # Separación entre inversores
        y_actual -= y_gap_inv

    # Leyenda
    if conexiones:
        y_min = min(c["y_neg"] for c in conexiones) - 0.75
    else:
        y_min = -1.0

    ax.text(
        X_PANEL,
        y_min,
        "Rojo: conductor positivo (+)     Negro: conductor negativo (-)",
        ha="left",
        va="top",
        fontsize=7.5,
    )

    ax.set_xlim(-1.2, X_INV + inv_w + 0.35)
    ax.set_ylim(y_min - 0.35, 1.45)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=220, bbox_inches="tight", pad_inches=0.10)
    plt.close()

    return str(out_path)

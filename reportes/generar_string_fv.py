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
COLOR_BORDE_INV = "#222222"


def generar_string_fv(strings, out_path, *_, **__):
    """
    Genera diagrama gráfico limpio de strings FV.

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

    n_strings = len(strings_ordenados)
    n_inversores = len(set(int(getattr(s, "inversor", 1) or 1) for s in strings_ordenados))
    n_mppt_usados = len(set(
        (
            int(getattr(s, "inversor", 1) or 1),
            int(getattr(s, "mppt", 1) or 1),
        )
        for s in strings_ordenados
    ))

    # ==============================
    # CONFIG VISUAL
    # ==============================
    X_LABEL = -0.75
    X_PANEL = 0.0
    X_RESUMEN = 0.0
    X_CABLE_FIN = 11.20
    X_INV = 11.60

    panel_w = 0.36
    panel_h = 0.70
    gap = 0.10

    inv_w = 1.70
    inv_h = 0.62

    y_step = 1.05
    y_gap_inv = 0.55

    fig_h = max(5.8, n_strings * 0.58)
    fig, ax = plt.subplots(figsize=(14, fig_h))

    conexiones = []
    y_actual = 0.0
    inv_anterior = None

    # ==============================
    # RESUMEN SUPERIOR
    # ==============================
    ax.text(
        X_RESUMEN,
        1.15,
        f"{n_strings} strings FV  |  {n_inversores} inversores  |  {n_mppt_usados} MPPT utilizados",
        ha="left",
        va="bottom",
        fontsize=8.5,
        weight="bold",
    )

    # ==============================
    # DIBUJAR STRINGS
    # ==============================
    for idx, s in enumerate(strings_ordenados, start=1):

        inv = int(getattr(s, "inversor", 1) or 1)
        mppt = int(getattr(s, "mppt", 1) or 1)
        n = int(getattr(s, "n_series", 0) or 0)

        if n <= 0:
            continue

        if inv_anterior is not None and inv != inv_anterior:
            y_actual -= y_gap_inv

        y = y_actual

        ax.text(
            X_LABEL,
            y + panel_h / 2,
            f"STR-{idx:02d}",
            ha="right",
            va="center",
            fontsize=7,
            weight="bold",
        )

        # Paneles en serie
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
                    [y + panel_h / 2, y + panel_h / 2],
                    color="black",
                    lw=0.7,
                )

        x_end = X_PANEL + n * (panel_w + gap)

        y_pos = y + panel_h * 0.66
        y_neg = y + panel_h * 0.34
        y_mid = y + panel_h / 2

        # Conductores DC
        ax.plot([x_end, X_CABLE_FIN], [y_pos, y_pos], color="red", lw=1.75)
        ax.plot([x_end, X_CABLE_FIN], [y_neg, y_neg], color="black", lw=1.75)

        # Etiqueta técnica limpia
        ax.text(
            X_CABLE_FIN - 0.20,
            y_mid,
            f"MPPT {mppt}",
            ha="right",
            va="center",
            fontsize=6.8,
            bbox=dict(
                boxstyle="round,pad=0.12",
                facecolor="white",
                edgecolor="#CCCCCC",
                linewidth=0.3,
                alpha=0.95,
            ),
        )

        conexiones.append(
            {
                "idx": idx,
                "inv": inv,
                "mppt": mppt,
                "y_pos": y_pos,
                "y_neg": y_neg,
                "y_mid": y_mid,
            }
        )

        y_actual -= y_step
        inv_anterior = inv

    # ==============================
    # DIBUJAR INVERSORES
    # ==============================
    for c in conexiones:
        inv = c["inv"]
        y_mid = c["y_mid"]
        y_inv = y_mid - inv_h / 2

        ax.add_patch(
            Rectangle(
                (X_INV, y_inv),
                inv_w,
                inv_h,
                edgecolor=COLOR_BORDE_INV,
                facecolor=COLOR_INV,
                linewidth=0.9,
            )
        )

        ax.text(
            X_INV + inv_w / 2,
            y_mid,
            f"INV {inv}",
            ha="center",
            va="center",
            fontsize=7.5,
        )

        # Bornes del inversor
        ax.plot(X_INV, c["y_pos"], "o", color="red", markersize=3.5)
        ax.plot(X_INV, c["y_neg"], "o", color="black", markersize=3.5)

    # ==============================
    # SEPARADORES SUAVES ENTRE INVERSORES
    # ==============================
    inversores = sorted(set(c["inv"] for c in conexiones))

    for inv in inversores:
        ys = [c["y_mid"] for c in conexiones if c["inv"] == inv]
        if not ys:
            continue

        y_grupo = min(ys) - 0.48

        ax.plot(
            [X_PANEL - 0.15, X_INV + inv_w],
            [y_grupo, y_grupo],
            color="#DDDDDD",
            lw=0.5,
            linestyle="--",
        )

    # ==============================
    # LEYENDA
    # ==============================
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

    # ==============================
    # FINAL
    # ==============================
    ax.set_xlim(-1.2, X_INV + inv_w + 0.6)
    ax.set_ylim(y_min - 0.35, 1.55)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=220, bbox_inches="tight", pad_inches=0.10)
    plt.close()

    return str(out_path)

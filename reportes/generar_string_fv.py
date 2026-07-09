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


def leer(obj, campo, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(campo, default)
    return getattr(obj, campo, default)


def to_int(valor, default=0):
    try:
        return int(valor)
    except Exception:
        return default


def generar_string_fv(strings, out_path, *_, **__):
    """
    Diagrama de strings FV con inversores y MPPT visibles.

    Compatible con:
    - s.inversor
    - s.mppt
    - s.n_series
    - s.string_id
    - dict u objeto
    """

    if not strings:
        raise ValueError("Lista vacía")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    strings_ordenados = sorted(
        strings,
        key=lambda s: (
            to_int(leer(s, "inversor", 1), 1),
            to_int(leer(s, "mppt", 1), 1),
            to_int(leer(s, "string_id", leer(s, "id", 0)), 0),
        ),
    )

    grupos_inv = {}

    for idx_visual, s in enumerate(strings_ordenados, start=1):
        inv = to_int(leer(s, "inversor", 1), 1)
        mppt = to_int(leer(s, "mppt", 1), 1)
        n_series = to_int(leer(s, "n_series", 0), 0)

        string_id = leer(s, "string_id", leer(s, "id", idx_visual))
        string_id = to_int(string_id, idx_visual)

        grupos_inv.setdefault(inv, []).append(
            {
                "string_id": string_id,
                "idx_visual": idx_visual,
                "mppt": mppt,
                "n_series": n_series,
            }
        )

    # =====================================================
    # CONFIG VISUAL
    # =====================================================
    X_LABEL = -0.85
    X_PANEL = 0.0
    X_INV = 11.4

    panel_w = 0.34
    panel_h = 0.66
    gap = 0.09

    inv_w = 2.75
    mppt_w = 1.45
    mppt_h = 0.56

    y_step = 0.98
    y_gap_inv = 0.78

    total_strings = len(strings_ordenados)
    total_strings_validos = sum(
        1
        for items in grupos_inv.values()
        for item in items
        if item["n_series"] > 0
    )

    fig_h = max(6.0, total_strings_validos * 0.66)

    fig, ax = plt.subplots(figsize=(14.5, fig_h))

    y_actual = 0.0
    conexiones = []

    n_inversores = len(grupos_inv)
    n_mppt = len(
        set(
            (inv, item["mppt"])
            for inv, items in grupos_inv.items()
            for item in items
            if item["n_series"] > 0
        )
    )

    # =====================================================
    # RESUMEN SUPERIOR
    # =====================================================
    ax.text(
        X_PANEL,
        1.18,
        f"{total_strings_validos} strings FV   |   {n_inversores} inversores   |   {n_mppt} MPPT utilizados",
        ha="left",
        va="bottom",
        fontsize=10,
        weight="bold",
    )

    # =====================================================
    # DIBUJAR STRINGS
    # =====================================================
    for inv, items in sorted(grupos_inv.items()):

        y_centros_inv = []
        conexiones_inv = []

        for item in items:
            string_id = item["string_id"]
            mppt = item["mppt"]
            n = item["n_series"]

            if n <= 0:
                continue

            y = y_actual
            y_mid = y + panel_h / 2
            y_pos = y + panel_h * 0.66
            y_neg = y + panel_h * 0.34

            y_centros_inv.append(y_mid)

            # Etiqueta string real
            ax.text(
                X_LABEL,
                y_mid,
                f"STR-{string_id:02d}",
                ha="right",
                va="center",
                fontsize=8.5,
                weight="bold",
            )

            # Texto de serie
            ax.text(
                X_PANEL,
                y - 0.10,
                f"{n}S",
                ha="left",
                va="top",
                fontsize=7.5,
                color="#444444",
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
                        linewidth=0.80,
                    )
                )

                if i < n - 1:
                    ax.plot(
                        [x + panel_w, x + panel_w + gap],
                        [y_mid, y_mid],
                        color="black",
                        lw=0.75,
                    )

            x_end = X_PANEL + n * (panel_w + gap)

            conexion = {
                "inv": inv,
                "mppt": mppt,
                "string_id": string_id,
                "x_end": x_end,
                "y_pos": y_pos,
                "y_neg": y_neg,
                "y_mid": y_mid,
            }

            conexiones.append(conexion)
            conexiones_inv.append(conexion)

            y_actual -= y_step

        if not y_centros_inv:
            continue

        y_top = max(y_centros_inv) + 0.62
        y_bottom = min(y_centros_inv) - 0.62
        inv_h = y_top - y_bottom

        # =================================================
        # CAJA INVERSOR
        # =================================================
        ax.add_patch(
            Rectangle(
                (X_INV, y_bottom),
                inv_w,
                inv_h,
                edgecolor=COLOR_BORDE,
                facecolor=COLOR_INV,
                linewidth=1.05,
            )
        )

        ax.text(
            X_INV + inv_w - 0.45,
            (y_top + y_bottom) / 2,
            f"INV {inv}",
            ha="center",
            va="center",
            fontsize=9,
            weight="bold",
        )

        # =================================================
        # MPPT AGRUPADOS
        # =================================================
        grupos_mppt = {}

        for c in conexiones_inv:
            grupos_mppt.setdefault(c["mppt"], []).append(c)

        for mppt, conns in sorted(grupos_mppt.items()):

            y_mppt = sum(c["y_mid"] for c in conns) / len(conns)

            mppt_x = X_INV + 0.18
            mppt_y = y_mppt - mppt_h / 2

            ax.add_patch(
                Rectangle(
                    (mppt_x, mppt_y),
                    mppt_w,
                    mppt_h,
                    edgecolor="#555555",
                    facecolor=COLOR_MPPT,
                    linewidth=0.85,
                )
            )

            texto_mppt = f"MPPT {mppt}"

            if len(conns) > 1:
                texto_mppt += f"\n{len(conns)} strings"

            ax.text(
                mppt_x + mppt_w / 2,
                y_mppt,
                texto_mppt,
                ha="center",
                va="center",
                fontsize=7.8,
                weight="bold",
                linespacing=0.95,
            )

            # Bornes principales del MPPT
            y_borne_pos = y_mppt + mppt_h * 0.23
            y_borne_neg = y_mppt - mppt_h * 0.23

            ax.plot(mppt_x, y_borne_pos, "o", color="red", markersize=4)
            ax.plot(mppt_x, y_borne_neg, "o", color="black", markersize=4)

            for c in conns:

                # Positivo
                ax.plot(
                    [c["x_end"], mppt_x],
                    [c["y_pos"], y_borne_pos],
                    color="red",
                    lw=1.55,
                )

                # Negativo
                ax.plot(
                    [c["x_end"], mppt_x],
                    [c["y_neg"], y_borne_neg],
                    color="black",
                    lw=1.55,
                )

                # Bornes del string
                ax.plot(c["x_end"], c["y_pos"], "o", color="red", markersize=3)
                ax.plot(c["x_end"], c["y_neg"], "o", color="black", markersize=3)

        y_actual -= y_gap_inv

    # =====================================================
    # LEYENDA
    # =====================================================
    if conexiones:
        y_min = min(c["y_neg"] for c in conexiones) - 0.85
    else:
        y_min = -1.0

    ax.text(
        X_PANEL,
        y_min,
        "Rojo: conductor positivo (+)     Negro: conductor negativo (-)",
        ha="left",
        va="top",
        fontsize=8.5,
    )

    # =====================================================
    # FINAL
    # =====================================================
    ax.set_xlim(-1.35, X_INV + inv_w + 0.35)
    ax.set_ylim(y_min - 0.40, 1.55)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=220, bbox_inches="tight", pad_inches=0.10)
    plt.close()

    return str(out_path)

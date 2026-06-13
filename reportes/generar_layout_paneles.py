# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


COLOR_PANEL = "#1F3A5F"
COLOR_BORDE = "#0B2E4A"
COLOR_FONDO = "#FFFFFF"
COLOR_CUMBRERA = "#DDDDDD"
COLOR_CAJA = "#F7F7F7"
COLOR_LINEA = "#222222"


def _validar_entrada(n_paneles, max_cols, panel_w, panel_h, gap, gap_cumbrera_m):
    if n_paneles <= 0:
        raise ValueError("n_paneles debe ser mayor que cero.")
    if max_cols <= 0:
        raise ValueError("max_cols debe ser mayor que cero.")
    if panel_w <= 0:
        raise ValueError("panel_w debe ser mayor que cero.")
    if panel_h <= 0:
        raise ValueError("panel_h debe ser mayor que cero.")
    if gap < 0:
        raise ValueError("gap no puede ser negativo.")
    if gap_cumbrera_m < 0:
        raise ValueError("gap_cumbrera_m no puede ser negativo.")


def _dibujar_grid(n, cols, rows, x0, y0, w, h, gap, start_num=1):
    patches = []
    labels = []
    num = start_num

    for r in range(rows):
        for c in range(cols):
            if num >= start_num + n:
                break

            x = x0 + c * (w + gap)
            y = y0 + r * (h + gap)

            patches.append(
                Rectangle(
                    (x, y),
                    w,
                    h,
                    facecolor=COLOR_PANEL,
                    edgecolor=COLOR_BORDE,
                    linewidth=0.7,
                )
            )

            labels.append((x + w / 2, y + h / 2, str(num)))
            num += 1

    return patches, labels, num



def _agregar_paneles(ax, patches, labels):
    for p in patches:
        ax.add_patch(p)

    for x, y, txt in labels:
        ax.text(
            x,
            y,
            txt,
            color="white",
            ha="center",
            va="center",
            fontsize=6.4,
        )


def _generar_layout_rectangular(ax, n_paneles, max_cols, panel_w, panel_h, gap):
    cols = min(max_cols, n_paneles)
    rows = math.ceil(n_paneles / cols)

    patches, labels, _ = _dibujar_grid(
        n=n_paneles,
        cols=cols,
        rows=rows,
        x0=0,
        y0=0,
        w=panel_w,
        h=panel_h,
        gap=gap,
        start_num=1,
    )

    _agregar_paneles(ax, patches, labels)

    ancho_total = cols * panel_w + max(cols - 1, 0) * gap
    alto_total = rows * panel_h + max(rows - 1, 0) * gap

    return ancho_total, alto_total, cols, rows


def _generar_layout_por_strings(
    ax,
    n_paneles,
    n_strings,
    paneles_por_string,
    panel_w,
    panel_h,
    gap,
    separacion_sombra_m=0.0,
):
    """
    Genera layout físico orientativo agrupado por strings.
    """

    n_strings = int(n_strings or 0)
    paneles_por_string = int(paneles_por_string or 0)
    separacion_sombra_m = float(separacion_sombra_m or 0.0)

    if n_strings <= 0 or paneles_por_string <= 0:
        raise ValueError("n_strings y paneles_por_string deben ser mayores que cero.")

    cols = paneles_por_string
    rows = n_strings
    total_dibujado = min(n_paneles, n_strings * paneles_por_string)

    gap_col = gap
    gap_fila = max(gap, separacion_sombra_m)

    ancho_total_preview = cols * panel_w + max(cols - 1, 0) * gap_col

    patches = []
    labels = []
    num = 1

    for r in range(rows):
        y = (rows - 1 - r) * (panel_h + gap_fila)

        ax.text(
            -0.35,
            y + panel_h / 2,
            f"STR-{r + 1:02d}",
            ha="right",
            va="center",
            fontsize=7,
            weight="bold",
            color=COLOR_LINEA,
        )

        for c in range(cols):
            if num > total_dibujado:
                break

            x = c * (panel_w + gap_col)

            patches.append(
                Rectangle(
                    (x, y),
                    panel_w,
                    panel_h,
                    facecolor=COLOR_PANEL,
                    edgecolor=COLOR_BORDE,
                    linewidth=0.7,
                )
            )

            labels.append((x + panel_w / 2, y + panel_h / 2, str(num)))
            num += 1

        # Cota visual de separación por sombra entre esta fila y la siguiente
        if separacion_sombra_m > gap and r < rows - 1:
            y_sup = y - gap_fila
            y_inf = y

            y_mid = (y_sup + y_inf) / 2
            x_cota_sombra = ancho_total_preview + 0.55

            ax.plot(
                [0, ancho_total_preview],
                [y_mid, y_mid],
                linestyle="--",
                linewidth=0.45,
                color="#888888",
            )

            ax.annotate(
                "",
                xy=(x_cota_sombra, y_sup),
                xytext=(x_cota_sombra, y_inf),
                arrowprops=dict(
                    arrowstyle="<->",
                    linewidth=0.8,
                    color="#555555",
                ),
            )

            ax.text(
                x_cota_sombra + 0.15,
                y_mid,
                f"Sombra: {separacion_sombra_m:.2f} m",
                fontsize=6,
                va="center",
                ha="left",
                color="#555555",
            )

    _agregar_paneles(ax, patches, labels)

    ancho_total = cols * panel_w + max(cols - 1, 0) * gap_col
    alto_total = rows * panel_h + max(rows - 1, 0) * gap_fila

    # Solo título arriba. Las separaciones se pondrán abajo en generar_layout_paneles().
    ax.text(
        ancho_total / 2,
        alto_total + 1.15,
        f"Distribución física por strings: {n_strings} strings × {paneles_por_string} módulos",
        ha="center",
        va="bottom",
        fontsize=9,
        weight="bold",
        color=COLOR_LINEA,
    )

    return ancho_total, alto_total, cols, rows
    
def _generar_layout_dos_aguas(
    ax,
    n_paneles,
    max_cols,
    panel_w,
    panel_h,
    gap,
    gap_cumbrera_m,
):
    n_abajo = n_paneles // 2
    n_arriba = n_paneles - n_abajo

    cols = min(max_cols, max(n_arriba, n_abajo))

    rows_abajo = math.ceil(n_abajo / cols)
    rows_arriba = math.ceil(n_arriba / cols)

    ancho_total = cols * panel_w + max(cols - 1, 0) * gap

    alto_abajo = rows_abajo * panel_h + max(rows_abajo - 1, 0) * gap
    alto_arriba = rows_arriba * panel_h + max(rows_arriba - 1, 0) * gap

    alto_total = alto_abajo + gap_cumbrera_m + alto_arriba

    patches_abajo, labels_abajo, next_num = _dibujar_grid(
        n=n_abajo,
        cols=cols,
        rows=rows_abajo,
        x0=0,
        y0=0,
        w=panel_w,
        h=panel_h,
        gap=gap,
        start_num=1,
    )

    y_arriba = alto_abajo + gap_cumbrera_m

    patches_arriba, labels_arriba, _ = _dibujar_grid(
        n=n_arriba,
        cols=cols,
        rows=rows_arriba,
        x0=0,
        y0=y_arriba,
        w=panel_w,
        h=panel_h,
        gap=gap,
        start_num=next_num,
    )

    _agregar_paneles(
        ax,
        patches_abajo + patches_arriba,
        labels_abajo + labels_arriba,
    )

    ax.add_patch(
        Rectangle(
            (0, alto_abajo),
            ancho_total,
            gap_cumbrera_m,
            linewidth=0.0,
            facecolor=COLOR_CUMBRERA,
        )
    )

    ax.text(
        ancho_total / 2,
        alto_abajo + gap_cumbrera_m / 2,
        "Cumbrera",
        ha="center",
        va="center",
        fontsize=7,
        color="#555555",
    )

    return ancho_total, alto_total, cols, rows_abajo + rows_arriba


def _agregar_cotas(ax, ancho_total, alto_total):
    margen_x = 3.50
    margen_y = 0.85

    y_cota = -margen_y

    ax.annotate(
        "",
        xy=(0, y_cota),
        xytext=(ancho_total, y_cota),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0, color=COLOR_LINEA),
    )

    ax.text(
        ancho_total / 2,
        y_cota - 0.22,
        f"Ancho estimado: {ancho_total:.2f} m",
        ha="center",
        va="top",
        fontsize=8,
    )

    x_cota = -margen_x

    ax.annotate(
        "",
        xy=(x_cota, 0),
        xytext=(x_cota, alto_total),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0, color=COLOR_LINEA),
    )

    ax.text(
        x_cota - 0.18,
        alto_total / 2,
        f"Largo estimado: {alto_total:.2f} m",
        ha="right",
        va="center",
        rotation=90,
        fontsize=8,
    )


def _agregar_norte(ax, ancho_total, y_base):
    x = ancho_total + 0.75
    y = y_base + 0.55

    ax.annotate(
        "",
        xy=(x, y + 0.85),
        xytext=(x, y),
        arrowprops=dict(arrowstyle="->", linewidth=1.4, color=COLOR_LINEA),
    )

    ax.text(
        x,
        y + 1.00,
        "N",
        ha="center",
        va="bottom",
        fontsize=11,
        weight="bold",
    )


def _agregar_caja_tecnica(
    ax,
    ancho_total,
    y_caja,
    n_paneles,
    cols,
    rows,
    ancho_total_m,
    largo_total_m,
    panel_w,
    panel_h,
    gap,
    dos_aguas,
    orientacion_panel,
    tipo_montaje,
):
    """
    Caja técnica reservada para uso futuro.

    Por ahora no se llama para evitar duplicar información
    con la tabla del PDF.
    """

    alto_caja = 1.95
    ancho_caja = max(ancho_total, 9.0)

    ax.add_patch(
        Rectangle(
            (0, y_caja),
            ancho_caja,
            alto_caja,
            facecolor=COLOR_CAJA,
            edgecolor="#BBBBBB",
            linewidth=0.8,
        )
    )

    texto = (
        "Dimensiones estimadas:\n"
        f"Ancho: {ancho_total_m:.2f} m\n"
        f"Largo: {largo_total_m:.2f} m\n\n"
        f"Panel: {panel_h:.2f} m (alto) × {panel_w:.2f} m (ancho)\n"
        f"Separación entre paneles: {gap:.2f} m\n\n"
        f"Tipo: {tipo_montaje}\n"
        f"Orientación: {orientacion_panel}\n"
        f"Total de paneles: {n_paneles}\n"
        f"Distribución: {cols} columnas × {rows} filas"
    )

    ax.text(
        0.30,
        y_caja + alto_caja - 0.25,
        texto,
        ha="left",
        va="top",
        fontsize=7.5,
        linespacing=1.25,
    )

def calcular_separacion_sombra_m(
    latitud: float = 15.0,
    inclinacion_grados: float = 15.0,
    panel_h: float = 2.2,
    altura_solar_min_grados: float = 30.0,
):
    """
    Calcula separación aproximada entre filas por sombra.

    Criterio conservador:
    separación = altura trasera del panel / tan(altura solar mínima)

    altura trasera = largo_panel * sin(inclinación)
    """

    latitud = abs(float(latitud or 15.0))
    inclinacion_grados = float(inclinacion_grados or 0.0)
    panel_h = float(panel_h or 2.2)

    # Si no mandan altura solar, se estima conservadora para Honduras.
    # Honduras aprox. 13°N a 16°N.
    if not altura_solar_min_grados:
        altura_solar_min_grados = max(25.0, 90.0 - latitud - 23.45)

    beta = math.radians(inclinacion_grados)
    alfa = math.radians(float(altura_solar_min_grados))

    altura_trasera = panel_h * math.sin(beta)

    if altura_trasera <= 0 or alfa <= 0:
        return 0.0

    separacion = altura_trasera / math.tan(alfa)

    return round(max(separacion, 0.0), 2)


def generar_layout_paneles(
    n_paneles: int,
    out_path: str | Path,
    max_cols: int | None = None,
    panel_w: float = 1.1,
    panel_h: float = 2.2,
    gap: float = 0.08,
    dos_aguas: bool = False,
    gap_cumbrera_m: float = 0.35,
    separacion_sombra_m: float = 0.0,
    latitud: float = 15.0,
    inclinacion_panel_grados: float = 15.0,
    altura_solar_min_grados: float = 30.0,
    modo_sistema: str | None = None,
    zonas: list | None = None,
    orientacion_panel: str = "Vertical (Portrait)",
    tipo_montaje: str = "Terraza / cubierta plana",
    layout_por_strings: bool = False,
    n_strings: int | None = None,
    paneles_por_string: int | None = None,
):
    """
    Genera una imagen PNG del layout de paneles FV.

    Modos:
    - Rectangular tradicional.
    - Techo a dos aguas.
    - Layout físico por strings.

    No modifica cálculos eléctricos, strings ni optimización.
    """

    if max_cols is None:
        if layout_por_strings and paneles_por_string:
            max_cols = int(paneles_por_string)
        else:
            max_cols = math.ceil(math.sqrt(n_paneles))

    _validar_entrada(
        n_paneles=n_paneles,
        max_cols=max_cols,
        panel_w=panel_w,
        panel_h=panel_h,
        gap=gap,
        gap_cumbrera_m=gap_cumbrera_m,
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(13.5, 10.5))
    ax.set_facecolor(COLOR_FONDO)

    if separacion_sombra_m <= 0 and tipo_montaje in ["Terraza / cubierta plana", "Suelo"]:
        separacion_sombra_m = calcular_separacion_sombra_m(
            latitud=latitud,
            inclinacion_grados=inclinacion_panel_grados,
            panel_h=panel_h,
            altura_solar_min_grados=altura_solar_min_grados,
    )

    if layout_por_strings and n_strings and paneles_por_string:
        ancho_total, alto_total, cols, rows = _generar_layout_por_strings(
            ax=ax,
            n_paneles=n_paneles,
            n_strings=n_strings,
            paneles_por_string=paneles_por_string,
            panel_w=panel_w,
            panel_h=panel_h,
            gap=gap,
            separacion_sombra_m=separacion_sombra_m,
        )

    elif dos_aguas:
        ancho_total, alto_total, cols, rows = _generar_layout_dos_aguas(
            ax=ax,
            n_paneles=n_paneles,
            max_cols=max_cols,
            panel_w=panel_w,
            panel_h=panel_h,
            gap=gap,
            gap_cumbrera_m=gap_cumbrera_m,
        )

    else:
        ancho_total, alto_total, cols, rows = _generar_layout_rectangular(
            ax=ax,
            n_paneles=n_paneles,
            max_cols=max_cols,
            panel_w=panel_w,
            panel_h=panel_h,
            gap=gap,
        )

    _agregar_cotas(ax, ancho_total, alto_total)

    if layout_por_strings:
        ax.text(
            ancho_total / 2,
            -1.18,
            (
                f"Separación entre paneles: {gap:.2f} m   |   "
                f"Separación entre filas por sombra: {separacion_sombra_m:.2f} m"
            ),
            ha="center",
            va="top",
            fontsize=7,
            color=COLOR_LINEA,
        )
    else:
        ax.text(
            ancho_total,
            alto_total + 0.28,
            f"Separación entre paneles: {gap:.2f} m",
            ha="right",
            va="bottom",
            fontsize=7,
            color=COLOR_LINEA,
        )

        ax.text(
            ancho_total,
            y_sep,
            f"Separación entre paneles: {gap:.2f} m",
            ha="right",
            va="bottom",
            fontsize=7,
        )

    _agregar_norte(ax, ancho_total, 0)

    ax.set_aspect("equal")

    ax.set_xlim(-4.0, max(ancho_total + 1.45, 10.8))
    ax.set_ylim(-1.35, alto_total + 2.25)

    ax.axis("off")

    plt.savefig(
        out_path,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.08,
    )

    plt.close()

    return str(out_path)

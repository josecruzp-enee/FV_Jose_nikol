# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch


# =========================================================
# COLORES PROFESIONALES
# =========================================================
COLOR_PANEL = "#163A5F"
COLOR_PANEL_2 = "#1F4E79"
COLOR_BORDE = "#0B2E4A"
COLOR_TEXTO = "#1F1F1F"
COLOR_AZUL = "#0B5394"
COLOR_GRIS = "#666666"
COLOR_GRIS_CLARO = "#E6E6E6"
COLOR_CAJA = "#F8FAFC"
COLOR_FONDO = "#FFFFFF"
COLOR_SOMBRA = "#D9EAF7"
COLOR_CUMBRERA = "#DDDDDD"


# =========================================================
# VALIDACIONES
# =========================================================
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


def _normalizar_tipo_montaje(tipo_montaje: str | None) -> str:
    return str(tipo_montaje or "").strip().lower()


# =========================================================
# CÁLCULO DE SOMBRA
# =========================================================
def calcular_separacion_sombra_m(
    latitud: float = 15.0,
    inclinacion_grados: float = 15.0,
    panel_h: float = 2.2,
    altura_solar_min_grados: float = 30.0,
):
    """
    Separación preliminar entre filas por sombra.

    Criterio:
    separación = altura trasera del panel / tan(altura solar mínima)

    altura trasera = largo_panel * sin(inclinación)

    Nota:
    Este cálculo es preliminar. Para ingeniería final debe revisarse
    con azimut, fecha/hora crítica, obstáculos y modelo solar.
    """

    latitud = abs(float(latitud or 15.0))
    inclinacion_grados = float(inclinacion_grados or 0.0)
    panel_h = float(panel_h or 2.2)

    if not altura_solar_min_grados:
        altura_solar_min_grados = max(25.0, 90.0 - latitud - 23.45)

    beta = math.radians(inclinacion_grados)
    alfa = math.radians(float(altura_solar_min_grados))

    altura_trasera = panel_h * math.sin(beta)

    if altura_trasera <= 0 or alfa <= 0:
        return 0.0

    separacion = altura_trasera / math.tan(alfa)
    return round(max(separacion, 0.0), 2)


# =========================================================
# DIBUJO BASE
# =========================================================
def _dibujar_panel(ax, x, y, w, h, numero=None, fontsize=6.2):
    panel = Rectangle(
        (x, y),
        w,
        h,
        facecolor=COLOR_PANEL,
        edgecolor=COLOR_BORDE,
        linewidth=0.65,
    )
    ax.add_patch(panel)

    # Líneas internas sutiles tipo módulo FV
    for i in range(1, 3):
        ax.plot(
            [x + i * w / 3, x + i * w / 3],
            [y + 0.03, y + h - 0.03],
            color="#2F5F8F",
            linewidth=0.25,
            alpha=0.65,
        )

    for j in range(1, 4):
        ax.plot(
            [x + 0.03, x + w - 0.03],
            [y + j * h / 4, y + j * h / 4],
            color="#2F5F8F",
            linewidth=0.25,
            alpha=0.65,
        )

    if numero is not None:
        ax.text(
            x + w / 2,
            y + h / 2,
            str(numero),
            color="white",
            ha="center",
            va="center",
            fontsize=fontsize,
            weight="bold",
        )


def _dibujar_grid(n, cols, rows, x0, y0, w, h, gap, start_num=1):
    num = start_num

    for r in range(rows):
        for c in range(cols):
            if num >= start_num + n:
                break

            x = x0 + c * (w + gap)
            y = y0 + r * (h + gap)

            _dibujar_panel(ax=plt.gca(), x=x, y=y, w=w, h=h, numero=num)
            num += 1

    return num


# =========================================================
# LAYOUT RECTANGULAR
# =========================================================
def _generar_layout_rectangular(ax, n_paneles, max_cols, panel_w, panel_h, gap):
    cols = min(max_cols, n_paneles)
    rows = math.ceil(n_paneles / cols)

    num = 1
    for r in range(rows):
        for c in range(cols):
            if num > n_paneles:
                break

            x = c * (panel_w + gap)
            y = (rows - 1 - r) * (panel_h + gap)
            _dibujar_panel(ax, x, y, panel_w, panel_h, num)
            num += 1

    ancho_total = cols * panel_w + max(cols - 1, 0) * gap
    alto_total = rows * panel_h + max(rows - 1, 0) * gap

    return ancho_total, alto_total, cols, rows


# =========================================================
# LAYOUT POR STRINGS — VERSIÓN PROFESIONAL
# =========================================================
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
    Layout físico agrupado por strings.

    Mejoras:
    - Menos ruido visual.
    - Sombra como banda suave.
    - Una sola cota general de separación.
    - Títulos separados del dibujo.
    - Etiquetas limpias por string.
    """

    n_strings = int(n_strings or 0)
    paneles_por_string = int(paneles_por_string or 0)
    separacion_sombra_m = float(separacion_sombra_m or 0.0)

    if n_strings <= 0 or paneles_por_string <= 0:
        raise ValueError("n_strings y paneles_por_string deben ser mayores que cero.")

    cols = paneles_por_string
    rows = n_strings
    total_dibujado = min(n_paneles, n_strings * paneles_por_string)

    gap_col = float(gap)
    gap_fila = max(float(gap), separacion_sombra_m)

    ancho_total = cols * panel_w + max(cols - 1, 0) * gap_col
    alto_total = rows * panel_h + max(rows - 1, 0) * gap_fila

    num = 1

    for r in range(rows):
        y = (rows - 1 - r) * (panel_h + gap_fila)

        ax.text(
            -0.55,
            y + panel_h / 2,
            f"STR-{r + 1:02d}",
            ha="right",
            va="center",
            fontsize=7.2,
            weight="bold",
            color=COLOR_TEXTO,
        )

        for c in range(cols):
            if num > total_dibujado:
                break

            x = c * (panel_w + gap_col)
            _dibujar_panel(
                ax=ax,
                x=x,
                y=y,
                w=panel_w,
                h=panel_h,
                numero=num,
                fontsize=5.8 if total_dibujado > 120 else 6.4,
            )
            num += 1

        # Banda de separación/sombra entre filas
        if separacion_sombra_m > gap and r < rows - 1:
            y_banda = y - gap_fila
            ax.add_patch(
                Rectangle(
                    (0, y_banda),
                    ancho_total,
                    gap_fila,
                    facecolor=COLOR_SOMBRA,
                    edgecolor="none",
                    alpha=0.32,
                    zorder=-1,
                )
            )

            ax.plot(
                [0, ancho_total],
                [y_banda + gap_fila / 2, y_banda + gap_fila / 2],
                linestyle="--",
                linewidth=0.45,
                color="#8AA6BF",
                alpha=0.9,
            )

    # Cota única de separación entre filas
    if separacion_sombra_m > gap and rows > 1:
        x_cota = ancho_total + 0.55
        y1 = alto_total - panel_h
        y2 = alto_total - panel_h - gap_fila

        ax.annotate(
            "",
            xy=(x_cota, y1),
            xytext=(x_cota, y2),
            arrowprops=dict(
                arrowstyle="<->",
                linewidth=1.0,
                color=COLOR_AZUL,
            ),
        )

        ax.text(
            x_cota + 0.18,
            (y1 + y2) / 2,
            f"{separacion_sombra_m:.2f} m\nseparación\nentre filas",
            ha="left",
            va="center",
            fontsize=6.8,
            color=COLOR_AZUL,
            linespacing=1.15,
        )

    return ancho_total, alto_total, cols, rows


# =========================================================
# LAYOUT DOS AGUAS
# =========================================================
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

    num = 1

    for r in range(rows_abajo):
        for c in range(cols):
            if num > n_abajo:
                break
            x = c * (panel_w + gap)
            y = r * (panel_h + gap)
            _dibujar_panel(ax, x, y, panel_w, panel_h, num)
            num += 1

    y_arriba = alto_abajo + gap_cumbrera_m

    for r in range(rows_arriba):
        for c in range(cols):
            if num > n_paneles:
                break
            x = c * (panel_w + gap)
            y = y_arriba + r * (panel_h + gap)
            _dibujar_panel(ax, x, y, panel_w, panel_h, num)
            num += 1

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
        color=COLOR_GRIS,
    )

    return ancho_total, alto_total, cols, rows_abajo + rows_arriba


# =========================================================
# COTAS Y ELEMENTOS GRÁFICOS
# =========================================================
def _agregar_cotas(ax, ancho_total, alto_total):
    margen_x = 1.10
    margen_y = 0.75

    y_cota = -margen_y

    ax.annotate(
        "",
        xy=(0, y_cota),
        xytext=(ancho_total, y_cota),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0, color=COLOR_TEXTO),
    )

    ax.text(
        ancho_total / 2,
        y_cota - 0.22,
        f"Ancho estimado: {ancho_total:.2f} m",
        ha="center",
        va="top",
        fontsize=7.6,
        color=COLOR_TEXTO,
    )

    x_cota = -margen_x

    ax.annotate(
        "",
        xy=(x_cota, 0),
        xytext=(x_cota, alto_total),
        arrowprops=dict(arrowstyle="<->", linewidth=1.0, color=COLOR_TEXTO),
    )

    ax.text(
        x_cota - 0.16,
        alto_total / 2,
        f"Largo estimado: {alto_total:.2f} m",
        ha="right",
        va="center",
        rotation=90,
        fontsize=7.6,
        color=COLOR_TEXTO,
    )


def _agregar_norte(ax, ancho_total, alto_total):
    x = ancho_total + 0.90
    y = max(0.35, alto_total - 1.30)

    ax.annotate(
        "",
        xy=(x, y + 0.85),
        xytext=(x, y),
        arrowprops=dict(arrowstyle="->", linewidth=1.35, color=COLOR_TEXTO),
    )

    ax.text(
        x,
        y + 0.98,
        "N",
        ha="center",
        va="bottom",
        fontsize=10,
        weight="bold",
        color=COLOR_TEXTO,
    )


def _agregar_encabezado(
    ax,
    ancho_total,
    alto_total,
    n_paneles,
    cols,
    rows,
    gap,
    separacion_sombra_m,
    orientacion_panel,
    tipo_montaje,
    layout_por_strings,
    n_strings,
    paneles_por_string,
    inclinacion_panel_grados,
):
    y0 = alto_total + 2.45

    titulo = "LAYOUT PRELIMINAR DEL GENERADOR FOTOVOLTAICO"

    ax.text(
        0,
        y0,
        titulo,
        ha="left",
        va="bottom",
        fontsize=12.5,
        weight="bold",
        color=COLOR_TEXTO,
    )

    ax.plot([0, min(ancho_total, 5.0)], [y0 - 0.16, y0 - 0.16], color=COLOR_AZUL, linewidth=2.0)

    if layout_por_strings and n_strings and paneles_por_string:
        subtitulo = f"{int(n_strings)} strings × {int(paneles_por_string)} módulos/string · {int(n_paneles)} módulos totales"
    else:
        subtitulo = f"{int(n_paneles)} módulos · {cols} columnas × {rows} filas"

    ax.text(
        0,
        y0 - 0.55,
        subtitulo,
        ha="left",
        va="top",
        fontsize=8.6,
        color=COLOR_TEXTO,
    )

    ax.text(
        0,
        y0 - 0.92,
        f"Montaje: {tipo_montaje} · Orientación: {orientacion_panel} · Inclinación: {inclinacion_panel_grados:.1f}°",
        ha="left",
        va="top",
        fontsize=7.6,
        color=COLOR_GRIS,
    )


def _agregar_resumen_inferior(
    ax,
    ancho_total,
    y,
    n_paneles,
    gap,
    separacion_sombra_m,
    orientacion_panel,
    inclinacion_panel_grados,
):
    ancho_caja = max(ancho_total, 11.0)
    alto_caja = 1.05

    caja = FancyBboxPatch(
        (0, y),
        ancho_caja,
        alto_caja,
        boxstyle="round,pad=0.10,rounding_size=0.10",
        linewidth=0.8,
        edgecolor="#B8C7D9",
        facecolor=COLOR_CAJA,
    )

    ax.add_patch(caja)

    items = [
        ("Módulos", f"{int(n_paneles)}"),
        ("Panel-panel", f"{gap:.2f} m"),
        ("Fila-fila", f"{separacion_sombra_m:.2f} m" if separacion_sombra_m > 0 else "N/A"),
        ("Orientación", orientacion_panel),
        ("Inclinación", f"{inclinacion_panel_grados:.1f}°"),
    ]

    x = 0.35
    paso = ancho_caja / len(items)

    for i, (k, v) in enumerate(items):
        xi = x + i * paso

        ax.text(
            xi,
            y + 0.68,
            k,
            ha="left",
            va="center",
            fontsize=6.8,
            color=COLOR_GRIS,
        )

        ax.text(
            xi,
            y + 0.35,
            v,
            ha="left",
            va="center",
            fontsize=8.0,
            weight="bold",
            color=COLOR_AZUL,
        )

        if i > 0:
            ax.plot(
                [xi - 0.25, xi - 0.25],
                [y + 0.18, y + alto_caja - 0.18],
                color="#D0D7DE",
                linewidth=0.7,
            )


def _agregar_nota_tecnica(ax, ancho_total, y):
    texto = (
        "Nota: Layout preliminar referencial. La separación entre filas debe validarse "
        "en ingeniería final considerando azimut, obstáculos, estructura y condición solar crítica."
    )

    ax.text(
        0,
        y,
        texto,
        ha="left",
        va="top",
        fontsize=6.3,
        color=COLOR_GRIS,
        wrap=True,
    )


# =========================================================
# FUNCIÓN PRINCIPAL
# =========================================================
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
    Genera una imagen PNG profesional del layout preliminar de paneles FV.

    Compatible con:
    - Layout rectangular.
    - Techo a dos aguas.
    - Layout físico por strings.
    - Separación por sombra para montaje en terraza/cubierta plana o suelo.
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

    tipo_norm = _normalizar_tipo_montaje(tipo_montaje)

    if separacion_sombra_m <= 0 and any(t in tipo_norm for t in ["terraza", "cubierta", "plana", "suelo"]):
        separacion_sombra_m = calcular_separacion_sombra_m(
            latitud=latitud,
            inclinacion_grados=inclinacion_panel_grados,
            panel_h=panel_h,
            altura_solar_min_grados=altura_solar_min_grados,
        )

    # Figura más ancha y limpia
    fig, ax = plt.subplots(figsize=(12.4, 7.4))
    fig.patch.set_facecolor(COLOR_FONDO)
    ax.set_facecolor(COLOR_FONDO)

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
    _agregar_norte(ax, ancho_total, alto_total)

    _agregar_encabezado(
        ax=ax,
        ancho_total=ancho_total,
        alto_total=alto_total,
        n_paneles=n_paneles,
        cols=cols,
        rows=rows,
        gap=gap,
        separacion_sombra_m=separacion_sombra_m,
        orientacion_panel=orientacion_panel,
        tipo_montaje=tipo_montaje,
        layout_por_strings=layout_por_strings,
        n_strings=n_strings,
        paneles_por_string=paneles_por_string,
        inclinacion_panel_grados=float(inclinacion_panel_grados or 0.0),
    )

    y_resumen = -2.15

    _agregar_resumen_inferior(
        ax=ax,
        ancho_total=ancho_total,
        y=y_resumen,
        n_paneles=n_paneles,
        gap=gap,
        separacion_sombra_m=separacion_sombra_m,
        orientacion_panel=orientacion_panel,
        inclinacion_panel_grados=float(inclinacion_panel_grados or 0.0),
    )

    _agregar_nota_tecnica(
        ax=ax,
        ancho_total=ancho_total,
        y=y_resumen - 0.35,
    )

    ax.set_aspect("equal")

    margen_izq = -1.85
    margen_der = 2.25
    margen_inf = -2.75
    margen_sup = 3.10

    ax.set_xlim(margen_izq, max(ancho_total + margen_der, 11.8))
    ax.set_ylim(margen_inf, alto_total + margen_sup)

    ax.axis("off")

    plt.savefig(
        out_path,
        dpi=240,
        bbox_inches="tight",
        pad_inches=0.12,
    )

    plt.close(fig)

    return str(out_path)

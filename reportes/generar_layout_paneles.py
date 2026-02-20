# =========================================================
# 8B) Layout paneles (igual que el tuyo)
# =========================================================
import matplotlib
matplotlib.use("Agg")
import math
def elegir_cols_compacto(n: int, max_cols: int) -> int:
    """
    Elige cols (1..max_cols) para que el arreglo quede compacto:
    - Minimiza huecos (cols*rows - n)
    - Penaliza grids muy alargados (rows/cols lejos de 1)
    """
    import math

    n = int(n)
    max_cols = max(1, int(max_cols))
    if n <= 0:
        return 1

    mejor_cols = 1
    mejor_score = float("inf")

    for cols in range(1, min(max_cols, n) + 1):
        rows = int(math.ceil(n / cols))
        huecos = cols * rows - n
        aspect = abs((rows / cols) - 1.0)  # 0 = cuadrado perfecto

        # Huecos manda. Aspect solo ajusta.
        score = huecos * 10.0 + aspect

        if score < mejor_score:
            mejor_score = score
            mejor_cols = cols

    return mejor_cols


def generar_layout_paneles(
    n_paneles: int,
    out_path: str,
    *,
    panel_w_m: float = 1.134,
    panel_h_m: float = 2.279,
    gap_m: float = 0.02,
    max_cols: int = 7,
    titulo: str = "Arreglo FV (vista superior referencial)",
    margen_techo_m: float = 0.60,
    norte: bool = True,
    dos_aguas: bool = False,
    gap_cumbrera_m: float = 0.35,
):
    """
    Vista superior referencial:
    - 1 agua: arreglo compacto (cols elegido por elegir_cols_compacto).
    - 2 aguas: divide en Izq/Der (~50/50) y fuerza misma altura visual (mismas filas),
               con franja de cumbrera gap_cumbrera_m.
    - Criterio constructivo: si n < 6 => fuerza dos_aguas=False.
    """
    import math
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    n = int(n_paneles)
    if n <= 0:
        raise ValueError("n_paneles debe ser > 0")

    # criterio constructivo real
    if n < 6:
        dos_aguas = False

    # -----------------------------
    # Helpers (locales)
    # -----------------------------
    def _dims(cols: int, rows: int) -> tuple[float, float]:
        if cols <= 0 or rows <= 0:
            return 0.0, 0.0
        W_ = cols * panel_w_m + (cols - 1) * gap_m
        H_ = rows * panel_h_m + (rows - 1) * gap_m
        return W_, H_

    # ===== 1) Geometría del arreglo =====
    if dos_aguas and n >= 6:
        n_izq = (n + 1) // 2
        n_der = n // 2

        # Izq: compacto
        cols_izq = elegir_cols_compacto(n_izq, max_cols)
        rows_izq = int(math.ceil(n_izq / cols_izq))

        # Der: forzar misma altura (mismas filas)
        rows_obj = rows_izq

        if n_der > 0:
            cols_der = int(math.ceil(n_der / rows_obj))
            cols_der = max(1, min(max_cols, cols_der))
            rows_der = int(math.ceil(n_der / cols_der))

            # Aumentar cols hasta que quepa en rows_obj
            while rows_der > rows_obj and cols_der < max_cols:
                cols_der += 1
                rows_der = int(math.ceil(n_der / cols_der))
        else:
            cols_der, rows_der = 0, 0

        # Dimensiones por lado
        W_izq, H_izq = _dims(cols_izq, rows_izq)
        W_der, H_der = _dims(cols_der, rows_der)

        W = W_izq + (gap_cumbrera_m if n_der > 0 else 0.0) + W_der
        H = max(H_izq, H_der)

    else:
        # 1 agua
        n_izq, n_der = n, 0
        cols = elegir_cols_compacto(n, max_cols)
        rows = int(math.ceil(n / cols))
        cols_izq, rows_izq = cols, rows
        cols_der, rows_der = 0, 0
        W_izq, H_izq = _dims(cols_izq, rows_izq)
        W_der, H_der = 0.0, 0.0
        W, H = W_izq, H_izq

    # ===== 2) Techo referencial =====
    roof_W = W + 2 * margen_techo_m
    roof_H = H + 2 * margen_techo_m

    ratio = roof_W / roof_H if roof_H else 1.0
    fig_w = 8.0
    fig_h = max(4.2, fig_w / max(ratio, 0.65))

    fig = plt.figure(figsize=(fig_w, fig_h), dpi=170)
    ax = fig.add_subplot(111)

    ax.set_title(titulo)
    ax.set_aspect("equal")

    extra_top = 0.45
    ax.set_xlim(-0.25, roof_W + 0.25)
    ax.set_ylim(-0.35, roof_H + extra_top)

    # Techo (fondo)
    ax.add_patch(Rectangle(
        (0, 0), roof_W, roof_H,
        linewidth=1.2,
        edgecolor="#98A2B3",
        facecolor="#F2F4F7"
    ))

    # Contorno del arreglo total
    off_x = margen_techo_m
    off_y = margen_techo_m

    ax.add_patch(Rectangle(
        (off_x, off_y), W, H,
        linewidth=1.1,
        edgecolor="#667085",
        facecolor="none"
    ))

    # Cumbrera (franja)
    if dos_aguas and n_der > 0:
        x_c = off_x + W_izq
        ax.add_patch(Rectangle(
            (x_c, off_y), gap_cumbrera_m, H,
            linewidth=0.0,
            edgecolor="none",
            facecolor="#FFFFFF"
        ))
 
       # ===== 3) Dibujo de paneles =====
    def _dibujar_grid(n_local, cols_local, rows_local, x0, y0, start_num):
        k = 0
        for r in range(rows_local):
            for c in range(cols_local):
                if k >= n_local:
                    return start_num + k

                x = x0 + c * (panel_w_m + gap_m)
                y = y0 + (rows_local - 1 - r) * (panel_h_m + gap_m)

                ax.add_patch(Rectangle(
                    (x, y),
                    panel_w_m,
                    panel_h_m,
                    linewidth=0.8,
                    edgecolor="#0B2E4A",
                    facecolor="#1F2A37"
                ))

                ax.text(
                    x + panel_w_m / 2,
                    y + panel_h_m / 2,
                    str(start_num + k),
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white"
                )
                k += 1
        return start_num + k


    # Izquierda o único plano
    next_num = _dibujar_grid(
        n_izq,
        cols_izq,
        rows_izq,
        off_x,
        off_y,
        start_num=1
    )

    # Derecha si es dos aguas
    if dos_aguas and n_der > 0:
        x0_der = off_x + W_izq + gap_cumbrera_m
        _dibujar_grid(
            n_der,
            cols_der,
            rows_obj,
            x0_der,
            off_y,
            start_num=next_num
        )

    # ===== Norte =====
    if norte:
        nx = roof_W - 0.35
        ny = roof_H - 0.20
        ax.text(nx, ny, "N", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color="#0B2E4A")
        ax.arrow(nx, ny - 0.15, 0, 0.22,
                 head_width=0.12, head_length=0.10,
                 fc="#0B2E4A", ec="#0B2E4A")

    # ===== Limpieza y guardado =====
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

# reportes/imagenes.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib
matplotlib.use("Agg")


# =========================================================
# BASE PATHS
# =========================================================

def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def construir_paths_salida(base_dir: str | Path) -> Dict[str, Any]:
    base = Path(base_dir)
    _ensure_dir(base)

    charts_dir = _ensure_dir(base / "charts")

    return {
        "out_dir": str(base),
        "charts_dir": str(charts_dir),
        "layout_paneles": str(base / "layout_paneles.png"),
    }


# =========================================================
# HELPERS NUMÉRICOS
# =========================================================

def _as_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x)) if x is not None else int(default)
    except Exception:
        return int(default)


# =========================================================
# LECTURA SEGURA
# =========================================================

def _leer(obj: Any, campo: str, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(campo, default)

    return getattr(obj, campo, default)


# =========================================================
# INFERENCIA DE PANELES
# =========================================================

def inferir_n_paneles(res: Any) -> int:
    sizing = res.get("sizing") if isinstance(res, dict) else getattr(res, "sizing", None)

    if sizing and not isinstance(sizing, dict):
        n = _as_int(getattr(sizing, "n_paneles", 0))
        if n > 0:
            return n

        n = _as_int(getattr(sizing, "n_paneles_string", 0))
        if n > 0:
            return n

    if isinstance(sizing, dict):
        n = _as_int(sizing.get("n_paneles"), 0)
        if n > 0:
            return n

        n = _as_int(sizing.get("n_paneles_string"), 0)
        if n > 0:
            return n

    n = _as_int(
        res.get("n_paneles") if isinstance(res, dict) else getattr(res, "n_paneles", 0)
    )

    if n > 0:
        return n

    return 0


def inferir_strings(res: Any):
    """
    Busca strings en las rutas conocidas sin romper compatibilidad.

    Rutas soportadas:
    - res["strings"]
    - res.strings
    - res["paneles"]["strings"]
    - res.paneles.strings
    - res["paneles"].strings
    """

    strings = _leer(res, "strings", None)

    if strings:
        return strings

    paneles = _leer(res, "paneles", None)

    if paneles is not None:
        strings = _leer(paneles, "strings", None)
        if strings:
            return strings

    # fallback adicional: algunos resultados guardan paneles como dict anidado
    if isinstance(res, dict):
        paneles_dict = res.get("paneles", None)

        if isinstance(paneles_dict, dict):
            strings = paneles_dict.get("strings", None)
            if strings:
                return strings

    return []

def inferir_layout_strings(strings) -> tuple[bool, int | None, int | None]:
    """
    Devuelve:
    - layout_por_strings
    - n_strings
    - paneles_por_string

    Solo activa layout por strings si todos los strings tienen el mismo n_series.
    """

    if not strings:
        return False, None, None

    n_series_lista = []

    for s in strings:
        n = _as_int(_leer(s, "n_series", 0), 0)
        if n > 0:
            n_series_lista.append(n)

    if not n_series_lista:
        return False, None, None

    valores = set(n_series_lista)

    if len(valores) != 1:
        return False, None, None

    return True, len(n_series_lista), int(n_series_lista[0])


# =========================================================
# PIPELINE PRINCIPAL
# =========================================================

def generar_artefactos(
    *,
    res: Dict[str, Any],
    out_dir: str | Path,
    proyecto=None,
    vista_resultados: Optional[Dict[str, Any]] = None,
    dos_aguas: bool = True,
    max_cols: int = 7,
    gap_cumbrera_m: float = 0.35,
) -> Dict[str, Any]:

    from reportes.generar_charts import generar_charts
    from reportes.generar_layout_paneles import generar_layout_paneles
    from electrical.catalogos import catalogo_paneles

    paths = construir_paths_salida(out_dir)

    # =====================================================
    # CHARTS
    # =====================================================
    charts = generar_charts(
        res,
        paths["charts_dir"],
        vista_resultados=vista_resultados or {},
        proyecto=proyecto,
    )

    if charts:
        paths.update({k: str(v) for k, v in charts.items()})

    # =====================================================
    # STRINGS DISPONIBLES
    # =====================================================
    strings = inferir_strings(res)

    layout_por_strings, n_strings, paneles_por_string = inferir_layout_strings(strings)

    paths["layout_por_strings"] = layout_por_strings
    paths["n_strings_layout"] = n_strings
    paths["paneles_por_string_layout"] = paneles_por_string

    # =====================================================
    # LAYOUT PANELES
    # =====================================================
    n_paneles = inferir_n_paneles(res)

    sf = {}
    equipos = {}

    try:
        sf = getattr(proyecto, "sistema_fv", {}) or {}
    except Exception:
        sf = {}

    try:
        equipos = getattr(proyecto, "equipos", {}) or {}
    except Exception:
        equipos = {}

    modo_sistema = sf.get("modo")
    zonas = sf.get("zonas") or []

    tipo_montaje = (
        sf.get("tipo_montaje")
        or "Terraza / cubierta plana"
    )

    orientacion_panel = (
        sf.get("orientacion_panel")
        or "Vertical (Portrait)"
    )

    dos_aguas_layout = tipo_montaje == "Techo a dos aguas"

    paths["modo_sistema"] = modo_sistema
    paths["zonas"] = zonas
    paths["tipo_montaje"] = tipo_montaje
    paths["orientacion_panel"] = orientacion_panel

    # =====================================================
    # DIMENSIONES REALES DEL PANEL
    # =====================================================
    panel_w = 1.10
    panel_h = 2.20

    try:
        panel_id = equipos.get("panel_id")

        paneles_catalogo = {
            p["id"]: p for p in catalogo_paneles()
        }

        panel = paneles_catalogo.get(panel_id, {}) or {}
        mecanico = panel.get("mecanico", {}) or {}

        largo_mm = float(mecanico.get("largo_mm", 2200))
        ancho_mm = float(mecanico.get("ancho_mm", 1100))

        largo_m = largo_mm / 1000.0
        ancho_m = ancho_mm / 1000.0

        if orientacion_panel == "Horizontal (Landscape)":
            panel_w = largo_m
            panel_h = ancho_m
        else:
            panel_w = ancho_m
            panel_h = largo_m

    except Exception:
        panel_w = 1.10
        panel_h = 2.20

    paths["panel_w_m"] = panel_w
    paths["panel_h_m"] = panel_h

    if n_paneles > 0:
        generar_layout_paneles(
            n_paneles=n_paneles,
            out_path=paths["layout_paneles"],
            max_cols=None,
            panel_w=panel_w,
            panel_h=panel_h,
            dos_aguas=dos_aguas_layout,
            gap_cumbrera_m=float(gap_cumbrera_m),
            modo_sistema=modo_sistema,
            zonas=zonas,
            orientacion_panel=orientacion_panel,
            tipo_montaje=tipo_montaje,
            layout_por_strings=layout_por_strings,
            n_strings=n_strings,
            paneles_por_string=paneles_por_string,
            latitud=float(_leer(proyecto, "lat", 15.0) or 15.0),
            inclinacion_panel_grados=float(
                sf.get("inclinacion_panel_grados", 15.0) or 15.0
            ),
        )

    return paths

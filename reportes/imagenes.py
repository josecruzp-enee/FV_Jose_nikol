# reportes/artefactos.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


def _ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def construir_paths_salida(base_dir: str | Path) -> Dict[str, str]:
    """
    Contrato único de carpetas/paths para artefactos.
    """
    base = Path(base_dir)
    _ensure_dir(base)

    charts_dir = _ensure_dir(base / "charts")
    return {
        "out_dir": str(base),
        "charts_dir": str(charts_dir),
        "layout_paneles": str(base / "layout_paneles.png"),
        # opcional: logo, portada, etc.
        # "logo": str(base / "logo.png"),
    }


def generar_artefactos(
    *,
    res: Dict[str, Any],
    out_dir: str | Path,
    vista_resultados: Optional[Dict[str, Any]] = None,
    dos_aguas: bool = True,
    max_cols: int = 7,
    gap_cumbrera_m: float = 0.35,
) -> Dict[str, str]:
    """
    Genera todos los artefactos gráficos y devuelve 'paths' listos para el PDF.
    No depende de Streamlit.
    """
    from reportes.generar_charts import generar_charts
    from reportes.generar_layout_paneles import generar_layout_paneles

    paths = construir_paths_salida(out_dir)

    # --- charts
    if "tabla_12m" in res and res["tabla_12m"]:
        charts = generar_charts(
            res["tabla_12m"],
            paths["charts_dir"],
            vista_resultados=vista_resultados or {},
        )
        # charts suele devolver dict de paths, lo agregamos
        for k, v in (charts or {}).items():
            paths[k] = str(v)

    # --- layout paneles
    # Intento tolerante: buscar n_paneles en sizing
    sizing = res.get("sizing") or {}
    n_paneles = int(sizing.get("n_paneles") or 0)

    if n_paneles > 0:
        generar_layout_paneles(
            n_paneles=n_paneles,
            out_path=paths["layout_paneles"],
            max_cols=max_cols,
            dos_aguas=bool(dos_aguas),
            gap_cumbrera_m=float(gap_cumbrera_m),
        )

    return paths

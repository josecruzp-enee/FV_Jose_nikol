
# reportes/generar_layout_paneles.py
from __future__ import annotations

from pathlib import Path

def generar_layout_paneles(
    n_paneles: int,
    out_path: str,
    max_cols: int = 7,
    dos_aguas: bool = True,
    gap_cumbrera_m: float = 0.35,
) -> None:
    """
    Stub temporal del layout de paneles.
    Solo crea un archivo placeholder para que Streamlit no falle.
    """

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # archivo placeholder (luego pondrás el layout real)
    p.write_text("Layout paneles placeholder")


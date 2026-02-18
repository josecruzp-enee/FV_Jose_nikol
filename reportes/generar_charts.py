
# reportes/generar_charts.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

def generar_charts(resultado: Dict[str, Any], out_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Genera (o prepara) charts para el reporte.
    Versión mínima: NO rompe el app aunque no haya datos/plots todavía.
    Retorna dict de rutas (vacío si no genera nada).
    """
    # Carpeta de salida (por si luego guardas PNG)
    base = Path(out_dir) if out_dir else Path("salidas")
    base.mkdir(parents=True, exist_ok=True)

    # Stub: todavía no generamos nada
    return {}


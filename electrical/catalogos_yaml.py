from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import yaml

def cargar_paneles_yaml(path: str = "data/paneles.yaml") -> Dict[str, Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe: {path}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("paneles.yaml debe ser un dict raíz {id: {...}}")
    return data

# core/configuracion.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"


def _leer_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"No existe config: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config inválida (debe ser dict): {path}")
    return data


@dataclass(frozen=True)
class ConfigFV:
    tecnicos: Dict[str, Any]
    financieros: Dict[str, Any]


def cargar_configuracion() -> ConfigFV:
    tecnicos = _leer_yaml(CONFIG_DIR / "parametros_tecnicos.yaml")
    financieros = _leer_yaml(CONFIG_DIR / "parametros_financieros.yaml")
    return ConfigFV(tecnicos=tecnicos, financieros=financieros)


def construir_config_efectiva(cfg_base: ConfigFV, overrides: Optional[dict]) -> ConfigFV:
    if not overrides:
        return cfg_base
    tec = {**cfg_base.tecnicos, **(overrides.get("tecnicos") or {})}
    fin = {**cfg_base.financieros, **(overrides.get("financieros") or {})}
    return ConfigFV(tecnicos=tec, financieros=fin)

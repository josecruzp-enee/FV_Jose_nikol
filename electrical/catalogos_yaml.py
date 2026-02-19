# electrical/catalogos_yaml.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import yaml

DATA_DIR = Path("data")

def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def _req(d: Dict[str, Any], k: str, ctx: str) -> Any:
    if k not in d or d[k] is None:
        raise ValueError(f"Falta '{k}' en {ctx}")
    return d[k]

def _req_num(d: Dict[str, Any], k: str, ctx: str) -> float:
    v = _req(d, k, ctx)
    try:
        return float(v)
    except Exception as e:
        raise ValueError(f"'{k}' debe ser numérico en {ctx}. Valor={v!r}") from e

def _validate_panel(pid: str, p: Dict[str, Any]) -> None:
    _req(p, "marca", f"paneles.{pid}")
    _req(p, "nombre", f"paneles.{pid}")
    _req(p, "codigo", f"paneles.{pid}")
    stc = _req(p, "stc", f"paneles.{pid}")
    for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a"):
        _req_num(stc, k, f"paneles.{pid}.stc")
    co = _req(p, "coeficientes_pct_c", f"paneles.{pid}")
    _req_num(co, "voc", f"paneles.{pid}.coeficientes_pct_c")

def _validate_inversor(iid: str, inv: Dict[str, Any]) -> None:
    _req(inv, "marca", f"inversores.{iid}")
    _req(inv, "nombre", f"inversores.{iid}")
    _req(inv, "codigo", f"inversores.{iid}")
    dc = _req(inv, "entrada_dc", f"inversores.{iid}")
    for k in ("vdc_max_v", "mppt_min_v", "mppt_max_v", "n_mppt", "imppt_max_a"):
        _req(dc, k, f"inversores.{iid}.entrada_dc")

def cargar_paneles_yaml(path: str = "paneles.yaml") -> Dict[str, Dict[str, Any]]:
    doc = _read_yaml(DATA_DIR / path)
    paneles = (doc.get("paneles") or {}) if isinstance(doc, dict) else {}
    for pid, p in paneles.items():
        _validate_panel(pid, p)
    return paneles

def cargar_inversores_yaml(path: str = "inversores.yaml") -> Dict[str, Dict[str, Any]]:
    doc = _read_yaml(DATA_DIR / path)
    inversores = (doc.get("inversores") or {}) if isinstance(doc, dict) else {}
    for iid, inv in inversores.items():
        _validate_inversor(iid, inv)
    return inversores

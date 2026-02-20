# electrical/catalogos_yaml.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml

from .modelos import Panel, Inversor

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
    for k in ("vdc_max_v", "mppt_min_v", "mppt_max_v", "n_mppt"):
        _req_num(dc, k, f"inversores.{iid}.entrada_dc")

    # opcional
    if "imppt_max_a" in dc and dc["imppt_max_a"] is not None:
        _req_num(dc, "imppt_max_a", f"inversores.{iid}.entrada_dc")


def cargar_paneles_yaml(path: str = "paneles.yaml") -> Dict[str, Panel]:
    doc = _read_yaml(DATA_DIR / path)
    paneles = (doc.get("paneles") or {}) if isinstance(doc, dict) else {}

    out: Dict[str, Panel] = {}
    for pid, p in paneles.items():
        _validate_panel(pid, p)
        stc = p["stc"]
        out[pid] = Panel(
            nombre=str(p["nombre"]).strip(),
            w=float(stc["pmax_w"]),
            vmp=float(stc["vmp_v"]),
            voc=float(stc["voc_v"]),
            imp=float(stc["imp_a"]),
            isc=float(stc["isc_a"]),
        )
    return out


def cargar_inversores_yaml(path: str = "inversores.yaml") -> Dict[str, Inversor]:
    doc = _read_yaml(DATA_DIR / path)
    inversores = (doc.get("inversores") or {}) if isinstance(doc, dict) else {}

    out: Dict[str, Inversor] = {}
    for iid, inv in inversores.items():
        _validate_inversor(iid, inv)
        dc = inv["entrada_dc"]

        # pac_kw: intenta leer salida_ac.pac_kw, si no existe usa inv.pac_kw, si no 0.0
        salida = inv.get("salida_ac", {}) if isinstance(inv, dict) else {}
        pac_kw = float(salida.get("pac_kw", inv.get("pac_kw", 0.0)) or 0.0)

        out[iid] = Inversor(
            nombre=str(inv["nombre"]).strip(),
            kw_ac=pac_kw,
            n_mppt=int(dc["n_mppt"]),
            vmppt_min=float(dc["mppt_min_v"]),
            vmppt_max=float(dc["mppt_max_v"]),
            vdc_max=float(dc["vdc_max_v"]),
        )
    return out

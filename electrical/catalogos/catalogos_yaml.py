from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml
from functools import lru_cache

from electrical.modelos.paneles import PanelSpec as Panel
from electrical.modelos.inversor import InversorSpec as Inversor


DATA_DIR = Path("data")


# ==========================================================
# Lectura YAML con cache
# ==========================================================

@lru_cache(maxsize=32)
def _read_yaml_cached(path_str: str) -> Dict[str, Any]:
    path = Path(path_str)
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


# ==========================================================
# Validaciones básicas
# ==========================================================

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


def _opt_num(d: Dict[str, Any], k: str, ctx: str, default: float | None = None) -> float | None:
    if k not in d or d[k] is None:
        return default
    v = d[k]
    try:
        return float(v)
    except Exception as e:
        raise ValueError(f"'{k}' debe ser numérico en {ctx}. Valor={v!r}") from e


# ==========================================================
# Validación panel
# ==========================================================

def _validate_panel(pid: str, p: Dict[str, Any]) -> None:

    _req(p, "marca", f"paneles.{pid}")
    _req(p, "nombre", f"paneles.{pid}")
    _req(p, "codigo", f"paneles.{pid}")

    stc = _req(p, "stc", f"paneles.{pid}")

    for k in ("pmax_w", "vmp_v", "imp_a", "voc_v", "isc_a"):
        _req_num(stc, k, f"paneles.{pid}.stc")

    co = _req(p, "coeficientes_pct_c", f"paneles.{pid}")

    _req_num(co, "voc", f"paneles.{pid}.coeficientes_pct_c")

    if "vmp" in co and co["vmp"] is not None:
        _req_num(co, "vmp", f"paneles.{pid}.coeficientes_pct_c")

    if "pmax" in co and co["pmax"] is not None:
        _req_num(co, "pmax", f"paneles.{pid}.coeficientes_pct_c")


# ==========================================================
# Validación inversor
# ==========================================================

def _validate_inversor(iid: str, inv: Dict[str, Any]) -> None:

    _req(inv, "marca", f"inversores.{iid}")
    _req(inv, "nombre", f"inversores.{iid}")
    _req(inv, "codigo", f"inversores.{iid}")

    dc = _req(inv, "entrada_dc", f"inversores.{iid}")

    for k in ("vdc_max_v", "mppt_min_v", "mppt_max_v", "n_mppt"):
        _req_num(dc, k, f"inversores.{iid}.entrada_dc")

    if "imppt_max_a" in dc and dc["imppt_max_a"] is not None:
        _req_num(dc, "imppt_max_a", f"inversores.{iid}.entrada_dc")


# ==========================================================
# Carga paneles
# ==========================================================

def cargar_paneles_yaml(path: str = "paneles.yaml") -> Dict[str, Panel]:

    doc = _read_yaml_cached(str(DATA_DIR / path))
    paneles = (doc.get("paneles") or {}) if isinstance(doc, dict) else {}

    out: Dict[str, Panel] = {}

    for pid, p in paneles.items():

        _validate_panel(pid, p)

        stc = p["stc"]
        co = p.get("coeficientes_pct_c", {})

        coef_voc = float(co.get("voc"))

        coef_vmp = _opt_num(co, "vmp", f"paneles.{pid}.coeficientes_pct_c")

        if coef_vmp is None:
            coef_vmp = _opt_num(co, "pmax", f"paneles.{pid}.coeficientes_pct_c")

        if coef_vmp is None:
            coef_vmp = -0.34

        panel_obj = Panel(
            pmax_w=float(stc["pmax_w"]),
            vmp_v=float(stc["vmp_v"]),
            voc_v=float(stc["voc_v"]),
            imp_a=float(stc["imp_a"]),
            isc_a=float(stc["isc_a"]),
            coef_voc_pct_c=float(coef_voc),
            coef_vmp_pct_c=float(coef_vmp),
        )

        out[pid] = panel_obj

    return out


# ==========================================================
# Carga inversores
# ==========================================================

def cargar_inversores_yaml(path: str = "inversores.yaml") -> Dict[str, Inversor]:

    doc = _read_yaml_cached(str(DATA_DIR / path))
    inversores = (doc.get("inversores") or {}) if isinstance(doc, dict) else {}

    out: Dict[str, Inversor] = {}

    for iid, inv in inversores.items():

        _validate_inversor(iid, inv)

        dc = inv["entrada_dc"]

        salida = inv.get("salida_ac", {})
        kw_ac = float(salida.get("kw_ac", inv.get("kw_ac", 0.0)) or 0.0)

        imppt = _opt_num(dc, "imppt_max_a", f"inversores.{iid}.entrada_dc")

        inv_obj = Inversor(
            kw_ac=kw_ac,
            n_mppt=int(dc["n_mppt"]),
            mppt_min_v=float(dc["mppt_min_v"]),
            mppt_max_v=float(dc["mppt_max_v"]),
            vdc_max_v=float(dc["vdc_max_v"]),
            imppt_max_a=imppt,
        )

        out[iid] = inv_obj

    return out

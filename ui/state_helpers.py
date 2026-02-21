# ui/state_helpers.py
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict


# Solo INPUTS. No metas resultados aquí.
_FINGERPRINT_KEYS = ("datos_cliente", "consumo", "sistema_fv", "equipos", "electrico")

# Subset estable de inputs eléctricos (evita “stale” por outputs guardados en ctx.electrico)
_ELECTRICO_INPUT_KEYS = (
    "vac",
    "fases",
    "fp",
    "dist_dc_m",
    "dist_ac_m",
    "vdrop_obj_dc_pct",
    "vdrop_obj_ac_pct",
    "t_min_c",
    "incluye_neutro_ac",
    "otros_ccc",
    "dos_aguas",
)


def ensure_dict(ctx: Any, key: str, default_factory: Callable[[], Dict[str, Any]] | None = None) -> Dict[str, Any]:
    if default_factory is None:
        default_factory = dict

    cur = getattr(ctx, key, None)
    if not isinstance(cur, dict):
        cur = default_factory() or {}
        setattr(ctx, key, cur)
    return cur


def merge_defaults(dst: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in (defaults or {}).items():
        dst.setdefault(k, v)
    return dst


def sync_fields(dst: Dict[str, Any], mapping: Dict[str, str] | Callable[[Dict[str, Any]], None]) -> Dict[str, Any]:
    if callable(mapping):
        mapping(dst)
        return dst

    for src, target in (mapping or {}).items():
        if src in dst:
            dst[target] = dst[src]
    return dst


def _norm_value(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _norm_value(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, list):
        return [_norm_value(v) for v in x]
    if isinstance(x, tuple):
        return [_norm_value(v) for v in x]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return str(x)


def _electrico_inputs_only(e: Any) -> Dict[str, Any]:
    """
    Evita que el fingerprint cambie si alguien guarda resultados o campos extra en ctx.electrico.
    Solo tomamos las keys eléctricas de INPUT.
    """
    if not isinstance(e, dict):
        return {}
    return {k: _norm_value(e.get(k)) for k in _ELECTRICO_INPUT_KEYS if k in e}


def build_inputs_fingerprint(ctx: Any) -> str:
    payload: Dict[str, Any] = {}

    for k in _FINGERPRINT_KEYS:
        v = getattr(ctx, k, None)

        if k == "electrico":
            payload[k] = _electrico_inputs_only(v)
        else:
            payload[k] = _norm_value(v)

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def save_result_fingerprint(ctx: Any) -> str:
    fp = build_inputs_fingerprint(ctx)
    setattr(ctx, "result_inputs_fingerprint", fp)
    return fp


def is_result_stale(ctx: Any) -> bool:
    saved = getattr(ctx, "result_inputs_fingerprint", None)
    if not saved:
        return False
    return str(saved) != build_inputs_fingerprint(ctx)

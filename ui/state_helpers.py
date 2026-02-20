from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict


_FINGERPRINT_KEYS = ("datos_cliente", "consumo", "sistema_fv", "equipos", "electrico")


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


def build_inputs_fingerprint(ctx: Any) -> str:
    payload = {k: _norm_value(getattr(ctx, k, None)) for k in _FINGERPRINT_KEYS}
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

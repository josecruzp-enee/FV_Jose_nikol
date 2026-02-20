from __future__ import annotations

from typing import Any, Callable, Dict


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

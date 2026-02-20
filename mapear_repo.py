#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mapear_repo.py
Mapa + análisis de arquitectura: módulos, imports, funciones/clases + deps + duplicados + tablas repetidas.

Uso:
  python mapear_repo.py --root . --out mapa_repo.txt
  python mapear_repo.py --root . --out mapa_repo.txt --include-tests
  python mapear_repo.py --root . --out mapa_repo.txt --json mapa_repo.json
  python mapear_repo.py --root . --out mapa_repo.txt --focus electrical
  python mapear_repo.py --root . --out mapa_repo.txt --deps
  python mapear_repo.py --root . --out mapa_repo.txt --dups
  python mapear_repo.py --root . --out mapa_repo.txt --tables
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set


# ==========================================================
# Modelos
# ==========================================================
@dataclass
class FuncInfo:
    name: str
    lineno: int
    signature: str
    is_async: bool
    is_method: bool


@dataclass
class ClassInfo:
    name: str
    lineno: int
    bases: List[str]
    methods: List[FuncInfo]


@dataclass
class ImportInfo:
    raw: str
    lineno: int
    kind: str  # "import" | "from"
    module: str  # nombre del módulo importado (sin alias)
    is_relative: bool


@dataclass
class TableInfo:
    name: str
    lineno: int
    kind: str  # "dict" | "list" | "set" | "tuple"
    n_items: int
    keys_sample: List[str]
    fingerprint: str  # huella por keys/valores simples


@dataclass
class FileInfo:
    rel_path: str
    module: str
    imports: List[str]
    import_infos: List[ImportInfo]
    functions: List[FuncInfo]
    classes: List[ClassInfo]
    tables: List[TableInfo]
    loc: int
    parse_error: Optional[str] = None


# ==========================================================
# Main
# ==========================================================
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Root del repo")
    ap.add_argument("--out", default="mapa_repo.txt", help="Salida TXT")
    ap.add_argument("--json", default="", help="Salida JSON (opcional)")
    ap.add_argument("--include-tests", action="store_true", help="Incluye tests/ y archivos *_test.py")
    ap.add_argument("--focus", default="", help="Filtra por prefijo de ruta (ej: electrical o core)")
    ap.add_argument("--deps", action="store_true", help="Incluye secciones de dependencias/import graph")
    ap.add_argument("--dups", action="store_true", help="Incluye secciones de duplicados")
    ap.add_argument("--tables", action="store_true", help="Incluye análisis de tablas/dicts grandes")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_path = Path(args.out).resolve()
    json_path = Path(args.json).resolve() if args.json else None

    py_files = _listar_py(root, include_tests=args.include_tests, focus=args.focus)
    infos: List[FileInfo] = [_analizar_archivo(root, f) for f in py_files]

    txt = _render_txt(root, infos, show_deps=args.deps, show_dups=args.dups, show_tables=args.tables)
    out_path.write_text(txt, encoding="utf-8")
    print(f"OK: generado {out_path} ({len(infos)} archivos .py)")

    if json_path:
        payload = _render_json(root, infos)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: generado {json_path}")

    return 0


# ==========================================================
# Descubrimiento de archivos
# ==========================================================
def _listar_py(root: Path, *, include_tests: bool, focus: str) -> List[Path]:
    out: List[Path] = []
    focus = (focus or "").strip().replace("\\", "/").strip("/")
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()

        if any(x in rel for x in ["/.git/", "/__pycache__/", "/.venv/", "/venv/", "/.tox/"]):
            continue
        if any(rel.startswith(x) for x in ["build/", "dist/"]):
            continue
        if not include_tests:
            if rel.startswith("tests/") or rel.endswith("_test.py") or rel.endswith("test_.py"):
                continue
        if focus and not rel.startswith(focus + "/") and rel != f"{focus}.py":
            continue

        out.append(p)

    out.sort()
    return out


# ==========================================================
# Análisis AST
# ==========================================================
def _analizar_archivo(root: Path, path: Path) -> FileInfo:
    rel = path.relative_to(root).as_posix()
    module = _ruta_a_modulo(root, path)

    try:
        src = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        src = path.read_text(encoding="latin-1")

    loc = sum(1 for _ in src.splitlines())

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return FileInfo(
            rel_path=rel,
            module=module,
            imports=[],
            import_infos=[],
            functions=[],
            classes=[],
            tables=[],
            loc=loc,
            parse_error=f"SyntaxError: {e.msg} (line {e.lineno})",
        )

    visitor = _Visitor()
    visitor.visit(tree)

    return FileInfo(
        rel_path=rel,
        module=module,
        imports=visitor.imports,
        import_infos=visitor.import_infos,
        functions=visitor.functions,
        classes=visitor.classes,
        tables=visitor.tables,
        loc=loc,
    )


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: List[str] = []
        self.import_infos: List[ImportInfo] = []
        self.functions: List[FuncInfo] = []
        self.classes: List[ClassInfo] = []
        self.tables: List[TableInfo] = []
        self._class_stack: List[ClassInfo] = []

    # ---------- imports ----------
    def visit_Import(self, node: ast.Import) -> None:
        for a in node.names:
            raw = f"import {a.name} as {a.asname}  (L{node.lineno})" if a.asname else f"import {a.name}  (L{node.lineno})"
            self.imports.append(raw)
            self.import_infos.append(ImportInfo(raw=raw, lineno=node.lineno, kind="import", module=a.name, is_relative=False))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = "." * (node.level or 0) + (node.module or "")
        names = [(f"{a.name} as {a.asname}" if a.asname else a.name) for a in node.names]
        raw = f"from {mod} import {', '.join(names)}  (L{node.lineno})"
        self.imports.append(raw)

        # para deps: módulo origen (sin los nombres importados)
        is_rel = bool(node.level and node.level > 0)
        base_mod = (node.module or "")
        self.import_infos.append(ImportInfo(raw=raw, lineno=node.lineno, kind="from", module=base_mod, is_relative=is_rel))

    # ---------- funcs ----------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_func(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_func(node, is_async=True)

    def _handle_func(self, node: ast.AST, *, is_async: bool) -> None:
        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        sig = _firma_func(node)
        fi = FuncInfo(
            name=node.name,
            lineno=getattr(node, "lineno", 0),
            signature=sig,
            is_async=is_async,
            is_method=bool(self._class_stack),
        )
        if self._class_stack:
            self._class_stack[-1].methods.append(fi)
        else:
            self.functions.append(fi)
        self.generic_visit(node)

    # ---------- classes ----------
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [_expr_str(b) for b in (node.bases or [])]
        ci = ClassInfo(name=node.name, lineno=node.lineno, bases=bases, methods=[])
        self._class_stack.append(ci)
        self.generic_visit(node)
        self._class_stack.pop()
        self.classes.append(ci)

    # ---------- tables ----------
    def visit_Assign(self, node: ast.Assign) -> None:
        # Solo top-level: si estamos dentro de clase, ignoramos
        if self._class_stack:
            return

        # buscamos patrones: NOMBRE = { ... } / [ ... ] / ( ... ) / set(...)
        name = _first_target_name(node.targets)
        if not name:
            return

        ti = _table_from_value(name, node.lineno, node.value)
        if ti:
            self.tables.append(ti)

        self.generic_visit(node)


# ==========================================================
# Render TXT / JSON + análisis
# ==========================================================
def _render_txt(root: Path, infos: List[FileInfo], *, show_deps: bool, show_dups: bool, show_tables: bool) -> str:
    total_funcs = sum(len(x.functions) for x in infos)
    total_classes = sum(len(x.classes) for x in infos)
    total_methods = sum(sum(len(c.methods) for c in x.classes) for x in infos)
    total_imports = sum(len(x.imports) for x in infos)
    parse_errors = [x for x in infos if x.parse_error]

    lines: List[str] = []
    lines.append("MAPA DEL REPO (módulos, imports, funciones, clases)")
    lines.append(f"Root: {root.as_posix()}")
    lines.append("")
    lines.append("RESUMEN")
    lines.append(f"- Archivos .py: {len(infos)}")
    lines.append(f"- Imports: {total_imports}")
    lines.append(f"- Funciones (top-level): {total_funcs}")
    lines.append(f"- Clases: {total_classes}")
    lines.append(f"- Métodos: {total_methods}")
    lines.append(f"- Archivos con error de parseo: {len(parse_errors)}")
    lines.append("")

    if parse_errors:
        lines.append("ARCHIVOS CON ERRORES DE PARSEO")
        for x in parse_errors:
            lines.append(f"- {x.rel_path}: {x.parse_error}")
        lines.append("")

    # ---- ranking archivos “pesados” ----
    lines.extend(_seccion_pesos(infos))

    # ---- deps / duplicados / tablas ----
    if show_deps:
        lines.extend(_seccion_deps(root, infos))
    if show_dups:
        lines.extend(_seccion_dups(infos))
    if show_tables:
        lines.extend(_seccion_tablas(infos))

    # ---- detalle por archivo (como tu versión) ----
    lines.append("DETALLE POR ARCHIVO")
    lines.append("=" * 80)

    for x in infos:
        lines.append(f"\nFILE: {x.rel_path}")
        lines.append(f"MODULE: {x.module}")
        lines.append(f"LOC: {x.loc}")
        if x.parse_error:
            lines.append(f"PARSE_ERROR: {x.parse_error}")
            continue

        if x.imports:
            lines.append("\n  IMPORTS:")
            for imp in x.imports:
                lines.append(f"    - {imp}")
        else:
            lines.append("\n  IMPORTS: (none)")

        if x.functions:
            lines.append("\n  FUNCIONES:")
            for f in sorted(x.functions, key=lambda z: z.lineno):
                a = "async " if f.is_async else ""
                lines.append(f"    - L{f.lineno}: {a}{f.signature}")
        else:
            lines.append("\n  FUNCIONES: (none)")

        if x.classes:
            lines.append("\n  CLASES:")
            for c in sorted(x.classes, key=lambda z: z.lineno):
                bases = f"({', '.join(c.bases)})" if c.bases else ""
                lines.append(f"    - L{c.lineno}: class {c.name}{bases}")
                if c.methods:
                    for m in sorted(c.methods, key=lambda z: z.lineno):
                        a = "async " if m.is_async else ""
                        lines.append(f"        * L{m.lineno}: {a}{m.signature}")
                else:
                    lines.append("        * (sin métodos)")
        else:
            lines.append("\n  CLASES: (none)")

        if x.tables:
            lines.append("\n  TABLAS/CONSTANTES (top-level):")
            for t in sorted(x.tables, key=lambda z: z.lineno):
                lines.append(f"    - L{t.lineno}: {t.name} [{t.kind}] items={t.n_items} fp={t.fingerprint}")
        else:
            lines.append("\n  TABLAS/CONSTANTES (top-level): (none)")

        lines.append("\n" + "-" * 80)

    return "\n".join(lines) + "\n"


def _render_json(root: Path, infos: List[FileInfo]) -> Dict[str, Any]:
    return {
        "root": root.as_posix(),
        "summary": {
            "py_files": len(infos),
            "imports": sum(len(x.imports) for x in infos),
            "functions_top_level": sum(len(x.functions) for x in infos),
            "classes": sum(len(x.classes) for x in infos),
            "methods": sum(sum(len(c.methods) for c in x.classes) for x in infos),
            "parse_errors": sum(1 for x in infos if x.parse_error),
        },
        "files": [asdict(x) for x in infos],
        "analysis": {
            "heavy_files": _heavy_files(infos),
            "deps": _deps_payload(root, infos),
            "dups": _dups_payload(infos),
            "tables": _tables_payload(infos),
        },
    }


# ==========================================================
# Secciones “inteligentes”
# ==========================================================
def _seccion_pesos(infos: List[FileInfo]) -> List[str]:
    # score: loc + 20*imports + 15*funcs + 25*classes (heurístico)
    scored = []
    for x in infos:
        if x.parse_error:
            continue
        score = x.loc + 20 * len(x.imports) + 15 * len(x.functions) + 25 * len(x.classes)
        scored.append((score, x))
    scored.sort(key=lambda t: t[0], reverse=True)

    out: List[str] = []
    out.append("ARCHIVOS MÁS PESADOS (heurístico)")
    out.append("-" * 80)
    for score, x in scored[:10]:
        out.append(f"- {x.rel_path}: score={score} | loc={x.loc} | imports={len(x.imports)} | funcs={len(x.functions)} | clases={len(x.classes)} | tablas={len(x.tables)}")
    out.append("")
    return out


def _deps_payload(root: Path, infos: List[FileInfo]) -> Dict[str, Any]:
    internal = _internal_modules_set(infos)
    edges: Dict[str, Set[str]] = {}
    for fi in infos:
        if fi.parse_error:
            continue
        deps = _deps_for_file(fi, internal)
        edges[fi.module] = set(sorted(deps))
    indeg: Dict[str, int] = {m: 0 for m in edges}
    for m, ds in edges.items():
        for d in ds:
            if d in indeg:
                indeg[d] += 1
    top = sorted(indeg.items(), key=lambda t: t[1], reverse=True)[:15]
    return {"edges": {k: sorted(v) for k, v in edges.items()}, "top_imported": top}


def _seccion_deps(root: Path, infos: List[FileInfo]) -> List[str]:
    payload = _deps_payload(root, infos)
    out: List[str] = []
    out.append("DEPENDENCIAS ENTRE MÓDULOS (imports internos)")
    out.append("-" * 80)

    out.append("MÓDULOS MÁS IMPORTADOS (top 15)")
    for m, n in payload["top_imported"]:
        out.append(f"- {m}: {n} imports internos")
    out.append("")

    # mostrar edges solo para los 20 módulos más “salientes”
    edges = payload["edges"]
    ranked = sorted(edges.items(), key=lambda kv: len(kv[1]), reverse=True)[:20]
    out.append("TOP MÓDULOS QUE MÁS IMPORTAN OTROS (top 20)")
    for mod, deps in ranked:
        out.append(f"- {mod} -> {len(deps)} deps")
        for d in deps[:12]:
            out.append(f"    * {d}")
        if len(deps) > 12:
            out.append("    * ...")
    out.append("")
    return out


def _dups_payload(infos: List[FileInfo]) -> Dict[str, Any]:
    # duplicados por nombre y por firma “normalizada”
    by_name: Dict[str, List[Tuple[str, int, str]]] = {}
    by_sig: Dict[str, List[Tuple[str, int, str]]] = {}

    for fi in infos:
        if fi.parse_error:
            continue
        for f in fi.functions:
            by_name.setdefault(f.name, []).append((fi.rel_path, f.lineno, f.signature))
            by_sig.setdefault(_norm_sig(f.signature), []).append((fi.rel_path, f.lineno, f.signature))

    dup_names = {k: v for k, v in by_name.items() if len(v) >= 2}
    dup_sigs = {k: v for k, v in by_sig.items() if len(v) >= 2}

    # ordenar por cantidad de colisiones
    top_names = sorted(dup_names.items(), key=lambda kv: len(kv[1]), reverse=True)[:30]
    top_sigs = sorted(dup_sigs.items(), key=lambda kv: len(kv[1]), reverse=True)[:30]
    return {"by_name_top": top_names, "by_signature_top": top_sigs}


def _seccion_dups(infos: List[FileInfo]) -> List[str]:
    payload = _dups_payload(infos)
    out: List[str] = []
    out.append("DUPLICADOS (funciones top-level)")
    out.append("-" * 80)

    out.append("NOMBRES REPETIDOS (top 30)")
    for name, occ in payload["by_name_top"]:
        out.append(f"- {name}: {len(occ)} ocurrencias")
        for rel, ln, sig in occ[:8]:
            out.append(f"    * {rel}:L{ln} {sig}")
        if len(occ) > 8:
            out.append("    * ...")
    out.append("")

    out.append("FIRMAS NORMALIZADAS REPETIDAS (top 30)")
    for nsig, occ in payload["by_signature_top"]:
        out.append(f"- {nsig}: {len(occ)} ocurrencias")
        for rel, ln, sig in occ[:8]:
            out.append(f"    * {rel}:L{ln} {sig}")
        if len(occ) > 8:
            out.append("    * ...")
    out.append("")
    return out


def _tables_payload(infos: List[FileInfo]) -> Dict[str, Any]:
    # agrupamos por fingerprint para detectar tablas repetidas
    groups: Dict[str, List[Tuple[str, int, str, int, List[str]]]] = {}
    for fi in infos:
        if fi.parse_error:
            continue
        for t in fi.tables:
            # solo tablas “grandes” o interesantes
            if t.n_items < 6:
                continue
            groups.setdefault(t.fingerprint, []).append((fi.rel_path, t.lineno, t.name, t.n_items, t.keys_sample))
    dup = {fp: occ for fp, occ in groups.items() if len(occ) >= 2}
    top = sorted(dup.items(), key=lambda kv: len(kv[1]), reverse=True)[:30]
    return {"duplicates_top": top}


def _seccion_tablas(infos: List[FileInfo]) -> List[str]:
    payload = _tables_payload(infos)
    out: List[str] = []
    out.append("TABLAS / CONSTANTES REPETIDAS (heurística por fingerprint)")
    out.append("-" * 80)

    if not payload["duplicates_top"]:
        out.append("(no se detectaron tablas repetidas con fingerprint similar)")
        out.append("")
        return out

    for fp, occ in payload["duplicates_top"]:
        out.append(f"- fp={fp} | {len(occ)} ocurrencias")
        for rel, ln, name, n, sample in occ[:10]:
            out.append(f"    * {rel}:L{ln} {name} items={n} keys~{sample}")
        if len(occ) > 10:
            out.append("    * ...")
    out.append("")
    out.append("SUGERENCIA: si fp coincide en 2+ archivos, centraliza esa tabla en un solo módulo (source of truth).")
    out.append("")
    return out


def _heavy_files(infos: List[FileInfo]) -> List[Dict[str, Any]]:
    scored = []
    for x in infos:
        if x.parse_error:
            continue
        score = x.loc + 20 * len(x.imports) + 15 * len(x.functions) + 25 * len(x.classes)
        scored.append((score, x))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [{"rel_path": x.rel_path, "score": s, "loc": x.loc, "imports": len(x.imports), "funcs": len(x.functions), "classes": len(x.classes), "tables": len(x.tables)} for s, x in scored[:15]]


# ==========================================================
# Dependencias internas
# ==========================================================
def _internal_modules_set(infos: List[FileInfo]) -> Set[str]:
    # módulos python internos del repo
    return {fi.module for fi in infos if not fi.parse_error}

def _deps_for_file(fi: FileInfo, internal_modules: Set[str]) -> List[str]:
    deps: Set[str] = set()

    for imp in fi.import_infos:
        # import X / from X import Y
        if imp.kind == "import":
            mod = imp.module
            # tomamos paquete base
            base = mod.split(".")[0]
            # si existe módulo interno exacto o paquete base, lo contamos
            if mod in internal_modules:
                deps.add(mod)
            elif base in internal_modules:
                deps.add(base)
        else:
            # from .algo import ...
            if imp.is_relative:
                # relativo: lo tratamos como dependencia del paquete del archivo
                # ej: core.sizing from .modelo -> depende de core.modelo
                pkg = fi.module.rsplit(".", 1)[0] if "." in fi.module else ""
                if pkg and imp.module:
                    guess = f"{pkg}.{imp.module}".strip(".")
                    if guess in internal_modules:
                        deps.add(guess)
                continue

            # absoluto
            mod = imp.module
            base = mod.split(".")[0] if mod else ""
            if mod in internal_modules:
                deps.add(mod)
            elif base in internal_modules:
                deps.add(base)

    return sorted(deps)


# ==========================================================
# Helpers de firma / strings / tablas
# ==========================================================
def _ruta_a_modulo(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)

def _firma_func(node: ast.AST) -> str:
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    args = node.args
    parts: List[str] = []

    for a in args.posonlyargs:
        parts.append(a.arg)
    if args.posonlyargs:
        parts.append("/")

    for a in args.args:
        parts.append(a.arg)

    if args.vararg:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")

    for a in args.kwonlyargs:
        parts.append(a.arg)

    if args.kwarg:
        parts.append("**" + args.kwarg.arg)

    return f"def {node.name}({', '.join(parts)})"

def _norm_sig(sig: str) -> str:
    # normaliza: quita nombre de función, deja “forma” de args
    # def foo(a,b,*args,**kw) -> (a,b,*args,**kw)
    if "(" not in sig or ")" not in sig:
        return sig.strip()
    inside = sig.split("(", 1)[1].rsplit(")", 1)[0].strip()
    return f"({inside})"

def _expr_str(e: ast.AST) -> str:
    try:
        return ast.unparse(e)  # type: ignore[attr-defined]
    except Exception:
        return e.__class__.__name__

def _first_target_name(targets: List[ast.expr]) -> str:
    # soporta: X = ... ; (X, Y) = ...
    if not targets:
        return ""
    t = targets[0]
    if isinstance(t, ast.Name):
        return t.id
    if isinstance(t, ast.Tuple) and t.elts and isinstance(t.elts[0], ast.Name):
        return t.elts[0].id
    return ""

def _table_from_value(name: str, lineno: int, value: ast.AST) -> Optional[TableInfo]:
    # dict literal
    if isinstance(value, ast.Dict):
        n = len(value.keys)
        keys = [_lit_key(k) for k in value.keys[:10]]
        fp = _fingerprint_dict(value)
        return TableInfo(name=name, lineno=lineno, kind="dict", n_items=n, keys_sample=keys, fingerprint=fp)

    # list / tuple / set literal
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        n = len(value.elts)
        sample = [_lit_key(e) for e in value.elts[:10]]
        fp = f"{value.__class__.__name__}:{','.join(sample)}"
        kind = "list" if isinstance(value, ast.List) else ("tuple" if isinstance(value, ast.Tuple) else "set")
        return TableInfo(name=name, lineno=lineno, kind=kind, n_items=n, keys_sample=sample, fingerprint=fp)

    # set(...) / dict(...)
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in ("set", "dict", "list", "tuple"):
        # si es dict({...}) o set([...]) lo ignoramos para mantener robusto
        return None

    return None

def _lit_key(node: Optional[ast.AST]) -> str:
    if node is None:
        return "None"
    if isinstance(node, ast.Constant):
        return str(node.value)
    # para keys no-constantes: intenta unparse
    return _expr_str(node)

def _fingerprint_dict(d: ast.Dict) -> str:
    # huella basada en conjunto de keys (ordenadas) y “tipo” de valores simples
    keys = []
    vtypes = []
    for k, v in zip(d.keys, d.values):
        keys.append(_lit_key(k))
        vtypes.append(_val_type(v))
    keys_s = "|".join(sorted(keys))
    vt_s = "|".join(sorted(vtypes))
    return f"dict:k={keys_s}::v={vt_s}"

def _val_type(v: ast.AST) -> str:
    if isinstance(v, ast.Constant):
        return f"const:{type(v.value).__name__}"
    if isinstance(v, ast.Dict):
        return "dict"
    if isinstance(v, ast.List):
        return "list"
    if isinstance(v, ast.Tuple):
        return "tuple"
    if isinstance(v, ast.Set):
        return "set"
    return v.__class__.__name__


if __name__ == "__main__":
    raise SystemExit(main())

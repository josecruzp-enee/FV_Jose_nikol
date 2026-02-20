#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mapear_repo.py
Genera un TXT con mapa del sistema: módulos, imports, funciones y clases.

Uso:
  python mapear_repo.py --root . --out mapa_repo.txt
  python mapear_repo.py --root . --out mapa_repo.txt --include-tests
"""

from __future__ import annotations

import argparse
import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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
class FileInfo:
    rel_path: str
    module: str
    imports: List[str]
    functions: List[FuncInfo]
    classes: List[ClassInfo]
    parse_error: Optional[str] = None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Root del repo")
    ap.add_argument("--out", default="mapa_repo.txt", help="Salida TXT")
    ap.add_argument("--include-tests", action="store_true", help="Incluye tests/ y archivos *_test.py")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_path = Path(args.out).resolve()

    py_files = _listar_py(root, include_tests=args.include_tests)
    infos: List[FileInfo] = []

    for f in py_files:
        infos.append(_analizar_archivo(root, f))

    txt = _render_txt(root, infos)
    out_path.write_text(txt, encoding="utf-8")

    print(f"OK: generado {out_path} ({len(infos)} archivos .py)")
    return 0


# -------------------------
# Descubrimiento de archivos
# -------------------------
def _listar_py(root: Path, *, include_tests: bool) -> List[Path]:
    out: List[Path] = []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()

        # ignora venv, .git, __pycache__
        if any(x in rel for x in ["/.git/", "/__pycache__/", "/.venv/", "/venv/", "/.tox/"]):
            continue

        # ignora carpetas típicas de build
        if any(rel.startswith(x) for x in ["build/", "dist/"]):
            continue

        if not include_tests:
            if rel.startswith("tests/") or rel.endswith("_test.py") or rel.endswith("test_.py"):
                continue

        out.append(p)
    out.sort()
    return out


# -------------------------
# Análisis AST
# -------------------------
def _analizar_archivo(root: Path, path: Path) -> FileInfo:
    rel = path.relative_to(root).as_posix()
    module = _ruta_a_modulo(root, path)

    try:
        src = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # fallback
        src = path.read_text(encoding="latin-1")

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return FileInfo(
            rel_path=rel,
            module=module,
            imports=[],
            functions=[],
            classes=[],
            parse_error=f"SyntaxError: {e.msg} (line {e.lineno})",
        )

    visitor = _Visitor()
    visitor.visit(tree)

    return FileInfo(
        rel_path=rel,
        module=module,
        imports=visitor.imports,
        functions=visitor.functions,
        classes=visitor.classes,
    )


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: List[str] = []
        self.functions: List[FuncInfo] = []
        self.classes: List[ClassInfo] = []

        self._class_stack: List[ClassInfo] = []

    def visit_Import(self, node: ast.Import) -> None:
        for a in node.names:
            if a.asname:
                self.imports.append(f"import {a.name} as {a.asname}  (L{node.lineno})")
            else:
                self.imports.append(f"import {a.name}  (L{node.lineno})")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = "." * (node.level or 0) + (node.module or "")
        names = []
        for a in node.names:
            names.append(f"{a.name} as {a.asname}" if a.asname else a.name)
        self.imports.append(f"from {mod} import {', '.join(names)}  (L{node.lineno})")

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

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [_expr_str(b) for b in (node.bases or [])]
        ci = ClassInfo(name=node.name, lineno=node.lineno, bases=bases, methods=[])
        self._class_stack.append(ci)

        # visitar cuerpo
        self.generic_visit(node)

        self._class_stack.pop()
        self.classes.append(ci)


# -------------------------
# Render TXT
# -------------------------
def _render_txt(root: Path, infos: List[FileInfo]) -> str:
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

    lines.append("DETALLE POR ARCHIVO")
    lines.append("=" * 80)

    for x in infos:
        lines.append(f"\nFILE: {x.rel_path}")
        lines.append(f"MODULE: {x.module}")
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

        lines.append("\n" + "-" * 80)

    return "\n".join(lines) + "\n"


# -------------------------
# Helpers de firma / strings
# -------------------------
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
    # pos-only
    for a in args.posonlyargs:
        parts.append(_arg_str(a))
    if args.posonlyargs:
        parts.append("/")

    # args normales
    for a in args.args:
        parts.append(_arg_str(a))

    # *args o *
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")

    # kw-only
    for a in args.kwonlyargs:
        parts.append(_arg_str(a))

    # **kwargs
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)

    return f"def {node.name}({', '.join(parts)})"


def _arg_str(a: ast.arg) -> str:
    # no imprimimos anotaciones para mantenerlo simple/robusto
    return a.arg


def _expr_str(e: ast.AST) -> str:
    # compat robusta para python 3.10+ (sin ast.unparse depender)
    try:
        return ast.unparse(e)  # type: ignore[attr-defined]
    except Exception:
        return e.__class__.__name__


if __name__ == "__main__":
    raise SystemExit(main())

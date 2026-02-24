# tools/resumen_paneles.py
from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class DefInfo:
    kind: str            # "function" | "class"
    name: str
    lineno: int
    doc1: str


@dataclass
class FileInfo:
    path: str
    module: str
    imports: List[str]
    from_imports: List[Tuple[str, List[str]]]
    defs: List[DefInfo]
    calls: Set[str]


def _doc1(node: ast.AST) -> str:
    s = ast.get_docstring(node) or ""
    s = s.strip().splitlines()[0].strip() if s.strip() else ""
    return s[:180]


def _module_name(root: str, filepath: str) -> str:
    rel = os.path.relpath(filepath, root).replace(os.sep, "/")
    rel = rel[:-3] if rel.endswith(".py") else rel
    return rel.replace("/", ".")


def _scan_file(root: str, filepath: str) -> FileInfo:
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()

    tree = ast.parse(src, filename=filepath)

    imports: List[str] = []
    from_imports: List[Tuple[str, List[str]]] = []
    defs: List[DefInfo] = []
    calls: Set[str] = set()

    # recolectar imports + defs
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = [n.name for n in node.names]
            from_imports.append((mod, names))
        elif isinstance(node, ast.FunctionDef):
            defs.append(DefInfo("function", node.name, getattr(node, "lineno", -1), _doc1(node)))
        elif isinstance(node, ast.ClassDef):
            defs.append(DefInfo("class", node.name, getattr(node, "lineno", -1), _doc1(node)))
        elif isinstance(node, ast.Call):
            # intento simple: nombre directo foo() o modulo.foo()
            fn = node.func
            if isinstance(fn, ast.Name):
                calls.add(fn.id)
            elif isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                calls.add(f"{fn.value.id}.{fn.attr}")

    return FileInfo(
        path=filepath,
        module=_module_name(root, filepath),
        imports=sorted(set(imports)),
        from_imports=sorted(from_imports, key=lambda x: x[0]),
        defs=sorted(defs, key=lambda d: (d.kind, d.name)),
        calls=set(sorted(calls)),
    )


def _iter_py_files(folder: str) -> List[str]:
    out: List[str] = []
    for dirpath, _, filenames in os.walk(folder):
        for fn in filenames:
            if fn.endswith(".py") and not fn.startswith("."):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def _is_internal_import(mod: str) -> bool:
    # heurística: imports relativos o paquete electrical.*
    return mod.startswith(".") or mod.startswith("electrical") or mod.startswith("paneles")


def _md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def main() -> None:
    repo_root = os.getcwd()
    paneles_dir = os.path.join(repo_root, "electrical", "paneles")
    if not os.path.isdir(paneles_dir):
        raise SystemExit(f"No existe carpeta: {paneles_dir}")

    files = _iter_py_files(paneles_dir)
    infos = [_scan_file(repo_root, p) for p in files]

    # matriz de dependencias por imports (simple)
    dep_edges: Set[Tuple[str, str]] = set()
    for fi in infos:
        for mod, _names in fi.from_imports:
            if mod:
                dep_edges.add((fi.module, mod))
        for imp in fi.imports:
            dep_edges.add((fi.module, imp))

    # reporte
    lines: List[str] = []
    lines.append("# Resumen automático — electrical/paneles\n")
    lines.append("## Archivos\n")
    for fi in infos:
        lines.append(f"### {fi.module}\n")
        lines.append(f"- Ruta: `{os.path.relpath(fi.path, repo_root)}`\n")
        if fi.imports or fi.from_imports:
            lines.append("- Imports:\n")
            for imp in fi.imports:
                lines.append(f"  - `import {imp}`\n")
            for mod, names in fi.from_imports:
                nm = ", ".join(names)
                lines.append(f"  - `from {mod} import {nm}`\n")
        if fi.defs:
            lines.append("- Definiciones:\n")
            for d in fi.defs:
                doc = f" — {_md_escape(d.doc1)}" if d.doc1 else ""
                lines.append(f"  - **{d.kind}** `{d.name}` (L{d.lineno}){doc}\n")
        if fi.calls:
            # limitar para no explotar
            calls = sorted(list(fi.calls))[:40]
            lines.append(f"- Llamadas detectadas (muestra ≤40): {', '.join(f'`{c}`' for c in calls)}\n")
        lines.append("\n")

    lines.append("## Dependencias (por imports)\n")
    for a, b in sorted(dep_edges):
        if _is_internal_import(b):
            lines.append(f"- `{a}` → `{b}`\n")

    out_path = os.path.join(repo_root, "resumen_paneles.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    print(f"OK: generado {out_path}")


if __name__ == "__main__":
    main()

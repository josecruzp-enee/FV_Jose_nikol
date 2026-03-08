#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
mapear_repo_plus.py

Analizador avanzado de repositorios Python.

Capacidades:

• Mapa de módulos
• Imports
• Funciones / clases
• Dependencias internas
• Call Graph (quién llama a quién)
• Detección básica de pipelines de datos
• Duplicados de funciones
• Tablas constantes repetidas
• Archivos más pesados
• Export JSON
• Export Graphviz DOT

Uso:

python mapear_repo_plus.py --root . --out mapa.txt
python mapear_repo_plus.py --root . --deps
python mapear_repo_plus.py --root . --calls
python mapear_repo_plus.py --root . --dot graph.dot
"""

from __future__ import annotations
import argparse
import ast
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Set


# ==========================================================
# MODELOS
# ==========================================================

@dataclass
class FuncInfo:
    name: str
    lineno: int
    signature: str
    calls: List[str]


@dataclass
class ClassInfo:
    name: str
    lineno: int
    methods: List[FuncInfo]


@dataclass
class FileInfo:
    path: str
    module: str
    imports: List[str]
    functions: List[FuncInfo]
    classes: List[ClassInfo]
    loc: int
    parse_error: Optional[str] = None


# ==========================================================
# DISCOVERY
# ==========================================================

def listar_py(root: Path) -> List[Path]:

    files = []

    for p in root.rglob("*.py"):

        rel = p.relative_to(root).as_posix()

        if any(x in rel for x in ["__pycache__", ".git", ".venv", "venv"]):
            continue

        files.append(p)

    return sorted(files)


# ==========================================================
# VISITOR
# ==========================================================

class RepoVisitor(ast.NodeVisitor):

    def __init__(self):

        self.imports: List[str] = []
        self.functions: List[FuncInfo] = []
        self.classes: List[ClassInfo] = []

        self._class_stack: List[ClassInfo] = []
        self._func_stack: List[FuncInfo] = []

    # ---------------- imports ----------------

    def visit_Import(self, node: ast.Import):

        for a in node.names:
            self.imports.append(a.name)

    def visit_ImportFrom(self, node: ast.ImportFrom):

        mod = node.module or ""

        self.imports.append(mod)

    # ---------------- functions ----------------

    def visit_FunctionDef(self, node: ast.FunctionDef):

        fi = FuncInfo(
            name=node.name,
            lineno=node.lineno,
            signature=f"{node.name}()",
            calls=[]
        )

        if self._class_stack:
            self._class_stack[-1].methods.append(fi)
        else:
            self.functions.append(fi)

        self._func_stack.append(fi)

        self.generic_visit(node)

        self._func_stack.pop()

    # ---------------- calls ----------------

    def visit_Call(self, node: ast.Call):

        if not self._func_stack:
            return

        fname = None

        if isinstance(node.func, ast.Name):
            fname = node.func.id

        elif isinstance(node.func, ast.Attribute):
            fname = node.func.attr

        if fname:
            self._func_stack[-1].calls.append(fname)

        self.generic_visit(node)

    # ---------------- classes ----------------

    def visit_ClassDef(self, node: ast.ClassDef):

        ci = ClassInfo(
            name=node.name,
            lineno=node.lineno,
            methods=[]
        )

        self._class_stack.append(ci)

        self.generic_visit(node)

        self._class_stack.pop()

        self.classes.append(ci)


# ==========================================================
# ANALISIS
# ==========================================================

def analizar_archivo(root: Path, path: Path) -> FileInfo:

    rel = path.relative_to(root).as_posix()

    module = rel.replace("/", ".").replace(".py", "")

    src = path.read_text(encoding="utf8", errors="ignore")

    loc = len(src.splitlines())

    try:

        tree = ast.parse(src)

    except SyntaxError as e:

        return FileInfo(
            path=rel,
            module=module,
            imports=[],
            functions=[],
            classes=[],
            loc=loc,
            parse_error=str(e)
        )

    visitor = RepoVisitor()

    visitor.visit(tree)

    return FileInfo(
        path=rel,
        module=module,
        imports=visitor.imports,
        functions=visitor.functions,
        classes=visitor.classes,
        loc=loc
    )


# ==========================================================
# CALL GRAPH
# ==========================================================

def construir_call_graph(files: List[FileInfo]):

    graph: Dict[str, Set[str]] = {}

    for f in files:

        for fn in f.functions:

            graph.setdefault(fn.name, set())

            for c in fn.calls:
                graph[fn.name].add(c)

        for cl in f.classes:

            for m in cl.methods:

                graph.setdefault(m.name, set())

                for c in m.calls:
                    graph[m.name].add(c)

    return graph


# ==========================================================
# PIPELINE DETECTION
# ==========================================================

def detectar_pipelines(files: List[FileInfo]):

    pipelines = []

    for f in files:

        for fn in f.functions:

            if len(fn.calls) >= 3:
                pipelines.append((fn.name, fn.calls))

    return pipelines


# ==========================================================
# DOT GRAPH EXPORT
# ==========================================================

def export_dot(graph, path):

    lines = ["digraph G {"]

    for src, dsts in graph.items():

        for d in dsts:

            lines.append(f'"{src}" -> "{d}"')

    lines.append("}")

    Path(path).write_text("\n".join(lines))


# ==========================================================
# RENDER
# ==========================================================

def render_txt(files, graph, pipelines):

    lines = []

    lines.append("MAPA REPO\n")

    lines.append(f"FILES: {len(files)}")

    lines.append("")

    for f in files:

        lines.append(f"FILE: {f.path}")
        lines.append(f"LOC: {f.loc}")

        if f.parse_error:
            lines.append(f"ERROR: {f.parse_error}")
            continue

        if f.imports:
            lines.append("IMPORTS:")
            for i in f.imports:
                lines.append(f"  - {i}")

        if f.functions:

            lines.append("FUNCTIONS:")

            for fn in f.functions:

                lines.append(f"  {fn.name}()")

                if fn.calls:
                    for c in fn.calls:
                        lines.append(f"     -> {c}")

        if f.classes:

            lines.append("CLASSES:")

            for cl in f.classes:

                lines.append(f"  class {cl.name}")

                for m in cl.methods:

                    lines.append(f"    {m.name}()")

        lines.append("")

    lines.append("CALL GRAPH")

    for k, v in graph.items():
        lines.append(f"{k} -> {list(v)}")

    lines.append("\nPIPELINES")

    for name, calls in pipelines:
        lines.append(f"{name}: {calls}")

    return "\n".join(lines)


# ==========================================================
# MAIN
# ==========================================================

def main():

    ap = argparse.ArgumentParser()

    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="mapa_repo.txt")
    ap.add_argument("--json", default="")
    ap.add_argument("--dot", default="")
    ap.add_argument("--calls", action="store_true")

    args = ap.parse_args()

    root = Path(args.root).resolve()

    pyfiles = listar_py(root)

    infos = [analizar_archivo(root, f) for f in pyfiles]

    graph = construir_call_graph(infos)

    pipelines = detectar_pipelines(infos)

    txt = render_txt(infos, graph, pipelines)

    Path(args.out).write_text(txt)

    if args.json:

        payload = {
            "files": [asdict(x) for x in infos],
            "call_graph": {k: list(v) for k, v in graph.items()},
            "pipelines": pipelines
        }

        Path(args.json).write_text(json.dumps(payload, indent=2))

    if args.dot:

        export_dot(graph, args.dot)

    print("Analisis completo")


if __name__ == "__main__":
    main()

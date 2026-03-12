#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
analizador_arquitectura.py

Analizador arquitectónico para repositorios Python.

Detecta:

• Dependencias entre módulos
• Violaciones de capas
• Ciclos de dependencias
• Funciones huérfanas
• Pipeline de llamadas
• Export Graphviz
"""

from __future__ import annotations
import ast
from pathlib import Path
from collections import defaultdict

ROOT = Path(".").resolve()

IGNORAR = ["__pycache__", ".git", ".venv", "venv"]

# arquitectura esperada
CAPAS = {
    "ui": 0,
    "core": 1,
    "electrical": 2,
    "reportes": 3
}


# ==========================================================
# LISTAR PY
# ==========================================================

def listar_py():

    files = []

    for p in ROOT.rglob("*.py"):

        rel = p.relative_to(ROOT).as_posix()

        if any(x in rel for x in IGNORAR):
            continue

        files.append(p)

    return files


# ==========================================================
# PARSE FILE
# ==========================================================

def analizar_archivo(path):

    src = path.read_text(encoding="utf8", errors="ignore")

    try:
        tree = ast.parse(src)
    except:
        return None

    imports = []

    functions = {}

    class Visitor(ast.NodeVisitor):

        current = None

        def visit_Import(self, node):

            for n in node.names:
                imports.append(n.name)

        def visit_ImportFrom(self, node):

            if node.module:
                imports.append(node.module)

        def visit_FunctionDef(self, node):

            fname = node.name

            functions[fname] = []

            self.current = fname

            self.generic_visit(node)

            self.current = None

        def visit_Call(self, node):

            if not self.current:
                return

            name = None

            if isinstance(node.func, ast.Name):
                name = node.func.id

            if isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name:
                functions[self.current].append(name)

            self.generic_visit(node)

    Visitor().visit(tree)

    return imports, functions


# ==========================================================
# CONSTRUIR GRAFOS
# ==========================================================

def construir_grafos(files):

    deps = defaultdict(set)
    calls = defaultdict(set)

    for f in files:

        mod = f.relative_to(ROOT).as_posix().replace("/", ".").replace(".py","")

        data = analizar_archivo(f)

        if not data:
            continue

        imports, funcs = data

        for i in imports:
            deps[mod].add(i)

        for fn, cs in funcs.items():

            for c in cs:
                calls[fn].add(c)

    return deps, calls


# ==========================================================
# DETECTAR VIOLACIONES
# ==========================================================

def detectar_violaciones(deps):

    violaciones = []

    for mod, imports in deps.items():

        capa_mod = None

        for k in CAPAS:
            if mod.startswith(k):
                capa_mod = CAPAS[k]

        if capa_mod is None:
            continue

        for i in imports:

            for k in CAPAS:

                if i.startswith(k):

                    capa_imp = CAPAS[k]

                    if capa_imp < capa_mod:
                        violaciones.append((mod, i))

    return violaciones


# ==========================================================
# DETECTAR CICLOS
# ==========================================================

def detectar_ciclos(deps):

    ciclos = []

    for a, bs in deps.items():

        for b in bs:

            if b in deps and a in deps[b]:
                ciclos.append((a,b))

    return ciclos


# ==========================================================
# FUNCIONES HUERFANAS
# ==========================================================

def detectar_huerfanas(calls):

    llamadas = set()

    for v in calls.values():
        llamadas.update(v)

    huerfanas = []

    for f in calls:

        if f not in llamadas:
            huerfanas.append(f)

    return huerfanas


# ==========================================================
# EXPORT DOT
# ==========================================================

def export_dot(deps, path):

    lines = ["digraph G {"]

    for src, dsts in deps.items():

        for d in dsts:

            lines.append(f'"{src}" -> "{d}"')

    lines.append("}")

    Path(path).write_text("\n".join(lines))


# ==========================================================
# MAIN
# ==========================================================

def main():

    files = listar_py()

    deps, calls = construir_grafos(files)

    violaciones = detectar_violaciones(deps)

    ciclos = detectar_ciclos(deps)

    huerfanas = detectar_huerfanas(calls)

    print("\nFILES:", len(files))

    print("\nVIOLACIONES DE CAPAS")

    for a,b in violaciones:
        print(a, "->", b)

    print("\nCICLOS")

    for a,b in ciclos:
        print(a,"<->",b)

    print("\nFUNCIONES HUERFANAS")

    for f in huerfanas[:50]:
        print(f)

    export_dot(deps, "deps_graph.dot")

    print("\nDOT generado: deps_graph.dot")


if __name__ == "__main__":
    main()

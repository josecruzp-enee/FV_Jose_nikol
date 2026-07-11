#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analizador arquitectónico estático para repositorios Python."""
from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(".").resolve()
SALIDA = ROOT / "arquitectura_salida"
IGNORAR = {"__pycache__", ".git", ".venv", "venv", "env", "node_modules", "arquitectura_salida"}

# Una capa solo puede importar las capas indicadas. Ajusta esto si tu diseño lo requiere.
DEPENDENCIAS_PERMITIDAS = {
    "ui": {"ui", "core", "electrical", "energy", "reportes", "data", "config", "ayuda"},
    "reportes": {"reportes", "core", "electrical", "energy", "data", "config", "ayuda"},
    "core": {"core", "electrical", "energy", "data", "config", "ayuda"},
    "electrical": {"electrical", "data", "config", "ayuda"},
    "energy": {"energy", "data", "config", "ayuda"},
    "data": {"data", "config"},
    "config": {"config"},
    "ayuda": {"ayuda"},
}


def texto_nodo(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def modulo_desde_path(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    partes = list(rel.parts)
    if partes and partes[-1] == "__init__":
        partes.pop()
    return ".".join(partes)


def listar_py() -> list[Path]:
    archivos = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if any(parte in IGNORAR for parte in rel.parts):
            continue
        archivos.append(path)
    return sorted(archivos, key=lambda p: p.as_posix().lower())


def nombre_llamada(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = nombre_llamada(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return nombre_llamada(node.func)
    return ""


def parametros_funcion(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, Any]]:
    args = node.args
    posicionales = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(posicionales) - len(args.defaults)) + list(args.defaults)
    salida = []
    for arg, default in zip(posicionales, defaults):
        salida.append({"nombre": arg.arg, "tipo": texto_nodo(arg.annotation) or None,
                       "default": texto_nodo(default) if default is not None else None,
                       "clase": "posicional"})
    if args.vararg:
        salida.append({"nombre": "*" + args.vararg.arg, "tipo": texto_nodo(args.vararg.annotation) or None,
                       "default": None, "clase": "varargs"})
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        salida.append({"nombre": arg.arg, "tipo": texto_nodo(arg.annotation) or None,
                       "default": texto_nodo(default) if default is not None else None,
                       "clase": "keyword-only"})
    if args.kwarg:
        salida.append({"nombre": "**" + args.kwarg.arg, "tipo": texto_nodo(args.kwarg.annotation) or None,
                       "default": None, "clase": "kwargs"})
    return salida


class AnalizadorArchivo(ast.NodeVisitor):
    def __init__(self, modulo: str):
        self.modulo = modulo
        self.imports: list[dict[str, str | None]] = []
        self.funciones: list[dict[str, Any]] = []
        self.clases: list[dict[str, Any]] = []
        self._clases: list[str] = []
        self._funciones: list[dict[str, Any]] = []

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            self.imports.append({"modulo": item.name, "alias": item.asname})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        base = "." * node.level + (node.module or "")
        for item in node.names:
            self.imports.append({"modulo": base, "nombre": item.name, "alias": item.asname})

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        dato = {"nombre": node.name, "linea": node.lineno,
                "bases": [texto_nodo(x) for x in node.bases], "metodos": []}
        self.clases.append(dato)
        self._clases.append(node.name)
        self.generic_visit(node)
        self._clases.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visitar_funcion(node, asincrona=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visitar_funcion(node, asincrona=True)

    def _visitar_funcion(self, node, asincrona: bool) -> None:
        clase = ".".join(self._clases) if self._clases else None
        local = ".".join([x["nombre"] for x in self._funciones] + [node.name])
        calificado = ".".join(x for x in [self.modulo, clase, local] if x)
        dato = {
            "nombre": node.name, "nombre_calificado": calificado, "clase": clase,
            "linea": node.lineno, "fin_linea": getattr(node, "end_lineno", None),
            "asincrona": asincrona, "parametros": parametros_funcion(node),
            "tipo_retorno": texto_nodo(node.returns) or None, "retornos": [], "llamadas": [],
            "decoradores": [texto_nodo(x) for x in node.decorator_list],
        }
        self.funciones.append(dato)
        if clase:
            self.clases[-1]["metodos"].append(calificado)
        self._funciones.append(dato)
        for sentencia in node.body:
            self.visit(sentencia)
        self._funciones.pop()

    def visit_Return(self, node: ast.Return) -> None:
        if self._funciones:
            valor = texto_nodo(node.value) if node.value is not None else "None"
            if valor not in self._funciones[-1]["retornos"]:
                self._funciones[-1]["retornos"].append(valor)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._funciones:
            nombre = nombre_llamada(node.func)
            if nombre and nombre not in self._funciones[-1]["llamadas"]:
                self._funciones[-1]["llamadas"].append(nombre)
        self.generic_visit(node)


def analizar_archivo(path: Path) -> dict[str, Any]:
    rel = path.relative_to(ROOT).as_posix()
    try:
        fuente = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(fuente, filename=rel)
    except SyntaxError as exc:
        return {"archivo": rel, "modulo": modulo_desde_path(path), "error": str(exc),
                "loc": 0, "imports": [], "funciones": [], "clases": []}
    visitor = AnalizadorArchivo(modulo_desde_path(path))
    visitor.visit(tree)
    return {"archivo": rel, "modulo": visitor.modulo, "error": None,
            "loc": len(fuente.splitlines()), "imports": visitor.imports,
            "funciones": visitor.funciones, "clases": visitor.clases}


def resolver_import(origen: str, importado: str) -> str:
    if not importado.startswith("."):
        return importado
    puntos = len(importado) - len(importado.lstrip("."))
    resto = importado[puntos:]
    partes = origen.split(".")[:-1]
    base = partes[:max(0, len(partes) - puntos + 1)]
    return ".".join(base + ([resto] if resto else []))


def construir_dependencias(datos: list[dict[str, Any]]) -> dict[str, set[str]]:
    modulos = {x["modulo"] for x in datos}
    deps = defaultdict(set)
    for archivo in datos:
        for imp in archivo["imports"]:
            destino = resolver_import(archivo["modulo"], str(imp["modulo"]))
            candidatos = [m for m in modulos if destino == m or destino.startswith(m + ".")]
            if candidatos:
                deps[archivo["modulo"]].add(max(candidatos, key=len))
    return deps


def detectar_ciclos(deps: dict[str, set[str]]) -> list[list[str]]:
    encontrados, visitando, visitados = set(), [], set()
    def dfs(nodo: str) -> None:
        if nodo in visitando:
            ciclo = visitando[visitando.index(nodo):] + [nodo]
            cuerpo = ciclo[:-1]
            rotaciones = [tuple(cuerpo[i:] + cuerpo[:i]) for i in range(len(cuerpo))]
            encontrados.add(min(rotaciones))
            return
        if nodo in visitados:
            return
        visitando.append(nodo)
        for vecino in deps.get(nodo, set()):
            dfs(vecino)
        visitando.pop()
        visitados.add(nodo)
    for nodo in deps:
        dfs(nodo)
    return [list(x) + [x[0]] for x in sorted(encontrados)]


def detectar_violaciones(deps: dict[str, set[str]]) -> list[tuple[str, str]]:
    salida = []
    for origen, destinos in deps.items():
        capa = origen.split(".")[0]
        permitidas = DEPENDENCIAS_PERMITIDAS.get(capa)
        if permitidas is None:
            continue
        for destino in destinos:
            if destino.split(".")[0] not in permitidas:
                salida.append((origen, destino))
    return sorted(salida)


def posibles_no_llamadas(datos: list[dict[str, Any]]) -> list[str]:
    llamadas = {c.split(".")[-1] for a in datos for f in a["funciones"] for c in f["llamadas"]}
    excluir = {"main", "render", "validar", "__init__", "__enter__", "__exit__", "__str__", "__repr__"}
    return sorted(f["nombre_calificado"] for a in datos for f in a["funciones"]
                  if f["nombre"] not in llamadas and f["nombre"] not in excluir
                  and not f["nombre"].startswith("visit_"))


def exportar_dot(deps: dict[str, set[str]]) -> None:
    lineas = ["digraph dependencias {", "  rankdir=LR;"]
    for origen in sorted(deps):
        for destino in sorted(deps[origen]):
            lineas.append(f"  {json.dumps(origen)} -> {json.dumps(destino)};")
    lineas.append("}")
    (SALIDA / "dependencias_modulos.dot").write_text("\n".join(lineas), encoding="utf-8")


def exportar_txt(datos, deps, violaciones, ciclos, candidatos) -> None:
    total_funciones = sum(len(x["funciones"]) for x in datos)
    out = ["MAPA DETALLADO DEL REPOSITORIO", "=" * 90,
           f"Archivos: {len(datos)}", f"Funciones y métodos: {total_funciones}",
           f"Violaciones posibles: {len(violaciones)}", f"Ciclos: {len(ciclos)}", ""]
    for archivo in datos:
        out += ["", f"FILE: {archivo['archivo']}", f"MODULE: {archivo['modulo']}",
                f"LOC: {archivo['loc']}", f"ERROR: {archivo['error'] or 'Ninguno'}", "IMPORTS:"]
        for imp in archivo["imports"]:
            out.append(f"  - {imp}")
        out.append("CLASSES:")
        for clase in archivo["clases"]:
            out.append(f"  - {clase['nombre']} (línea {clase['linea']}) bases={clase['bases']}")
        out.append("FUNCTIONS:")
        for fn in archivo["funciones"]:
            out += [f"  - {fn['nombre_calificado']} (líneas {fn['linea']}-{fn['fin_linea']})",
                    "      ENTRADAS:"]
            if fn["parametros"]:
                for p in fn["parametros"]:
                    out.append(f"        - {p['nombre']}: tipo={p['tipo'] or 'sin anotar'}, default={p['default']}")
            else:
                out.append("        - Ninguna")
            out += [f"      SALIDA ANOTADA: {fn['tipo_retorno'] or 'sin anotar'}",
                    "      RETURNS: " + (" | ".join(fn["retornos"]) if fn["retornos"] else "No detectados"),
                    "      LLAMADAS: " + (", ".join(fn["llamadas"]) if fn["llamadas"] else "Ninguna")]
    out += ["", "VIOLACIONES POSIBLES", "=" * 90]
    out += [f"- {a} -> {b}" for a, b in violaciones] or ["Ninguna"]
    out += ["", "CICLOS DETECTADOS", "=" * 90]
    out += [" -> ".join(c) for c in ciclos] or ["Ninguno"]
    out += ["", "POSIBLES FUNCIONES SIN LLAMADAS INTERNAS", "=" * 90,
            "Requieren revisión manual: callbacks y puntos de entrada pueden dar falsos positivos."]
    out += [f"- {x}" for x in candidatos] or ["Ninguna"]
    (SALIDA / "arquitectura_detallada.txt").write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    archivos = listar_py()
    datos = [analizar_archivo(path) for path in archivos]
    deps = construir_dependencias(datos)
    violaciones = detectar_violaciones(deps)
    ciclos = detectar_ciclos(deps)
    candidatos = posibles_no_llamadas(datos)
    exportar_txt(datos, deps, violaciones, ciclos, candidatos)
    exportar_dot(deps)
    paquete = {"root": str(ROOT), "archivos": datos,
               "dependencias": {k: sorted(v) for k, v in deps.items()},
               "violaciones_posibles": violaciones, "ciclos": ciclos,
               "posibles_sin_llamadas_internas": candidatos}
    (SALIDA / "arquitectura_detallada.json").write_text(
        json.dumps(paquete, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nArchivos analizados: {len(datos)}")
    print(f"Funciones y métodos: {sum(len(x['funciones']) for x in datos)}")
    print(f"Violaciones posibles: {len(violaciones)}")
    print(f"Ciclos detectados: {len(ciclos)}")
    print(f"\nResultados: {SALIDA}")
    print("- arquitectura_detallada.txt")
    print("- arquitectura_detallada.json")
    print("- dependencias_modulos.dot")


if __name__ == "__main__":
    main()

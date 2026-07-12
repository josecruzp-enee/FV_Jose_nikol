from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from typing import List, Set, Tuple


@dataclass
class DefInfo:
    kind: str
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
    texto = ast.get_docstring(node) or ""

    if not texto.strip():
        return ""

    return texto.strip().splitlines()[0].strip()[:180]


def _module_name(
    root: str,
    filepath: str,
) -> str:

    relativo = os.path.relpath(
        filepath,
        root,
    ).replace(os.sep, "/")

    if relativo.endswith(".py"):
        relativo = relativo[:-3]

    return relativo.replace("/", ".")


def _nombre_llamada(node: ast.Call) -> str | None:
    funcion = node.func

    if isinstance(funcion, ast.Name):
        return funcion.id

    if (
        isinstance(funcion, ast.Attribute)
        and isinstance(funcion.value, ast.Name)
    ):
        return (
            f"{funcion.value.id}."
            f"{funcion.attr}"
        )

    return None


def _scan_file(
    root: str,
    filepath: str,
) -> FileInfo:

    with open(
        filepath,
        "r",
        encoding="utf-8",
    ) as archivo:
        codigo = archivo.read()

    tree = ast.parse(
        codigo,
        filename=filepath,
    )

    imports: List[str] = []
    from_imports: List[Tuple[str, List[str]]] = []
    defs: List[DefInfo] = []
    calls: Set[str] = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for nombre in node.names:
                imports.append(nombre.name)

        elif isinstance(node, ast.ImportFrom):
            modulo = node.module or ""

            nombres = [
                nombre.name
                for nombre in node.names
            ]

            from_imports.append(
                (modulo, nombres)
            )

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            defs.append(
                DefInfo(
                    kind="function",
                    name=node.name,
                    lineno=getattr(
                        node,
                        "lineno",
                        -1,
                    ),
                    doc1=_doc1(node),
                )
            )

        elif isinstance(node, ast.ClassDef):
            defs.append(
                DefInfo(
                    kind="class",
                    name=node.name,
                    lineno=getattr(
                        node,
                        "lineno",
                        -1,
                    ),
                    doc1=_doc1(node),
                )
            )

        elif isinstance(node, ast.Call):
            llamada = _nombre_llamada(node)

            if llamada:
                calls.add(llamada)

    return FileInfo(
        path=filepath,
        module=_module_name(
            root,
            filepath,
        ),
        imports=sorted(set(imports)),
        from_imports=sorted(
            from_imports,
            key=lambda item: item[0],
        ),
        defs=sorted(
            defs,
            key=lambda definicion: (
                definicion.kind,
                definicion.name,
            ),
        ),
        calls=calls,
    )


def _iter_py_files(folder: str) -> List[str]:
    archivos: List[str] = []

    for carpeta, _, nombres in os.walk(folder):
        for nombre in nombres:

            if not nombre.endswith(".py"):
                continue

            if nombre.startswith("."):
                continue

            archivos.append(
                os.path.join(
                    carpeta,
                    nombre,
                )
            )

    return sorted(archivos)


def _es_dependencia_bateria(
    modulo: str,
) -> bool:

    return (
        modulo.startswith(".")
        or modulo.startswith(
            "energy.baterias"
        )
    )


def _md_escape(texto: str) -> str:
    return texto.replace("|", "\\|")


def _agregar_archivo(
    lines: List[str],
    info: FileInfo,
    repo_root: str,
) -> None:

    lines.append(f"### {info.module}\n")

    ruta = os.path.relpath(
        info.path,
        repo_root,
    )

    lines.append(f"- Ruta: `{ruta}`\n")

    if info.imports or info.from_imports:
        lines.append("- Imports:\n")

        for modulo in info.imports:
            lines.append(
                f"  - `import {modulo}`\n"
            )

        for modulo, nombres in info.from_imports:
            nombres_texto = ", ".join(nombres)

            lines.append(
                f"  - `from {modulo} "
                f"import {nombres_texto}`\n"
            )

    if info.defs:
        lines.append("- Definiciones:\n")

        for definicion in info.defs:
            doc = ""

            if definicion.doc1:
                doc = (
                    " — "
                    + _md_escape(
                        definicion.doc1
                    )
                )

            lines.append(
                f"  - **{definicion.kind}** "
                f"`{definicion.name}` "
                f"(L{definicion.lineno})"
                f"{doc}\n"
            )

    if info.calls:
        llamadas = sorted(info.calls)[:60]

        llamadas_texto = ", ".join(
            f"`{llamada}`"
            for llamada in llamadas
        )

        lines.append(
            "- Llamadas detectadas "
            f"(muestra ≤60): "
            f"{llamadas_texto}\n"
        )

    lines.append("\n")


def _obtener_dependencias(
    infos: List[FileInfo],
) -> Set[Tuple[str, str]]:

    dependencias: Set[Tuple[str, str]] = set()

    for info in infos:

        for modulo, _ in info.from_imports:
            if modulo:
                dependencias.add(
                    (info.module, modulo)
                )

        for modulo in info.imports:
            dependencias.add(
                (info.module, modulo)
            )

    return dependencias


def main() -> None:
    repo_root = os.getcwd()

    baterias_dir = os.path.join(
        repo_root,
        "energy",
        "baterias",
    )

    if not os.path.isdir(baterias_dir):
        raise SystemExit(
            f"No existe carpeta: {baterias_dir}"
        )

    archivos = _iter_py_files(
        baterias_dir
    )

    infos = [
        _scan_file(
            repo_root,
            archivo,
        )
        for archivo in archivos
    ]

    lines: List[str] = []

    lines.append(
        "# Resumen automático — energy/baterias\n\n"
    )

    lines.append("## Archivos\n\n")

    for info in infos:
        _agregar_archivo(
            lines,
            info,
            repo_root,
        )

    dependencias = _obtener_dependencias(
        infos
    )

    lines.append(
        "## Dependencias internas\n\n"
    )

    for origen, destino in sorted(dependencias):
        if _es_dependencia_bateria(destino):
            lines.append(
                f"- `{origen}` → `{destino}`\n"
            )

    out_path = os.path.join(
        repo_root,
        "resumen_baterias.md",
    )

    with open(
        out_path,
        "w",
        encoding="utf-8",
    ) as archivo:
        archivo.write("".join(lines))

    print(f"OK: generado {out_path}")
    print(
        f"Archivos Python analizados: "
        f"{len(archivos)}"
    )


if __name__ == "__main__":
    main()

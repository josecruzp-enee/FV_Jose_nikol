import ast
from pathlib import Path

ROOT = Path(__file__).parent

TARGET_CLASSES = {
    "ResultadoSizing",
    "ResultadoStrings",
    "ResultadoNEC",
    "ResultadoFinanciero",
}

def scan_file(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return

    for node in ast.walk(tree):

        # Buscar ResultadoX(**algo)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in TARGET_CLASSES:
                    for kw in node.keywords:
                        if kw.arg is None:  # esto es el **
                            print(f"[EXPANSION] {path}:{node.lineno} → {node.func.id}(**...)")

        # Buscar .get()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "get":
                    print(f"[GET CALL] {path}:{node.lineno}")

def main():
    for file in ROOT.rglob("*.py"):
        if "venv" in str(file):
            continue
        scan_file(file)

if __name__ == "__main__":
    main()

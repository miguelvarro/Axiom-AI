"""
rename_to_axiom_ai.py
=====================
Ejecutar desde la RAÍZ del proyecto (donde ves data/, frontend/, scripts/, src/):

    python rename_to_axiom_ai.py

Qué hace:
  1. Renombra src/ai_consensus_clone/ → src/axiom_ai/
  2. Sustituye todos los imports y referencias de texto en los ficheros fuente
  3. Elimina el directorio .egg-info antiguo (se regenera con `pip install -e .`)
  4. Muestra un resumen de lo que ha cambiado

No toca: .git/, data/, ficheros binarios, .jsonl de datos.
"""

import os
import shutil
from pathlib import Path

# ── Configuración ──────────────────────────────────────────────────────────────
OLD_NAME  = "ai_consensus_clone"   # nombre Python del paquete (con _)
NEW_NAME  = "axiom_ai"             # nombre nuevo (con _)
OLD_SLUG  = "ai-consensus-clone"   # nombre del proyecto con guiones
NEW_SLUG  = "axiom-ai"             # nombre nuevo con guiones
OLD_TITLE = "AI Consensus Clone"   # nombre humano antiguo
NEW_TITLE = "Axiom AI"             # nombre humano nuevo

# Extensiones de fichero donde hacer sustitución de texto
TEXT_EXTENSIONS = {
    ".py", ".toml", ".cfg", ".ini", ".txt", ".md",
    ".html", ".js", ".json", ".yaml", ".yml", ".env",
    ".example",
}

# Directorios a ignorar completamente
IGNORE_DIRS = {".git", "__pycache__", ".mypy_cache", ".ruff_cache", "node_modules"}

# ── Helpers ────────────────────────────────────────────────────────────────────
def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {".env", ".env.example", ".gitignore"}

def replace_in_file(path: Path, substitutions: list[tuple[str, str]]) -> bool:
    """Devuelve True si el fichero fue modificado."""
    try:
        original = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [SKIP] No se puede leer {path}: {e}")
        return False

    updated = original
    for old, new in substitutions:
        updated = updated.replace(old, new)

    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False

def walk_project(root: Path):
    """Genera todos los ficheros del proyecto ignorando IGNORE_DIRS."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fname in filenames:
            yield Path(dirpath) / fname

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    root = Path(".").resolve()
    print(f"Raíz del proyecto: {root}\n")

    # Sanity check
    src_old = root / "src" / OLD_NAME
    if not src_old.exists():
        print(f"ERROR: No se encuentra {src_old}")
        print("Asegúrate de ejecutar el script desde la raíz del proyecto.")
        print("(la carpeta donde ves data/, frontend/, scripts/, src/)")
        return

    # ── Paso 1: sustituir texto en todos los ficheros ANTES de mover carpetas ──
    substitutions = [
        (OLD_NAME, NEW_NAME),    # imports Python
        (OLD_SLUG, NEW_SLUG),    # nombre con guiones (pyproject.toml, etc.)
        (OLD_TITLE, NEW_TITLE),  # nombre humano (títulos, comentarios)
    ]

    modified = []
    for fpath in walk_project(root):
        if not fpath.is_file():
            continue
        if not is_text_file(fpath):
            continue
        if fpath.name == "rename_to_axiom_ai.py":
            continue
        if replace_in_file(fpath, substitutions):
            modified.append(fpath.relative_to(root))

    print(f"Ficheros modificados ({len(modified)}):")
    for f in modified:
        print(f"  ✏️  {f}")

    # ── Paso 2: renombrar la carpeta del paquete ──────────────────────────────
    src_new = root / "src" / NEW_NAME
    print(f"\nRenombrando carpeta del paquete:")
    print(f"  {src_old}  →  {src_new}")
    shutil.move(str(src_old), str(src_new))

    # ── Paso 3: eliminar el .egg-info antiguo ────────────────────────────────
    egg_old = root / "src" / f"{OLD_NAME}.egg-info"
    if egg_old.exists():
        print(f"\nEliminando .egg-info antiguo: {egg_old.name}")
        shutil.rmtree(egg_old)

    # ── Resumen final ─────────────────────────────────────────────────────────
    print("""
╔══════════════════════════════════════════════════════════╗
║  Renombrado completado con éxito                         ║
╚══════════════════════════════════════════════════════════╝

Próximos pasos:
  1. Reinstala el paquete en modo editable:
       pip install -e .

  2. Si usas Poetry:
       poetry install

  3. Verifica que todo arranca bien:
       uvicorn axiom_ai.app.api.main:app --reload
""")

if __name__ == "__main__":
    main()
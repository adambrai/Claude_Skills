#!/usr/bin/env python3
"""List every file of a subject folder, so no source is skipped.

Usage: python3 inventaire.py <dossier> [sortie.md]

Walks the folder recursively (hidden folders and revision/ outputs excluded) and writes
a checklist: path, kind, size, pages (PDF, on macOS). Each line is ticked once the file
has been read in full. Standard library only.
"""
import os
import subprocess
import sys

KINDS = {
    ".pdf": "pdf", ".ppt": "slides", ".pptx": "slides", ".key": "slides", ".odp": "slides",
    ".doc": "texte", ".docx": "texte", ".odt": "texte", ".rtf": "texte", ".pages": "texte",
    ".txt": "texte", ".md": "texte", ".tex": "texte", ".html": "texte",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".heic": "image", ".webp": "image",
    ".xls": "tableur", ".xlsx": "tableur", ".csv": "tableur", ".ods": "tableur",
    ".c": "code", ".h": "code", ".py": "code", ".java": "code", ".js": "code", ".sql": "code",
    ".pml": "code", ".sh": "code", ".cpp": "code", ".asm": "code", ".s": "code",
    ".zip": "archive", ".rar": "archive", ".7z": "archive",
}
SKIP_DIRS = {"revision", "node_modules", "__pycache__"}


def pages(path):
    if sys.platform != "darwin" or not path.lower().endswith(".pdf"):
        return ""
    try:
        out = subprocess.run(["mdls", "-raw", "-name", "kMDItemNumberOfPages", path],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return out if out.isdigit() else ""
    except Exception:
        return ""


def size(n):
    return f"{n // 1024} Ko" if n < 1024 * 1024 else f"{n / 1024 / 1024:.1f} Mo"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = os.path.abspath(sys.argv[1])
    rows = []
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if not x.startswith(".") and x not in SKIP_DIRS)
        for name in sorted(files):
            if name.startswith(".") or name.startswith("~$"):
                continue
            p = os.path.join(d, name)
            ext = os.path.splitext(name)[1].lower()
            rows.append((os.path.relpath(p, root), KINDS.get(ext, "autre"),
                         size(os.path.getsize(p)), pages(p)))

    lines = [f"# Sources : {os.path.basename(root)}", "",
             f"{len(rows)} fichiers. Cocher chaque ligne une fois le fichier lu **en entier**.", "",
             "| lu | fichier | format | taille | pages | type (cours, TD, examen…) |",
             "|---|---|---|---|---|---|"]
    lines += [f"| [ ] | {r} | {k} | {s} | {pg} | |" for r, k, s, pg in rows]
    text = "\n".join(lines) + "\n"

    if len(sys.argv) > 2:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(text)
        print(f"{len(rows)} fichiers -> {sys.argv[2]}")
    else:
        print(text)


if __name__ == "__main__":
    main()

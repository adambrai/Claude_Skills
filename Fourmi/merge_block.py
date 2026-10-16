#!/usr/bin/env python3
"""merge_block.py — merge a marked block into a CLAUDE.md, or copy a file, showing
the change first.

Usage:
  python3 merge_block.py TARGET SOURCE            # print the diff, change nothing
  python3 merge_block.py TARGET SOURCE --write    # apply it

SOURCE starts with a marker line like `<!-- name:start -->` and ends with
`<!-- name:end -->`. If TARGET already holds a block with the same markers, that block
is replaced in place; otherwise SOURCE is appended at the end. The rest of TARGET is
never touched. With --copy, TARGET is replaced by SOURCE as a whole (used for the
sub-agent file). Standard library only.
"""
import argparse
import difflib
import os
import re
import sys

MARKER = re.compile(r"<!--\s*([\w-]+):start\s*-->")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def merge(target, block):
    """Return target with block inserted or replaced. Raises ValueError if block has no markers."""
    block = block.strip("\n") + "\n"
    m = MARKER.search(block)
    if not m or f"<!-- {m.group(1)}:end -->" not in block:
        raise ValueError("the block must start with <!-- name:start --> and end with <!-- name:end -->")
    name = re.escape(m.group(1))
    existing = re.compile(rf"<!--\s*{name}:start\s*-->.*?<!--\s*{name}:end\s*-->\n?", re.S)
    if existing.search(target):
        return existing.sub(lambda _: block, target, count=1)
    if not target.strip():
        return block
    return target.rstrip("\n") + "\n\n" + block


def diff(old, new, path):
    return "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                        fromfile=path + " (avant)", tofile=path + " (après)"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target")
    ap.add_argument("source")
    ap.add_argument("--copy", action="store_true", help="replace TARGET by SOURCE as a whole")
    ap.add_argument("--write", action="store_true", help="apply the change (default: show it only)")
    a = ap.parse_args(argv)
    target = os.path.expanduser(a.target)
    old, src = read(target), read(os.path.expanduser(a.source))
    if not src:
        print(f"Source vide ou introuvable : {a.source}", file=sys.stderr)
        return 2
    try:
        new = src if a.copy else merge(old, src)
    except ValueError as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 2
    if new == old:
        print(f"Rien à changer dans {target}.")
        return 0
    print(diff(old, new, target), end="")
    if a.write:
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"\nÉcrit : {target}")
    else:
        print("\n(aperçu seulement ; relance avec --write pour appliquer)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

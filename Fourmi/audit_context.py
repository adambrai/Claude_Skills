#!/usr/bin/env python3
"""audit_context.py — measure what a Claude Code project loads into context on
every turn, and what could be trimmed.

Usage:
  python3 audit_context.py [PROJECT_DIR] [--json]

Looks at: CLAUDE.md files (global, project, local, and @imports), skills and their
descriptions, MCP servers, enabled plugins, and large files an agent could read by
accident. Prints an estimate in tokens (about 4 characters per token) and concrete
suggestions. Standard library only. Never prints secret values: for MCP servers it
reports names only.
"""
import argparse
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
CHARS_PER_TOKEN = 4
BIG_FILE = 400_000            # bytes; bigger files are worth keeping out of reach
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
             ".next", ".debat", ".purple", ".mypy_cache", ".pytest_cache", "target"}


def tok(n_chars):
    return round(n_chars / CHARS_PER_TOKEN)


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def expand_imports(path, seen=None, depth=0):
    """Return (total_chars, [files]) for a CLAUDE.md and the @imports it pulls in."""
    seen = seen if seen is not None else set()
    path = os.path.abspath(os.path.expanduser(path))
    if path in seen or depth > 5 or not os.path.isfile(path):
        return 0, []
    seen.add(path)
    text = read(path)
    total, files = len(text), [(path, len(text))]
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for m in re.finditer(r"(?:^|\s)@((?:~|\.{1,2})?/?[\w./-]+\.\w+)", line):
            ref = m.group(1)
            target = os.path.expanduser(ref) if ref.startswith("~") else os.path.join(os.path.dirname(path), ref)
            t, f = expand_imports(target, seen, depth + 1)
            total += t
            files += f
    return total, files


def claude_md(project):
    always = []
    for p in (os.path.join(HOME, ".claude", "CLAUDE.md"),
              os.path.join(project, "CLAUDE.md"),
              os.path.join(project, ".claude", "CLAUDE.md"),
              os.path.join(project, "CLAUDE.local.md")):
        if os.path.isfile(p):
            total, files = expand_imports(p)
            always.append({"file": p, "tokens": tok(total), "imports": [f for f, _ in files[1:]]})
    nested = []
    for dirpath, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        if os.path.abspath(dirpath) == os.path.abspath(project):
            continue
        if "CLAUDE.md" in files:
            p = os.path.join(dirpath, "CLAUDE.md")
            nested.append({"file": p, "tokens": tok(len(read(p)))})
    return always, nested


def skills(project):
    out = []
    for base in (os.path.join(HOME, ".claude", "skills"), os.path.join(project, ".claude", "skills")):
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            p = os.path.join(base, name, "SKILL.md")
            if not os.path.isfile(p):
                continue
            text = read(p)
            m = re.search(r"^description:\s*(>-?|\|)?\s*(.*?)(?=^\w[\w-]*:|^---)", text, re.S | re.M)
            desc = re.sub(r"\s+", " ", (m.group(2) if m else "")).strip()
            out.append({"name": name, "where": base, "description_tokens": tok(len(desc)),
                        "body_tokens": tok(len(text))})
    return out


def mcp_servers(project):
    found = []
    proj = load_json(os.path.join(project, ".mcp.json")).get("mcpServers", {})
    found += [{"name": n, "scope": "project (.mcp.json)"} for n in proj]
    user = load_json(os.path.join(HOME, ".claude.json"))
    found += [{"name": n, "scope": "user"} for n in (user.get("mcpServers") or {})]
    per_project = (user.get("projects") or {}).get(os.path.abspath(project), {})
    found += [{"name": n, "scope": "local"} for n in (per_project.get("mcpServers") or {})]
    return found


def plugins():
    s = load_json(os.path.join(HOME, ".claude", "settings.json"))
    enabled = s.get("enabledPlugins") or {}
    return sorted(k for k, v in enabled.items() if v)


def big_files(project):
    out = []
    for dirpath, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            p = os.path.join(dirpath, fn)
            try:
                size = os.path.getsize(p)
            except OSError:
                continue
            if size >= BIG_FILE:
                out.append({"file": os.path.relpath(p, project), "kb": size // 1024})
    return sorted(out, key=lambda x: -x["kb"])[:15]


def deny_rules(project):
    rules = []
    for p in (os.path.join(project, ".claude", "settings.json"),
              os.path.join(project, ".claude", "settings.local.json")):
        rules += ((load_json(p).get("permissions") or {}).get("deny") or [])
    return rules


def audit(project):
    project = os.path.abspath(project)
    always, nested = claude_md(project)
    sk = skills(project)
    mcp = mcp_servers(project)
    pl = plugins()
    big = big_files(project)
    deny = deny_rules(project)
    memory_tokens = sum(x["tokens"] for x in always)
    skill_desc_tokens = sum(x["description_tokens"] for x in sk)
    advice = []
    if memory_tokens > 2500:
        advice.append(f"Les CLAUDE.md chargés à chaque message font ~{memory_tokens} tokens : garde "
                      "les règles courtes, déplace les détails dans des fichiers lus à la demande ou dans une skill.")
    for x in always:
        if x["tokens"] > 1500:
            advice.append(f"{x['file']} fait ~{x['tokens']} tokens à lui seul.")
    if len(mcp) > 5:
        advice.append(f"{len(mcp)} serveurs MCP configurés : désactive ceux que ce projet n'utilise pas "
                      "(chacun ajoute ses outils au contexte).")
    if skill_desc_tokens > 3000:
        advice.append(f"Les descriptions de {len(sk)} skills font ~{skill_desc_tokens} tokens : supprime "
                      "celles que tu n'utilises jamais.")
    if len(pl) > 8:
        advice.append(f"{len(pl)} plugins activés : coupe ceux qui ne servent pas ici.")
    undenied = [b for b in big if not any(b["file"] in r or "**" in r for r in deny)]
    if undenied:
        advice.append("Gros fichiers lisibles par l'agent ("
                      + ", ".join(f"{b['file']} {b['kb']} Ko" for b in undenied[:5])
                      + ") : si l'agent n'a pas besoin de les lire, ajoute des règles permissions.deny "
                      "Read(...) dans .claude/settings.json ; sinon, donne-lui plutôt un résumé court à lire.")
    if not always:
        advice.append("Aucun CLAUDE.md : un fichier court (règles de délégation et de choix du modèle) "
                      "évite de répéter les mêmes consignes à chaque session.")
    return {"project": project, "claude_md_always": always, "claude_md_nested": nested,
            "memory_tokens": memory_tokens, "skills": len(sk), "skill_description_tokens": skill_desc_tokens,
            "mcp_servers": mcp, "plugins": pl, "big_files": big, "deny_rules": deny, "advice": advice}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = audit(a.project)
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0
    print(f"Projet : {r['project']}")
    print(f"Mémoire chargée à chaque message (CLAUDE.md + imports) : ~{r['memory_tokens']} tokens")
    for x in r["claude_md_always"]:
        imp = f" (+ {len(x['imports'])} import(s))" if x["imports"] else ""
        print(f"  {x['file']} ~{x['tokens']} tokens{imp}")
    if r["claude_md_nested"]:
        print(f"CLAUDE.md de sous-dossiers (chargés seulement quand l'agent y travaille) : {len(r['claude_md_nested'])}")
    print(f"Skills : {r['skills']} (descriptions ~{r['skill_description_tokens']} tokens)")
    print(f"Serveurs MCP : {len(r['mcp_servers'])}" + (" — " + ", ".join(m["name"] for m in r["mcp_servers"]) if r["mcp_servers"] else ""))
    print(f"Plugins activés : {len(r['plugins'])}")
    if r["big_files"]:
        print("Gros fichiers : " + ", ".join(f"{b['file']} ({b['kb']} Ko)" for b in r["big_files"][:5]))
    print("\nSuggestions :" if r["advice"] else "\nRien d'important à alléger.")
    for s in r["advice"]:
        print(f"  - {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

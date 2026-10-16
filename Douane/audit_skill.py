#!/usr/bin/env python3
"""audit_skill.py — review a Claude Code skill (or any agent skill folder) before
installing it.

Usage:
  python3 audit_skill.py PATH [--json]
  python3 audit_skill.py PATH --check-install [--full-depth] [--json]

PATH is a skill folder, a folder containing several skills, or a single SKILL.md.
Reports what the skill contains and anything that deserves a human look before it
runs on your machine: executable scripts, commands that download and run code,
access to credential files, instructions that tell the agent to act without asking,
hidden characters, encoded blobs, and broad tool permissions. Standard library only.
It reads files; it never runs them.

With --check-install, instead checks that a repo or folder can be installed with the
`npx skills` tool: every skill has a SKILL.md with name and description in its YAML
header, and sits where the tool looks for it. It lists the skills it would find.

Exit code: 0 if nothing high was found, 1 if at least one high finding, 2 on error.
"""
import argparse
import json
import os
import re
import stat
import sys
import unicodedata

TEXT_EXT = {".md", ".txt", ".py", ".sh", ".bash", ".zsh", ".fish", ".js", ".mjs", ".cjs",
            ".ts", ".rb", ".pl", ".php", ".ps1", ".bat", ".cmd", ".json", ".yaml", ".yml",
            ".toml", ".ini", ".cfg", ".html", ".css", ".xml", ".csv", ".env", ""}
SCRIPT_EXT = {".py", ".sh", ".bash", ".zsh", ".fish", ".js", ".mjs", ".cjs", ".ts", ".rb",
              ".pl", ".php", ".ps1", ".bat", ".cmd", ".exe", ".bin", ".so", ".dylib", ".dll"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
MAX_BYTES = 2_000_000
SEVERITY = {"high": 3, "medium": 2, "low": 1, "info": 0}
LABEL = {"high": "ÉLEVÉ", "medium": "MOYEN", "low": "FAIBLE", "info": "INFO"}

SHELL = r"(?:sudo\s+)?(?:ba|z|k|da)?sh\b|python[0-9.]*\b|node\b|perl\b|ruby\b|php\b"

DOWNLOAD_RUN = [
    (r"\b(?:curl|wget|fetch)\b[^|\n]*\|\s*(?:" + SHELL + r")", "télécharge puis exécute (pipe vers un interpréteur)"),
    (r"(?:ba|z)?sh\s+(?:-c\s+)?[\"']?\s*<\(\s*(?:curl|wget)", "exécute un script téléchargé (process substitution)"),
    (r"(?:eval|source|\.)\s+[\"']?\$\(\s*(?:curl|wget)", "évalue le résultat d'un téléchargement"),
    (r"\b(?:iwr|irm|Invoke-WebRequest|Invoke-RestMethod|DownloadString)\b.*\b(?:iex|Invoke-Expression)\b",
     "PowerShell : télécharge puis exécute"),
    (r"\b(?:iex|Invoke-Expression)\b.*\b(?:iwr|irm|Invoke-WebRequest|DownloadString)\b",
     "PowerShell : télécharge puis exécute"),
    (r"\bexec\s*\(\s*(?:urllib\.request\.)?urlopen\s*\(", "Python : exécute du code téléchargé"),
    (r"\bexec\s*\(\s*requests\.get\s*\(", "Python : exécute du code téléchargé"),
    (r"\beval\s*\(\s*(?:await\s+)?\(?\s*(?:await\s+)?fetch\s*\(", "JavaScript : évalue du code téléchargé"),
    (r"base64\s+(?:-d|--decode|-D)\b[^|\n]*\|\s*(?:" + SHELL + r")", "décode un bloc puis l'exécute"),
    (r"\b(?:curl|wget)\b[^;&\n]*(?:-o|-O|--output)\b[^;&\n]*(?:;|&&)\s*(?:chmod\s+\+x|(?:ba|z)?sh\s|\./)",
     "télécharge un fichier puis le lance"),
]

INSTALL_FROM_NET = [
    (r"\bpip3?\s+install\s+[^\n]*(?:git\+|https?://)", "installe un paquet Python depuis une URL"),
    (r"\bnpm\s+(?:install|i)\s+[^\n]*(?:git\+|https?://|github:)", "installe un paquet npm depuis une URL"),
    (r"\bnpx\s+(?:-y|--yes)\b", "lance un paquet npm sans confirmation (npx -y)"),
]

CREDENTIALS = [
    r"~?/?\.ssh/(?:id_\w+|authorized_keys|config|known_hosts)?", r"\bid_(?:rsa|ed25519|ecdsa|dsa)\b",
    r"\.aws/(?:credentials|config)", r"\.netrc\b", r"\.npmrc\b", r"\.pypirc\b",
    r"\.docker/config\.json", r"\.kube/config", r"\.gnupg\b", r"\.git-credentials\b",
    r"\.config/gh/hosts\.yml", r"\bgh\s+auth\s+token\b", r"\.claude\.json\b",
    r"\.claude/\.credentials", r"\bsecurity\s+(?:find|dump)-(?:generic|internet)-password\b",
    r"\bsecurity\s+dump-keychain\b", r"Library/Keychains", r"(?:Login Data|Cookies)\b.*(?:Chrome|Chromium|Brave|Edge)",
    r"(?:Chrome|Chromium|Brave|Edge)\b.*(?:Login Data|Cookies)", r"\bkey4\.db\b|\blogins\.json\b",
    r"(?:^|[\s\"'/])\.env(?:\.local|\.production)?\b", r"/etc/shadow\b",
    r"\b(?:AWS_SECRET_ACCESS_KEY|ANTHROPIC_API_KEY|OPENAI_API_KEY|GITHUB_TOKEN|GH_TOKEN|NPM_TOKEN)\b",
]
CREDENTIALS_RE = re.compile("|".join(f"(?:{p})" for p in CREDENTIALS))

NO_ASK = [
    (r"\bwithout\s+(?:asking|confirmation|confirming|prompting|telling)\b", "medium"),
    (r"\b(?:do\s+not|don't|never)\s+(?:ask|prompt|wait\s+for|request)\b[^.\n]{0,40}\b(?:user|permission|confirmation|approval)",
     "medium"),
    (r"\b(?:skip|bypass|disable)\w*\s+(?:the\s+)?(?:confirmation|permission|approval)s?\b", "medium"),
    (r"--dangerously-skip-permissions|\bbypassPermissions\b|\bdangerouslyDisableSandbox\b", "high"),
    (r"\b(?:do\s+not|don't|never)\s+(?:tell|inform|mention\s+(?:this\s+)?to|show)\s+(?:the\s+)?user\b", "high"),
    (r"\bignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|rules)\b", "high"),
    (r"\b(?:silently|quietly)\s+(?:run|execute|send|upload|delete|install|modify)\b", "high"),
    (r"\bsans\s+(?:demander|confirmation|me\s+demander|lui\s+demander|(?:mon\s+|ton\s+|son\s+|l')accord|prévenir)\b",
     "medium"),
    (r"\bne\s+(?:demande|demandez|lui\s+demande)\s+(?:pas|jamais)\b", "medium"),
    (r"\bne\s+(?:dis|dites|mentionne|signale)\s+(?:rien|pas|jamais)\b[^.\n]{0,30}\butilisateur", "high"),
    (r"\bignore\s+(?:les\s+)?(?:consignes|instructions)\s+(?:précédentes|ci-dessus)\b", "high"),
]

# "Never install it without asking" is the opposite of what we look for.
NEGATION_RE = re.compile(r"\b(?:do\s+not|don't|never|not|no|ne|n'|jamais|pas)\b", re.I)

HIDDEN = {}
for lo, hi, what in ((0x200B, 0x200F, "espace ou marque invisible"), (0x202A, 0x202E, "contrôle de direction (bidi)"),
                     (0x2060, 0x2064, "caractère invisible"), (0x2066, 0x2069, "contrôle de direction (bidi)"),
                     (0x00AD, 0x00AD, "trait d'union invisible"), (0x180E, 0x180E, "séparateur invisible"),
                     (0xE0000, 0xE007F, "caractère « tag » invisible"),
                     (0xE0100, 0xE01EF, "sélecteur de variante (peut cacher des données)")):
    for cp in range(lo, hi + 1):
        HIDDEN[cp] = what
HIDDEN[0xFEFF] = "BOM au milieu du texte"

BASE64_RE = re.compile(r"[A-Za-z0-9+/]{160,}={0,2}|[A-Za-z0-9_-]{200,}")
HEX_RE = re.compile(r"(?:\\x[0-9a-fA-F]{2}){40,}|\b[0-9a-fA-F]{160,}\b")
NETWORK_RE = re.compile(r"\b(?:urlopen|urllib\.request|requests\.(?:get|post)|http\.client|socket\.socket|"
                        r"fetch\s*\(|axios|XMLHttpRequest|curl\s|wget\s|Invoke-WebRequest|nc\s+-)")
DESTRUCTIVE_RE = re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(?:/|~|\$HOME|\*)(?:\s|$|/)|\bmkfs\b|\bdd\s+if=.*of=/dev/|"
                            r"\bgit\s+push\s+[^\n]*--force\b|\bchmod\s+-R\s+777\b")


def finding(sev, kind, path, line, message, excerpt=""):
    return {"severity": sev, "kind": kind, "file": path, "line": line, "message": message,
            "excerpt": excerpt}


def show(text, limit=120):
    """Make hidden characters visible and keep excerpts short."""
    out = "".join(f"<U+{ord(c):04X}>" if ord(c) in HIDDEN or (unicodedata.category(c) == "Cc" and c != "\t") else c
                  for c in text.strip())
    return out if len(out) <= limit else out[:limit - 1] + "…"


def collect(root):
    """List files without following symlinks. Returns (files, symlinks)."""
    files, links = [], []
    if os.path.isfile(root) or os.path.islink(root):
        return ([root], []) if not os.path.islink(root) else ([], [root])
    for dirpath, dirs, names in os.walk(root, followlinks=False):
        for d in list(dirs):
            if os.path.islink(os.path.join(dirpath, d)):
                links.append(os.path.join(dirpath, d))
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not os.path.islink(os.path.join(dirpath, d)))
        for n in sorted(names):
            p = os.path.join(dirpath, n)
            (links if os.path.islink(p) else files).append(p)
    return files, links


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read(MAX_BYTES + 1)


def frontmatter(text):
    if not text.startswith("---"):
        return {}, 0
    end = text.find("\n---", 3)
    if end == -1:
        return {}, 0
    block = text[3:end]
    fields, key = {}, None
    for line in block.splitlines():
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            fields[key] = m.group(2).strip()
        elif key and line.strip():
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, block.count("\n") + 1


def split_tools(value):
    value = value.strip().strip("[]")
    tools, depth, cur = [], 0, ""
    for c in value:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        if c in ", " and depth == 0:
            if cur.strip(" -\"'"):
                tools.append(cur.strip(" -\"'"))
            cur = ""
        else:
            cur += c
    if cur.strip(" -\"'"):
        tools.append(cur.strip(" -\"'"))
    return tools


def check_tools(tools, path, line, field):
    out = []
    for t in tools:
        name = t.split("(")[0]
        arg = t[len(name):].strip("()") if "(" in t else ""
        if t in ("*", "all") or name.endswith("*") and not name.startswith("mcp__"):
            out.append(finding("high", "permissions", path, line, f"{field} accorde tous les outils ({t})", t))
        elif name == "Bash" and arg in ("", "*", ":*", "*:*"):
            out.append(finding("high", "permissions", path, line,
                               f"{field} autorise toutes les commandes shell sans demander ({t})", t))
        elif name == "Bash" and re.match(r"^(?:curl|wget|sudo|rm|sh|bash|zsh|python\d*|node|eval|chmod|ssh|scp|nc)\b", arg):
            out.append(finding("medium", "permissions", path, line,
                               f"{field} autorise sans demander une commande sensible ({t})", t))
        elif name in ("Write", "Edit", "MultiEdit") and arg in ("", "*", "**", "/**", "~/**", "//**"):
            out.append(finding("low", "permissions", path, line,
                               f"{field} autorise l'écriture de n'importe quel fichier sans demander ({t})", t))
        elif name in ("WebFetch", "WebSearch") and not arg:
            out.append(finding("low", "permissions", path, line, f"{field} autorise l'accès au web sans demander ({t})", t))
        elif name.startswith("mcp__") and name.endswith("*"):
            out.append(finding("medium", "permissions", path, line, f"{field} autorise tout un serveur MCP ({t})", t))
    return out


def check_settings(data, path):
    out = []
    if not isinstance(data, dict):
        return out
    perms = data.get("permissions") or {}
    if isinstance(perms, dict):
        out += check_tools([str(x) for x in perms.get("allow") or []], path, 0, "permissions.allow")
        if perms.get("defaultMode") in ("bypassPermissions", "acceptEdits"):
            out.append(finding("high" if perms["defaultMode"] == "bypassPermissions" else "medium", "permissions",
                               path, 0, f"defaultMode = {perms['defaultMode']}", perms["defaultMode"]))
    if data.get("hooks"):
        out.append(finding("medium", "hooks", path, 0,
                           "définit des hooks : des commandes lancées automatiquement à chaque événement",
                           ", ".join(map(str, data["hooks"]))[:120]))
    if data.get("mcpServers"):
        out.append(finding("low", "mcp", path, 0, "ajoute des serveurs MCP",
                           ", ".join(map(str, data["mcpServers"]))[:120]))
    if data.get("env"):
        out.append(finding("low", "env", path, 0, "définit des variables d'environnement",
                           ", ".join(map(str, data["env"]))[:120]))
    return out


def scan_text(text, rel, is_doc):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        hidden = sorted({HIDDEN[ord(c)] for c in line if ord(c) in HIDDEN and not (i == 1 and line.index(c) == 0 and c == "﻿")})
        if hidden:
            out.append(finding("high", "hidden", rel, i, "caractères Unicode cachés : " + ", ".join(hidden), show(line)))
        for pat, msg in DOWNLOAD_RUN:
            if re.search(pat, line, re.I):
                out.append(finding("high", "download-exec", rel, i, msg, show(line)))
                break
        else:
            for pat, msg in INSTALL_FROM_NET:
                if re.search(pat, line, re.I):
                    out.append(finding("medium", "install", rel, i, msg, show(line)))
                    break
        if CREDENTIALS_RE.search(line):
            out.append(finding("high", "credentials", rel, i, "mentionne un fichier ou une variable d'identifiants",
                               show(line)))
        for pat, sev in NO_ASK:
            m = re.search(pat, line, re.I)
            if m and not (sev == "medium" and NEGATION_RE.search(line[:m.start()].split(".")[-1])):
                out.append(finding(sev, "no-confirmation", rel, i,
                                   "consigne d'agir sans demander ou de cacher quelque chose à l'utilisateur",
                                   show(line)))
                break
        if DESTRUCTIVE_RE.search(line):
            out.append(finding("high", "destructive", rel, i, "commande destructrice", show(line)))
        for m in BASE64_RE.finditer(line):
            out.append(finding("medium", "encoded", rel, i, f"long bloc encodé (base64 probable, {len(m.group())} caractères)",
                               show(m.group(), 60)))
        for m in HEX_RE.finditer(line):
            out.append(finding("medium", "encoded", rel, i, f"long bloc encodé (hexadécimal, {len(m.group())} caractères)",
                               show(m.group(), 60)))
        if not is_doc and NETWORK_RE.search(line):
            out.append(finding("low", "network", rel, i, "accès réseau dans un script", show(line)))
    return out


def audit(root):
    root = os.path.abspath(os.path.expanduser(root))
    if not os.path.exists(root) and not os.path.islink(root):
        raise FileNotFoundError(root)
    base = root if os.path.isdir(root) else os.path.dirname(root)
    files, links = collect(root)
    inventory, findings, skills = [], [], []
    for p in links:
        rel = os.path.relpath(p, base)
        target = os.readlink(p)
        resolved = os.path.realpath(p)
        outside = not (resolved == base or resolved.startswith(base + os.sep))
        findings.append(finding("high" if outside else "low", "symlink", rel, 0,
                                "lien symbolique vers l'extérieur du dossier" if outside else "lien symbolique",
                                target))
        inventory.append({"file": rel, "kind": "lien", "bytes": 0, "executable": False})
    for p in files:
        rel = os.path.relpath(p, base)
        ext = os.path.splitext(p)[1].lower()
        try:
            mode = os.stat(p, follow_symlinks=False).st_mode
            raw = read_bytes(p)
        except OSError as e:
            findings.append(finding("low", "unreadable", rel, 0, f"illisible : {e.strerror}"))
            continue
        executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        binary = b"\0" in raw[:8192]
        shebang = raw[:2] == b"#!"
        kind = "binaire" if binary else ("script" if ext in SCRIPT_EXT or shebang else "texte")
        inventory.append({"file": rel, "kind": kind, "bytes": os.path.getsize(p), "executable": executable})
        if binary:
            sev = "high" if executable or ext in SCRIPT_EXT else "medium"
            findings.append(finding(sev, "binary", rel, 0, "fichier binaire : impossible à relire, à ne pas lancer"))
            continue
        if executable:
            findings.append(finding("medium", "executable", rel, 0, "fichier marqué exécutable"
                                    + (" (" + raw[:80].split(b"\n")[0].decode("utf-8", "replace") + ")" if shebang else "")))
        elif kind == "script":
            findings.append(finding("info", "script", rel, 0, "script que la skill peut lancer"))
        if len(raw) > MAX_BYTES:
            findings.append(finding("medium", "large", rel, 0, f"fichier de plus de {MAX_BYTES // 1_000_000} Mo, lu en partie"))
        if ext not in TEXT_EXT and not shebang:
            findings.append(finding("low", "unknown-type", rel, 0, f"type de fichier inhabituel ({ext})"))
        text = raw[:MAX_BYTES].decode("utf-8", "replace")
        findings += scan_text(text, rel, is_doc=kind == "texte")
        name = os.path.basename(p)
        if name == "SKILL.md":
            fm, fm_lines = frontmatter(text)
            skills.append({"file": rel, "name": fm.get("name", ""), "description": fm.get("description", "")[:300]})
            if not fm:
                findings.append(finding("low", "frontmatter", rel, 1, "pas d'en-tête YAML (name, description)"))
            for field in ("allowed-tools", "tools"):
                if field in fm:
                    findings += check_tools(split_tools(fm[field]), rel, 1, field)
            if fm.get("hooks"):
                findings.append(finding("medium", "hooks", rel, 1,
                                        "l'en-tête définit des hooks : commandes lancées automatiquement", fm["hooks"][:120]))
            if fm.get("model"):
                findings.append(finding("info", "model", rel, 1, f"impose le modèle {fm['model']}"))
        elif ext == ".json" and ("settings" in name or name in (".mcp.json", "hooks.json", "plugin.json")):
            try:
                findings += check_settings(json.loads(text), rel)
            except ValueError:
                findings.append(finding("low", "json", rel, 0, "JSON invalide"))
    findings.sort(key=lambda f: (-SEVERITY[f["severity"]], f["file"], f["line"]))
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITY}
    if counts["high"]:
        verdict = "Ne pas installer sans avoir lu et compris chaque point ÉLEVÉ."
    elif counts["medium"]:
        verdict = "À relire : rien de clairement dangereux, mais des points à vérifier."
    else:
        verdict = "Rien d'inquiétant repéré par l'analyse automatique. Lis quand même SKILL.md."
    return {"path": root, "skills": skills, "files": inventory, "findings": findings,
            "counts": counts, "verdict": verdict}


# Where `npx skills` looks for skills, relative to the repo root.
DISCOVERY_DIRS = ["skills", "skills/.curated", ".claude/skills", ".agents/skills", ".codex/skills",
                  ".cursor/skills", ".gemini/skills", ".github/skills", ".windsurf/skills",
                  ".opencode/skills", ".goose/skills", ".roo/skills", ".kiro/skills"]
MANIFESTS = [".claude-plugin/marketplace.json", ".claude-plugin/plugin.json", "plugin.json"]
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _inside(root, path):
    real = os.path.realpath(path)
    return real == root or real.startswith(root + os.sep)


def _skill_dirs_under(base, root, max_depth):
    """Folders holding a SKILL.md at most max_depth levels below base (symlinks not followed)."""
    found = []
    if not os.path.isdir(base) or os.path.islink(base):
        return found
    base_depth = base.rstrip(os.sep).count(os.sep)
    for dirpath, dirs, names in os.walk(base, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not os.path.islink(os.path.join(dirpath, d)))
        depth = dirpath.rstrip(os.sep).count(os.sep) - base_depth
        if "SKILL.md" in names and not os.path.islink(os.path.join(dirpath, "SKILL.md")):
            found.append(dirpath)
        if depth >= max_depth:
            dirs[:] = []
    return found


def _manifest_dirs(root):
    """Skill folders declared in marketplace.json / plugin.json (paths must stay inside root)."""
    out, problems = [], []
    for rel in MANIFESTS:
        mp = os.path.join(root, rel)
        if not os.path.isfile(mp) or os.path.islink(mp):
            continue
        try:
            with open(mp, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            problems.append(("error", f"{rel} : JSON invalide ou illisible"))
            continue
        entries = [data] if isinstance(data, dict) else []
        if isinstance(data, dict) and isinstance(data.get("plugins"), list):
            entries += [e for e in data["plugins"] if isinstance(e, dict)]
        for e in entries:
            src = e.get("source")
            plugin_root = os.path.normpath(os.path.join(root, src)) if isinstance(src, str) else root
            skills = e.get("skills")
            for sk in skills if isinstance(skills, list) else []:
                if not isinstance(sk, str):
                    continue
                d = os.path.normpath(os.path.join(plugin_root, sk))
                if not _inside(root, d):
                    problems.append(("error", f"{rel} : le chemin « {sk} » sort du dépôt"))
                elif os.path.isfile(os.path.join(d, "SKILL.md")):
                    out.append(d)
                else:
                    problems.append(("warning", f"{rel} : « {sk} » ne contient pas de SKILL.md"))
    return out, problems


def check_install(root, full_depth=False):
    """Check that a repo can be installed with `npx skills`. Reads only, never runs anything."""
    root = os.path.realpath(os.path.expanduser(root))
    if not os.path.isdir(root):
        raise FileNotFoundError(root)
    problems = []
    dirs = []
    if os.path.isfile(os.path.join(root, "SKILL.md")):
        dirs.append(root)
    for rel in DISCOVERY_DIRS:
        dirs += _skill_dirs_under(os.path.join(root, *rel.split("/")), root, 3)
    md, mp = _manifest_dirs(root)
    dirs += md
    problems += mp
    if full_depth or not dirs:
        dirs += _skill_dirs_under(root, root, 99 if full_depth else 8)
        if not full_depth and dirs:
            problems.append(("info", "aucun dossier standard : skills trouvées par recherche récursive"))
    seen, skills, names = set(), [], {}
    for d in dirs:
        d = os.path.realpath(d)
        if d in seen or not _inside(root, d):
            continue
        seen.add(d)
        rel = os.path.relpath(d, root)
        rel = "." if rel == "." else rel
        try:
            text = read_bytes(os.path.join(d, "SKILL.md")).decode("utf-8", "replace")
        except OSError:
            problems.append(("error", f"{rel} : SKILL.md illisible"))
            continue
        fm, _ = frontmatter(text)
        block = text[3:text.find("\n---", 3)] if fm else ""
        internal = bool(re.search(r"^\s+internal:\s*true\b", block, re.M | re.I))
        issues = []
        if not fm:
            issues.append(("error", "pas d'en-tête YAML (entre deux lignes ---)"))
        else:
            if not fm.get("name"):
                issues.append(("error", "champ name absent"))
            elif not NAME_RE.match(fm["name"].strip("\"'")):
                issues.append(("warning", f"name « {fm['name']} » : minuscules, chiffres et tirets attendus"))
            if not fm.get("description") or fm["description"] in (">-", ">", "|", "|-"):
                issues.append(("error", "champ description absent ou vide"))
        name = fm.get("name", "").strip("\"'")
        if name:
            names.setdefault(name, []).append(rel)
        skills.append({"dir": rel, "name": name, "internal": internal,
                       "issues": [{"level": l, "message": m} for l, m in issues]})
    for name, where in names.items():
        if len(where) > 1:
            problems.append(("warning", f"nom « {name} » utilisé par plusieurs skills : " + ", ".join(where)))
    if not skills:
        problems.append(("error", "aucune skill trouvée : il faut un dossier avec un SKILL.md "
                                  "(dans skills/, skills/.curated/, un dossier d'agent, ou un manifeste)"))
    errors = sum(1 for s in skills for i in s["issues"] if i["level"] == "error") + \
        sum(1 for l, _ in problems if l == "error")
    visible = [s for s in skills if not s["internal"]]
    if skills and not visible:
        problems.append(("warning", "toutes les skills sont internal : cachées sauf avec INSTALL_INTERNAL_SKILLS=1"))
    return {"path": root, "skills": skills, "problems": [{"level": l, "message": m} for l, m in problems],
            "errors": errors, "installable": errors == 0 and bool(skills)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check-install", action="store_true",
                    help="check that the folder can be installed with `npx skills`")
    ap.add_argument("--full-depth", action="store_true", help="with --check-install: search every level")
    a = ap.parse_args(argv)
    if a.check_install:
        try:
            r = check_install(a.path, a.full_depth)
        except FileNotFoundError:
            print(f"Introuvable ou pas un dossier : {a.path}", file=sys.stderr)
            return 2
        if a.json:
            print(json.dumps(r, indent=2, ensure_ascii=True))
        else:
            print(f"Vérification d'installation : {r['path']}")
            for s in r["skills"]:
                tag = " (internal)" if s["internal"] else ""
                print(f"  skill « {s['name'] or '?'} » ({s['dir']}){tag}")
                for i in s["issues"]:
                    print(f"      {i['level']} : {i['message']}")
            for p in r["problems"]:
                print(f"  {p['level']} : {p['message']}")
            print("\nInstallable avec npx skills." if r["installable"] else
                  f"\nPas installable en l'état : {r['errors']} erreur(s).")
        return 0 if r["installable"] else 1
    try:
        r = audit(a.path)
    except FileNotFoundError:
        print(f"Introuvable : {a.path}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=True))
        return 1 if r["counts"]["high"] else 0
    print(f"Analyse de : {r['path']}")
    for s in r["skills"]:
        print(f"  skill « {s['name'] or '?'} » ({s['file']})")
    scripts = [f for f in r["files"] if f["kind"] != "texte"]
    print(f"Fichiers : {len(r['files'])}, dont {len(scripts)} script(s), binaire(s) ou lien(s)")
    for f in scripts:
        print(f"  {f['file']} — {f['kind']}{', exécutable' if f['executable'] else ''}")
    c = r["counts"]
    print(f"\nPoints relevés : {c['high']} élevé(s), {c['medium']} moyen(s), {c['low']} faible(s), {c['info']} info")
    for f in r["findings"]:
        where = f["file"] + (f":{f['line']}" if f["line"] else "")
        print(f"  [{LABEL[f['severity']]}] {where} — {f['message']}")
        if f["excerpt"]:
            print(f"      {f['excerpt']}")
    print(f"\n{r['verdict']}")
    return 1 if c["high"] else 0


if __name__ == "__main__":
    sys.exit(main())

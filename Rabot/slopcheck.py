#!/usr/bin/env python3
"""slopcheck.py — find the tells that make a text read as unreviewed AI output.

Usage:
  python3 slopcheck.py FILE [FILE ...]        # human-readable report
  python3 slopcheck.py --json FILE            # machine-readable
  cat text.md | python3 slopcheck.py -        # read stdin

Prints a score from 0 to 100 (100 = no tells found) and every finding with its
line number. Standard library only. French and English.
"""
import argparse
import json
import re
import statistics
import sys

# Marker vocabulary: words and phrases that appear far more often in generated
# text than in human writing. Kept short on purpose: each entry must be a strong
# signal, not just a common word.
MARKERS = {
    "en": [
        r"\bdelve[sd]?\b", r"\bdelving\b", r"\bdive (?:deep )?into\b", r"\bdeep dive\b",
        r"\bit(?:'s| is) worth noting\b", r"\bit(?:'s| is) important to note\b",
        r"\bin today'?s (?:fast-paced|digital|ever-changing)\b", r"\bever-evolving\b",
        r"\bthe (?:digital |ever-changing )?landscape of\b", r"\btapestry\b", r"\btestament to\b",
        r"\bseamless(?:ly)?\b", r"\bleverag(?:e|es|ing)\b", r"\bunlock(?:s|ing)? the\b",
        r"\belevate[sd]? your\b", r"\bgame[- ]changer\b", r"\bcutting[- ]edge\b",
        r"\bnavigat(?:e|ing) the (?:complexities|world)\b", r"\bharness(?:ing)? the power\b",
        r"\bin conclusion\b", r"\bi hope this helps\b", r"\bfeel free to\b",
        r"\bmoreover\b", r"\bfurthermore\b", r"\brobust\b",
    ],
    "fr": [
        r"\bplong(?:er|eons|ez) (?:au cœur|dans)\b", r"\bil (?:est|convient) (?:important )?de noter\b",
        r"\bil est essentiel de\b", r"\bdans le paysage\b", r"\bpaysage (?:numérique|actuel)\b",
        r"\bà l'ère du numérique\b", r"\bdans un monde où\b", r"\bau cœur de\b",
        r"\brévolutionn(?:er|e|ez|aire)\b", r"\bincontournable\b", r"\bvéritable (?:levier|atout|révolution)\b",
        r"\bn'hésite[zs]? pas à\b", r"\ben (?:somme|conclusion)\b", r"\bdécortiqu(?:er|ons)\b",
        r"\bbooster\b", r"\bsans effort\b", r"\bde manière fluide\b", r"\brobuste\b",
        r"\bj'espère que (?:cela|ça) (?:t'|vous )?aide\b", r"\bpar ailleurs\b", r"\bde surcroît\b",
        r"\bun atout (?:majeur|précieux)\b", r"\bpleinement\b",
    ],
}
CONTRAST = [  # "not X, but Y" used as a default rhetorical move
    r"\bnot (?:just|only|merely) [^.;:!?]{1,60}, but\b",
    r"\bit'?s not (?:about )?[^.;:!?]{1,50}[,;—-]+ it'?s\b",
    r"\bpas (?:seulement|uniquement|juste) [^.;:!?]{1,60}, (?:mais|c'est)\b",
    r"\bce n'est pas [^.;:!?]{1,50}[,;—-]+ c'est\b",
]
HEDGES = [
    r"\bit is possible that\b", r"\bcould potentially\b", r"\bmay potentially\b", r"\bin some cases\b",
    r"\bil est possible que\b", r"\bdans certains cas\b", r"\bpotentiellement\b", r"\bdans une certaine mesure\b",
]
OPENERS = [
    r"^(?:great|excellent|good) question\b", r"^(?:certainly|absolutely|of course)[!,.]",
    r"^(?:bonne|excellente) question\b", r"^(?:bien sûr|absolument|certainement)\s*[!,.]",
    r"^(?:you(?:'re| are) asking|tu (?:me )?demandes|vous (?:me )?demandez)\b",
]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")


def lines_of(text):
    return text.splitlines()


def strip_code(text):
    """Ignore fenced code blocks and inline code: they are not prose."""
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def find_all(patterns, lines, kind, label=None):
    out = []
    for n, line in enumerate(lines, 1):
        low = line.lower()
        for p in patterns:
            for m in re.finditer(p, low):
                out.append({"line": n, "kind": kind, "match": line[m.start():m.end()], "label": label or kind})
    return out


def analyse(text):
    prose = strip_code(text)
    lines = lines_of(prose)
    words = re.findall(r"\w+", prose)
    n_words = max(1, len(words))
    findings = []

    # 1. dashes used as sentence connectors
    for n, line in enumerate(lines, 1):
        if line.lstrip().startswith(("|", "#", "-", "*", ">")) and "—" not in line:
            continue
        for m in re.finditer(r"\S\s+[—–]\s+\S|\w—\w", line):
            findings.append({"line": n, "kind": "dash", "match": m.group(0), "label": "tiret long en connecteur"})

    # 2. marker vocabulary
    for lang, pats in MARKERS.items():
        findings += find_all(pats, lines, "marker", f"vocabulaire marqueur ({lang})")

    # 3. "not X but Y" reflex
    findings += find_all(CONTRAST, lines, "contrast", "tournure « pas X, mais Y »")

    # 4. hedging
    findings += find_all(HEDGES, lines, "hedge", "précaution inutile")

    # 5. openers that restate or flatter
    first = next((l.strip() for l in lines if l.strip()), "")
    for p in OPENERS:
        if re.search(p, first.lower()):
            findings.append({"line": 1, "kind": "opener", "match": first[:60], "label": "ouverture de politesse / reformulation"})

    # 6. emoji used as bullets or headings
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if s and (EMOJI.match(s) or re.match(r"^(?:[-*]|\d+\.)\s*" + EMOJI.pattern, s) or
                  (s.startswith("#") and EMOJI.search(s))):
            findings.append({"line": n, "kind": "emoji", "match": s[:40], "label": "émoji en puce ou en titre"})

    # 7. bold density
    bolds = re.findall(r"\*\*[^*\n]+\*\*", prose)
    bold_per_100 = 100 * len(bolds) / n_words
    one_word_bolds = sum(1 for b in bolds if len(b.strip("*").split()) == 1)
    if bold_per_100 > 2.5 and len(bolds) >= 4:
        findings.append({"line": 0, "kind": "bold", "match": f"{len(bolds)} passages en gras",
                         "label": f"trop de gras ({bold_per_100:.1f} pour 100 mots)"})
    if one_word_bolds >= 5:
        findings.append({"line": 0, "kind": "bold", "match": f"{one_word_bolds} mots isolés en gras",
                         "label": "gras sur des mots isolés"})

    # 8. bullet-heavy text
    bullet_lines = sum(1 for l in lines if re.match(r"^\s*(?:[-*•]|\d+\.)\s+", l))
    text_lines = sum(1 for l in lines if l.strip())
    if text_lines >= 12 and bullet_lines / text_lines > 0.6:
        findings.append({"line": 0, "kind": "bullets", "match": f"{bullet_lines}/{text_lines} lignes",
                         "label": "presque tout en listes à puces"})

    # 9. paragraphs of near-identical length
    paras = [len(re.findall(r"\w+", p)) for p in re.split(r"\n\s*\n", prose)
             if len(re.findall(r"\w+", p)) >= 15 and not p.lstrip().startswith(("#", "|", "-", "*"))]
    if len(paras) >= 4:
        mean = statistics.mean(paras)
        if mean and statistics.pstdev(paras) / mean < 0.15:
            findings.append({"line": 0, "kind": "rhythm", "match": f"{len(paras)} paragraphes ~{mean:.0f} mots",
                             "label": "paragraphes tous de la même longueur"})

    # 10. reflexive groups of three ("A, B et C" / "A, B, and C") — only flagged when frequent
    triads = [n for n, l in enumerate(lines, 1)
              if re.search(r"\b\w+(?: \w+)?, \w+(?: \w+)?,? (?:et|and) \w+", l)]
    if len(triads) >= 4 and len(triads) / max(1, text_lines) > 0.2:
        findings.append({"line": triads[0], "kind": "triad", "match": f"{len(triads)} énumérations en trois",
                         "label": "énumérations par trois à répétition"})

    weights = {"dash": 3, "marker": 4, "contrast": 4, "hedge": 2, "opener": 6, "emoji": 3,
               "bold": 5, "bullets": 6, "rhythm": 5, "triad": 4}
    penalty = sum(weights[f["kind"]] for f in findings)
    # normalise by length: long texts naturally contain a few hits
    penalty = penalty * 300 / max(300, n_words)
    score = max(0, round(100 - penalty))
    return {"score": score, "words": len(words), "findings": sorted(findings, key=lambda f: (f["line"], f["kind"]))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+", help="files to check, or - for stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min", type=int, default=0, help="exit 1 if a file scores below this")
    args = ap.parse_args(argv)
    worst = 100
    reports = {}
    for f in args.files:
        if f == "-":
            text = sys.stdin.read()
        else:
            with open(f, encoding="utf-8") as fh:
                text = fh.read()
        r = analyse(text)
        reports[f] = r
        worst = min(worst, r["score"])
    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        for f, r in reports.items():
            print(f"{f}: score {r['score']}/100 ({r['words']} mots, {len(r['findings'])} signaux)")
            for x in r["findings"]:
                where = f"l.{x['line']}" if x["line"] else "global"
                print(f"  {where:>7}  {x['label']}: {x['match']}")
    return 1 if worst < args.min else 0


if __name__ == "__main__":
    sys.exit(main())

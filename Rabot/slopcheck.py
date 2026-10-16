#!/usr/bin/env python3
"""slopcheck.py — find the tells that make a text read as unreviewed AI output.

Usage:
  python3 slopcheck.py FILE [FILE ...]        # human-readable report
  python3 slopcheck.py --json FILE            # machine-readable
  cat text.md | python3 slopcheck.py -        # read stdin
  python3 slopcheck.py --fix-suggestions FILE # add a plain replacement per finding

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
        r"\blet'?s (?:explore|dive|unpack)\b", r"\bembark on\b",
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
        r"\bexplorons\b", r"\bplongeons\b", r"\bparcourons ensemble\b",
        r"\bpaysage (?:de|du|des)\b", r"\btapisserie\b",
    ],
}
CONTRAST = [  # "not X, but Y" used as a default rhetorical move
    r"\bnot (?:just|only|merely) [^.;:!?]{1,60}, but\b",
    r"\bit'?s not (?:about )?[^.;:!?]{1,50}[,;—-]+ it'?s\b",
    r"\bpas (?:seulement|uniquement|juste) [^.;:!?]{1,60}, (?:mais|c'est)\b",
    r"\bce n'est pas [^.;:!?]{1,50}[,;—-]+ c'est\b",
]
HEDGES = [
    r"\bit is possible that\b", r"\bpourrait potentiellement\b", r"\bpeut potentiellement\b",
    r"\bit might (?:be|possibly)\b", r"\bil se (?:peut|pourrait) que\b", r"\bil semblerait que\b", r"\bcould potentially\b", r"\bmay potentially\b", r"\bin some cases\b",
    r"\bil est possible que\b", r"\bdans certains cas\b", r"\bpotentiellement\b", r"\bdans une certaine mesure\b",
]
OPENERS = [
    r"^(?:great|excellent|good) question\b", r"^(?:certainly|absolutely|of course)[!,.]",
    r"^(?:bonne|excellente) question\b", r"^(?:bien sûr|absolument|certainement)\s*[!,.]",
    r"^(?:you(?:'re| are) asking|tu (?:me )?demandes|vous (?:me )?demandez)\b",
    # restating the question
    r"^(?:you want to know|you(?:'re| are) wondering|your question (?:is|about|concerns)|as for your question|regarding your question)\b",
    r"^(?:tu veux savoir|vous voulez savoir|tu te demandes|vous vous demandez|ta question|votre question|la question (?:de savoir|est de))\b",
    r"^(?:pour répondre à|concernant|à propos de) (?:ta|votre|la) question\b",
    # announcing what comes next
    r"^(?:let'?s (?:dive|explore|break|unpack)|here'?s (?:a |an |the )?(?:breakdown|overview|rundown)|i'?ll (?:walk you|explain|break))\b",
    r"^(?:explorons|plongeons|voyons ensemble|voici (?:un|une|le|la) (?:aperçu|tour d'horizon|résumé|panorama)|je vais (?:vous|te) (?:présenter|expliquer|détailler))\b",
]
CURLY = "\u201c\u201d\u2018\u2019"
FR_WORDS = {"le", "la", "les", "des", "est", "une", "un", "et", "de", "du", "que", "qui", "pour", "dans",
            "je", "tu", "vous", "nous", "pas", "sur", "avec", "ce", "ça", "au", "aux", "mais", "ou"}
EN_WORDS = {"the", "and", "is", "of", "to", "in", "that", "for", "with", "this", "are", "it", "you", "we",
            "was", "not", "but", "have", "on", "as"}

# Plain replacement per finding, used by --fix-suggestions. First matching entry wins.
KIND_FIX = {
    "dash": "remplacer par une virgule, deux points ou un point (deux phrases)",
    "contrast": "affirmer directement ce qui est vrai (« c'est Y »), sans nier X d'abord",
    "hedge": "affirmer, ou écrire « je ne sais pas » ; garder une seule précaution là où elle compte",
    "opener": "supprimer la phrase et commencer par la réponse",
    "emoji": "retirer l'émoji ; si c'est une puce, garder le texte seul",
    "bold": "garder le gras pour un ou deux termes à ne pas rater, retirer le reste",
    "bullets": "réécrire les puces qui ne sont pas de vraies listes en paragraphes",
    "rhythm": "couper ou fusionner des paragraphes pour varier les longueurs",
    "triad": "garder deux éléments, ou quatre, selon ce qui est vrai",
    "curly": "taper des guillemets droits (\" et ') comme le reste du texte",
    "marker": "dire la chose avec un mot simple, ou supprimer la phrase",
}
MARKER_FIX = [
    (r"delv|dive|plong|explor|unpack|parcour", "aller droit au sujet : dire ce que la partie contient"),
    (r"worth noting|important (?:de|to) note|convient de noter|est essentiel", "supprimer l'annonce et écrire l'information"),
    (r"landscape|paysage|tapestry|tapisserie", "nommer le domaine précis (le marché, les outils, la loi)"),
    (r"robust", "solide, fiable, ou le critère réel (tient 10 000 requêtes)"),
    (r"seamless|fluide|sans effort", "dire ce qui est simplifié, avec un chiffre si possible"),
    (r"leverag|levier|booster", "utiliser, employer, augmenter"),
    (r"révolution|game|cutting|incontournable|atout", "décrire l'effet réel, sans superlatif"),
    (r"conclusion|somme", "supprimer, ou écrire la conclusion sans l'annoncer"),
    (r"hope this|espère|feel free|hésite", "supprimer la formule de fin"),
    (r"moreover|furthermore|par ailleurs|de surcroît", "un point, ou « et »"),
    (r"au cœur|monde où|ère du", "commencer par le fait concret"),
    (r"pleinement", "supprimer l'adverbe"),
]
# The ten writing markers; five or more together are what a trained reader notices.
FAMILIES = {"dash": "tiret long", "contrast": "pas X, c'est Y", "emoji": "émojis", "bold": "gras et puces",
            "bullets": "gras et puces", "triad": "groupes de trois", "hedge": "précautions",
            "rhythm": "paragraphes identiques", "opener": "reformulation de la question",
            "marker": "vocabulaire marqueur", "curly": "typographie trop parfaite"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")


def lines_of(text):
    return text.splitlines()


def strip_code(text):
    """Ignore fenced code blocks and inline code: they are not prose."""
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def detect_lang(text):
    """Very rough: compare common French and English function words."""
    toks = re.findall(r"[\wçéèêàù']+", text.lower())
    fr = sum(1 for t in toks if t in FR_WORDS)
    en = sum(1 for t in toks if t in EN_WORDS)
    return "fr" if fr > en else "en"


def suggest(finding):
    """Plain replacement for one finding."""
    if finding["kind"] == "marker":
        for pat, fix in MARKER_FIX:
            if re.search(pat, finding["match"].lower()):
                return fix
    return KIND_FIX[finding["kind"]]


def find_all(patterns, lines, kind, label=None):
    out = []
    for n, line in enumerate(lines, 1):
        low = line.lower().replace("\u2019", "'")
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
    lang = detect_lang(prose)

    # 1. dashes used as sentence connectors. In French the em dash is the
    # first sign people look for, so every one inside a line counts (a dash
    # that opens a line is dialogue and is left alone).
    for n, line in enumerate(lines, 1):
        if lang == "fr":
            body = line.lstrip()
            for m in re.finditer(r"—|\s–\s", body):
                if m.start() == 0 and m.group(0) == "—":
                    continue
                ctx = body[max(0, m.start() - 12):m.end() + 12].strip()
                findings.append({"line": n, "kind": "dash", "match": ctx, "w": 5,
                                 "label": "tiret long (signe n°1 en français)"})
        else:
            for m in re.finditer(r"\S\s+[—–]\s+\S|\w—\w", line):
                findings.append({"line": n, "kind": "dash", "match": m.group(0), "label": "tiret long en connecteur"})

    # 2. marker vocabulary
    for mlang, pats in MARKERS.items():
        findings += find_all(pats, lines, "marker", f"vocabulaire marqueur ({mlang})")

    # 3. "not X but Y" reflex
    findings += find_all(CONTRAST, lines, "contrast", "tournure « pas X, mais Y »")

    # 4. hedging
    findings += find_all(HEDGES, lines, "hedge", "précaution inutile")

    # 5. openers that restate or flatter
    first_n, first = next(((i, l.strip()) for i, l in enumerate(lines, 1)
                           if l.strip() and not l.lstrip().startswith("#")), (1, ""))
    low_first = first.lower().replace("\u2019", "'")
    for p in OPENERS:
        if re.search(p, low_first):
            findings.append({"line": first_n, "kind": "opener", "match": first[:60],
                             "label": "ouverture de politesse, de reformulation ou d'annonce"})
            break

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

    # 11. curly quotes in English text that is otherwise plain ASCII. In French,
    # « » and ’ are normal and are never flagged.
    if lang == "en":
        other = [c for c in prose if ord(c) > 127 and c not in CURLY and c not in "—–" and not EMOJI.match(c)]
        curly_total = sum(prose.count(c) for c in CURLY)
        if curly_total >= 2 and not other:
            for n, line in enumerate(lines, 1):
                m = re.search("[" + CURLY + "]", line)
                if m:
                    findings.append({"line": n, "kind": "curly", "match": line[max(0, m.start() - 10):m.end() + 10].strip(),
                                     "label": "guillemets typographiques dans un texte tapé simplement"})

    weights = {"dash": 3, "marker": 4, "contrast": 4, "hedge": 2, "opener": 6, "emoji": 3,
               "bold": 5, "bullets": 6, "rhythm": 5, "triad": 4, "curly": 2}
    penalty = sum(f.get("w", weights[f["kind"]]) for f in findings)
    # normalise by length: long texts naturally contain a few hits
    penalty = penalty * 300 / max(300, n_words)
    score = max(0, round(100 - penalty))
    families = sorted({FAMILIES[f["kind"]] for f in findings})
    # "bold" and "bullets" are one marker in the guide's list of ten
    return {"score": score, "words": len(words), "lang": lang, "families": families,
            "noticeable": len(families) >= 5,
            "findings": sorted(findings, key=lambda f: (f["line"], f["kind"]))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+", help="files to check, or - for stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fix-suggestions", action="store_true",
                    help="add a plain replacement to each finding")
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
        if args.fix_suggestions:
            for x in r["findings"]:
                x["suggestion"] = suggest(x)
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
                if "suggestion" in x:
                    print(f"           -> {x['suggestion']}")
            if r["noticeable"]:
                print(f"  {len(r['families'])} familles de signes sur 10 ({', '.join(r['families'])}) : "
                      "un lecteur averti le repère.")
    return 1 if worst < args.min else 0


if __name__ == "__main__":
    sys.exit(main())

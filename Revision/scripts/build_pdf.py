#!/usr/bin/env python3
"""Turn a revision HTML file into a PDF with the skill's print style.

Usage: python3 build_pdf.py <cours.html> [sortie.pdf]

- inlines assets/cours.css (where <!-- STYLE --> is, or at the end of <head>)
- fills <nav class="toc"></nav> with the h2/h3 titles if the page has one (optional)
- prints with headless Google Chrome (or Chromium / Edge / Brave)
Standard library only.
"""
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CSS = os.path.join(HERE, "..", "assets", "cours.css")

BROWSERS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def find_browser():
    for path in BROWSERS:
        if os.path.exists(path):
            return path
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge"):
        found = shutil.which(name)
        if found:
            return found
    return None


def slug(text, used):
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "s"
    s, n = base, 2
    while s in used:
        s, n = f"{base}-{n}", n + 1
    used.add(s)
    return s


def add_toc(doc):
    used = set()
    entries = []

    def tag(m):
        level, attrs, inner = m.group(1), m.group(2), m.group(3)
        text = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        if 'class="prio' in inner:
            text = html.unescape(re.sub(r"<span class=\"prio[^>]*>.*?</span>", "", inner))
            text = re.sub(r"<[^>]+>", "", text).strip()
        idm = re.search(r'id="([^"]+)"', attrs)
        ident = idm.group(1) if idm else slug(text, used)
        if not idm:
            attrs += f' id="{ident}"'
        entries.append((level, ident, text))
        return f"<h{level}{attrs}>{inner}</h{level}>"

    # titles inside <main> only (not the cover)
    m = re.search(r"<main[^>]*>(.*)</main>", doc, re.S)
    if not m:
        return doc
    body = re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", tag, m.group(1), flags=re.S)
    doc = doc[: m.start(1)] + body + doc[m.end(1):]
    items = []
    for level, ident, text in entries:
        cls = ' class="sub"' if level == "3" else ""
        items.append(f'<li{cls}><a href="#{ident}">{html.escape(text)}</a></li>')
    toc = '<nav class="toc"><h2>Sommaire</h2><ol>' + "".join(items) + "</ol></nav>"
    return re.sub(r'<nav class="toc">\s*</nav>', toc, doc, count=1)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".pdf"

    with open(src, encoding="utf-8") as f:
        doc = f.read()
    with open(CSS, encoding="utf-8") as f:
        style = "<style>\n" + f.read() + "\n</style>"

    doc = re.sub(r'<link[^>]+href="[^"]*cours\.css"[^>]*>', "", doc)
    if "<!-- STYLE -->" in doc:
        doc = doc.replace("<!-- STYLE -->", style, 1)
    else:
        doc = doc.replace("</head>", style + "\n</head>", 1)
    doc = add_toc(doc)

    browser = find_browser()
    if not browser:
        sys.exit("Aucun navigateur Chrome/Chromium/Edge trouvé : installe Google Chrome, "
                 "ou ouvre le HTML et fais Imprimer > Enregistrer en PDF.")

    # temp file next to the source, so relative image paths still work
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=os.path.dirname(src))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(doc)
    try:
        with tempfile.TemporaryDirectory() as profile:
            cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run",
                   f"--user-data-dir={profile}", "--no-pdf-header-footer",
                   "--virtual-time-budget=4000", f"--print-to-pdf={out}", "file://" + tmp]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    finally:
        os.remove(tmp)
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        sys.exit("Échec de l'impression PDF :\n" + r.stderr[-2000:])
    print(f"PDF : {out} ({os.path.getsize(out) // 1024} Ko)")


if __name__ == "__main__":
    main()

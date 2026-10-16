---
name: rabot
description: >-
  Copy-editing pass that removes verbal tics and filler from text, docs and
  website copy so it reads clearly and plainly, without changing the meaning or
  the facts. Includes slopcheck.py, a checker that scores a text 0-100 and lists
  each tic with its line number (filler phrases, dash-heavy sentences, bold
  everywhere, emoji bullets, hedging, identical paragraph lengths, curly quotes
  in plain English text), and a site review mode: signs of a generated site, a
  launch checklist and a security checklist. Use when the user types
  /rabot or asks to make a text simpler, clearer, less formulaic, or to review
  a README or landing page before publishing.
argument-hint: "[fichier | texte | site <chemin>]"
---

# rabot

A careful human editor's pass: shorter sentences, concrete words, no filler, no
template structure. The text keeps its meaning, its facts and its author's voice.

What the user typed after `/rabot`: `$ARGUMENTS`

This is an editing tool for quality. It does not hide how a text was produced. If a
context requires saying that AI helped (school work, journalism, a client contract),
that stays the user's responsibility, and the skill never claims a text is
"undetectable".

## The checker

```bash
python3 "${CLAUDE_SKILL_DIR}/slopcheck.py" FILE [FILE ...]
python3 "${CLAUDE_SKILL_DIR}/slopcheck.py" --json FILE
python3 "${CLAUDE_SKILL_DIR}/slopcheck.py" --fix-suggestions FILE
python3 "${CLAUDE_SKILL_DIR}/slopcheck.py" --min 80 FILE      # exit 1 below 80
cat texte.md | python3 "${CLAUDE_SKILL_DIR}/slopcheck.py" -
```

Score out of 100 (100 means no tic found) and the list of findings by line. Code
blocks are ignored. The language (French or English) is guessed from the text.

- In French, every em dash inside a line is flagged and weighs more (it is the
  first sign people look for). A dash that opens a line (dialogue) is left alone.
- Openers are checked on the first line of prose: compliments, restating the
  question ("you want to know", "ta question porte sur"), announcing what follows
  ("voici un aperçu", "let's dive").
- Curly quotes are flagged only in English text that is otherwise plain ASCII.
  French « » and the typographic apostrophe are normal and never flagged.
- `--fix-suggestions` adds one plain replacement under each finding.
- When five or more of the ten writing-marker families are present, the report
  says so: that is the point where a trained reader spots the text.

## Text mode (default)

No marker is a fault on its own. The accumulation is what betrays a text, and five
of them together are enough for a trained reader. Judge the whole text, not one
sentence.

1. Run the checker on the text and keep the score.
2. Rewrite, in the text's own language, going through the ten markers:
   1. **Em dash mid-sentence** (sign number one in French): turn it into a comma,
      a colon, or two sentences.
   2. **"It's not X, it's Y"** as the default structure: state what is true, once.
   3. **Emojis** as punctuation, bullets or section markers: remove them unless the
      author asked for them.
   4. **Bullets and bold everywhere**: lists only for real lists, prose for the
      rest; bold for one or two things a reader must not miss, never one word per
      sentence.
   5. **Reflexive groups of three**: keep the number of items that is true (often
      two, sometimes four).
   6. **Excessive hedging** ("il est possible que", "cela pourrait potentiellement",
      "dans certains cas", "it could potentially"): make the claim, or say you do
      not know; keep one hedge where it matters.
   7. **Paragraphs of identical length**: vary them; a short one after a long one.
   8. **Restating the question** at the start, flattering it, or announcing what
      comes next: start with the answer.
   9. **Marker vocabulary**: explorons, plongeons dans, il convient de noter,
      "paysage" used figuratively, au cœur de, robuste, révolutionner; in English
      delve, landscape, tapestry, seamless, leverage, it's worth noting. Use the
      plain word.
   10. **Curly quotes / over-perfect typography** where the rest of the text is
       typed casually: use the same quotes as the rest. In French, « » and ’ are
       normal: do not remove them blindly, only fix mismatches.
   Also cut closers ("hope this helps", "n'hésite pas à") and prefer a precise
   example or number over an adjective.
3. Never change facts, figures, names, code, links or the author's position. Keep
   the author's ideas and examples: change the form only. If a sentence is
   unclear, ask instead of guessing.
4. Run the checker again on the result.
5. Report to the user:
   - the new text, and the score before and after;
   - **what was removed or changed and why**: a short list by marker ("3 em dashes
     replaced by commas or full stops", "bold cut from 14 passages to 2",
     "opening sentence that restated the question removed"), not every edit;
   - anything left on purpose, with the reason (a quote, a legal wording).

For a file, edit it in place only if the user asked; otherwise show the new version.
The same behaviour applies when the user pastes a text and asks for a "cleanup":
ideas and examples untouched, form only, and a visible list of what went and why.

## Site mode (`site <path>`)

Review a website or landing page project before launch. Work in four passes. In each,
report every item as **present**, **missing** or **to improve**, name the **file
concerned**, give the **fix**, and rank the list from most to least urgent. Change
nothing until the user approves.

### Pass 1: signs of a site nobody looked at (20)

Check each one against the files and the live page if there is one.

1. Deployment subdomain left as the address (`*.vercel.app`, `*.netlify.app`, etc.).
2. Violet-to-blue gradient as the main look.
3. Photos that are visibly generated (odd hands, text that is not text, plastic skin).
4. Invented testimonials (stock faces, generic names, no company or link).
5. Buttons that do nothing (`href="#"`, no handler, dead form).
6. Scroll animations on every block.
7. A single page with everything stacked and no reason to be one page.
8. Logo that is only the name in the default font.
9. No favicon.
10. Headline with an animated colour gradient.
11. Empty privacy policy page (title and placeholder text).
12. Empty terms and conditions page.
13. Fake visitor counter ("1,247 people online").
14. Fake customer counter ("10,000+ happy users" with nothing behind it).
15. Invented figures and percentages with no source.
16. Emojis used as icons.
17. A headline that says nothing ("unlock your potential") instead of what the
    product does.
18. Script or handwriting font on a professional site.
19. Generator badge left in the footer ("Made with ...").
20. Em dashes in the site copy (run the checker on every page's text).

### Pass 2: chosen or default? (24 design reflexes)

None is forbidden. For each visual element, ask whether it was chosen for this
product or came by default, and flag the defaults. The reflexes are grouped in
section 2 of the charter (see Charter mode) and cover: colour (violet gradients, violet and black,
neon on dark, washed pastels, a new colour per section, pure white everywhere);
surfaces (a shadow on every element, the same radius everywhere, frosted glass
everywhere); decoration (blurred orbs, dot grids, colour strips, floating icons in
the margins, fake three-dot terminal); layout (three feature cards in a row, bento
grid for everything, three pricing tiers with the middle one highlighted when
there is one offer, green-tick bullets); motion (fade-in on every block, hover
animation on everything including what is not clickable, bouncing arrow, animated
gradient title); icons and type (a sparkle for "AI" on every button, emojis in
place of an icon set, Inter / Geist / Space Grotesk without a reason). Also ask for
a real demonstration of the product (screenshot, video, live example): the most
often missing element.

### Pass 3: missing before launch (20)

1. Custom 404 page with a way back.
2. Call to action visible above the fold.
3. A unique `<title>` per page.
4. A meta description per page.
5. A share image (Open Graph / social card).
6. A full favicon set (tab, Apple touch icon, manifest icons).
7. `robots.txt`.
8. A sitemap.
9. Alt text on every meaningful image.
10. Real mobile breakpoints, tested at 375 px wide, not just a shrunk desktop.
11. A sticky call to action on mobile.
12. Loading states (buttons, lists, images).
13. Form error messages that say which field and why.
14. A confirmation page or state after a form is sent.
15. A real privacy policy matching what is collected.
16. Real terms and conditions.
17. A compliant cookie banner with a real "refuse" button of equal weight.
18. Analytics (privacy-respecting if possible).
19. A real contact address that answers.
20. Compressed images (modern format, sensible dimensions).

Output for passes 1 to 3, per item: present / missing / to improve, file concerned,
fix, ordered most to least urgent.

### Pass 4: security (20)

Read the code only; this is a quick check, not a test of the running site. Report,
per finding: its **state** (ok / problem / cannot tell), the **file and line**, what
an **attacker could do** in one sentence, and the **fix**. Rank by real severity
(what is exploitable today first), not by list order. Change nothing.

The first two matter most:

1. Row-level security (or equivalent access control) enabled on every table.
2. No secret in git history: a key deleted in a later commit is still public. It
   must be revoked, then the history rewritten.

Then:

3. No secret key in the code shipped to the browser; only public keys client-side,
   the service key stays on the server.
4. Authentication checked on the server, not only hidden in the interface.
5. Ownership check on every object id (no reading another user's data by changing
   an id in the URL or request).
6. Protected fields (role, price, owner) cannot be set by a request body.
7. Session cookies `httpOnly`, `secure`, `sameSite`.
8. Passwords hashed with argon2 or bcrypt, never plain or MD5.
9. Rate limit on login, password reset and public forms; anti-bot on public forms.
10. Parameterised queries, no string-built SQL.
11. All input validated on the server.
12. User content escaped on output (XSS).
13. File uploads limited by type, size and extension, stored outside the web root.
14. API responses return only the needed fields (no password hash, no other users'
    emails).
15. Sensitive data encrypted at rest.
16. HTTPS forced everywhere, with redirect.
17. Security headers: content security policy, frame protection, content type.
18. Dependencies scanned and up to date.
19. CORS not set to `*` with credentials; CSRF protection on state-changing
    requests.
20. Errors and logs that do not leak stack traces, tokens or personal data; admin
    and debug routes closed in production.

This is a read-through. For a real security pass, hand over to `/purple`.

## Charter mode (`charte`)

The charter lives in its own repository, Garde-fou: a short set of permanent writing,
site and code rules between `<!-- rabot:start -->` and `<!-- rabot:end -->` markers.
Fetch the current version:

```bash
curl -fsSL https://raw.githubusercontent.com/adambrai/Garde-fou/main/CHARTE.md
```

If the fetch fails (offline), say so and point to
https://github.com/adambrai/Garde-fou instead of writing a charter from memory.

On `/rabot charte`, show it to the user and, only with their OK, add it to the
project's `CLAUDE.md` (or replace an existing block between the same markers, leaving
the rest of the file untouched). It can also be pasted into Claude's personal
preferences or another assistant's custom instructions.

## Rules

- Meaning, facts and voice first; style second.
- Show the before/after score so the user sees the effect.
- No new claims, no invented examples, no marketing tone.

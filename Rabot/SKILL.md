---
name: rabot
description: >-
  Copy-editing pass that removes verbal tics and filler from text, docs and
  website copy so it reads clearly and plainly, without changing the meaning or
  the facts. Includes slopcheck.py, a checker that scores a text 0-100 and lists
  each tic with its line number (filler phrases, dash-heavy sentences, bold
  everywhere, emoji bullets, hedging, identical paragraph lengths), and a
  checklist for reviewing a website before launch. Use when the user types
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
cat texte.md | python3 "${CLAUDE_SKILL_DIR}/slopcheck.py" -
```

Score out of 100 (100 means no tic found) and the list of findings by line. Code
blocks are ignored.

## Text mode (default)

1. Run the checker on the text and keep the score.
2. Rewrite, in the text's own language:
   - cut filler openers and closers (compliments on the question, restating it,
     "hope this helps", "feel free to");
   - replace stock phrases with the plain word;
   - turn dash-joined clauses into two sentences or a comma;
   - keep bold for at most one or two things a reader must not miss;
   - use lists only for real lists; write the rest as paragraphs;
   - vary sentence and paragraph length naturally;
   - say things once, directly; drop unnecessary hedging;
   - prefer a precise example or number over an adjective.
3. Never change facts, figures, names, code, links or the author's position. If a
   sentence is unclear, ask instead of guessing.
4. Run the checker again on the result.
5. Give the user the new text, the score before and after, and a short list of the
   kinds of changes made (not every edit).

For a file, edit it in place only if the user asked; otherwise show the new version.

## Site mode (`site <path>`)

Review a website or landing page project before launch. Report each item as
present, missing or to improve, with the file to change. Change nothing until the
user approves.

- **Copy**: run the checker on the main pages' text; a headline that says plainly
  what the product does; real testimonials and figures only.
- **Choices vs defaults**: for each visual element (palette, gradients, fonts,
  card grids, animations on every block), ask whether it was chosen for this
  product or came by default. Flag the defaults.
- **Launch basics**: custom domain, favicon set, a title and meta description per
  page, a social share image, alt text, robots.txt and sitemap, a 404 page with a
  way back, a clear call to action above the fold, mobile layout checked at 375 px,
  form error messages and a confirmation page, real privacy policy and legal notice
  matching what is actually collected, a cookie banner with a real refuse option, a
  real contact.
- **Security basics**: secrets out of the browser bundle and out of git history,
  server-side auth checks, ownership checks on every object id, rate limiting on
  login and public forms. For a real security pass, hand over to `/purple`.

## Rules

- Meaning, facts and voice first; style second.
- Show the before/after score so the user sees the effect.
- No new claims, no invented examples, no marketing tone.

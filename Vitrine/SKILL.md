---
name: vitrine
description: >-
  Design and build a web interface that looks chosen rather than generated,
  in five gated stages: direction, visual reference, implementation, check in a
  real browser (desktop and 375 px), and an interface audit (accessibility,
  forms, motion, launch basics). Works with whatever the session has: a design
  system file in the project, Playwright CLI if installed, or the built-in
  browser tools. Use when the user types /vitrine, asks to design or redesign
  a page, make a UI less generic, or check a front-end visually.
argument-hint: "[page ou projet à concevoir | redesign <chemin> | audit <url>]"
---

# vitrine

An interface is the shop window of a product. This skill gives it a direction that
fits the product, then checks the result with real screenshots instead of trusting
the code.

What the user typed after `/vitrine`: `$ARGUMENTS`

- Nothing, or a description of a page: run all five stages.
- `redesign <path>`: read the existing page first, then run all five stages on it.
- `audit <url or path>`: skip to Stage 4 and Stage 5 on what already exists.

## Golden rule

Work in stages and **do not start a stage until the previous one is finished and
shown to the user**. Doing everything in one pass is how pages end up generic.

At the end of each stage, show what it produced, say in one line what comes next, and
wait for the user's go-ahead (or a correction). If the user says "go on without
stopping", keep the order of the stages anyway and still show each result as you go.
Keep a short running log in the conversation: stage, decision, file changed.

## Stage 1 — Direction

1. Ask (once, briefly) or infer: who uses this, what they must find in three seconds,
   what the one main action is, and the tone (sober, warm, technical, playful...).
2. Look for an existing design source in the project, in this order of authority:
   `DESIGN.md`, a design-tokens file, the existing CSS/Tailwind theme, a brand guide.
   **The project's own design source always wins** over any style suggestion; say
   which one governs.
3. If there is none, propose one direction in a few lines: palette (3 to 5 colours
   with their role: background, text, accent, state), type pairing (one family for
   headings, one for text, with sizes on a scale), spacing unit, corner radius, and
   one distinctive idea that belongs to this product (a layout, a texture, a way of
   showing data). Avoid the defaults that make a page look generated: purple-to-blue
   gradients, a centred hero with two buttons over three icon cards, glassmorphism
   everywhere, emoji as icons, every block the same size.
4. Read the stack before choosing anything: framework, CSS approach, component
   library already in use. Work inside it; do not add a framework or a UI kit unless
   the user asks.

Done when: the user has approved the direction, or the project's design source has
been named as the one that governs.

## Stage 2 — Visual reference before code

Before touching the real code, make something the user can look at:

- a static HTML mock-up of the key screen (one file, inline CSS, real text from the
  product, no lorem ipsum), opened in the browser and captured as a screenshot; or
- when the change is small, an annotated description of the layout with the exact
  tokens it will use.

Show the hierarchy at desktop width and at 375 px: what is read first, second, third,
and where the main action sits. If you hesitate between two directions, show two
mock-ups side by side and let the user pick; never more than two.

Done when: the user has approved one reference. Keep the mock-up file outside the
production code (for example in a scratch folder) unless the user wants it kept.

## Stage 3 — Implementation

1. Turn the approved direction into tokens first (CSS custom properties, the Tailwind
   theme, or the project's token file), then build the components from those tokens.
   No colour, size or spacing value written by hand in a component if a token exists.
2. Semantic HTML first: landmarks (`header`, `nav`, `main`, `footer`), one `h1`, real
   `button` and `a` elements, `label` tied to each field.
3. Mobile first: the 375 px layout must work without horizontal scroll; add
   breakpoints only where the content needs them.
4. Every interactive element gets its states: hover, focus-visible, active, disabled,
   loading, error, empty. Design the empty and error states too, not only the happy path.
5. Images: explicit `width` and `height`, `alt` text, modern formats, lazy loading
   below the fold. Fonts: at most two families, `font-display: swap`.
6. Motion only where it explains something (an element appearing, a state changing),
   short (150–300 ms), and disabled under `prefers-reduced-motion: reduce`.
7. Change only the files the task needs. Say which files you changed.

Done when: the page runs locally and the user has seen the list of changed files.

## Stage 4 — Check in a real browser

Code that looks right is not proof. Open the page and look at it.

1. Start the project's dev server (or open the static file) and note the URL.
2. Pick the browser tool:
   - **Playwright CLI**, if installed. Check with `command -v playwright` or
     `npx --no-install playwright --version`. Do not install it without asking.
     ```bash
     npx playwright screenshot --viewport-size=1440,900 --full-page URL desktop.png
     npx playwright screenshot --viewport-size=375,812 --full-page URL mobile.png
     ```
   - Otherwise, the **browser tools built into the session** (browser pane, preview
     tools, or a connected browser): resize to 1440 × 900, then to 375 × 812, and take
     a screenshot at each size.
   - If no browser is available at all, say so plainly and list what could not be
     checked. Never claim a visual check that did not happen.
3. Look at both screenshots for: horizontal scroll, text that overflows or is cut,
   overlapping elements, images distorted or missing, tap targets crowded together,
   the main action out of sight on mobile, contrast that looks weak, fonts not loaded.
4. Read the browser console for errors and failed requests.
5. Fix what you found, take the screenshots again, and show the before and after.

Done when: both widths have been captured after the last change and shown to the user.

## Stage 5 — Interface audit

Go through this list on the real page and report each line as OK, fixed, or to do
(with the file and the change needed):

- **Keyboard**: every action reachable with Tab, in a logical order; Enter and Space
  work on buttons; Escape closes menus and dialogs; no keyboard trap; a "skip to
  content" link if there is a long navigation.
- **Focus**: a visible focus ring on every interactive element (never
  `outline: none` without a replacement); focus moves into a dialog when it opens and
  back when it closes.
- **Contrast**: text at least 4.5:1 against its background (3:1 for text 24 px and
  up, or 19 px bold), icons and field borders at least 3:1. Compute the ratio from
  the actual colours; check the hover, disabled and placeholder states too.
- **Touch targets**: at least 24 × 24 px, 44 × 44 px for the main actions on mobile,
  with space between neighbours.
- **Forms**: a visible label on every field (a placeholder is not a label), the right
  `type` and `autocomplete`, errors written in words next to the field and announced
  (`aria-describedby`, `aria-invalid`), required fields marked, nothing lost when
  submission fails.
- **Motion**: `prefers-reduced-motion` respected, nothing flashing more than three
  times per second, no autoplay with sound, carousels that can be paused.
- **Content**: one `h1`, headings in order, `lang` on `html`, link text that makes
  sense out of context, `alt` on informative images and empty `alt` on decorative ones.
- **Launch basics**: `<title>` and meta description per page, favicon, Open Graph
  image, a 404 page, `viewport` meta tag, no console errors, no broken links, real
  legal pages where the law requires them, a cookie banner with a refusal as easy as
  acceptance if non-essential cookies are used.

If the project has automated checks (Lighthouse, axe, a linter), run them and include
the result, but they do not replace the list above.

Finish with a short report: the direction used and which source governs, the files
changed, the two screenshots, and the audit table with what is left to do.

## Rules

- The project's design source beats this skill's taste. When they disagree, follow
  the project and mention the point once.
- Never skip Stage 4 because "the code is fine".
- Do not add dependencies, fonts from new providers, or tracking scripts without the
  user's go-ahead.
- Do not copy another site's design, logo or images. Inspiration is a direction, not
  a template.

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

## Why generated pages look alike, and what to do about it

A model writes what is statistically most common: white background, rounded cards,
a violet-to-blue gradient, one neutral sans-serif everywhere. Asking for "a modern
page" does not change that. What changes it is constraints that come from outside the
model. This skill applies five of them, one per stage or rule:

1. **A reference taste**: a direction chosen on purpose (Stage 1, with optional
   style presets).
2. **A rulebook**: the audit list (Stage 5).
3. **A design system**: tokens and component rules the project already owns, or one
   chosen after previewing it (Stage 1).
4. **A visual reference**: something to look at before coding (Stage 2).
5. **Visual verification**: real screenshots after every change (Stage 4).

If one of them is missing, say which and work without pretending it was there.

## Golden rule

Work in stages and **do not start a stage until the previous one is finished and
shown to the user**. Doing everything in one pass is how pages end up generic.

At the end of each stage, show what it produced, say in one line what comes next, and
wait for the user's go-ahead (or a correction). If the user says "go on without
stopping", keep the order of the stages anyway and still show each result as you go.
Keep a short running log in the conversation: stage, decision, file changed.
Do not move to the next step until the previous one is complete, and change one
thing at a time: if a pass touches palette, layout and type together, nobody can say
which change helped or broke the page.

**Design-decision log.** From Stage 1 on, keep a small table (in the conversation, or
in `design-decisions.md` if the user wants it kept) with one row per decision: what
was decided, why (audience, brand, constraint), which source it comes from, and the
stage. Later stages read it before changing anything, so a late fix does not quietly
undo an early choice. When a decision is reversed, add a row instead of erasing the old one.

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
4. Check the default reflexes in `reflexes.md` (same folder as this file) against the
   proposed direction. For each one that appears, answer "chosen or default?" in a
   sentence. Keep it only if it is chosen for this product.
5. Read the stack before choosing anything: framework, CSS approach, component
   library already in use. Work inside it; do not add a framework or a UI kit unless
   the user asks.

Product decisions stay with the user: audience, purpose, what comes first on the
page. A tool or a style can help execute them but cannot make them. If they are not
known, ask before drawing anything.

### Style presets (optional)

Offer these as named options, never impose one. Each is a starting point to adapt to
the product, not a theme to paste.

- **Redesign of an existing project**: read the current pages, keep the content and
  the routes, list what works and what does not, then change the look in layers
  (tokens, then layout, then components) so the result can be compared with the before.
- **Finish everything**: an output discipline that can be combined with any other
  preset. No empty section, no `TODO`, no "content coming soon", no button without a
  destination, no placeholder image. If something is missing, ask for it or remove the
  block.
- **Minimalist**: one accent colour, large type, generous space, few components, no
  decoration that carries no information. Hierarchy comes from size and spacing.
- **Soft**: gentle contrast between surfaces, rounded but not identical shapes,
  warm neutrals instead of pure white and black, subtle depth, calm motion. Keep body
  text dark enough to read (see the contrast rule in Stage 5).
- **Brutalist**: raw structure, thick borders, strong grid, flat saturated colours,
  system or monospaced type, visible links and no softening. Still readable and
  keyboard-friendly: the roughness is a choice, not a bug.

### Design systems

- Look first for one inside the project (`DESIGN.md`, token files, theme).
- If the user points to a design-system registry or library, remember that each system
  usually comes as two files: a `SKILL.md` (tokens, component rules, accessibility
  constraints, written for the agent) and a `DESIGN.md` (the human intent and the
  reasoning behind it). Read both.
- **Preview before choosing.** Names mislead: render the candidate's colours, type and
  two or three components and look at them. Never pick a system by its name.
- Never mix two systems silently. If two compete, say which governs: the project's own
  `DESIGN.md` has authority.

Done when: the user has approved the direction, or the project's design source has
been named as the one that governs, and the first rows of the decision log exist.

## Stage 2 — Visual reference before code

Before touching the real code, make something the user can look at:

- a static HTML mock-up of the key screen (one file, inline CSS, real text from the
  product, no lorem ipsum), opened in the browser and captured as a screenshot; or
- when the change is small, an annotated description of the layout with the exact
  tokens it will use.

Two ways to get a reference:

- **The user brings one** (screenshot, design export, photo of a site they like):
  implement it faithfully. Describe what you see (layout, spacing, type, colours) and
  list anything you cannot read from the image, then ask instead of inventing. Do not
  copy logos, photos or trademarked elements.
- **No reference exists**: propose and produce one first (the mock-up above, or an
  image if an image tool is available), show it, and only then code from it. Code
  follows the approved image, not the other way round.

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
   - **Playwright CLI as an agent tool** (`playwright-cli`). It uses far less context
     than an MCP browser server. Ask before installing, then:
     ```bash
     npm i -g @playwright/cli@latest
     playwright-cli install-browser
     playwright-cli install --skills
     ```
     The last step matters: without it the agent has no skill describing the tool
     and never knows it exists. With it, the agent can open a page, take screenshots,
     read the accessibility tree, click, fill forms and read console and network.
     Keep an MCP browser server for complex exploratory automation only.
   - Otherwise, the **browser tools built into the session** (browser pane, preview
     tools, or a connected browser): resize to 1440 × 900, then to 375 × 812, and take
     a screenshot at each size.
   - If no browser is available at all, say so plainly and list what could not be
     checked. Never claim a visual check that did not happen.
3. Look at both screenshots for: horizontal scroll, text that overflows or is cut,
   overlapping elements, images distorted or missing, tap targets crowded together,
   the main action out of sight on mobile, contrast that looks weak, fonts not loaded.
4. Read the browser console for errors and failed requests.
5. Also check: hover states exist, buttons do not overflow their container at 375 px,
   grids do not collapse into one broken column, text stays readable on its background,
   loading and empty states appear instead of blank areas.
6. Fix what you found, take the screenshots again, and show the before and after.
   Run the loop open localhost, capture, fix, capture at 375 px again, one problem at
   a time. After each fix, re-check the earlier points quickly: a fix often breaks
   something next to it.
7. **Login walls.** A browser opens a blank session, so a page behind a login shows
   only the sign-in screen. Check a public page or a demo route filled with sample
   data instead, and never type real credentials. Do not accept a screenshot of the
   login form as proof that the dashboard works.
8. **Read the screenshot yourself**, with your own eyes on the image, and describe what
   is on it. A saved file is not a check.

Done when: both widths have been captured after the last change and shown to the user,
and each issue found is recorded as fixed or still open.

## Stage 5 — Interface audit

Triggered by the stage itself or by requests such as "review the interface", "check
accessibility" or "audit the design". Go through this list on the real page and report each line as OK, fixed, or to do
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

- **Default reflexes**: run `reflexes.md` on the finished page, not only on the plan.
  Pay most attention to the costliest one: a page with no real view of the product.
- **Honesty of content**: no invented testimonials, user counters or figures; no
  button or link that goes nowhere; a headline that says what the product does for
  whom, not a vague promise.
- **Three-second test**: can someone who arrives for the first time find what they
  came for within three seconds? Try it on the 375 px screenshot, then on desktop.

**When the audit fights the style.** If a low-contrast style (soft greys, pale text)
fails the contrast check, darken only the body text and the action labels. Light grey
can stay for decoration, dividers and non-essential details. Record the change in the
decision log. If a fix would alter the approved direction, say so before applying it.

If the project has automated checks (Lighthouse, axe, a linter), run them and include
the result, but they do not replace the list above.

Finish with a short report: the direction used and which source governs, the files
changed, the two screenshots, and the audit table with what is left to do.

## Order of adoption and starter prompt

When the user is new to this approach, add the constraints one at a time rather than
all at once: first a direction, then the audit list, then a design system, then a
visual reference, and last browser verification. Test each on a small page before
trusting it on a large one. A prompt that starts the full flow:

```
/vitrine <page>. Work in five steps: 1) direction, 2) visual reference, 3) code,
4) check in a browser at 1440 and 375 px, 5) accessibility and launch audit.
Show the result of each step. Do not move to the next step until the previous one
is complete.
```

## Common mistakes

- Changing everything at once, so no one can tell what changed what.
- Choosing a design system by its name without previewing it.
- Believing a tool makes the product decisions. Audience, purpose and information
  hierarchy belong to the user.
- Trusting the code without looking at the page.
- Fixing one problem and not checking the others again.

## Rules

- The project's design source beats this skill's taste. When they disagree, follow
  the project and mention the point once.
- Never skip Stage 4 because "the code is fine".
- Do not add dependencies, fonts from new providers, or tracking scripts without the
  user's go-ahead.
- Do not copy another site's design, logo or images. Inspiration is a direction, not
  a template.
- Never invent testimonials, customer counts, statistics or logos of clients.
- If the style, the audit and the project disagree, say which one governs and why,
  and write it in the decision log.

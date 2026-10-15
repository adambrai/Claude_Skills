# Debat rubric

Every judge in /debat scores against this page. Scores are 0–10 per criterion;
`debat.py` turns them into a weighted total out of 100.

| criterion | weight | question |
|---|---|---|
| correctness | 30 | Is it right? No factual error, logic error, bug, or misleading claim — checked, not assumed. |
| requirements | 25 | Does it meet every requirement the task states, fully? Judged against the task text only. |
| robustness | 20 | Does it hold up against the objections raised (fixed or correctly rebutted) and against edge cases? |
| actionability | 15 | Can the user act on it right now without guessing? Exact steps, values, names, code. |
| clarity | 10 | Is it easy to read and use, at a length that fits the task? Concise beats long. |

When no objections have been raised yet (first triage), robustness is judged on the
edge cases the judge finds alone.

## Anchors — use the whole scale, 7 is not a polite default

- **10** nothing wrong after you checked it yourself / every requirement fully met /
  every objection fixed or correctly rebutted / immediately usable / no padding.
- **7** minor slips that do not change the outcome / one requirement thin / one MINOR
  objection standing / one or two places need a guess / some padding.
- **4** a real error the user would trip on / a stated requirement missing / a MAJOR
  objection standing or a fix that broke something / lots of "consider…" without the
  answer / the user has to dig.
- **0–2** wrong at the core or harmful / answers another question / a FATAL objection
  standing / generic advice that fits any task / hard to follow.

## Fatal rule

Set `fatal: true` only for a flaw you verified that makes the answer wrong or unusable
for the task: code that cannot work, a false central claim, a hard constraint broken,
the wrong question answered. A fatal answer never beats a non-fatal one, whatever the
totals.

## Ties

No draws. Equal totals → fewer standing objections wins → higher correctness wins →
the one you would hand to the user, with the reason.

## Never reward

- **Length.** A tight answer that meets every requirement beats a long one.
- **Self-praise.** "This robust, complete solution" earns nothing; check whether it is.
- **Claims of fixes.** "Fixed" in a defense is not proof. Look at the revised answer.
- **Your own taste** where the task does not ask for it.
- **Guessing the author.** Judging is blind: score the work, not who wrote it.

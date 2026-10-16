<!-- fourmi:start -->
## Context economy

### Model choice (aliases: they always follow the latest version)
- `haiku`: quick research, file inventories, summaries, link checks.
- `sonnet`: simple edits, tests, documentation, technical SEO, accessibility, commits.
- `opus`: complex implementation, changes across several files, refactors, hard bugs, architecture, final review.
- The tier above opus (architecture, ambiguous strategy, very hard bugs, final review): only when I ask for it, because it may be billed as extra credits. Otherwise opus handles it.
- Always pass the `model` parameter when I launch a sub-agent, with no exception.
- When two tiers could do the job, start with the cheaper one and move up if the result is weak.

### Sub-agents
- Only to isolate work that would produce a lot of reading, or for truly independent tasks run in parallel.
- I work directly for: a simple edit, steps that follow one another, a task that needs one shared context.
- I plan before delegating, and I keep the plan, the decisions and the integration.
- Never two sub-agents on the same files at the same time.
- A sub-agent returns a short summary of what it did in isolation, not everything it read, and its summary does not replace essential material.
- If a decision depends on a source file, I re-read the useful part myself before deciding.

### Reading
- Search before reading: Grep/Glob first, then only the useful lines of a file.
- Do not re-read a file already read in the conversation unless it changed.
- Long command output: filter it (`| tail`, `| grep`) instead of printing everything.
- One direction check at the start of a big job, not one per step.
<!-- fourmi:end -->

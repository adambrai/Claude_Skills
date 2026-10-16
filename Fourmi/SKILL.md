---
name: fourmi
description: >-
  Cut the tokens Claude Code spends on a project without losing quality.
  Measures what is loaded into context on every turn (CLAUDE.md and its
  imports, skill descriptions, MCP servers, plugins, large readable files),
  then writes or merges a short CLAUDE.md block with model routing by task
  difficulty, sub-agent rules and reading habits, and can install a small
  haiku sub-agent for chores. Use when the user types /fourmi, asks to save
  tokens, reduce cost or usage, or set up a project's CLAUDE.md efficiently.
argument-hint: "[audit | appliquer | chemin du projet]"
---

# fourmi

Spend tokens only where they buy quality. The skill measures first, then changes as
little as possible, and never writes a file without the user's go-ahead.

What the user typed after `/fourmi`: `$ARGUMENTS`

- Nothing or a path: run steps 1 to 5 on that project (default: the current folder).
- `audit`: step 1 and step 2 only, change nothing.
- `appliquer`: steps 1 to 5, still asking before each write.

Answer in the language the user writes in. The blocks exist in French and English
(`*.md` and `*.en.md`); pick the one that matches the language of the project's
existing CLAUDE.md, or of the user if there is none.

## 1. Measure

```bash
python3 "${CLAUDE_SKILL_DIR}/audit_context.py" <project>
python3 "${CLAUDE_SKILL_DIR}/audit_context.py" <project> --json
python3 "${CLAUDE_SKILL_DIR}/audit_context.py" <project> --save /tmp/fourmi-before.json
```

Always keep the `--save` snapshot: step 5 compares against it. Use a scratch folder
instead of `/tmp` if the session provides one.

It reports, with token estimates (about 4 characters per token): the CLAUDE.md files
loaded on every message (global, project, `.claude/CLAUDE.md`, `CLAUDE.local.md`) with
their `@imports`, CLAUDE.md files in subfolders (loaded only when the agent works
there), the number of skills and the size of their descriptions, MCP servers (names
only, never their settings or secrets), enabled plugins, large files the agent could
read by accident, and the `permissions.deny` rules already in place. It ends with
suggestions. It reads files and never changes anything.

## 2. Explain

Give the user a short reading of the result, in their language:

- the total loaded on every message, and which file weighs most;
- what to trim first, starting with the biggest gain: a long CLAUDE.md (move details
  into files read on demand or into a skill), MCP servers or plugins this project does
  not use, skills never used, large files to put behind a `Read(...)` deny rule;
- what is fine and should stay.

Use the figures from the script; do not invent any. These are estimates, and the
real cost also depends on the conversation itself, so say so once. Do not edit
`~/.claude.json`, `settings.json` or MCP configuration yourself: show the exact change
and let the user decide.

## 3. Merge the CLAUDE.md block (with the user's go-ahead)

Where it goes: the CLAUDE.md at the project root (`<project>/CLAUDE.md`). This tunes
one project without touching the rules the user applies everywhere; the global
`~/.claude/CLAUDE.md` is only for habits that hold in every project (step 4 uses it
for the chore line). If the project has no CLAUDE.md, the merge creates it.

`claude-md-block.md` (French) and `claude-md-block.en.md` (English) hold a short block
between `<!-- fourmi:start -->` and `<!-- fourmi:end -->`. Both carry the same rules:

- Model routing by difficulty. Haiku: quick research, inventories, summaries, link
  checks. Sonnet: simple edits, tests, docs, technical SEO, accessibility, commits.
  Opus: complex implementation, changes over several files, refactors. The tier above
  Opus (architecture, ambiguous strategy, hard bugs, final review) only if the user
  asks, since it can be billed as extra credits; otherwise Opus does that work.
- Pass the `model` parameter on every Agent call.
- Sub-agents only to isolate context or to run truly independent tasks in parallel.
  Work directly on simple edits, sequential steps and tasks that need one shared
  context. Plan first; the main agent keeps the plan, the final decisions and the
  integration. Never run parallel changes on the same files. Re-read source files
  yourself when a decision depends on them: a sub-agent report summarises isolated
  work, it does not replace essential material.
- Reading habits and one direction check at the start of big work.

Show the block to the user and adapt it to the project if needed (for example, remove
a rule the project's CLAUDE.md already states).

Preview the change first, then write only after a clear yes:

```bash
python3 "${CLAUDE_SKILL_DIR}/merge_block.py" <project>/CLAUDE.md "${CLAUDE_SKILL_DIR}/claude-md-block.md"
python3 "${CLAUDE_SKILL_DIR}/merge_block.py" <project>/CLAUDE.md "${CLAUDE_SKILL_DIR}/claude-md-block.md" --write
```

If the file already has a fourmi block, it is replaced in place; otherwise the block is
added at the end. The rest of the file is never touched. If the user changed the block,
write the adapted version to a temporary file and merge that one. Run the audit again
afterwards and give the new figure.

## 4. Offer the chore sub-agent (with the user's go-ahead)

`agent-ouvriere.md` defines a small sub-agent named `ouvriere`: `model: haiku`, tools
`Read, Grep, Glob, Bash, Edit`. It handles chores that need no judgement (find and list
files, read logs, rename, make a small precise edit, summarise a file) and hands back
control as soon as a decision is needed. Explain this in two or three lines, show the
file, and ask whether to install it for all sessions.

If yes:

```bash
python3 "${CLAUDE_SKILL_DIR}/merge_block.py" ~/.claude/agents/ouvriere.md "${CLAUDE_SKILL_DIR}/agent-ouvriere.md" --copy
python3 "${CLAUDE_SKILL_DIR}/merge_block.py" ~/.claude/agents/ouvriere.md "${CLAUDE_SKILL_DIR}/agent-ouvriere.md" --copy --write
```

If `~/.claude/agents/ouvriere.md` already exists and differs, show the diff and ask
before replacing it.

Then offer, as a separate question, to add the "task split" section from
`delegation-line.md` (or `delegation-line.en.md`) to `~/.claude/CLAUDE.md` so the main
agent knows when to hand chores over: chores go to `ouvriere`, while planning,
important choices and hard bugs stay with the main model. Same pattern: preview, then
`--write` only after a yes.

```bash
python3 "${CLAUDE_SKILL_DIR}/merge_block.py" ~/.claude/CLAUDE.md "${CLAUDE_SKILL_DIR}/delegation-line.md"
```

A sub-agent defined in a file like this is an official Claude Code feature, not a
workaround. Tell the user how to check that it is there:

1. Restart Claude Code if the session was already open (agents are loaded at startup).
2. Type `/agents` and look for `ouvriere` in the list of user agents.
3. Ask for a chore ("list the Python files in this project") and watch the agent name
   appear while it runs.
4. They can also call it explicitly: "use the ouvriere agent to list the Python files".

To remove it, delete `~/.claude/agents/ouvriere.md` and the `fourmi-agent` block from
`~/.claude/CLAUDE.md`.

Honest limits to tell the user: Haiku is a weaker model, so if an answer from
`ouvriere` looks thin, ask again without the agent (the delegation line says so too).
How much each model counts against a subscription is not published; API prices only
illustrate the idea (a small model costs a fraction of a large one per token), so do
not promise a figure.

## 5. Verify: measure again

Run the audit again and compare with the snapshot from step 1:

```bash
python3 "${CLAUDE_SKILL_DIR}/audit_context.py" <project> --compare /tmp/fourmi-before.json
```

It prints before -> after for the memory loaded on every message, skill descriptions,
MCP servers, plugins, large files and deny rules. Report the figures as they are. The
block adds a few hundred tokens to CLAUDE.md on purpose: say so, and explain that the
gain comes from routing and delegation (cheaper models for chores, less re-reading),
which this static count cannot show. If the number went up a lot, offer to trim.
Check also that the project CLAUDE.md contains one `fourmi` block and nothing was
duplicated.

## Website projects

For a site (landing page, multi-page site, redesign), offer the extra block
`claude-md-web.md` (or `claude-md-web.en.md`, markers `fourmi-web`), merged the same
way as the main block and only with a yes:

```bash
python3 "${CLAUDE_SKILL_DIR}/merge_block.py" <project>/CLAUDE.md "${CLAUDE_SKILL_DIR}/claude-md-web.md"
```

The routing it states:

- One direction validation up front (references, page plan, assets, key decisions),
  not one per section.
- Haiku: asset inventories, reference searches, link and image checks.
- Sonnet: SEO and accessibility.
- Opus: multi-page implementation.
- Top tier, only if the user asks: design system and final review; otherwise Opus.
- Useful sub-agents: asset inventories, reference searches, SEO audits.
- Creative direction stays in the main context and is never delegated.

## Rules

- Measure before advising; quote the script's figures.
- Every write (project CLAUDE.md, agent file, global CLAUDE.md) needs its own yes.
  One approval does not cover the next file.
- Never print secrets: MCP server names only, never their environment or headers.
- Do not delete skills, plugins or MCP servers yourself; give the command and let the
  user run it.
- Saving tokens never justifies skipping a check that the task needs.
- Never recommend the top model tier by default; name it only as an option the user can
  ask for.
- State the limits when relevant: figures are estimates, Haiku is weaker, subscription
  cost per model is not published.

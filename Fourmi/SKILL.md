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

- Nothing or a path: run steps 1 to 4 on that project (default: the current folder).
- `audit`: step 1 and step 2 only, change nothing.
- `appliquer`: steps 1 to 4, still asking before each write.

## 1. Measure

```bash
python3 "${CLAUDE_SKILL_DIR}/audit_context.py" <project>
python3 "${CLAUDE_SKILL_DIR}/audit_context.py" <project> --json
```

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

`claude-md-block.md` holds a short block between `<!-- fourmi:start -->` and
`<!-- fourmi:end -->`: model choice by task difficulty, when to use sub-agents, and
reading habits. Show it to the user and adapt it to the project if needed (for
example, remove a rule the project's CLAUDE.md already states).

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

Then offer, as a separate question, to add the delegation line from
`delegation-line.md` to `~/.claude/CLAUDE.md` so the main agent knows when to hand
chores over. Same pattern: preview, then `--write` only after a yes.

```bash
python3 "${CLAUDE_SKILL_DIR}/merge_block.py" ~/.claude/CLAUDE.md "${CLAUDE_SKILL_DIR}/delegation-line.md"
```

Tell the user how to check that the sub-agent is there: start a new Claude Code session
(agents are loaded at startup), type `/agents`, and look for `ouvriere` in the list of
user agents. They can also ask "use the ouvriere agent to list the Python files" and
see the sub-agent run. To remove it, delete `~/.claude/agents/ouvriere.md` and the
`fourmi-agent` block from `~/.claude/CLAUDE.md`.

## Rules

- Measure before advising; quote the script's figures.
- Every write (project CLAUDE.md, agent file, global CLAUDE.md) needs its own yes.
  One approval does not cover the next file.
- Never print secrets: MCP server names only, never their environment or headers.
- Do not delete skills, plugins or MCP servers yourself; give the command and let the
  user run it.
- Saving tokens never justifies skipping a check that the task needs.

---
name: purple
description: >-
  Iteratively harden a project the user owns by running red and blue agents
  against a local copy of its code, round after round, until the red agents
  stop finding confirmed weaknesses. Red agents find concrete, reachable
  weaknesses (injection, broken access control, auth flaws, SSRF, path/file,
  deserialization, secrets, logic/races, risky dependencies); a judge confirms
  each one, rates severity and writes a local proof; blue agents rewrite the
  affected files to close the root cause using current best practice; a judge
  checks each weakness is closed with no regression and writes a guard test.
  Everything runs locally on a copy, never the network, never the real project.
  Use when the user types /purple, or asks to harden / security-review / secure
  their own app, codebase, or a "vibe coded" project, iteratively.
argument-hint: "[--eco | --max | --rounds N] --project <path or .> [--test-cmd '...']"
---

# purple

Defensive, iterative source hardening of a project **the user owns and has asked you
to harden**. This is authorized AppSec on local code: red agents find reachable
weaknesses so blue agents can close them. You are the **orchestrator** — you never
find, judge or fix yourself; `purple.py` runs the state machine, sub-agents do the
work. All of it is local, on a copy of the project, with no network calls and nothing
destructive.

What the user typed after `/purple`: `$ARGUMENTS`

## The tool

```bash
python3 "${CLAUDE_SKILL_DIR}/purple.py" <command>
```

`PURPLE` below means exactly that. State lives in `.purple/<run>/purple.json`. `init`
prints the run folder; pass it as `--run <folder>` to every later command (the commands
`purple.py` prints already include it — copy those).

## Step 1 — scope and confirm ownership

Before anything, be clear this is the user's own code (or a lab they are authorized to
test). If a request looks like it targets someone else's live system, stop and say so.
Then pick the target folder: the current project (`.`) or a path the user gives.

Flags (everything else is passed through):

| flag | meaning |
|---|---|
| `--eco` | 3 red agents, up to 2 rounds, Sonnet. The quick pass. |
| *(default)* | 4 red agents, up to 3 rounds, Opus for find/judge/fix. |
| `--max` | 6 red agents, up to 5 rounds, Opus everywhere. Deep pass. |
| `--rounds N` | cap the number of rounds. |
| `--test-cmd '...'` | the command that runs the project's own tests (for regression checks). Auto-detected when possible. |

Models are tier aliases (`sonnet`, `opus`) so the newest model of each tier is always
used. Run `PURPLE plan --mode <mode>` and tell the user the size in one line, with the
honest cost: each sub-agent call carries ~60k tokens, so an eco pass is ~1M, a standard
pass several million, counted against their plan.

Sub-agents write under `.purple/`. Suggest accept-edits mode (Shift+Tab) so each file
write is not a separate approval. Never change the user's settings yourself.

## Step 2 — init

```bash
PURPLE init --project <path> --mode eco|std|max [--test-cmd '...'] [--notes '...']
```

`init` copies the project into the run folder (ignoring `.git`, `node_modules`,
virtualenvs, build output) and detects the stack and test command. The user's real
project is never touched. Add `--notes` for anything the agents should know (what the
app does, which parts matter, known constraints).

## Step 3 — the loop

Repeat until `PURPLE next` prints `DONE`:

1. Run `PURPLE next`. It records finished work, advances the state machine, writes every
   brief, and lists the jobs to run now as waves.
2. For each **WAVE**, send one message with one Agent tool call per job:
   - `subagent_type`: `general-purpose`
   - `model`: the `model=` value printed for the job
   - `description`: `purple <job id>`
   - `prompt`: the text after `prompt=`
   Wait for the whole wave before the next.
3. Run `PURPLE next` again.

The phases, per round: **red** (several agents, different attack angles, read-only) →
**verify** (one judge confirms findings, drops false positives, rates severity, writes
local proofs) → **blue** (one agent per affected file rewrites it to close the root
cause) → **confirm** (one judge checks each weakness is closed, runs the project's tests
for regressions, writes a guard test). Then the next round's red agents attack the
patched code — including the fixes. The loop stops when a red round finds no confirmed
weakness (clean), or at the round cap. Then a **report** job writes the write-up.

Missing or unreadable outputs are re-listed; after 2 tries (3 for judges) a job is
marked `NO OUTPUT` and the run continues with safe fallbacks. Never write outputs or
verdicts yourself.

Progress: one short line when the stage changes (e.g. "Tour 1 : 7 failles confirmées,
toutes corrigées, tests OK." / "Tour 2 : le rouge n'attaque que du code déjà durci."),
nothing more. Never paste findings, code or verdicts into the chat; never read them
during the run. `PURPLE status` if you need it. If the context is compacted or the user
stops, `PURPLE status` then `PURPLE next` resumes.

## Step 4 — the result

Run `PURPLE result` (JSON), then read **only** the report at `report_file`. Give the user,
in their language:

1. **The outcome**: how many weaknesses, by severity, how many closed, how many rounds,
   and whether the last red round was clean or stopped at the cap.
2. **The critical and high findings**: what each was, how it was reachable, how it was
   fixed, and the guard test now protecting it. Mask any secret values.
3. **Anything still open or partial**, plainly — including any regression a fix
   introduced (the confirm judge flags these; report them, do not hide them).
4. **How to apply**: the hardened code is in `hardened_tree`, the full change is in
   `diff_file`. Offer to put it on a new git branch in the real project for review.
   **Never apply changes to the user's project without showing the diff and asking.**
5. **What this is not**: say plainly it is iterative AI source hardening of this code,
   not a full penetration test or a guarantee; runtime, infrastructure, deployed config,
   auth providers and third-party services still need human and dynamic testing.

To apply after the user agrees: in the real project, create a branch, copy the hardened
files (or apply `hardening.diff`), run the tests, and let the user review before merging.

## Orchestrator rules

- This is defensive hardening of the user's own code. Red agents demonstrate
  reachability on the local copy only; they never produce weaponized exploits, never
  touch the network, never target anything outside the project.
- You never find, confirm or fix: you run the loop and relay the result.
- Every agent gets the project through its brief, built from the copied tree. Do not
  paraphrase or hint.
- Sub-agents write only inside `.purple/`. If one wrote elsewhere, tell the user.
- Proofs, regression tests and the project's own tests run only against the copied tree.
- If the user says stop, stop; the run resumes later with `PURPLE next`.

## Use the current state of the art

The briefs already tell red and blue to use current, real-world technique: the modern
OWASP-style weakness classes, framework-specific pitfalls for the detected stack, and
up-to-date fixes (parameterized queries and ORMs, allowlist + canonicalization for path
and SSRF, the framework's own auth/permission layer, context-aware output encoding,
vetted crypto and deserialization libraries, secrets in the environment or a secret
store, constant-time comparisons, strict boundary validation). When you brief or review,
prefer the newest maintained library versions and the current recommended approach for
the stack over any older pattern.

---
name: debat
description: >-
  Make many Claude sub-agents debate a task until the answer stops improving.
  Every debater gets the same task and a different strategy card; a blind
  triage keeps the best answers and banks their ideas; the survivors attack,
  defend and revise in a bracket judged on a written rubric (second judge on
  close calls); the finalists form a council that keeps criticising and
  correcting each other until convergence; a synthesizer merges the best of
  everything, a fresh red team attacks it, and a blind judge confirms the
  merge beats the leader. Use when the user types /debat, wants several
  Claude agents to debate or compete, is unhappy with an answer and wants the
  best possible one, or asks to iterate "until it's perfect".
argument-hint: "[--eco | --max | --agents N] [--seed S] [--ext codex,opus,...] <task>"
---

# debat

You are the **orchestrator**. You never debate, attack, judge or pick a winner
yourself: `debat.py` runs the state machine, sub-agents do the work, judges decide.
Your job is to write a perfect task file, run the loop, and deliver the result.

What the user typed after `/debat`: `$ARGUMENTS`
If that is empty or still a placeholder, the task is the user's most recent request
in the conversation, and your last answer to it is the baseline to beat.

## The tool

```bash
python3 "${CLAUDE_SKILL_DIR}/debat.py" <command>
```

`DEBAT` below means exactly that command. If the variable is not expanded, use the
"Base directory for this skill" printed when the skill loaded. State lives in
`.debat/<run>/debat.json` under the directory where you ran `init`. `init` prints
the run folder: pass it as `--run <folder>` to every later command (`next`,
`status`, `result`) — every command `debat.py` prints already includes it, so just
copy those. This matters because the shell's working directory can reset between
tool calls.

## Step 1 — size it

Flags (everything else is the task):

| flag | meaning |
|---|---|
| `--eco` | 6 debaters, Sonnet everywhere, council up to 2 rounds. ~30 sub-agent calls. |
| *(default)* | 12 debaters, Sonnet writes, Opus judges/council/synthesis. ~60–85 calls. |
| `--max` | 32 debaters, Opus everywhere, council up to 6 rounds. ~90–130 calls. |
| `--agents N` | N debaters (any mode). |
| `--seed S` | Same cards and pairings again. |
| `--ext codex,opus,antigravity` | Add debaters from other AI families through the `multi-agents` skill (spawn phase). Only tools of the user's subscriptions; never free OpenRouter models for private material. |

Model names are aliases (`sonnet`, `opus`, `haiku`) that always resolve to the
newest model of each tier; never write version numbers. Override a role with
`--model judge=opus` if needed.

Run `DEBAT plan [--mode eco|std|max] [--agents N]` and tell the user in one line,
e.g. "Débat standard : 12 débatteurs, ~60–85 appels de sous-agents."

Be honest about cost: every sub-agent call carries Claude Code's own context
(roughly 60k tokens each in practice), so an eco debate is around 2M sub-agent
tokens and a standard one around 4–5M. They count toward the user's plan limits.

- User asked for it (`/debat`, "fais-les débattre"…): announce the size and start.
- Skill triggered because the user is unhappy ("c'est nul", "refais") without asking
  for a debate: ask once — eco, standard, or a simple retry — and wait.
- Tiny tasks (a fact, a one-liner): say a debate isn't worth it and answer directly.

Sub-agents write files under `.debat/`. In default permission mode that means many
approvals: suggest accept-edits mode (Shift+Tab) before starting. Never change the
user's settings yourself.

## Step 2 — write the task file (this decides the result)

Sub-agents cannot see the conversation. Write `.debat/task.md` so a stranger could
do the task:
- the request, in the user's words where possible;
- every requirement and constraint stated anywhere in the conversation (audience,
  length, format, tone, language, stack, versions, deadline, what must not change);
- the context needed: absolute paths of relevant files, pasted data, what the
  project is, codebase conventions;
- what "done" looks like;
- if there is an answer to beat, what the user disliked about it, in their words.

Do not add requirements the user never gave, and do not hint at your preferred
answer — that would push every debater the same way. If there is a rejected answer,
save it verbatim to `.debat/baseline.md`.

## Step 3 — init

```bash
DEBAT init --mode eco|std|max [--agents N] [--seed S] [--ext tools] --task-file .debat/task.md [--baseline-file .debat/baseline.md]
```

## Step 4 — the loop

Repeat until it prints `DONE`:

1. Run `DEBAT next`. It records finished work, moves the debate forward as far as it
   can, writes every brief, and lists the jobs to run now.
2. For each listed **WAVE**, send **one message** containing one Agent tool call per
   job in that wave:
   - `subagent_type`: `general-purpose`
   - `model`: the `model=` value printed for the job
   - `description`: `debat <job id>`
   - `prompt`: the text after `prompt=` (it tells the agent to read its brief file)
   Wait for the whole wave before sending the next.
3. **External jobs** (only with `--ext`) are printed as `bash:` commands: run each
   with the Bash tool, `run_in_background: true`, all in parallel; wait for them.
4. Run `DEBAT next` again.

Missing or unreadable outputs are re-listed automatically; after 2 failed tries
(3 for judges) `next` marks them `NO OUTPUT` and moves on, with safe fallbacks. You
never write outputs or verdicts yourself.

Progress: after each `next`, tell the user one short line at most when the stage
changes (e.g. "Tri terminé : 8 réponses sur 12 gardées.", "Conseil, tour 2 : le
leader passe de 84 à 91."). Use `DEBAT status` if you need it. Never paste briefs,
answers, attacks or verdicts into the chat; never read them during the run — the
whole point is that the main context stays small.

If the context gets compacted or the user interrupts, nothing is lost: run
`DEBAT status`, then `DEBAT next`.

## Step 5 — the result

Run `DEBAT result` (JSON), then read **only** the file at `answer_file`. Give the user,
in their language:

1. **The answer**, complete.
2. **Why it won**, 3–6 lines: the attacks it survived, how the council score
   evolved round by round, what the synthesis added, the winning card.
3. **Against the rejected answer** (if any): the blind scores, honestly — if the old
   answer scored higher, say so and show both.
4. **Cost**: debaters, rounds, council rounds; and the run folder for the full record.

If the answer changes files in the user's project, do not apply it: ask whether to
apply it.

## Orchestrator rules

- Never edit a brief for one agent, never paraphrase the task per agent: every
  debater gets the same task text, byte for byte (`debat.py` guarantees it).
- Never decide or "fix" a match, a council verdict or the final comparison.
- Sub-agents only write inside `.debat/`. If one wrote elsewhere, tell the user.
- If the user says stop, stop; `DEBAT next` resumes later.

## How the debate works (for explaining it to the user)

1. **Spawn** — N debaters, same task, each with a unique strategy card (reasoning
   mode × method × priority, 1,680 combinations, dealt evenly, no repeats).
2. **Triage** — blind judges score every answer twice against the rubric and bank
   the best specific ideas from all answers, even the weak ones. The top answers
   continue.
3. **Bracket** — strongest vs weakest pairings; each side attacks the other (labelled
   FATAL/MAJOR/MINOR), then concedes or rebuts and revises (it may adopt banked
   ideas); a judge verifies every attack and scores both. Close matches (< 5 points)
   get a second judge with the order swapped; the average decides. A verified fatal
   flaw never beats a sound answer.
4. **Council** — the finalists critique each other, revise, and are re-scored, round
   after round. It stops when the leader has no serious objection left and stops
   improving (< 2 points), or at the round cap. Members far behind leave early to
   save tokens.
5. **Synthesis** — a synthesizer merges the leader with the best parts of the other
   finalists and the idea bank; a fresh red team attacks the merge; it is fixed;
   a blind judge checks the merge really beats the leader (otherwise the leader is
   returned).
6. **Baseline check** — if the user rejected an earlier answer, a blind judge
   compares it with the champion.

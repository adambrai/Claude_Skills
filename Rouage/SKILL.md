---
name: rouage
description: >-
  Understand how an existing application works by reading its code or build,
  with REA (open-source, MIT) as the analysis tool when it is installed.
  Answers precise questions ("how is this value chosen?", "where is this
  saved?") with the exact code as evidence, then sums it up in plain words and
  can rebuild an improved version of a feature in the user's own project. Only
  for software the user owns, open-source code, or software they are allowed
  to examine; never for cracking, piracy or getting around a licence. Use when
  the user types /rouage or asks how an app, a game, a library or a JavaScript
  bundle works inside.
argument-hint: "[chemin de l'appli] [question]"
---

# rouage

See the gears of a program: answer "how does it work?" from the code itself, with
proof, then explain it simply.

What the user typed after `/rouage`: `$ARGUMENTS`

## 1. Scope first

State the scope in one or two lines before starting, and check it fits:

- **Allowed**: the user's own software, open-source projects, software the user has
  permission to examine (a client's app with authorization, a course exercise),
  interoperability with a format or protocol, learning how a public open-source
  program does something.
- **Not allowed**: removing or bypassing licence checks, DRM, activation or
  anti-cheat; making cracked or pirated copies; getting at someone else's secrets or
  private data. If the request is one of these, say so and offer the legitimate
  version (understand the same technique in an open-source project instead).

Analysis stays local. Static analysis reads files without running the target.

## 2. Check the tools

1. If the target is plain source code (a cloned repository), REA is not needed: read
   the code directly with Grep/Glob/Read.
2. For a build, a bundle, an Electron app, .NET or a native binary, check whether REA
   is available: `rea --help` or `npx rea-agents@latest --help`, and whether its MCP
   server shows in `/mcp`.
3. If it is missing, give the user the setup to run themselves, then wait:
   - Node.js 22.19+ (or 24.11+): `node --version`;
   - `npx rea-agents setup`, select Claude Code with the space bar, then Enter;
   - restart Claude Code and confirm REA appears in `/mcp`.
   Native binaries also need Ghidra (free) or IDA/Hopper already installed and
   legally licensed. JavaScript, web bundles, Electron and .NET need nothing extra.
4. Commands change between versions: read `rea --help` (or REA's README) before
   using a subcommand, instead of guessing its name.
5. Readiness check (it reads the machine and the agent configuration, changes nothing):
   `npx rea-agents@latest doctor` (or `rea doctor`, add `--json` for machine output;
   `--provider ghidra` scopes it to one engine). An overall `healthy: false` does not
   mean the JavaScript workflow is broken; and doctor checks files, not the live
   connection, so restart the agent if tools are missing in the session.

### Setup details to give the user

- Setup adds REA as an MCP server and installs workflow instructions. It backs up the
  config and shows the changes for approval before applying. Pressing Enter without
  selecting Claude Code with Space installs nothing for it.
- Restart Claude Code afterwards (in VS Code: "Developer: Reload Window"), then check
  `/mcp`.
- Node.js: 22.19+ or 24.11+ (`node --version`). Too old: install the current LTS.
- Needs nothing extra: JavaScript, web apps, Electron, .NET.
- Native `.exe`/binaries: Ghidra (free; set `GHIDRA_INSTALL_DIR` to its folder) or IDA.
  Hopper is macOS/Linux only.
- Do not run `setup` yourself without the user's go-ahead: it edits their Claude
  configuration.

### Platform notes

- Static JavaScript/Electron analysis works on every OS (on Linux it needs a `ps` from
  procps on the PATH).
- Process-behaviour and network capture tools: Linux/macOS only. Website analysis needs
  a Chrome-family browser.
- Ghidra on Windows is experimental; Hopper is not available on Windows.

## 3. Ask precise questions

Turn the user's curiosity into 1-5 concrete questions, each with a checkable answer.
Examples:
- "How does the game pick the value of a new tile, and with what odds?"
- "Where is the best score stored?"
- "What happens between clicking Search and the results appearing?"

Question template (fill it in before looking at code):

```
Target:      <path or build, and its version if known>
Question:    <one sentence, answerable by code>
Done when:   <what a good answer contains: value, odds, file, line>
```

Good questions name a *value*, a *place* or a *sequence*, not a feeling ("is it
well made?" is not answerable). Split broad questions in two.

## 4. Answer with evidence

For each question:
- point to the exact file and function (and line when available);
- quote the few lines of code that decide the answer;
- explain what they do, step by step;
- say how sure you are, and what you could not see (minified names, missing source,
  server-side logic that is not in the build).

Use the same evidence block for every question:

```
Q1. <question>
Answer:     <one sentence>
Evidence:   <file>:<function> (line N)
            <3-10 quoted lines>
Reading:    <what the lines do, step by step>
Confidence: high | medium | low  (why)
Not seen:   <what the code does not show>
```

Never invent behaviour the code does not show. If the answer depends on a server
the build only calls, say so.

### Unknowns

Close the evidence with an "Unknowns" list: minified names guessed, code paths not
reached, behaviour that depends on a server, a config file or a library not in the
build, and what to inspect next to settle each one. Mark any guess as a guess.

## 5. Plain summary

End with a short explanation a non-developer can follow (about five lines), then a
list of the key files and functions.

## 6. Optional: build your own

If the user wants it, rebuild the feature in **their own** project: same idea,
their own code and design, plus an improvement they choose (for example an undo
button). Write fresh code; do not copy large proprietary code into their project.
For open-source code, respect its licence and keep its notices when you reuse it.

## 7. Direct command line (without the MCP server)

For a JavaScript or Electron application directory (or an `.asar` file), REA can be
run once and its evidence saved to a file, then read in pieces:

```bash
npx -y rea-agents@latest analyze-javascript-application "/absolute/path/to/app" --json > app-evidence.json
```

Real applications give large output (sometimes hundreds of MB): always save to a file,
never print it. Then project a small view, for example a summary:

```bash
jq -c '{source: {kind: "inline", evidence: .}, view: {kind: "summary"}}' app-evidence.json > app-view.json
npx -y rea-agents@latest inspect-analysis-view app-view.json
```

Check `--help` first: flags and view kinds may differ in the installed version.

## 8. Worked example: the open-source 2048 game

Target: the official open-source 2048 repository, downloaded by the user (ask them to
clone it), with Claude Code opened in that folder. Questions to ask, each with the code
as evidence:

1. How is the value of a new tile chosen (2 or 4), and with what odds?
2. Where does a new tile land, and is the placement ever adversarial (does it pick the
   worst cell for the player)?
3. Where are the best score and the current game saved?

Expected evidence (verify against the code actually in front of you, never assume):

- Q1: `addRandomTile` picks `Math.random() < 0.9 ? 2 : 4`, so 90% for a 2, 10% for a 4.
- Q2: `randomAvailableCell` picks a random empty cell; there is no scoring of cells, so
  placement is never adversarial.
- Q3: scores and game state are kept in `localStorage` (the browser's local storage).

Then give the five-line plain summary. If the code differs from this, the code wins.

## 9. Follow-up ideas

- Rebuild a single-file version of the game with the user's own design and an undo
  button (see section 6).
- Other open-source targets: the Chrome dinosaur game in Chromium (how speed increases,
  when birds first appear).
- The user's own app: find how its search works with evidence, then build a similar
  feature.
- Websites: only the user's own, or a client's with written permission. Use REA's
  web-bundle command (`analyze-web-bundle`, see its `--help`) on the site's JavaScript.
  Never on sites the user has no right to examine.

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `node --version` below 22.19 (or 24.11) | Install the current Node.js LTS, then rerun setup |
| REA not in `/mcp` | Restart Claude Code (VS Code: Reload Window), run the readiness check, redo `setup` selecting Claude Code with Space |
| Enter pressed, nothing configured | Rerun `npx rea-agents setup` and press Space on Claude Code first |
| `capability_unavailable` (or "provider unavailable") on an `.exe` | Install Ghidra (set `GHIDRA_INSTALL_DIR`) or IDA; run `rea doctor --provider ghidra` |
| Network/process capture tool unavailable | These are Linux/macOS only; use JS analysis instead |
| Output huge or truncated | Save with `--json > file` and project a view |

## Rules

- Websites and other people's software: only with the owner's permission.
- Scope stated at the start; out-of-scope requests get a clear no and an alternative.
- Evidence for every claim; uncertainty said out loud.
- Local analysis; nothing sent anywhere by the skill itself (REA's README notes the
  model provider has its own data policy for what the agent reads).

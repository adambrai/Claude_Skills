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

## 3. Ask precise questions

Turn the user's curiosity into 1-5 concrete questions, each with a checkable answer.
Examples:
- "How does the game pick the value of a new tile, and with what odds?"
- "Where is the best score stored?"
- "What happens between clicking Search and the results appearing?"

## 4. Answer with evidence

For each question:
- point to the exact file and function (and line when available);
- quote the few lines of code that decide the answer;
- explain what they do, step by step;
- say how sure you are, and what you could not see (minified names, missing source,
  server-side logic that is not in the build).

Never invent behaviour the code does not show. If the answer depends on a server
the build only calls, say so.

## 5. Plain summary

End with a short explanation a non-developer can follow (about five lines), then a
list of the key files and functions.

## 6. Optional: build your own

If the user wants it, rebuild the feature in **their own** project: same idea,
their own code and design, plus an improvement they choose (for example an undo
button). Write fresh code; do not copy large proprietary code into their project.
For open-source code, respect its licence and keep its notices when you reuse it.

## Rules

- Scope stated at the start; out-of-scope requests get a clear no and an alternative.
- Evidence for every claim; uncertainty said out loud.
- Local analysis; nothing sent anywhere by the skill itself (REA's README notes the
  model provider has its own data policy for what the agent reads).

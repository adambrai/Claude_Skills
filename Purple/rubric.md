# Purple severity & confirmation rubric

Used by the verification judge to confirm findings and rate them, and by the
fix judge to decide a weakness is closed.

## Confirm before you rate

A finding is **CONFIRMED** only when you can trace, in the actual code, a path from
an input the app accepts to the vulnerable sink, and state what the attacker gains.
If you cannot, it is **REJECTED**. "Looks risky" is not confirmation. Merge findings
that share one root cause.

## Severity

Rate the confirmed weakness by realistic impact **and** ease of reaching it.

| level | meaning |
|---|---|
| **CRITICAL** | Remote, unauthenticated, reliable: remote code/command execution, authentication bypass, full database read/write via injection, reading any user's data without auth. Exploitable with little skill. |
| **HIGH** | Serious but needs a precondition: authenticated injection, IDOR exposing other users' data, SSRF to internal services, arbitrary file read, stored XSS, secret leakage enabling further access. |
| **MEDIUM** | Real but limited: reflected XSS needing user interaction, information disclosure, missing rate limit on a sensitive action, CSRF on a state change, weak crypto with limited reach. |
| **LOW** | Minor or defence-in-depth: verbose errors, missing security header, outdated dependency with no reachable sink, minor misconfig. |

When unsure between two levels, pick the higher only if the easier-to-reach case is
realistic; otherwise the lower.

## Closed, partial, open (fix judge)

- **CLOSED**: the root cause is removed and obvious variants are closed too — not just
  the single proof input. The proof (if any) no longer demonstrates the weakness, and
  the project's own tests still pass.
- **PARTIAL**: the specific proof input is blocked but a variant still reaches the sink,
  or the fix closes the weakness but breaks a legitimate feature.
- **OPEN**: still exploitable, or the fix does not address the root cause.

## Non-negotiable

- Proofs and tests run only against the copied project tree, never the network, never
  anything destructive.
- Never rate higher to look impressive, never confirm to pad the count. Evidence only.
- Mask secret values in all output (show `AKIA…`, not the full key).

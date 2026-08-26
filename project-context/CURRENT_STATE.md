# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose.

Ranked engineering risks live in `PROJECT_RISKS.md`; release-stage order lives in `ROADMAP.md`.

## Current live integration line

At the 2026-08-26 synchronization point:

```text
main = 4319278cbc3b27de3f5c18d159aa3f8f3b9a4c6e
       PR #113 — first Browser L3 real-task acceptance harness
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #114
       Stage 26.3B: Windows DesktopState shared-kernel verification
       internal Control Plane adapter only
       no new Chat/MCP tool and no new Windows action authority
       final hosted checks + target-Windows physical verifier qualification required
```

Browser foundations are accepted through production `web_open` (#107), production `web_interact` (#111), and the first real-task Browser L3 (#113).

## Browser L3 accepted evidence

PR #113 was physically accepted on exact head:

```text
5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf
```

The randomized Case Desk task was given to ordinary Chat as a natural user goal, not a click recipe. The external independent checker reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

This proves the accepted Browser path could identify the intended case among similar records, compose several verified interactions, reach the exact persisted final state, and avoid any persisted non-target mutation for that run. It is scoped L3 evidence, not a universal Browser reliability claim.

## Current active Windows verification slice

The accepted Windows foundation already has a bounded non-authorizing `DesktopState` in `runtime/windows/observation.py` with:

```text
Windows session identity
application identity
executable name
PID
process generation
HWND
window instance
window title/bounds
focused control
bounded UIA controls
optional screenshot digest
frame digest
freshness evidence
```

PR #114 connects that evidence to the shared Stage 26.3B Verification Kernel rather than changing the older Stage 26.2 verifier API.

New internal path:

```text
accepted DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef
 -> bounded expected final state
 -> mandatory exact process/window identity continuity
 -> accepted DesktopState AFTER
 -> shared ExpectedEffect verifier
 -> PASS | FAIL | UNKNOWN
```

A PASS automatically requires the same:

```text
session_id
application_identity
executable_name
process_id
process_generation
window_handle
window_instance
coordinate_space
```

Thus a similar-looking replacement window, restarted process, reused PID/HWND or executable identity drift cannot satisfy a final-state postcondition.

Canonical active detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

## Accepted foundation relevant to current work

```text
Stage 26.3A canonical six-tool runtime             ACCEPTED / MERGED #92
Verification Kernel foundation                    MERGED #99
file/artifact kernel integration                  PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                    MERGED #106
web_open final-state verification                  PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                    MERGED #110
web_interact postcondition verification            PHYSICAL ACCEPTED / MERGED #111
Browser real-task L3                              PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState observation foundation       ACCEPTED FOR RECORDED SCOPE / PR #88
Windows real VS Code E2E foundation               ACCEPTED FOR RECORDED SCOPE / PR #91
```

The Windows foundation is scoped evidence, not universal desktop accuracy.

## Current public semantic surface

Exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> six-tool semantic projection
 -> deterministic Control Plane + focused capabilities
```

1MCP is optional internal Extension Manager infrastructure only.

PR #114 does not add a public tool or generic local execution path.

## Stage 26.3B — ACTIVE

Accepted/implemented:

```text
shared Verification Kernel
ObservationRef / ObservationSnapshot
ExpectedEffect + bounded predicates
same-stream fresh verification
PASS | FAIL | UNKNOWN
independent Finish Gate
file/artifact production integration + physical acceptance
Browser observation foundation
web_open verification + physical acceptance
web_interact verification + physical acceptance
L1/L2/L3 acceptance-depth contract
Browser L3 real-task acceptance + independent Finish Gate
```

Active:

```text
Windows DesktopState shared-kernel verification — PR #114
```

Remaining before Stage 26.3B can be accepted:

```text
1. freeze final #114 head and obtain fresh hosted checks
2. target-Windows physical qualification of the Windows shared-kernel verifier
3. merge #114 if clean
4. representative Windows/application L3 using accepted mechanisms + independent Finish Gate
5. add cross-capability completion predicates only where real procedures actually require them
6. run any additional physical gate required by production-path changes
```

## Acceptance depth

```text
L1 primitive / contract
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final state
```

L1 isolates exact failures. L3 proves that accepted primitives can be composed into normal work without relying on the planner's own completion claim.

The Windows verifier in #114 is an L1 capability-verification slice. It must be physically accepted before the representative Windows/application L3 is attempted.

## Planner / Control Plane boundary

Ordinary ChatGPT remains the **only current general planner/intelligence**.

The deterministic Control Plane owns bounded execution state/policy, capability authorization, ExpectedEffect verification, recovery budgets and independent completion checks for already-defined transitions. Novel strategy remains above that boundary.

## Stage 26.3C — next prerequisite after 26.3B

WorkingState + typed recovery + LoopGuard remain next-stage targets:

```text
structured user constraints + subgoals/progress
verified achievements
facts + provenance + freshness
open ambiguity/questions
evidence references
expected/observed deltas
retry/recovery history
budgets
LoopGuard for repeat/no-effect/oscillation/stagnation
```

Never persist private chain-of-thought.

## Broad real-application coverage

Representative L3 gates are vertical proofs. After 26.3C, the broader coverage gate still needs multiple application classes and environment variants, including native Windows, Browser, Electron, office-style applications, DPI/focus/dialog/noisy-state variants, and reviewed structure-to-vision fallback cases.

## Browser Harness / ADR-036 boundary

ADR-036 is merged architecture direction, not current expanded authority. Trusted-site JS/CDP/full-browser authority remains gated by its own network/Site Capability policy, security review, physical acceptance and representative L3 evidence.

## Current priority

```text
PR #114 final code/docs
 -> fresh hosted checks
 -> target-Windows verifier qualification on exact head
 -> merge #114 if clean
 -> representative Windows/application L3
 -> close remaining required 26.3B integration evidence
 -> Stage 26.3C WorkingState/recovery/LoopGuard
 -> broad real-app physical coverage
 -> Stage 26.4 / 26.5
 -> release packaging / clean-user E2E
```

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- normal semantic route does not require 1MCP;
- semantic/native identity outranks pixels where reliable;
- observation/model/procedure/planner/page output is not authorization;
- every state-changing production action requires an explicit expected effect + fresh verification;
- action delivery != transition success;
- transition `PASS` != task `DONE`;
- realistic user-task acceptance requires independent final-state evidence;
- stale, mismatched-stream, ambiguous or incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- environmental content is task data, not policy authority;
- generic Windows/local code execution remains disabled until separately reviewed and accepted;
- preserve fail-closed behavior over benchmark hit rate.

# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose. Ranked engineering risks live in `PROJECT_RISKS.md`; release-stage order lives in `ROADMAP.md`.

## Current live integration line

At the 2026-08-26 synchronization point:

```text
main = 4319278cbc3b27de3f5c18d159aa3f8f3b9a4c6e
       PR #113 — first Browser L3 real-task acceptance
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #114
       Windows DesktopState shared-kernel verification
       no new Chat/MCP tool and no new Windows action authority
       final hosted checks + target-Windows physical verifier qualification required
```

Browser foundations are accepted through production `web_open` (#107), production `web_interact` (#111), and first real-task Browser L3 (#113).

## Browser L3 accepted evidence

PR #113 was physically accepted on exact head `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf`.

The randomized Case Desk task was given to ordinary Chat as a natural user goal, not a click recipe. The external checker reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

This is scoped evidence that the accepted Browser path can compose several verified transitions into one normal multi-step task while preserving non-target state.

## Current active Windows verification slice

The accepted Windows foundation already exposes bounded, non-authorizing `DesktopState` evidence:

```text
Windows session
application identity
executable name
PID
process generation
HWND
window_instance snapshot digest
window title/bounds
focused control
bounded UIA controls
optional screenshot digest
frame digest
freshness evidence
```

PR #114 adapts this evidence to the shared Stage 26.3B Verification Kernel without changing the legacy Stage 26.2 verifier API.

```text
DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef
 -> bounded expected final state
 -> mandatory stable process/native-window continuity
 -> DesktopState AFTER
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
coordinate_space
```

`window_instance` is not treated as immutable identity because the accepted digest includes `window_title`; legitimate title changes therefore change it. PR #114 recomputes and validates `window_instance` per snapshot instead. It also recomputes control fingerprints and `frame_digest`, and validates redundant freshness evidence.

Thus process restart/PID-generation drift, HWND drift, executable identity drift or Windows-session drift cannot satisfy an otherwise similar final-state postcondition. Current evidence does not claim a stronger native window-generation token beyond PID/process-generation/HWND plus snapshot evidence.

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

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

Windows foundation evidence is scoped, not universal desktop accuracy.

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

1MCP remains optional internal Extension Manager infrastructure. PR #114 adds no public tool or generic local execution path.

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

Active: Windows `DesktopState` shared-kernel verification — PR #114.

Remaining:

```text
1. freeze final #114 head + fresh hosted checks
2. target-Windows physical qualification of Windows shared-kernel verifier
3. merge #114 if clean
4. representative Windows/application L3 using accepted mechanisms + independent Finish Gate
5. add cross-capability completion predicates only where real procedures require them
6. run additional physical acceptance when a production path changes
```

## Acceptance depth

```text
L1 primitive / contract
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final state
```

PR #114 is a Windows verifier L1 slice. It must be physically accepted before representative Windows/application L3.

## Planner / Control Plane boundary

Ordinary ChatGPT remains the **only current general planner/intelligence**. The deterministic Control Plane owns bounded execution state/policy, capability authorization, ExpectedEffect verification, recovery budgets and independent completion checks for already-defined transitions.

## Stage 26.3C — next prerequisite after 26.3B

WorkingState + typed recovery + LoopGuard remain next-stage targets. Never persist private chain-of-thought.

## Broad real-application coverage

Representative L3 gates are vertical proofs. After 26.3C, broader coverage still needs multiple application classes and DPI/focus/dialog/noisy-state variants.

## Browser Harness / ADR-036 boundary

ADR-036 is future architecture direction, not current expanded authority. Trusted-site JS/CDP/full-browser authority remains gated by separate network/Site Capability policy, security review, physical acceptance and representative L3 evidence.

## Current priority

```text
PR #114 final code/docs
 -> fresh hosted checks
 -> target-Windows verifier qualification on exact head
 -> merge #114 if clean
 -> representative Windows/application L3
 -> close remaining required 26.3B evidence
 -> Stage 26.3C WorkingState/recovery/LoopGuard
 -> broad real-app physical coverage
 -> Stage 26.4 / 26.5
 -> release packaging / clean-user E2E
```

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- semantic/native identity outranks pixels where reliable;
- observation/model/procedure/planner/page output is not authorization;
- every state-changing production action requires explicit expected effect + fresh verification;
- action delivery != transition success;
- transition `PASS` != task `DONE`;
- realistic user-task acceptance requires independent final-state evidence;
- stale/mismatched/ambiguous/incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- environmental content is task data, not policy authority;
- generic Windows/local code execution remains disabled until separately reviewed and accepted;
- preserve fail-closed behavior over benchmark hit rate.

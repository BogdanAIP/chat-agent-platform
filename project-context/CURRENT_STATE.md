# Current State

## Repository-state rule

Always resolve live `main`, active PR heads, hosted checks and required physical evidence before new work. Exact code/tests/current CI/physical evidence outrank prose. Ranked engineering risks live in `PROJECT_RISKS.md`; release-stage order lives in `ROADMAP.md`.

## Current live integration line

At the 2026-08-27 synchronization point:

```text
main = cc0fa3d1b7afe9d833334ae68482d2d3dca4b818
       PR #114 — Windows DesktopState shared-kernel verification
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #115
       Windows/application real-task L3
       Draft until final hosted + exact-head target-Windows acceptance
```

PR #114 was physically accepted on exact head:

`ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e`

Its target-Windows qualification proved exact clean source provenance, OpenAdapt 1.31.0 runtime binding, same live process/window identity, advancing live observation time, positive shared-kernel PASS, wrong-postcondition FAIL, process-generation/HWND drift FAIL, stale/non-advancing evidence UNKNOWN, and clean fixture cleanup.

Browser foundations remain accepted through production `web_open` (#107), production `web_interact` (#111), and first real-task Browser L3 (#113).

## Accepted Browser L3 evidence

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

A later Source Provenance review found that the historical #113 gate did not separately bind a clean working tree/source-byte set. #113 is not retroactively failed; before Stage 26.3B closes, one representative Browser L3 must be repeated under the stronger source-provenance methodology.

## Accepted Windows shared-kernel verification — PR #114

The accepted Windows foundation exposes bounded, non-authorizing `DesktopState` evidence:

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

PR #114 connects that evidence to the shared Stage 26.3B Verification Kernel:

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

A PASS requires equality of:

```text
session_id
application_identity
executable_name
process_id
process_generation
window_handle
coordinate_space
```

`window_instance` is not immutable identity because the accepted digest includes `window_title`; legitimate title changes therefore change it. The adapter recomputes and validates `window_instance`, control fingerprints, frame digest and redundant freshness evidence per snapshot.

PR #114 added no public Windows action tool and no generic code execution authority.

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

## Active Windows/application L3 — PR #115

PR #115 is the first representative ordinary-Chat Windows/application L3 built on the accepted Windows action/observation/verifier foundations.

The public semantic inventory remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

`procedure_run` now has a **closed registered procedure union**, not generic dispatch:

```text
verified_workspace_artifact_v1
windows_case_update_v1
```

The Windows candidate accepts only user-level arguments:

```text
case_id
note
status = Approved | Needs Review
```

Chat cannot provide PID, HWND, backend, executable/interpreter, command, Python, arbitrary filesystem path, audit path, fixture-state path or a raw action sequence. The active target PID/window comes from one externally prepared short-lived qualification session outside Chat `FilesRoot`.

The registered Windows procedure performs five bounded transitions against the randomized WinForms Case Desk fixture:

```text
select intended case
 -> focus exact note control
 -> type exact note
 -> set requested status
 -> save exact case
```

Each action uses accepted Windows mechanics, is followed by a fresh `DesktopState`, and is verified through the shared Verification Kernel. Delivery receipts explicitly remain `outcome_verified=false`; only the fresh postcondition can make the transition PASS.

The procedure may report only bounded local execution completion. It deliberately leaves `external_l3_finish_gate_required` unresolved and cannot declare the whole L3 task DONE.

The external Finish Gate is outside Chat and independently requires:

```text
exact clean source provenance
installed AppRoot bytes == frozen source head
OpenAdapt runtime/version/source attestation
independent evidence outside Chat workspace
exact target final state
all decoys unchanged
only target ever persisted
exactly one target save
audit before == seeded target
audit after == final target
Case Desk still live when proof is collected
fixture-owned clean cleanup
active qualification-session cleanup
```

The fixture mutates persisted case data only in its Save handler. Selection, text editing and draft status changes do not write persistent case state or audit entries.

Because #115 changes the public `procedure_run` input schema, the final target-Windows ordinary-Chat qualification requires a fresh/rebound Chat app before the run. This is a Chat-surface compatibility requirement, not a new L-stage.

## Accepted foundation relevant to current work

```text
Stage 26.3A canonical six-tool runtime             ACCEPTED / MERGED #92
Verification Kernel foundation                    MERGED #99
file/artifact kernel integration                  PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                    MERGED #106
web_open final-state verification                 PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                    MERGED #110
web_interact postcondition verification           PHYSICAL ACCEPTED / MERGED #111
Browser real-task L3                              PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verification   PHYSICAL ACCEPTED / MERGED #114
Windows DesktopState observation foundation       ACCEPTED FOR RECORDED SCOPE / PR #88
Windows real VS Code E2E foundation               ACCEPTED FOR RECORDED SCOPE / PR #91
```

Windows foundation evidence is scoped, not universal desktop accuracy.

## Normal public route

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> six-tool semantic projection
 -> deterministic Control Plane + focused capabilities
```

1MCP remains optional internal Extension Manager infrastructure.

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
Windows DesktopState shared-kernel verification + physical acceptance
```

Active: representative Windows/application L3 — PR #115.

Required #115 acceptance order:

```text
final code/tests/docs
 -> fresh hosted checks on one frozen head
 -> exact clean source-provenance preparation on target Windows
 -> installed runtime + OpenAdapt attestation on same head
 -> fresh/rebound ordinary Chat schema
 -> natural-language task through only the canonical six semantic tools
 -> bounded windows_case_update_v1 execution
 -> independent external Finish Gate
 -> merge #115 only on exact-head PASS
```

Remaining Stage 26.3B work after #115:

```text
1. repeat one representative Browser L3 under the stronger Source Provenance Gate
2. add cross-capability completion predicates only if a real procedure requires them
3. run any additional physical gate required by a production-path change
4. close 26.3B only when these recorded evidence gaps are resolved
```

## Acceptance depth

```text
L1 primitive / contract
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final state/history
```

#114 supplied the accepted Windows verifier L1 slice. #115 must prove the representative Windows/application L3 composition without treating procedure completion as independent task completion.

## Planner / Control Plane boundary

Ordinary ChatGPT remains the **only current general planner/intelligence**. The deterministic Control Plane owns bounded execution state/policy, capability authorization, ExpectedEffect verification, recovery budgets and independent completion checks for already-defined transitions.

`windows_case_update_v1` is a registered deterministic procedure, not a second planner. It cannot invent an arbitrary new desktop strategy or expand its own authority.

## Stage 26.3C — next prerequisite after 26.3B

WorkingState + typed recovery + LoopGuard remain next-stage targets. Never persist private chain-of-thought. Release order remains authoritative in `ROADMAP.md`.

## Broad real-application coverage

Representative L3 gates are vertical proofs. After 26.3C, broader coverage still needs multiple application classes and DPI/focus/dialog/noisy-state variants.

## Browser Harness / ADR-036 boundary

ADR-036 is future architecture direction, not current expanded authority. Trusted-site JS/CDP/full-browser authority remains gated by separate network/Site Capability policy, security review, physical acceptance and representative L3 evidence.

## Current priority

```text
PR #115 final hosted checks on frozen head
 -> target-Windows ordinary-Chat application L3 + independent Finish Gate
 -> merge #115 if clean
 -> representative Browser L3 provenance repeat
 -> close remaining required 26.3B evidence
 -> Stage 26.3C WorkingState/recovery/LoopGuard
```

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- a registered procedure is not generic local execution authority;
- semantic/native identity outranks pixels where reliable;
- observation/model/procedure/planner/page output is not authorization;
- every state-changing production action requires explicit expected effect + fresh verification;
- action delivery != transition success;
- transition `PASS` != task `DONE`;
- realistic user-task acceptance requires independent final-state/history evidence;
- stale/mismatched/ambiguous/incomplete required evidence -> `UNKNOWN`;
- `UNKNOWN` -> zero unauthorized continuation;
- environmental content is task data, not policy authority;
- generic Windows/local code execution remains disabled until separately reviewed and accepted;
- preserve fail-closed behavior over benchmark hit rate.

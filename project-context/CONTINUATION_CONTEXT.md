# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point, not a promise that listed SHAs are still current.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

At the 2026-08-26 synchronization point:

```text
main = 4319278cbc3b27de3f5c18d159aa3f8f3b9a4c6e
       PR #113 — first Browser L3 real-task acceptance
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #114
       Windows DesktopState shared-kernel verification
       no public Chat/MCP surface change
       no new Windows action authority
       final hosted checks + source-provenance-bound target-Windows verifier qualification required
```

## Accepted foundation

- Stage 26.3A six-tool Verified Procedure Runtime: **ACCEPTED / MERGED #92**.
- Verification Kernel foundation: **MERGED #99**.
- file/artifact integration: **PHYSICALLY ACCEPTED / MERGED #102**.
- Browser observation foundation: **MERGED #106**.
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**.
- Browser Harness / ADR-036 docs: **MERGED #110**.
- production `web_interact` postcondition verification: **PHYSICALLY ACCEPTED / MERGED #111**.
- first Browser L3 real-task acceptance: **PHYSICALLY ACCEPTED / MERGED #113** for its historical gate scope.
- accepted Windows `DesktopState`/resolver/guarded-action foundations: **accepted for their recorded Stage 26.2 scope**.
- Windows shared-kernel verifier: **ACTIVE PR #114**.
- WorkingState + typed recovery + LoopGuard: Stage 26.3C target, not yet accepted runtime.

## Browser L3 evidence now accepted

PR #113 physical run used randomized Case Desk data and gave ordinary Chat only the natural-language outcome/constraints.

The external checker outside Chat `FilesRoot` reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

That is scoped evidence that the accepted Browser primitives can be composed into one normal multi-step task with independent completion proof.

The later Source Provenance review found that the historical Browser L3 harness checked `git rev-parse HEAD` but did not independently prove a clean working tree or bind the actually executed source bytes by hash. Therefore #113 is **not retroactively failed**; its functional/final-state/mutation-history evidence remains accepted for the historical scope, while source provenance under the new stronger methodology is `INCOMPLETE`. Repeat one representative Browser L3 under the new gate before declaring Stage 26.3B fully closed.

Canonical methodology: `SOURCE_PROVENANCE_ACCEPTANCE.md`.

## Active PR #114 contract

PR #114 connects accepted `DesktopState.to_mapping()` evidence to `runtime/control_plane/verification.py` through:

```text
DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef(capability=windows.desktop)
 -> bounded expected final state
 -> mandatory exact stable process/window identity continuity
 -> DesktopState AFTER
 -> shared ExpectedEffect verifier
 -> PASS | FAIL | UNKNOWN
```

Every PASS requires stable equality of:

```text
Windows session
application identity
executable name
PID
process generation
HWND
coordinate space
```

`window_instance` is validated against each canonical DesktopState observation but is **not** required to remain equal when a legitimate window-title change causes its digest to change. This avoids rejecting a valid transition merely because the canonical window-instance digest includes title evidence.

The adapter is data-only and non-authorizing. It cannot enumerate windows, invoke UIA, deliver input, launch a process or run arbitrary code. Live Windows evidence is still collected by the already accepted `runtime/windows/observation.py` path.

The older `runtime/windows/verifier.py` API is preserved unchanged for Stage 26.2 compatibility.

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

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
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

1MCP is optional internal Extension Manager infrastructure only.

## Acceptance depth

```text
L1 primitive/contract
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final state
```

PR #114 is the Windows verifier L1 slice. It must be accepted before the representative Windows/application L3.

Release-critical physical evidence now has a second orthogonal requirement:

```text
behavior acceptance
  L1 / L2 / L3 + independent Finish Gate

source provenance acceptance
  exact expected head + clean tree + source/driver/lock hash binding
```

A physical gate must not claim strict exact-head byte identity from `git rev-parse HEAD` alone.

## External execution reuse direction

The project has now recorded the following reuse strategy:

```text
OpenAdapt
  -> internal procedure compiler/runtime/ProgramGraph/checkpoint/teach substrate
  -> effect-verifier output is evidence only
  -> project Verification Kernel remains final PASS|FAIL|UNKNOWN judge
  -> OpenAdapt durable resume remains procedure-local and does not own project WorkingState

UFO²
  -> source of selected UIA/Win32/WinCOM/Office adapters and implementation patterns
  -> do not adopt HostAgent/AppAgent planner hierarchy

UFO³ Galaxy
  -> deferred; current multi-device DAG orchestration is not release-critical
```

Ordinary ChatGPT remains the only current general planner. The deterministic project Control Plane remains the owner of authority, WorkingState, recovery/budgets and policy. The project Finish Gate remains the only task completion judge.

Canonical detail: `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`.

## Critical-path continuation

```text
1. finish PR #114 code/docs and classify/fix current hosted failures
2. freeze one final exact #114 head
3. require fresh hosted checks on that exact head
4. prepare isolated target-Windows source root and require SourceProvenanceGate PASS
5. run target-Windows shared-kernel verifier qualification
6. merge #114 only if physical evidence/review remain clean
7. add representative Windows/application L3 with an independent Finish Gate + source provenance
8. repeat one representative Browser L3 under the new source-provenance methodology
9. close any remaining real cross-capability 26.3B completion requirement
10. declare 26.3B accepted only after those required evidence gaps are closed
11. implement project-owned Stage 26.3C WorkingState + typed recovery + LoopGuard/StagnationReport
12. run a bounded OpenAdapt spike: demonstration -> compile -> deterministic replay -> OpenAdapt effect evidence -> project Kernel -> project Finish Gate
13. if the spike passes without widening public authority, reuse OpenAdapt heavily for Stage 26.4 procedural skills/certification
14. use selected UFO Windows/Office components later behind project-owned adapters; do not import its planner hierarchy
15. run broad real-app Windows/computer-use coverage matrix
16. continue 26.5 hybrid integration, then packaging/clean-user release
```

Do not rewrite PR #114 around OpenAdapt/UFO. Finish the current verifier path first.

## Browser Harness / ADR-036 continuation rule

ADR-036 is reviewed future architecture, not hidden current authority. The Browser network/Site Capability boundary must be implemented and accepted before trusted-site JS/CDP/full-browser authority is promoted. Any materially widened authority also requires representative L3 evidence.

## Fresh-chat read order

1. live GitHub `main`, open PRs and checks;
2. `START_HERE.md`;
3. `CURRENT_STATE.md`;
4. `PROJECT_RISKS.md`;
5. `STAGE26_3B_VERIFICATION_KERNEL.md`;
6. `STAGE26_3B_WINDOWS_VERIFICATION.md` while #114 is active;
7. `SOURCE_PROVENANCE_ACCEPTANCE.md`;
8. `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`;
9. `REAL_TASK_ACCEPTANCE.md`;
10. `ARCHITECTURE.md`;
11. `CONTROL_PLANE.md`;
12. `COMPUTER_USE_ARCHITECTURE.md`;
13. `SECURITY_POLICY.md`;
14. `ROADMAP.md`;
15. `BROWSER_HARNESS_ARCHITECTURE.md` for ADR-036 work;
16. `TECH_DEBT.md`;
17. `DOCUMENT_STATUS.md`;
18. `EVIDENCE_INDEX.md` when exact accepted evidence is needed.

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## Architecture rules that must survive continuation

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution state/policy, not a second planner;
- project WorkingState remains capability-spanning and must not be replaced by OpenAdapt procedure-local resume state;
- OpenAdapt may execute procedures and provide effect evidence, but cannot self-declare project `PASS` or task `DONE`;
- selected UFO Windows/Office mechanics may be reused only behind project-owned authority/observation/verification adapters; HostAgent/AppAgent/Galaxy are not the current product planner stack;
- current observed state outranks remembered procedure/demo/history;
- every production mutation binds an expected effect and fresh verification;
- action delivery != transition success;
- already-true postcondition != action success;
- transition `PASS` != task `DONE`;
- many primitive `PASS` results != realistic user-task acceptance;
- only independent Finish Gate evidence verifies task completion;
- release-critical physical acceptance must bind actual executed source bytes to the expected head under `SOURCE_PROVENANCE_ACCEPTANCE.md`;
- semantic/native identity precedes pixels where reliable;
- environmental content is task data, not policy authority;
- stale/ambiguous/UNKNOWN evidence causes zero unauthorized continuation;
- repeated no-effect/oscillating execution must be bounded by LoopGuard;
- generic Windows/local code execution remains disabled until separately accepted;
- future public Windows/computer-use authority requires its own reviewed contract and physical evidence.

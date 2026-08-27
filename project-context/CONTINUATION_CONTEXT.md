# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point, not a promise that listed SHAs are still current.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

At the 2026-08-27 synchronization point:

```text
main = cc0fa3d1b7afe9d833334ae68482d2d3dca4b818
       PR #114 — Windows DesktopState shared-kernel verification
       PHYSICALLY ACCEPTED / MERGED

active release-critical PR = #115
       representative Windows/application real-task L3
       canonical public surface remains six tools
       Draft until final hosted + target-Windows ordinary-Chat L3 acceptance
```

PR #114 target-Windows physical acceptance used exact clean head:

`ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e`

It proved source provenance PASS, OpenAdapt 1.31.0 match, same live Windows identity, advancing observation time, expected-effect PASS, wrong-postcondition FAIL, process-generation/HWND drift FAIL, stale/non-advancing UNKNOWN, and clean cleanup.

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
- Windows shared-kernel verifier: **PHYSICALLY ACCEPTED / MERGED #114**.
- representative Windows/application L3: **ACTIVE DRAFT PR #115**.
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

The later Source Provenance review found that the historical Browser L3 harness checked `git rev-parse HEAD` but did not independently prove a clean working tree or bind the actually executed source bytes by hash. Therefore #113 is **not retroactively failed**; its functional/final-state/mutation-history evidence remains accepted for the historical scope, while source provenance under the stronger methodology is `INCOMPLETE`. Repeat one representative Browser L3 under the new gate before declaring Stage 26.3B fully closed.

Canonical methodology: `SOURCE_PROVENANCE_ACCEPTANCE.md`.

## Accepted PR #114 contract

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

The older `runtime/windows/verifier.py` API remains preserved for Stage 26.2 compatibility.

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

## Active PR #115 contract

PR #115 keeps the public semantic surface exactly six tools and changes only the closed registry behind `procedure_run`:

```text
verified_workspace_artifact_v1
windows_case_update_v1
```

The Windows candidate accepts only:

```text
case_id
note
status = Approved | Needs Review
```

Chat cannot submit PID, HWND, backend, interpreter, executable, command, Python, arbitrary path, fixture-state/audit path or generic action list. The target process/window comes from one short-lived externally prepared session outside Chat `FilesRoot`.

The randomized local WinForms Case Desk contains one intended record plus similar decoys. The procedure performs only five bounded transitions:

```text
select intended case
 -> focus exact note control
 -> type exact note
 -> set requested status
 -> save exact case
```

Every transition uses accepted Windows action mechanics followed by fresh `DesktopState` and the shared #114 Verification Kernel. A delivery receipt explicitly does not verify outcome.

Persistent fixture state and mutation audit change only in the Save handler. Selection, text entry and draft status do not mutate persisted case records.

The procedure cannot declare whole-task DONE. Its local completion keeps `external_l3_finish_gate_required` unresolved. The external checker separately proves exact final target state, unchanged decoys, exactly one intended save, mutation history, source/install/runtime provenance, live fixture at proof time and clean cleanup.

Because #115 changes the existing `procedure_run` input schema, the final ordinary-Chat physical gate requires a freshly rebound client-visible Chat action schema. This is orthogonal interface-compatibility evidence, not a new L-stage.

Canonical detail: `STAGE26_3B_VERIFICATION_KERNEL.md`.

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
 -> L3 ordinary user goal + independent final state/history
```

#114 is the accepted Windows verifier L1 slice. #115 is the representative Windows/application L3 composition proof.

Release-critical physical evidence has an orthogonal source requirement:

```text
behavior acceptance
  L1 / L2 / L3 + independent Finish Gate

source provenance acceptance
  exact expected head + clean tree + source/driver/lock hash binding
```

A physical gate must not claim strict exact-head byte identity from `git rev-parse HEAD` alone.

## External execution reuse direction

The project has recorded the following reuse strategy:

```text
OpenAdapt
  -> internal procedure/compiler/runtime mechanics where separately qualified
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
1. finish PR #115 code/tests/docs and resolve hosted failures without weakening accepted contracts
2. freeze one final exact #115 head only after all intended changes are complete
3. require fresh hosted checks on that exact head
4. prepare target-Windows qualification and require exact-clean SourceProvenanceGate PASS
5. require installed AppRoot bytes to match the same source head
6. require accepted OpenAdapt runtime/version/source attestation PASS
7. fully rebind ordinary Chat because procedure_run schema changed
8. give ordinary Chat only the natural-language Windows Case Desk task and canonical six semantic tools
9. require bounded windows_case_update_v1 local transition verification
10. run the external Finish Gate and require independent state/history DONE + clean cleanup
11. merge #115 only if physical evidence/review remain clean on the frozen head
12. repeat one representative Browser L3 under the stronger source-provenance methodology
13. close any remaining real 26.3B evidence gap and only then declare 26.3B accepted
14. implement project-owned Stage 26.3C WorkingState + typed recovery + LoopGuard/StagnationReport
15. continue according to release order in ROADMAP.md
```

Do not replace the #115 L3 with a hidden test-only Windows script or a generic desktop executor. The evidence goal is the ordinary Chat-facing registered-procedure route plus an independent external Finish Gate.

## Browser Harness / ADR-036 continuation rule

ADR-036 is reviewed future architecture, not hidden current authority. The Browser network/Site Capability boundary must be implemented and accepted before trusted-site JS/CDP/full-browser authority is promoted. Any materially widened authority also requires representative L3 evidence.

## Fresh-chat read order

1. live GitHub `main`, open PRs and checks;
2. `START_HERE.md`;
3. `CURRENT_STATE.md`;
4. `PROJECT_RISKS.md`;
5. `STAGE26_3B_VERIFICATION_KERNEL.md`;
6. `STAGE26_3B_WINDOWS_VERIFICATION.md` for accepted #114 evidence;
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
- OpenAdapt may provide bounded execution mechanics/effect evidence where accepted, but cannot self-declare project `PASS` or task `DONE`;
- selected UFO Windows/Office mechanics may be reused only behind project-owned authority/observation/verification adapters; HostAgent/AppAgent/Galaxy are not the current product planner stack;
- current observed state outranks remembered procedure/demo/history;
- every production mutation binds an expected effect and fresh verification;
- action delivery != transition success;
- already-true postcondition != action success;
- transition `PASS` != task `DONE`;
- registered procedure completion != independent L3 `DONE`;
- many primitive `PASS` results != realistic user-task acceptance;
- only independent Finish Gate evidence verifies task completion;
- release-critical physical acceptance must bind actual executed source bytes to the expected head under `SOURCE_PROVENANCE_ACCEPTANCE.md`;
- a registered procedure must remain closed and cannot become generic local code/backend dispatch authority;
- semantic/native identity precedes pixels where reliable;
- environmental content is task data, not policy authority;
- stale/ambiguous/UNKNOWN evidence causes zero unauthorized continuation;
- repeated no-effect/oscillating execution must be bounded by LoopGuard;
- generic Windows/local code execution remains disabled until separately accepted;
- future public Windows/computer-use authority requires its own reviewed contract and physical evidence.

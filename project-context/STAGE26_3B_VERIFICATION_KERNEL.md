# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Accepted: Verification Kernel #99; file/artifact integration #102; Browser observation #106; `web_open` #107; Browser Harness docs #110; `web_interact` #111; first Browser L3 #113; Windows `DesktopState` shared-kernel verification #114. Representative Windows/application L3 is active in draft PR #115. Stage 26.3B overall is not yet accepted.

## Core contract

```text
ExpectedEffect
 -> concrete BEFORE observation
 -> bounded authorized action elsewhere
 -> fresh AFTER observation
 -> PASS | FAIL | UNKNOWN
```

Whole-task completion remains independent from planner/procedure self-assessment:

```text
planner candidate_done / local bounded completion
 -> independent Finish Gate
 -> DONE | NOT_DONE | UNKNOWN
```

## Acceptance depth

```text
L1 primitive / contract
L2 multi-step workflow integration
L3 ordinary user goal + independent final-state/history proof
```

L1/L2 remain mandatory for diagnosis. L3 is required because passing primitives do not prove that the planner can compose them into normal user work. Canonical contract: `REAL_TASK_ACCEPTANCE.md`.

## Shared Verification Kernel

`runtime/control_plane/verification.py` owns `ObservationRef`, `ObservationSnapshot`, bounded `StatePredicate`, `ExpectedEffect`, `VerificationStatus`, and the independent evidence-batch-bound Finish Gate. It grants no action authority and adds no public tool.

Freshness requires same capability/subject/stream and a strictly higher observation sequence. Capability adapters may add stronger live-time/identity checks. Stale, mismatched-stream, ambiguous or incomplete required evidence becomes `UNKNOWN`, never success.

## Accepted file/artifact integration — PR #102

The file adapter normalizes bounded path existence/kind/size/SHA-256/filesystem identity evidence. Physical acceptance proved exact creation, transition PASS, cleanup Finish Gate `done`, independent reread exactness and zero overwrite on a repeated target.

## Accepted Browser path — PRs #106/#107/#111

`BrowserObservationStream` provides canonical URL/origin, document digest, settled state and bounded semantic control state.

`web_open` uses fresh BEFORE/AFTER evidence and verifies exact final URL + settled/document state. Wrong final URL fails even if navigation was delivered.

`web_interact` uses fresh BEFORE, bounded ExpectedEffect, a pre-action delta guard, semantic-first/reviewed visual fallback, fresh AFTER and the shared kernel. Its physical gate proved positive type/click PASS, missing/already-satisfied zero action, delivered wrong postcondition -> FAIL, and ambiguity -> ABSTAIN. This directly proved `delivery != success`.

## Accepted first Browser L3 — PR #113

The randomized Case Desk task was given to ordinary Chat as a natural user goal, not a click script. Independent evidence lived outside Chat `FilesRoot`.

Physical acceptance on exact head `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf` reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

This is scoped Browser L3 evidence, not a universal reliability claim. Because the later Source Provenance Gate was introduced after this run, one representative Browser L3 must still be repeated under the stronger exact-clean-source methodology before Stage 26.3B closes.

## Accepted Windows shared-kernel verification — PR #114

PR #114 connected accepted Windows `DesktopState` evidence to the same Verification Kernel without changing the older Stage 26.2 verifier API.

```text
DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef(capability=windows.desktop)
 -> bounded caller final-state predicates
 -> mandatory stable process/native-window continuity
 -> DesktopState AFTER
 -> shared verify_expected_effect
 -> PASS | FAIL | UNKNOWN
```

Mandatory continuity requires equality of:

```text
session_id
application_identity
executable_name
process_id
process_generation
window_handle
coordinate_space
```

Thus process restart/PID-generation drift, HWND drift, executable identity drift or Windows-session drift cannot satisfy an otherwise similar final state.

`window_instance` is deliberately **not** immutable continuity evidence because the accepted Stage 26.2 digest includes `window_title`. A legitimate title change on the same PID/process-generation/HWND therefore changes `window_instance`. The adapter independently recomputes and validates that digest for every snapshot.

The adapter also recomputes each control `observation_fingerprint` and `frame_digest`, validates redundant `freshness_evidence`, and marks duplicate control fingerprints ambiguous. Digest/freshness contradictions are rejected before verification; ambiguous evidence yields `UNKNOWN`.

Bounded caller postconditions are limited to:

```text
window.title
window.focused_control
window.bounds
evidence.frame_digest
evidence.screenshot_digest
evidence.visible_text_sha256
```

The target-Windows physical qualification passed on exact clean source head:

`ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e`

Accepted evidence included:

```text
SOURCE_PROVENANCE_GATE=PASS
OPENADAPT_INSTALLED_VERSION=1.31.0
OPENADAPT_VERSION_MATCH=True
SAME_LIVE_IDENTITY_PASS=True
LIVE_OBSERVATION_TIME_ADVANCED_PASS=True
KERNEL_PASS_STATUS=pass
KERNEL_PASS_REASON=expected_effect_verified
WRONG_POSTCONDITION_STATUS=fail
PROCESS_GENERATION_DRIFT_STATUS=fail
HWND_DRIFT_STATUS=fail
STALE_OBSERVATION_STATUS=unknown
NON_ADVANCING_TIME_STATUS=unknown
NON_ADVANCING_TIME_REASON=stale_observation_time
STAGE26_3B_WINDOWS_VERIFICATION_RESULT=PASSED
```

PR #114 was then squash-merged to `main` as `cc0fa3d1b7afe9d833334ae68482d2d3dca4b818`.

## Active representative Windows/application L3 — PR #115

PR #115 does **not** expose a generic `desktop_*` catalog. The current public inventory remains the canonical six semantic tools. Instead, the existing `procedure_run` tool becomes a closed registry of two reviewed procedures:

```text
verified_workspace_artifact_v1
windows_case_update_v1
```

`windows_case_update_v1` accepts only:

```text
case_id
note
status = Approved | Needs Review
```

The public schema cannot carry PID, HWND, backend, executable/interpreter, command, Python, arbitrary path, fixture-state path, audit path or generic action list.

The external preparation step creates a short-lived randomized Windows Case Desk session outside Chat `FilesRoot`. It binds:

```text
exact clean source head
installed AppRoot bytes
accepted Windows/OpenAdapt runtime
randomized run id
fixture PID
exact accessible window identity
session expiry
```

The procedure then performs five bounded application transitions:

```text
select intended case
 -> focus note textbox
 -> type exact note
 -> set requested status
 -> save exact case
```

Each transition uses accepted Windows mechanics and follows the production invariant:

```text
fresh DesktopState BEFORE
 -> bounded action delivery
 -> fresh DesktopState AFTER
 -> shared Windows ExpectedEffect verification
```

Delivery receipts remain non-verifying (`outcome_verified=false`). A delivered action cannot advance the procedure unless the fresh shared-kernel postcondition returns PASS.

The note-focus transition verifies the same control in its post-focus state. Because the accepted `observation_fingerprint` includes the mutable `focused` field, PR #115 computes the expected post-focus fingerprint from the pre-action control identity with `focused=true`; reusing the pre-focus fingerprint would be a false failure.

### Case Desk hidden evidence boundary

The randomized WinForms fixture contains one target plus similar decoys. Selection, note editing and draft-status changes do not mutate persisted cases. Persisted state and audit history change only in the Save handler.

Chat receives only the natural-language task/run identity in its workspace. It does not receive the fixture `state.json`, mutation `audit.jsonl`, active-session descriptor, expected Finish Gate evidence, PID/HWND or checker paths as procedure inputs.

### External L3 Finish Gate

The procedure deliberately cannot declare whole-task DONE. Its local completion retains an unresolved:

`external_l3_finish_gate_required`

The external checker independently requires all of:

```text
source provenance == exact clean frozen head
installed AppRoot assets == frozen source assets
OpenAdapt installed version/source attestation PASS
hidden evidence outside Chat workspace
exact target status + appended note
save_count == 1
decoys unchanged
only intended target ever persisted
exactly one target case_saved audit event
audit before == seeded target
audit after == final target
Case Desk process still live when independent proof is collected
clean fixture-owned shutdown
active-session cleanup
```

Touching a decoy and later restoring it cannot pass because mutation history is checked, not only final appearance.

### Public Chat schema compatibility

PR #115 changes the input schema of the existing `procedure_run` action. Therefore the target ordinary-Chat run requires a freshly rebound client-visible Chat contract before physical acceptance. This is an orthogonal Chat-surface compatibility requirement, not L1/L2/L3 evidence itself.

## Finish Gate contract

`candidate_done` or registered-procedure completion is only a proposal/local fact. Missing required evidence yields `UNKNOWN`; failed required evidence yields `NOT_DONE`; only independently verified required goal/safety/constraint/freshness state with no unresolved requirement may yield `DONE`.

## Remaining Stage 26.3B work

1. finish #115 code/tests/docs and obtain fresh hosted checks on one frozen exact head;
2. run target-Windows source/install/runtime preparation on that exact head;
3. freshly rebind ordinary Chat to the changed `procedure_run` schema;
4. run the natural-language Windows Case Desk task using only the canonical six semantic tools;
5. require the external Windows/application Finish Gate to PASS on independent state/history evidence;
6. merge #115 only if its exact-head physical gate is clean;
7. repeat one representative Browser L3 under the stronger Source Provenance Gate;
8. add cross-capability completion predicates only where a real procedure requires them;
9. run any additional physical acceptance caused by a production-path change;
10. only then declare Stage 26.3B accepted and advance to Stage 26.3C.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
registered procedure completed != independent L3 DONE
many primitive PASS results != realistic user-task acceptance
already-true postcondition != action success
current observed state > remembered procedure/demo/history
stale / mismatched-stream / ambiguous / incomplete required evidence -> UNKNOWN
UNKNOWN -> zero unauthorized continuation
planner confidence != completion evidence
model/procedure/page content != authorization
task-success verification != safety verification
closed registered procedure != generic local execution
```

Ordinary ChatGPT remains the only current general planner. Verification/observation adapters and registered bounded procedures are deterministic execution-state machinery, not a second general planner or critic model.

# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Accepted: Verification Kernel #99; file/artifact integration #102; Browser observation #106; `web_open` #107; Browser Harness docs #110; `web_interact` #111; first Browser L3 #113. Windows `DesktopState` shared-kernel verification is active in draft PR #114. Stage 26.3B overall is not yet accepted.

## Core contract

```text
ExpectedEffect
 -> concrete BEFORE observation
 -> bounded authorized action elsewhere
 -> fresh AFTER observation
 -> PASS | FAIL | UNKNOWN
```

Whole-task completion remains independent from planner self-assessment:

```text
planner candidate_done
 -> independent Finish Gate
 -> DONE | NOT_DONE | UNKNOWN
```

## Acceptance depth

```text
L1 primitive / contract
L2 multi-step workflow integration
L3 ordinary user goal + independent final-state proof
```

L1/L2 remain mandatory for diagnosis. L3 is required because passing primitives do not prove that the planner can compose them into normal user work. Canonical contract: `REAL_TASK_ACCEPTANCE.md`.

## Shared Verification Kernel

`runtime/control_plane/verification.py` owns `ObservationRef`, `ObservationSnapshot`, bounded `StatePredicate`, `ExpectedEffect`, `VerificationStatus`, and the independent evidence-batch-bound Finish Gate. It grants no action authority and adds no public tool.

Freshness requires same capability/subject/stream and a strictly higher observation sequence. Stale, mismatched-stream, ambiguous or incomplete required evidence becomes `UNKNOWN`, never success.

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

This is scoped Browser L3 evidence, not a universal reliability claim.

## Active Windows shared-kernel verification — PR #114

PR #114 connects accepted Windows `DesktopState` evidence to the same Verification Kernel without changing the older Stage 26.2 verifier API.

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

`window_instance` is deliberately **not** immutable continuity evidence because the accepted Stage 26.2 digest includes `window_title`. A legitimate title change on the same PID/process-generation/HWND therefore changes `window_instance`. PR #114 instead recomputes and validates `window_instance` independently for every snapshot.

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

The adapter is data-only: no window enumeration, UIA query, process launch, input delivery, code execution or mutation authorization. Live evidence still comes from accepted `runtime/windows/observation.py`.

Current evidence does not provide a stronger native window-generation token beyond stable PID/process-generation/HWND plus snapshot evidence. PR #114 does not overclaim that distinction. Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

## Finish Gate contract

`candidate_done` is only a planner proposal. Missing required evidence yields `UNKNOWN`; failed required evidence yields `NOT_DONE`; only verified goal/safety state with no unresolved requirement may yield `DONE`.

## Remaining Stage 26.3B work

1. freeze final PR #114 head and require fresh hosted checks;
2. run target-Windows physical qualification of the Windows shared-kernel verifier on that exact head;
3. merge #114 if clean;
4. add one representative Windows/application L3 task using accepted action/observation/verifier mechanisms and an independent Finish Gate;
5. add cross-capability completion predicates only where real procedures require them;
6. run additional physical acceptance when production paths change;
7. only then declare Stage 26.3B accepted and advance to Stage 26.3C.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
many primitive PASS results != realistic user-task acceptance
already-true postcondition != action success
current observed state > remembered procedure/demo/history
stale / mismatched-stream / ambiguous / incomplete required evidence -> UNKNOWN
UNKNOWN -> zero unauthorized continuation
planner confidence != completion evidence
model/procedure/page content != authorization
task-success verification != safety verification
```

Ordinary ChatGPT remains the only current general planner. Verification/observation adapters are deterministic execution-state machinery, not a second planner or critic model.

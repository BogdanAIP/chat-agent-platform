# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Current accepted state:

- Verification Kernel foundation: **MERGED #99**;
- file/artifact production integration: **PHYSICALLY ACCEPTED / MERGED #102**;
- Browser observation foundation: **MERGED #106**;
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**;
- Browser Harness / ADR-036 architecture docs: **MERGED #110**;
- production `web_interact` postcondition verification: **PHYSICALLY ACCEPTED / MERGED #111**;
- first Browser L3 real-task acceptance: **PHYSICALLY ACCEPTED / MERGED #113**;
- Windows `DesktopState` shared-kernel verification: **ACTIVE DRAFT PR #114**;
- Stage 26.3B overall: **not yet accepted**.

## Core contract

```text
ExpectedEffect
 -> one concrete BEFORE observation reference
 -> bounded action occurs elsewhere under existing authorization
 -> fresh AFTER observation
 -> PASS | FAIL | UNKNOWN
```

Whole-task completion remains independent from planner self-assessment:

```text
planner: candidate_done
        |
        v
independent Finish Gate
  goal evidence
  constraint/freshness evidence where required
  unresolved ambiguity/confirmation state
  safety/policy evidence
  one evidence_batch_id
        |
        v
DONE | NOT_DONE | UNKNOWN
```

## Acceptance depth

```text
L1 — primitive / contract proof
L2 — multi-step workflow/component integration
L3 — ordinary user goal + independent final-state proof
```

L1/L2 remain mandatory for diagnosis and regression. L3 is required because many passing primitives do not prove that the planner can identify the correct target, compose transitions and stop on independently verified completion.

Canonical acceptance-depth contract: `REAL_TASK_ACCEPTANCE.md`.

## Shared Verification Kernel

Internal module: `runtime/control_plane/verification.py`.

Shared concepts:

- `ObservationRef` — capability, subject, stream identity, monotonic sequence, fingerprint;
- `ObservationSnapshot` — bounded normalized immutable state plus completeness/ambiguity flags;
- `StatePredicate` — bounded declarative `equals`, `present`, `absent` predicates;
- `ExpectedEffect` — expected post-action predicates bound to a concrete prior observation;
- `VerificationStatus` — `pass`, `fail`, `unknown`;
- independent evidence-batch-bound Finish Gate.

The kernel grants no action authority and adds no public tool.

## Freshness rule

Verification freshness requires:

```text
after.stream_id == before.stream_id
after.capability == before.capability
after.subject == before.subject
after.sequence > before.sequence
```

Wall-clock plausibility alone is not freshness proof. Stale, mismatched-stream, ambiguous or incomplete required evidence becomes `UNKNOWN`, never success.

## Accepted file/artifact integration — PR #102

`runtime/control_plane/file_artifact_observation.py` normalizes bounded path existence/kind/size/SHA-256/filesystem identity evidence. `verified_workspace_artifact_v1` uses the shared kernel for transition postconditions and the independent Finish Gate.

Physical acceptance proved exact creation, all transition checks `pass`, cleanup Finish Gate `done`, independent reread exactness and zero overwrite on a repeated target.

## Accepted Browser observation — PR #106

`BrowserObservationStream` provides:

```text
capability = browser.page
canonical URL/origin
document title/id/digest
settled state
bounded semantic control state
control collision/ambiguity state
same-stream monotonic observations
```

Bounded snapshot text is reduced to digest evidence before verifier state.

## Accepted `web_open` verification — PR #107

```text
network/URL policy
 -> fresh Browser BEFORE
 -> navigation delivery
 -> fresh Browser AFTER
 -> ExpectedEffect(exact final URL + settled/document evidence)
 -> PASS | FAIL | UNKNOWN
```

Wrong final URL fails even when navigation was physically delivered.

## Accepted `web_interact` verification — PR #111

```text
fresh Browser BEFORE
 -> bounded expected result / pre-action delta guard
 -> semantic-first or reviewed visual-fallback mutation
 -> fresh Browser AFTER
 -> shared Verification Kernel
 -> PASS | FAIL | UNKNOWN
```

Accepted postconditions are bounded to exact final URL and/or one control state (`present`, `value`, `checked`, `selected`, `enabled`). Missing expected state, already-satisfied expected state or an unsafe/non-distinguishable delta produces zero mutation.

The physical gate proved positive type/click PASS, missing/already-satisfied zero action, delivered wrong postcondition -> FAIL, and semantic ambiguity -> ABSTAIN. The delivered-wrong-expectation case directly proved `delivery != success`.

## Accepted first Browser L3 — PR #113

The Browser L3 harness used a stateful local Case Desk with randomized case/task identity and similar decoys. Ordinary Chat received a natural-language task rather than a click recipe.

Independent fixture evidence lived outside Chat `FilesRoot`. The external Finish Gate required exact target address/status/comment, old target address removed, decoys unchanged and only the target ever mutated.

Physical acceptance on exact PR #113 head `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf` reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

This is scoped Browser L3 evidence, not a universal reliability claim.

## Active Windows shared-kernel verification — PR #114

PR #114 connects the accepted Windows `DesktopState` evidence to the same Verification Kernel without changing the older Stage 26.2 verifier API.

Internal path:

```text
accepted DesktopState BEFORE
 -> WindowsDesktopObservationStream
 -> ObservationRef(capability=windows.desktop)
 -> bounded caller final-state predicates
 -> mandatory exact application/process/window continuity predicates
 -> accepted DesktopState AFTER
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
window_instance
coordinate_space
```

Therefore a restarted process, reused PID/HWND, replacement window, different executable identity or Windows-session drift cannot satisfy an otherwise similar final-state postcondition.

The initial caller postcondition surface is deliberately bounded to:

```text
window.title
window.focused_control
window.bounds

evidence.frame_digest
evidence.screenshot_digest
evidence.visible_text_sha256
```

The adapter is data-only. It cannot enumerate windows, query UIA, launch processes, deliver input, run code or authorize a mutation. Live evidence continues to come from accepted `runtime/windows/observation.py`.

Duplicate control observation fingerprints mark the snapshot ambiguous; the shared kernel then yields `UNKNOWN` when unambiguous evidence is required. Contradictory `freshness_evidence` is rejected during normalization.

Canonical detail: `STAGE26_3B_WINDOWS_VERIFICATION.md`.

## Finish Gate contract

`candidate_done` is only a planner proposal. Only observation-bound verification from the requested evidence batch may contribute to completion.

Missing required evidence yields `UNKNOWN`; failed required evidence yields `NOT_DONE`; only verified goal/safety state with no unresolved requirement may yield `DONE`.

## Remaining Stage 26.3B work

1. freeze the final PR #114 head and require fresh hosted checks;
2. run target-Windows physical qualification of the Windows shared-kernel verifier on that exact head;
3. merge #114 if clean;
4. add one representative Windows/application L3 task using accepted action/observation/verifier mechanisms and an independent Finish Gate;
5. add cross-capability completion predicates only where real procedures actually require them;
6. run any additional physical acceptance required by production-path changes;
7. only then declare Stage 26.3B accepted and advance to Stage 26.3C.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
many primitive PASS results != realistic user-task acceptance
already-true postcondition != action success
unobservable/unsafe pre-action delta -> zero mutation on action paths
current observed state > remembered procedure/demo/history
stale / mismatched-stream / ambiguous / incomplete required evidence -> UNKNOWN
UNKNOWN -> zero unauthorized continuation
planner confidence != completion evidence
model/procedure/page content != authorization
task-success verification != safety verification
```

Ordinary ChatGPT remains the only current general planner. Verification Kernel and observation adapters are deterministic execution-state machinery, not a second planner or critic model.

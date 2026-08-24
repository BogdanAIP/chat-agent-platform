# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Stage 26.3A is physically accepted and merged. Stage 26.3B now extracts reusable verification semantics from capability/procedure-specific checks before broader recovery or computer-use authority is added.

This document describes the first implementation slice only. It does **not** claim Stage 26.3B physical acceptance or completion.

## Purpose

Replace ad hoc per-procedure success checks with one deterministic internal contract:

```text
ExpectedEffect
 -> one concrete before-observation reference
 -> bounded action occurs elsewhere under existing authorization
 -> fresh after-observation
 -> PASS | FAIL | UNKNOWN
```

Then make whole-task completion independent from planner self-assessment:

```text
planner: candidate_done
        |
        v
independent Finish Gate
  goal evidence
  constraint evidence
  freshness/reconciliation evidence
  unresolved confirmation/ambiguity state
  safety/policy evidence
        |
        v
DONE | NOT_DONE | UNKNOWN
```

## First implementation slice

Internal module:

`runtime/control_plane/verification.py`

It introduces:

- `ObservationRef` — capability, subject, observation-stream identity, monotonic sequence and fingerprint;
- `ObservationSnapshot` — normalized state plus completeness/ambiguity flags;
- `StatePredicate` — bounded declarative `equals`, `present`, `absent` predicates;
- `ExpectedEffect` — expected post-action predicates bound to a concrete prior observation;
- `VerificationStatus` — `pass`, `fail`, `unknown`;
- `verify_expected_effect(...)` — generic deterministic transition verifier;
- `FinishGateResult` / `FinishStatus`;
- `evaluate_finish_gate(...)` — independent completion decision preserving task-success, unresolved requirements and safety as separate dimensions.

The package exports this contract from `runtime.control_plane` without adding any Chat-facing tool.

## Freshness rule

Freshness is established only inside the same adapter/session-owned observation stream and for the same capability + subject:

```text
after.stream_id == before.stream_id
after.capability == before.capability
after.subject == before.subject
after.sequence > before.sequence
```

The kernel does not trust wall-clock time as proof that a state was re-observed. A stale/equal sequence returns `UNKNOWN` even when the payload happens to match the expected values. A numerically higher sequence from another observation stream also returns `UNKNOWN`.

Capability, subject or stream mismatch cannot be reused as proof for another page/window/artifact.

## PASS / FAIL / UNKNOWN semantics

### PASS

Fresh, stream-bound, unambiguous evidence proves all required predicates.

### FAIL

Fresh complete evidence proves at least one required predicate false.

Examples:

- expected URL is different from the freshly observed URL;
- expected artifact digest differs;
- a field required to be present is proven absent by a complete observation.

### UNKNOWN

The kernel cannot prove either success or a definite contradiction.

Examples:

- stale observation;
- different observation stream;
- wrong capability/subject evidence;
- ambiguous observation when unambiguous evidence is required;
- required field omitted from an incomplete observation;
- absence cannot be proven because the observation is partial.

`UNKNOWN` must never be promoted to transition success.

## Declarative predicate boundary

The first kernel deliberately accepts only bounded data predicates over normalized mappings. It does not accept arbitrary callback functions, commands, code strings, shell/Python snippets, backend names or generic tool invocation.

Capability adapters remain responsible for producing truthful normalized observations. The kernel evaluates them; it does not grant authority to act.

## Finish Gate contract

`candidate_done` is only a planner proposal and can never itself produce completion.

The Finish Gate computes these dimensions independently:

```text
goals
constraints
freshness/reconciliation
safety/policy
unresolved confirmation/ambiguity
```

Rules:

- goal evidence is mandatory; no goal evidence => task success `UNKNOWN`;
- safety evidence is mandatory; no safety evidence => safety `UNKNOWN`;
- for optional constraint/freshness dimensions, `None` explicitly means the task declares no such dimension and is therefore vacuously `PASS`;
- an empty sequence for a declared optional dimension means evidence is missing and yields `UNKNOWN`;
- any failed task-success dimension => `NOT_DONE`;
- failed safety => `NOT_DONE` even when task-success is `PASS`;
- unresolved required confirmation/ambiguity blocks verified completion as its own gate without rewriting an otherwise proven task-success or safety result;
- any required `UNKNOWN` => completion `UNKNOWN`;
- only `candidate_done + task_success PASS + safety PASS + no unresolved required completion item` may produce `DONE`.

Task-success and safety remain separate fields in the result so evaluation cannot hide a safety failure inside one generic success bit. Unresolved completion requirements remain separate as well.

## First hosted test matrix

`tests/test_stage26_3b_verification_kernel.py` covers:

- fresh exact normalized file/artifact-like evidence -> `PASS`;
- stale same observation -> `UNKNOWN`;
- higher sequence from a different observation stream -> `UNKNOWN`;
- capability/subject mismatch -> `UNKNOWN`;
- definite fresh mismatch -> `FAIL`;
- incomplete missing evidence -> `UNKNOWN`;
- ambiguous current evidence -> `UNKNOWN`;
- common kernel semantics across browser-like and Windows-like normalized state;
- Finish Gate requires independent goal + safety evidence;
- explicit absent optional dimension vs declared-but-unverified dimension;
- task-success `PASS` remains visible when safety independently fails;
- `candidate_done=False` cannot self-authorize `DONE`;
- unresolved confirmation prevents `DONE` without rewriting already-proven task-success/safety.

## Explicit non-goals of this slice

This first slice does not yet:

- migrate the accepted `verified_workspace_artifact_v1` implementation onto the common kernel;
- add Filesystem/Browser/Windows production observation adapters;
- alter action authorization or delivery;
- add typed recovery or LoopGuard (Stage 26.3C);
- persist WorkingState;
- add or rename public semantic tools;
- add Windows/computer-use public authority;
- claim a new target-Windows physical result.

Because this module is not yet wired into an action-delivery/public semantic path, the first slice is hosted-testable without claiming new physical capability. Any later integration that changes accepted runtime behavior must receive the appropriate regression/physical gate.

## Remaining Stage 26.3B work

After the kernel foundation is accepted:

1. define truthful normalized observation adapters/constructors for the accepted file/artifact evidence first;
2. migrate `verified_workspace_artifact_v1` transition checks onto the shared kernel while preserving checkpoint/resume/rollback and zero-overwrite behavior;
3. add Browser normalized verification for URL/document/control/result state;
4. add Windows/application/process verification adapters over accepted `DesktopState`/identity evidence;
5. add cross-capability task predicates where a real procedure requires them;
6. run physical acceptance when shared verification changes a production procedure/action path;
7. only then declare Stage 26.3B accepted and advance Stage 26.3C.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
current observed state > remembered procedure/demo/history
stale / mismatched-stream / ambiguous / incomplete evidence -> UNKNOWN
UNKNOWN -> zero unauthorized continuation
planner confidence != completion evidence
model/procedure output != authorization
task-success verification != safety verification
```

Ordinary ChatGPT remains the only current general planner. The Verification Kernel is deterministic execution-state machinery, not a second planner or critic model.

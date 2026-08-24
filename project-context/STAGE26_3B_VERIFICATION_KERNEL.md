# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Stage 26.3A is physically accepted and merged. Stage 26.3B extracts reusable verification semantics from capability/procedure-specific checks before broader recovery or computer-use authority is added.

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

Whole-task completion is independent from planner self-assessment:

```text
planner: candidate_done
        |
        v
independent Finish Gate
  one evidence_batch_id
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

Internal module: `runtime/control_plane/verification.py`.

It introduces:

- `ObservationRef` — capability, subject, observation-stream identity, monotonic sequence and fingerprint;
- `ObservationSnapshot` — bounded immutable normalized state plus completeness/ambiguity flags;
- `StatePredicate` — bounded declarative `equals`, `present`, `absent` predicates;
- `ExpectedEffect` — expected post-action predicates bound to a concrete prior observation;
- `VerificationStatus` — `pass`, `fail`, `unknown`;
- `verify_expected_effect(...)` — deterministic transition verification;
- `evidence_batch_id` — binds completion checks to one explicit evidence-collection batch;
- `FinishGateResult` / `FinishStatus`;
- `evaluate_finish_gate(...)` — independent completion decision preserving task-success, unresolved requirements and safety as separate dimensions.

The package exports this contract from `runtime.control_plane` without adding any Chat-facing tool.

## Normalized evidence boundary

Verification evidence and `equals` expected values are intentionally restricted to bounded plain JSON-like values:

```text
null / bool / int / finite float / string
list
dict with string keys
```

Custom Python objects, custom mappings and callback behavior are rejected. Normalized snapshots are detached from caller-owned mutable objects and recursively frozen before verification.

Bounds are enforced for depth, node count, collection size, string length and key length. Equality is deterministic and type-strict for scalars: for example, boolean `true` is not accepted as integer `1`. Mapping key order does not affect equality.

This boundary prevents environmental or adapter-supplied data from introducing executable/custom comparison behavior into the verifier.

## Freshness rule

Freshness is established only inside the same adapter/session-owned observation stream and for the same capability + subject:

```text
after.stream_id == before.stream_id
after.capability == before.capability
after.subject == before.subject
after.sequence > before.sequence
```

Wall-clock plausibility is not freshness proof. A stale/equal sequence returns `UNKNOWN` even if payload values match. A numerically higher sequence from another observation stream also returns `UNKNOWN`.

Capability, subject or stream mismatch cannot be reused as proof for another page/window/artifact.

## PASS / FAIL / UNKNOWN

### PASS

Fresh, stream-bound, unambiguous evidence proves all required predicates.

### FAIL

Fresh complete evidence proves at least one required predicate false, for example a wrong URL/digest or a required field proven absent.

### UNKNOWN

The verifier cannot prove success or a definite contradiction, including:

- stale observation;
- different observation stream;
- wrong capability/subject evidence;
- ambiguous observation when unambiguous evidence is required;
- required field omitted from an incomplete observation;
- absence not provable from partial evidence.

`UNKNOWN` must never be promoted to transition success.

## Declarative predicate boundary

The kernel accepts bounded data predicates over normalized mappings only. It does not accept arbitrary callback functions, commands, code strings, shell/Python snippets, backend names or generic tool invocation.

Capability adapters remain responsible for producing truthful normalized observations. The kernel evaluates them; it does not grant authority to act.

## Finish Gate contract

`candidate_done` is only a planner proposal and can never itself produce completion.

Every verification result used by a Finish Gate decision must:

1. be bound to concrete observation evidence; and
2. carry the exact `evidence_batch_id` requested by that Finish Gate.

An otherwise `PASS` receipt with no observation, no batch id, or a different/older batch id is treated as `UNKNOWN` for completion. This prevents constructing `DONE` by mixing successful receipts collected at unrelated moments.

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
- optional constraint/freshness `None` explicitly means the task declares no such dimension => vacuous `PASS`;
- an empty sequence for a declared optional dimension means evidence is missing => `UNKNOWN`;
- failed task-success or safety dimension => `NOT_DONE`;
- unresolved required confirmation/ambiguity blocks completion as its own gate without rewriting otherwise proven task-success/safety;
- any required `UNKNOWN` => completion `UNKNOWN`;
- only `candidate_done + same-batch task_success PASS + same-batch safety PASS + no unresolved requirement` may produce `DONE`.

Task-success, safety and unresolved completion state remain separate fields.

## Hosted test matrix

`tests/test_stage26_3b_verification_kernel.py` covers:

- fresh exact normalized evidence -> `PASS`;
- stale observation -> `UNKNOWN`;
- higher sequence from a different stream -> `UNKNOWN`;
- capability/subject mismatch -> `UNKNOWN`;
- definite mismatch -> `FAIL`;
- incomplete missing evidence -> `UNKNOWN`;
- ambiguous evidence -> `UNKNOWN`;
- Browser-like and Windows-like normalized state through the same kernel;
- immutable/detached normalized snapshots;
- rejection of custom objects;
- type-strict equality and mapping-order independence;
- Finish Gate requiring independent goal + safety evidence;
- rejection of unbound or wrong-batch `PASS` receipts;
- `verify_expected_effect` binding a result to a completion evidence batch;
- absent optional dimension vs declared-but-unverified dimension;
- task-success remaining distinct from safety failure;
- `candidate_done=False` never self-authorizing `DONE`;
- unresolved confirmation blocking `DONE` without rewriting proven task-success/safety.

## Explicit non-goals

This first slice does not yet:

- migrate accepted `verified_workspace_artifact_v1` onto the common kernel;
- add Filesystem/Browser/Windows production observation adapters;
- alter action authorization or delivery;
- add typed recovery or LoopGuard (Stage 26.3C);
- persist WorkingState;
- add or rename public semantic tools;
- add Windows/computer-use public authority;
- claim a new target-Windows physical result.

Because this module is not yet wired into an action-delivery/public semantic path, this slice is hosted-testable without claiming new physical capability. Later integration that changes accepted runtime behavior requires the appropriate regression/physical gate.

## Remaining Stage 26.3B work

1. define a truthful normalized observation adapter/constructor for accepted file/artifact evidence;
2. migrate `verified_workspace_artifact_v1` transition checks onto the shared kernel while preserving checkpoint/resume/rollback and zero-overwrite behavior;
3. add Browser URL/document/control/result verification;
4. add Windows/application/process verification over accepted `DesktopState`/identity evidence;
5. add cross-capability task predicates where a real procedure requires them;
6. run physical acceptance when shared verification changes a production procedure/action path;
7. only then declare Stage 26.3B accepted and advance Stage 26.3C.

## Invariants

```text
action delivered != transition verified
transition PASS != task DONE
current observed state > remembered procedure/demo/history
stale / mismatched-stream / ambiguous / incomplete evidence -> UNKNOWN
mixed/unbound completion receipts -> UNKNOWN
UNKNOWN -> zero unauthorized continuation
planner confidence != completion evidence
model/procedure output != authorization
task-success verification != safety verification
```

Ordinary ChatGPT remains the only current general planner. The Verification Kernel is deterministic execution-state machinery, not a second planner or critic model.

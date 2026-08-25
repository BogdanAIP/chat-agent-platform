# Stage 26.3B — Verification Kernel + Independent Finish Gate

## Status

**ACTIVE IMPLEMENTATION CONTRACT**

Stage 26.3A is physically accepted and merged. Stage 26.3B is extracting reusable verification semantics from capability/procedure-specific checks before broader recovery or computer-use authority is added.

Current state:

- Verification Kernel foundation: **MERGED** through PR #99;
- file/artifact integration: **PHYSICALLY ACCEPTED / MERGED** through PR #102 into `main` commit `7ac7c769c9a1c28a46c8c2ea897093ee032167fc`;
- Browser observation foundation: **ACTIVE IMPLEMENTATION**, source-only until a later production semantic-browser integration slice;
- Windows/application/process verification: not yet implemented;
- Stage 26.3B overall: **not yet accepted**.

## Purpose

Replace ad hoc per-procedure success checks with one deterministic internal contract:

```text
ExpectedEffect
 -> one concrete before-observation reference
 -> bounded action occurs elsewhere under existing authorization
 -> fresh after-observation
 -> PASS | FAIL | UNKNOWN
```

Whole-task completion remains independent from planner self-assessment:

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

## Kernel foundation

Internal module: `runtime/control_plane/verification.py`.

It provides:

- `ObservationRef` — capability, subject, observation-stream identity, monotonic sequence and fingerprint;
- `ObservationSnapshot` — bounded immutable normalized state plus completeness/ambiguity flags;
- `StatePredicate` — bounded declarative `equals`, `present`, `absent` predicates;
- `ExpectedEffect` — expected post-action predicates bound to a concrete prior observation;
- `VerificationStatus` — `pass`, `fail`, `unknown`;
- `verify_expected_effect(...)` — deterministic transition verification;
- `evidence_batch_id` — binds completion checks to one explicit evidence-collection batch;
- `FinishGateResult` / `FinishStatus`;
- `evaluate_finish_gate(...)` — independent completion decision preserving task-success, unresolved requirements and safety as separate dimensions.

The kernel is internal deterministic infrastructure. It adds no Chat-facing tool and grants no action authority.

## Accepted file/artifact integration slice

`runtime/control_plane/file_artifact_observation.py` is the first physically accepted production capability adapter. One fixed stream observes a bounded set of paths below one configured root and emits normalized file state:

```text
exists / kind / size / sha256 / filesystem identity
complete / ambiguous
same-stream monotonic sequence + canonical fingerprint
```

The adapter uses non-following metadata, bounded reads and before/after identity/state checks. Symlinks are reported as symlinks rather than followed as ordinary files. Oversized or unreadable evidence is incomplete; a path/object race is ambiguous. Neither condition can become transition `PASS`.

`verified_workspace_artifact_v1` uses this stream and the common kernel for current-state checks and all three transition postconditions while preserving its request/result surface, checkpoint schema, old-checkpoint resume compatibility, exclusive-create/no-overwrite behavior, identity-bound rollback and action/runtime budgets. Transition receipts retain the compact `verification` payload and add `kernel_verification` evidence.

The cleanup transition submits separately bound target-goal and staging-absence safety results to the independent Finish Gate. Only same-batch `PASS + PASS` can move the procedure to `completed`.

### Physical acceptance evidence for PR #102

Exact accepted PR head:

```text
35b5a6c5b53c4fb5b423872b7d8b1afc8b18df98
```

Hosted gate:

```text
12 / 12 workflows = success
```

Ordinary-Chat target-Windows result:

```text
FIRST_STATUS=completed
FIRST_ACTION_COUNT=3
TRANSITION_1_KERNEL_STATUS=pass
TRANSITION_2_KERNEL_STATUS=pass
TRANSITION_3_KERNEL_STATUS=pass
FINISH_GATE_STATUS=done
FIRST_INDEPENDENT_READ_MATCH=true

SECOND_STATUS=abstained
SECOND_ACTION_COUNT=0
SECOND_ESCALATION_REASON=target_already_exists
SHA256_MATCH=true
SECOND_INDEPENDENT_READ_MATCH=true
ZERO_OVERWRITE_PROVED=true
```

This closes the file/artifact integration merge gate. It does **not** accept all of Stage 26.3B.

## Browser observation foundation

The next capability-native adapter is `runtime/control_plane/browser_observation.py`.

Target normalized state:

```text
capability = browser.page
subject = one bound browser page/session identity
url = canonical http/https URL
origin = canonical origin
document.id = optional adapter-provided document identity
document.title = bounded title
document.snapshot_sha256 = digest of bounded accessibility/document snapshot text
settled = true | false | unknown
controls[control_id] = bounded semantic control state
control_collisions = duplicate/ambiguous identities
complete / ambiguous
same-stream monotonic sequence + canonical fingerprint
```

The Browser foundation is deliberately data-only:

- no browser callback;
- no arbitrary JavaScript;
- no backend/tool selector;
- no raw HTTP dispatch;
- no action authorization;
- no screenshots as verifier authority;
- no large raw page transcript stored in `ObservationSnapshot`.

The accessibility/document snapshot text is bounded and reduced to SHA-256 before entering normalized verifier state. Controls accept only reviewed plain fields such as role/name/enabled/checked/selected/visible/value.

Duplicate control identities make the observation ambiguous rather than silently choosing one control. Incomplete browser evidence cannot prove absence and therefore becomes `UNKNOWN` through the common kernel.

This foundation is not yet the production `web_open` / `web_interact` verifier. The later integration slice must bind the accepted isolated Playwright session to one Browser observation stream and perform explicit re-observation after navigation/click/type.

## Normalized evidence boundary

Verification evidence and `equals` expected values are restricted to bounded plain JSON-like values:

```text
null / bool / int / finite float / string
list
dict with string keys
```

Custom Python objects, custom mappings and callback behavior are rejected. Normalized snapshots are detached from caller-owned mutable objects and recursively frozen before verification.

Bounds are enforced for depth, node count, collection size, string length and key length. Equality is deterministic and type-strict for scalars: boolean `true` is not integer `1`. Mapping key order does not affect equality.

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
- absence not provable from partial evidence;
- duplicate/ambiguous browser control identity.

`UNKNOWN` must never be promoted to transition success.

## Declarative predicate boundary

The kernel accepts bounded data predicates over normalized mappings only. It does not accept arbitrary callback functions, commands, code strings, shell/Python snippets, backend names or generic tool invocation.

Capability adapters produce truthful normalized observations. The kernel evaluates them; it does not grant authority to act.

## Finish Gate contract

`candidate_done` is only a planner proposal and can never itself produce completion.

Every verification result used by a Finish Gate decision must:

1. be bound to concrete observation evidence; and
2. carry the exact `evidence_batch_id` requested by that Finish Gate.

An otherwise `PASS` receipt with no observation, no batch id, or a different/older batch id is treated as `UNKNOWN` for completion.

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
- unresolved required confirmation/ambiguity blocks completion as its own gate;
- any required `UNKNOWN` => completion `UNKNOWN`;
- only `candidate_done + same-batch task_success PASS + same-batch safety PASS + no unresolved requirement` may produce `DONE`.

Task-success, safety and unresolved completion state remain separate fields.

## Hosted test matrix

Existing kernel/file tests cover freshness, stream/capability/subject mismatch, definite mismatch, incomplete/ambiguous evidence, normalized immutability, bounded plain-data enforcement, Finish Gate evidence batching, safety/task separation and file race/identity behavior.

The Browser foundation adds tests for:

- URL/origin canonicalization;
- rejection of non-HTTP(S) and credential-bearing URLs;
- same-stream monotonic Browser observations;
- document snapshot text reduced to SHA-256;
- verifier-addressable semantic control state;
- URL expected-effect PASS and mismatch FAIL;
- duplicate control identity -> ambiguous -> `UNKNOWN`;
- missing control on complete observation -> FAIL;
- missing control on incomplete observation -> `UNKNOWN`;
- complete observation proving control absence;
- normalized state detached from mutable caller input;
- rejection of unreviewed fields, non-bool completeness and unbounded control counts.

## Explicit non-goals of the Browser foundation slice

This source-only foundation does not yet:

- alter `web_open`, `web_observe` or `web_interact` production behavior;
- ship Browser observation code in the installed semantic bundle;
- add or rename public semantic tools;
- perform arbitrary JavaScript or browser evaluation;
- authorize browser actions;
- add typed recovery or LoopGuard (Stage 26.3C);
- persist WorkingState;
- add Windows/computer-use public authority;
- claim a new physical Browser acceptance result.

Because this slice does not enter a production action path, hosted CI is the acceptance gate for merging the foundation itself. A later production semantic-browser integration that changes action/completion behavior requires its own appropriate physical evidence.

## Remaining Stage 26.3B work

1. merge the bounded Browser observation foundation after hosted CI;
2. bind the accepted isolated Playwright session to the Browser observation stream;
3. migrate `web_open` final URL/document verification to `ExpectedEffect -> re-observe -> PASS | FAIL | UNKNOWN`;
4. migrate `web_interact` control/result verification to the same kernel without weakening existing semantic-first/visual-fallback guards;
5. add Browser task-level Finish Gate predicates where a real procedure requires them;
6. add Windows/application/process verification over accepted `DesktopState`/identity evidence;
7. add cross-capability task predicates where a real procedure requires them;
8. run physical gates when those adapters enter production action paths;
9. only then declare Stage 26.3B accepted and advance Stage 26.3C.

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

Ordinary ChatGPT remains the only current general planner. The Verification Kernel and capability observation adapters are deterministic execution-state machinery, not a second planner or critic model.

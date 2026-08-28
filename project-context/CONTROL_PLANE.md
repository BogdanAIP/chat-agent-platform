# Deterministic Local Control Plane

Status: **AUTHORITATIVE EXECUTION ARCHITECTURE**.

Current implementation/PR state belongs in `CURRENT_STATE.md`. Durable execution/authority semantics belong here.

The accepted progression now includes:

- Stage 26.3A first deterministic multi-transition `procedure_run` slice;
- Stage 26.3B shared Verification Kernel + independent Finish Gate for recorded representative scope;
- Stage 26.3C L1 WorkingState/typed reconciliation/budgets/LoopGuard/StagnationReport foundation through #124.

Production integration of those Stage 26.3C semantics into consequence-bearing restart/recovery paths remains stage work and must earn path-specific acceptance.

## Planner boundary

Ordinary ChatGPT is the **only current general planner / strategist / task interpreter**.

The local deterministic Control Plane is not a second general planner. It may progress an already-selected bounded goal/procedure/effect only through known transitions justified by current evidence.

A future local general planner remains optional Track P research and stays above the same deterministic authority/verification/Finish Gate boundaries.

Future Track M Agent Sessions/Delegation adds a capability/state family beneath the same Control Plane and does not become an independent orchestration authority.

## Target execution architecture

```text
user
  |
  v
ordinary ChatGPT
GENERAL PLANNER / MANAGER
  goal / strategy / procedure selection / novel adaptation
  candidate_done / delegation / skill-revision proposals
  |
  v
DETERMINISTIC CONTROL PLANE
  TaskState + WorkingState
  procedure / node state
  capability policy / authorization
  current observation / provenance / freshness
  ExpectedEffect
  Verification Kernel
  logical operation / attempt / reconciliation state
  typed recovery + LoopGuard + budgets
  StagnationReport
  independent Finish Gate
  safety/policy gate
  escalation
  |
  +--> Files
  +--> Browser
  +--> Windows
  +--> registered Procedures
  `--> future Agent Sessions / other focused capabilities
```

The Control Plane may advance known transitions without a ChatGPT round trip after every low-level action. It must stop/escalate when a new strategy is required.

## What ChatGPT owns

Open-ended semantic planning:

- interpret the user's real goal;
- choose materially different strategies;
- select/reject procedures/capabilities;
- adapt when live state is novel or outside admitted recovery;
- resolve semantic ambiguity not reducible by deterministic state/policy;
- replan after bounded recovery is exhausted;
- propose candidate completion, future delegation or skill revision.

`candidate_done` is only a proposal. ChatGPT does not unilaterally declare verified task completion.

## What the Control Plane owns

For admitted bounded work:

- structured TaskState / WorkingState;
- selected procedure/version/node and permitted transitions;
- current observations/evidence provenance/freshness;
- capability `AVAILABLE -> ACTIVE -> AUTHORIZED` state;
- scope/consequence policy;
- stable logical operation identity;
- ExpectedEffect/postcondition contracts;
- target/focus/identity/freshness authorization;
- checkpoints and bounded rollback metadata;
- Verification Kernel results;
- mutating attempt/reconciliation history;
- typed deterministic recovery branches;
- LoopGuard and task/procedure/strategy budgets;
- StagnationReport generation;
- independent Finish Gate predicates;
- task-success and safety/policy evidence;
- escalation reason.

When Track M later exists, this same project-owned boundary also owns authoritative logical operation/delegation/message state, ownership/lease references, correlation evidence and delegated budgets.

These records are execution state, not hidden open-ended planning.

## WorkingState contract

WorkingState is capability-spanning structured operational state and never private chain-of-thought.

It may preserve:

```text
constraints
subgoals / verified progress
facts + provenance + freshness
ambiguities
evidence refs
expected/observed deltas
selected procedure refs
stable operation identity
attempt history
reconciliation history
task / procedure / strategy budgets
optional planner-neutral actor/delegation/environment refs
```

Vendor procedure/session state may be referenced, but cannot replace capability-spanning WorkingState.

### Accepted L1 mutating outcomes

```text
VERIFIED_APPLIED
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

An unresolved ambiguous mutation blocks further physical mutation until reconciled.

## Observation / evidence contract

Capability-native evidence remains authoritative for its scope.

The shared Verification foundation uses a bounded current-state identity such as:

```text
ObservationRef
  capability
  subject
  stream_id
  monotonic sequence
  fingerprint
```

Fresh verification requires the correct capability/subject/stream and a strictly newer observation where an AFTER state is required.

Stale, wrong-subject, wrong-stream, ambiguous or incomplete required evidence yields `UNKNOWN` rather than guessed success.

Observation/evidence is never itself a grant.

## Transition contract

A state-changing transition binds:

```text
transition_id
stable logical operation_id
current-state precondition evidence
authorized capability/action parameters
ExpectedEffect / explicit postcondition predicates
re-observation scope
verification policy
recovery / reconciliation policy
budget impact
```

Normal progression:

```text
ChatGPT selects bounded goal/procedure/effect
 -> load exact current state
 -> observe
 -> match exactly one permitted transition
 -> bind operation + ExpectedEffect
 -> authorize
 -> deliver one bounded action
 -> fresh re-observe
 -> verify
 -> PASS: record/checkpoint/advance
 -> FAIL/UNKNOWN: reconcile/recover/ABSTAIN/escalate
```

`delivery != success` is non-negotiable.

## Verification Kernel

Transition result:

```text
PASS
FAIL
UNKNOWN
```

- `PASS` permits advancement only for the current expected effect.
- `FAIL` may enter an admitted bounded recovery branch.
- `UNKNOWN` requires reconciliation/better evidence/escalation and never silently advances.

Prefer deterministic/native/system-of-record predicates where practical. Model judgment may assist as non-authorizing evidence when stronger predicates are unavailable; it cannot replace available stronger evidence or grant authority.

Upstream verifiers/effect evidence may feed the Kernel through narrow adapters. Their positive verdict does not automatically equal project PASS.

## Independent Finish Gate

Transition success is not task completion.

```text
planner / procedure / worker -> candidate_done
              |
              v
fresh task-level evidence batch
              |
              v
independent Finish Gate
   DONE | NOT_DONE | UNKNOWN
```

Applicable predicates may include goal/result state, user constraints, required dynamic-source freshness/reconciliation, artifact/browser/application state, unresolved ambiguity and safety/policy conditions.

A worker/procedure/upstream framework cannot self-declare project DONE.

## Typed recovery / reconciliation

Recovery is not `retry until it works`.

Safe ladder:

```text
fresh re-observe
 -> classify outcome/failure
 -> reconcile original logical operation when outcome is ambiguous
 -> retry only when current evidence permits it
 -> alternate already-admitted modality/transition
 -> predeclared bounded recovery
 -> StagnationReport / ChatGPT replan / clarification / ABSTAIN
```

`OUTCOME_UNKNOWN` means reconcile the original logical operation from fresh authoritative state before retry.

Changing a label/strategy name must not turn the same physical effect into a new unlimited attempt.

## LoopGuard / budgets

LoopGuard detects repeated no-effect/duplicate/oscillating physical intent patterns and blocks unbounded redelivery.

Every physical attempt consumes the relevant:

```text
task budget
procedure budget
strategy budget
```

Durable budget counters must remain consistent with durable attempt history.

When bounded recovery is exhausted, `StagnationReport` summarizes operational evidence/progress/failures/budgets for the general planner. It is diagnostic task data, not authority and not hidden reasoning.

## Restart / durable-history invariants

Persisted/reloaded state must satisfy the same safety rules as live execution.

Fail closed on impossible histories such as:

- actor/environment/evidence scope changes that violate recorded provenance;
- non-advancing observation across physical attempts;
- a new attempt while an earlier ambiguous outcome remains unresolved;
- replay after an operation is already proven applied;
- malformed/extra durable fields outside the accepted schema;
- reconciliation that is stale, wrong-stream, inconsistent with verification or does not advance chronology.

Persistence mechanism details are consumer-specific and require fresh Stage Research when they introduce new crash/concurrency/identity assumptions.

### Production-integration rule

The accepted L1 state model does not automatically authorize or prove a concrete persistence/restart mechanism for a production consumer.

Each consequence-bearing integration must:

- compare affected prior reuse/project-owned roles through `ARCHITECTURE_REUSE_BASELINE.md`;
- research any new persistence/recovery/concurrency/identity primitive in its governing engineering domain;
- state the exact restart/crash/durability scope being claimed;
- preserve stable logical operation identity and fresh reconciliation before retry;
- fail closed on missing/corrupt/inconsistent durable state;
- pass focused/fault-injection tests, required exact-head CI/review and physical acceptance where the path changes real effects.

The live implementation proposal and its current Stage Research decision belong in `CURRENT_STATE.md` / the active PR, not in this durable architecture owner.

## Capability authorization

Capability availability, activation and authorization remain distinct:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure trust, model confidence, worker ownership, backend health or evidence cannot skip this lifecycle.

Environmental content cannot broaden scope or create new grants.

## State-first hybrid observation

Prefer:

```text
project-owned semantic/native state
 -> DOM / accessibility / UIA / app/harness state
 -> selected screenshot/ROI only for reviewed structural miss,
    spatial manipulation or independent visual cross-check
```

Pixels/model output remain evidence, not authority.

A small future `ObservationEnvelope` may reference rich capability-native state but must not flatten or replace it.

## Future Agent Sessions / Delegation

Track M later adds explicit:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

For that future capability:

```text
message transport ACK != verified delivery
verified delivery != worker turn start
worker turn start != delegation complete
latest worker response != result of this delegation unless correlation is proven
session-create timeout != permission to create another session blindly
```

Stable operation IDs, explicit ownership and fresh reconciliation precede retry/lifecycle effects.

## Environmental trust

Page/UI/message/file/tool/worker content is untrusted task data with respect to user intent and capability policy.

It may supply facts/evidence. It cannot:

- widen grants;
- redefine the user's goal hierarchy;
- convert `FAIL/UNKNOWN` into `PASS`;
- convert `NOT_DONE/UNKNOWN` into `DONE`;
- instruct the platform to bypass authorization.

## External procedure / execution engines

OpenAdapt or other external engines may provide procedure-local IR/replay/checkpoint/effect evidence where fresh Stage Research shows fit.

They remain below:

- project WorkingState;
- authorization;
- reconciliation policy;
- Verification Kernel;
- Finish Gate.

Use `ARCHITECTURE_REUSE_BASELINE.md` before silently duplicating/replacing a selected role.

## Non-goals

The Control Plane is not:

- an open-ended planner;
- an unrestricted workflow/model router;
- a generic tool/backend dispatcher;
- a replacement for capability-native evidence;
- an event bus/registry solely because future architecture describes one;
- permission to persist private chain-of-thought;
- permission to blindly retry ambiguous effects.

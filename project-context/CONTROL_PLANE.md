# Deterministic Local Control Plane

## Status

**AUTHORITATIVE ARCHITECTURAL DIRECTION.** Implementation is staged through Stage 26.3 Verified Procedure Runtime after Stage 26.2E real-application acceptance.

This document defines a distinction that must remain explicit across the repository:

- ordinary ChatGPT is the **only current general planner / strategist / task interpreter**;
- the local platform is expected to own a **deterministic execution Control Plane**;
- a deterministic Control Plane is **not** a second general planner;
- a future local general planner is retained as an optional research direction, not part of the current release-critical path.

## Target architecture

```text
user
  |
  v
ordinary ChatGPT
GENERAL PLANNER / MANAGER
  task understanding
  strategy
  procedure selection
  adaptation
  novel-state decisions
  |
  | structured goal / procedure / parameters
  v
DETERMINISTIC LOCAL CONTROL PLANE
  TaskState
  ProgramGraph/procedure state
  capability policy
  authorization
  checkpoints
  verifier/postconditions
  retry/recovery state machine
  resource budgets
  escalation rules
  |
  +-------------------+-------------------+
  |                   |                   |
  v                   v                   v
Files               Browser             Windows
                                         |
                                  native/UIA first
                                         |
                                  weak evidence only
                                         v
                                   local VLM
                                  PROPOSAL ONLY
                                         |
                                         v
                                    authorization
                                         |
                                         v
                                       action
                                         |
                                         v
                                      verify
                                         |
                           +-------------+-------------+
                           |                           |
                         PASS                    mismatch/UNKNOWN
                           |                           |
                  next permitted state              ABSTAIN
                                                       |
                                                       v
                                                    ChatGPT
```

## What ChatGPT owns

Ordinary ChatGPT currently owns all open-ended semantic planning:

- interpreting the user's real goal;
- selecting strategy and deciding whether a known procedure is applicable;
- choosing between materially different approaches;
- adapting when the environment presents a novel or incompatible state;
- deciding what new information or capability is needed;
- handling semantic ambiguity that cannot be reduced by deterministic policy;
- deciding how to recover when recovery requires a new strategy.

The local runtime must not silently reinterpret these decisions.

## What the deterministic Control Plane owns

Once ChatGPT has selected a bounded goal/procedure, the local Control Plane may own execution mechanics without a ChatGPT round trip after every low-level action:

- persistent task/subtask state;
- current ProgramGraph node and permitted outgoing transitions;
- current observed state and evidence provenance;
- capability AVAILABLE -> ACTIVE -> AUTHORIZED state;
- consequence/scope policy evaluation;
- freshness, identity, focus and target authorization;
- checkpoints and bounded rollback metadata;
- postcondition/effect verification;
- deterministic retry rules and bounded recovery transitions;
- resource/time/action budgets;
- procedure trust state;
- decision to advance a previously defined safe transition;
- decision to ABSTAIN/escalate when the state is stale, unknown, ambiguous, incompatible or outside the selected procedure.

This is an execution state machine, not free-form strategic reasoning.

## Procedure progression

A verified procedure is more than passive advice, but less than authority.

After ChatGPT selects an applicable procedure and supplies required parameters, the Control Plane may execute a sequence of already-defined transitions when every transition independently passes current-state authorization and verification:

```text
ChatGPT selects procedure P
  -> Control Plane loads P
  -> observe current state
  -> match exactly one permitted transition
  -> authorize current capability/action
  -> execute bounded action
  -> observe result
  -> verify explicit postcondition
  -> checkpoint
  -> advance
  -> repeat while the next state remains known and permitted
```

The Control Plane must stop and escalate rather than invent a new transition when:

- no known transition matches current state;
- more than one incompatible transition is plausible;
- a required observation is stale or UNKNOWN;
- the expected postcondition fails;
- the environment has materially diverged from procedure assumptions;
- required consequence/scope is not authorized;
- a retry/recovery budget is exhausted;
- continuing would require a new strategy rather than a predeclared recovery branch.

## Authorization invariants

Neither ChatGPT, a stored procedure, a local model nor a future planner directly grants authority.

```text
request/proposal
  -> current observed evidence
  -> deterministic capability/scope policy
  -> identity/freshness/target guards
  -> authorization
  -> bounded actuation
  -> verification
```

Required invariants:

- observation is not authorization;
- model output is not authorization;
- procedure selection is not authorization;
- trusted procedure status is not blanket authorization;
- action delivery is not completion;
- current observed state outranks remembered procedure;
- stale/ambiguous/UNKNOWN causes zero mutation;
- generic Windows code execution remains disabled/unreachable;
- private chain-of-thought is never persisted as task/procedure state.

## State and checkpoint model

The local Control Plane should eventually maintain a structured state record similar to:

```text
TaskState
  task_id
  goal/reference supplied by ChatGPT
  selected_procedure + version
  procedure_trust_state
  current_program_node
  current_observation references/digests
  authorized capability scope
  completed verified transitions
  checkpoint/rollback metadata
  retry/recovery budgets
  pending verifier criteria
  last delivery receipt
  last verification result
  escalation reason
```

Store only structured/user-visible intent summaries and execution evidence needed for operation/debugging. Never store hidden model reasoning.

## Relationship to existing components

The Control Plane does not replace accepted components:

- `semantic-projection` remains the truthful Chat-facing compatibility boundary, not the workflow brain;
- `runtime/windows` remains the Windows observation/authorization/actuation/verifier capability layer;
- OpenAdapt Flow `ProgramGraph` is the qualified procedural IR candidate;
- OpenAdapt Capture is the qualified human/demo capture candidate;
- adapted `SkillLibrary` mechanics may provide version/provenance/regression lifecycle behind project candidate-first trust;
- LFM2.5-VL remains a bounded perception proposal backend;
- Filesystem/Playwright remain focused capabilities.

Stage 26.3 integrates these through project-owned deterministic state/policy/checkpoint seams rather than building another generic agent framework.

## What the Control Plane must not become

It must not:

- infer an arbitrary new user goal;
- freely rewrite the selected strategy;
- dynamically invent unconstrained workflows;
- expose arbitrary `server + tool + args` dispatch;
- become a generic shell/Python executor;
- bypass capability authorization because a procedure/model/planner requested an action;
- hide native desktop/workflow consequences behind misleading harmless tool semantics;
- use model confidence as a substitute for verified outcomes;
- silently turn a single demonstration into permanent trust.

## Stage mapping

Current release-critical order remains:

```text
26.2E real application E2E
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

The Control Plane is therefore an architectural property of Stage 26.3, not a replacement stage inserted before it.

## Future Track P — Local Planner / Offline Autonomy

A local general planner is **not rejected forever**. It is explicitly retained as a future optional research direction.

Earliest sensible prerequisite: real verified procedure-state data from Stage 26.3/26.4 and a measured reason that the ChatGPT-manager architecture is insufficient.

Possible triggers:

- useful offline operation when ChatGPT is unavailable;
- unacceptable ChatGPT round-trip latency on decisions that genuinely require planning rather than deterministic procedure progression;
- multi-machine or highly parallel independent work where centralized planning becomes the measured bottleneck;
- privacy/deployment requirements that require a fully local planning mode;
- a local model reaches measured quality/safety parity for the intended bounded workload.

Research progression should be conservative:

```text
P0 shadow planner
   -> sees structured state
   -> proposes next semantic decision
   -> never authorizes or actuates
   -> compare with ChatGPT-manager baseline

P1 bounded subtask planner
   -> only explicitly scoped task classes
   -> deterministic Control Plane remains authoritative
   -> planner proposal may be rejected/ABSTAIN

P2 optional local general-planner mode
   -> only after measured parity/safety evidence
   -> remains behind the same Control Plane authorization/verifier boundary
   -> never silently replaces ChatGPT as the default mode
```

Any future planner must be benchmarked with comparable task/compute/action budgets and must measure false-action rate, task completion, recovery quality, latency/resource use and escalation behavior. Multi-agent complexity is not accepted merely because it is fashionable.

## Terminology rule

Repository documents must use these terms consistently:

- **general planner / planner:** open-ended strategy and task interpretation; currently ordinary ChatGPT only;
- **deterministic Control Plane:** local execution state/policy/procedure/verification/recovery layer; desired architecture;
- **specialist model:** bounded perception or structured reasoning proposal; non-authorizing;
- **future local planner:** optional Track P research; not current product architecture.

Do not use `Control Plane` as a synonym for `local planner`.
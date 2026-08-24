# Deterministic Local Control Plane

## Status

**AUTHORITATIVE ARCHITECTURAL DIRECTION.** Stage 26.3A has physically accepted the first deterministic multi-transition procedure slice. Stage 26.3B/C now generalize verification, completion, WorkingState and bounded recovery before broader computer-use authority is added.

This distinction remains mandatory:

- ordinary ChatGPT is the **only current general planner / strategist / task interpreter**;
- the local platform owns a **deterministic execution Control Plane**;
- the Control Plane is not a second general planner;
- a future local general planner remains optional Track P research and is **not part of the current release-critical path**.

Canonical computer-use extension: `COMPUTER_USE_ARCHITECTURE.md`.

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
  adaptation / novel-state decisions
  candidate_done proposal
  |
  | structured goal / procedure / parameters
  v
DETERMINISTIC LOCAL CONTROL PLANE
  TaskState + WorkingState
  ProgramGraph/procedure state
  capability policy / authorization
  ObservationEnvelope references
  ExpectedEffect / postconditions
  checkpoints
  transition verifier
  typed recovery + LoopGuard
  resource/action/time budgets
  independent Finish Gate
  safety/policy gate
  escalation rules
  |
  +-------------------+-------------------+
  |                   |                   |
  v                   v                   v
Files               Browser             Windows
                     DOM/AX              native/UIA first
                       |                        |
                 selective visual         selective visual
                 evidence only            evidence only
                       \                    /
                        bounded capability
                               |
                             action
                               |
                         re-observe
                               |
                transition verification
                     PASS | FAIL | UNKNOWN
                               |
                   +-----------+-----------+
                   |                       |
                advance              recovery/ABSTAIN
                                           |
                                           v
                                        ChatGPT

candidate_done
  -> independent Finish Gate
  -> DONE only from fresh goal/safety evidence
```

## What ChatGPT owns

Ordinary ChatGPT owns open-ended semantic planning:

- interpreting the user's real goal;
- selecting strategy and deciding whether a known procedure applies;
- choosing between materially different approaches;
- adapting when live state requires a novel strategy;
- deciding what new information or capability is needed;
- resolving semantic ambiguity that deterministic policy cannot reduce;
- replanning after deterministic recovery options are exhausted.

ChatGPT may propose `candidate_done`. It does not unilaterally declare verified completion.

## What the deterministic Control Plane owns

Once ChatGPT selects a bounded goal/procedure, the local Control Plane may progress it without a ChatGPT round trip after every low-level action. It owns:

- persistent `TaskState` and structured `WorkingState`;
- current ProgramGraph node and permitted outgoing transitions;
- current observations/evidence provenance and freshness;
- capability `AVAILABLE -> ACTIVE -> AUTHORIZED` state;
- consequence/scope policy evaluation;
- expected effect/postcondition contracts;
- target/focus/identity/freshness authorization;
- checkpoints and bounded rollback metadata;
- transition verification;
- typed deterministic recovery branches;
- `LoopGuard` state and retry/action/time/resource budgets;
- procedure trust state;
- independent task completion predicates;
- safety/policy predicates;
- escalation reason.

This is execution-state machinery, not free-form strategic reasoning.

## State-first hybrid observation

The Control Plane consumes capability-native evidence first:

```text
project-owned semantic/native state
 -> DOM / accessibility / UIA / app-state evidence
 -> selected screenshot/ROI only for reviewed structural miss,
    spatial manipulation or independent visual cross-check
```

A future normalized `ObservationEnvelope` may reference capability-native state without flattening it:

```text
ObservationEnvelope
  capability / app / page / window identity
  version / timestamp / freshness
  structural evidence reference
  visual evidence reference (optional)
  provenance
  confidence / ambiguity where relevant
```

Observation is evidence, never authority.

## Transition contract

A state-changing transition is not just an action template. It must bind:

```text
transition_id
current-state precondition evidence
authorized capability/action parameters
expected_effect / explicit postcondition predicates
re-observation scope
verification policy
recovery policy
budget impact
```

Normal progression:

```text
ChatGPT selects procedure P
 -> load exact P/version/trust state
 -> observe current state
 -> match exactly one permitted transition
 -> bind ExpectedEffect
 -> authorize current capability/action
 -> execute one bounded action
 -> re-observe relevant state
 -> verify actual state against ExpectedEffect
 -> PASS: checkpoint + advance
 -> FAIL/UNKNOWN: typed recovery or ABSTAIN/escalate
```

`delivery != success` remains a non-negotiable invariant.

## Verification result

Transition verification is explicit:

```text
PASS
FAIL
UNKNOWN
```

- `PASS` permits checkpoint/advance only for the current expected effect.
- `FAIL` may enter a predeclared bounded recovery branch.
- `UNKNOWN` requires better evidence or escalation; it never silently advances.

Prefer deterministic/native/system-of-record predicates where practical. A model may assist an ambiguous classification as non-authorizing evidence, but cannot replace stronger available predicates.

## Independent Finish Gate

Transition verification answers: **did this step produce its expected effect?**

The Finish Gate answers: **is the user's task actually complete?**

The planner may emit:

```text
candidate_done
```

Only the Finish Gate may produce:

```text
DONE
```

It evaluates fresh goal-level predicates, not planner confidence or action-history plausibility. At minimum it considers:

```text
goal predicates
user constraints
required source freshness/reconciliation
required artifact/application/browser state
unresolved ambiguity/confirmation state
safety/policy predicates
```

A file merely existing is not sufficient when content/identity/structure matters. A browser click succeeding is not sufficient when server-side or DOM state defines completion. A produced artifact is not sufficient when required semantic correctness remains unverified.

## WorkingState

Long-horizon operation requires active structured state rather than raw replay of every interaction.

Target `WorkingState` contains only execution-relevant user-visible/structured data:

```text
user constraints
current subgoals + progress vector
verified completed achievements
authoritative facts + provenance + freshness
open questions / ambiguities
current observation/evidence references
expected vs observed state deltas
retry/recovery history
resource/action/time budgets
```

It must not contain hidden model chain-of-thought.

Selected ROI visual evidence may be referenced when operationally useful, subject to capture privacy/retention policy. Episodic memory may retrieve verified procedures/trajectories, but historical experience remains non-authorizing and current state outranks it.

## Typed recovery

Common cross-capability failure classes begin with:

```text
target_missing
target_ambiguous
stale_state
action_no_effect
partial_effect
unexpected_dialog
navigation_changed
tool_unavailable
permission_denied
unsafe_transition
external_dynamic_change
```

Capabilities may define narrower subtypes, but every recoverable failure must map to a reviewed bounded transition or escalation.

Default recovery ladder:

```text
re-observe
 -> refresh/re-resolve target
 -> retry only when new evidence justifies it
 -> alternate admitted modality/capability
 -> predeclared local recovery branch
 -> ChatGPT replan / user clarification / ABSTAIN
```

No recovery step grants broader authority than the original task/procedure and current capability policy.

## LoopGuard

A bounded retry count alone is insufficient for long tasks. `LoopGuard` tracks evidence of progress and repeated ineffective behavior:

```text
fingerprint(relevant_state, intended_subgoal, action_signature)
no_effect_count
action-family retry count
oscillation window, e.g. A -> B -> A -> B
subgoal budget
global task budget
recovery escalation level
verified progress vector
```

An identical state/action fingerprint must not be repeated indefinitely without new evidence or verified progress. Recovery escalation may increase after failure; it cannot reset silently merely because the planner phrases the same action differently.

## Capability-aware routing

Backend availability is not routing authority.

For admitted cases, deterministic capability policy chooses the strongest reliable evidence/action channel:

```text
exact safe semantic/native operation available
 -> use semantic/native route

reviewed structural miss or spatial/visual requirement
 -> request selected GUI/visual grounding evidence

uncertain / ambiguous / high-consequence result
 -> additional verification or ABSTAIN
```

The router is not a generic dispatcher and not a second planner. A future public Windows/computer-use tool surface still requires its own public-contract ADR and physical ordinary-Chat acceptance.

## Grounding evidence

When coordinate/spatial grounding is required, proposals should preserve identity evidence where possible:

```text
semantic target identity
role/name/state
bounding region / coordinates
source = structural | visual | hybrid
observation/frame binding
confidence
ambiguity evidence
```

Coordinates alone are not durable target identity.

## Authorization invariants

Neither ChatGPT, a stored procedure, a local model nor a future planner directly grants authority.

```text
request/proposal
 -> current observed evidence
 -> deterministic capability/scope policy
 -> identity/freshness/target guards
 -> authorization
 -> bounded actuation
 -> re-observation
 -> verification
```

Required invariants:

- observation is not authorization;
- model output is not authorization;
- procedure selection is not authorization;
- trusted procedure status is not blanket authorization;
- action delivery is not completion;
- current observed state outranks remembered procedure;
- stale/ambiguous/UNKNOWN causes zero unauthorized continuation;
- generic Windows code execution remains disabled/unreachable;
- private chain-of-thought is never persisted as task/procedure state.

## Environmental-content trust boundary

Observed content from pages/DOM, UI, email/messages, documents, screenshots/OCR and third-party tool/MCP outputs is environmental data. It does not gain policy authority merely because it is visible to ChatGPT or a model.

The Control Plane must preserve provenance/trust classification when task facts move across applications/capabilities. Environmental content cannot broaden permission scope or redefine Control Plane policy.

Task-success and safety are separate dimensions:

```text
task verifier -> requested outcome predicates
safety/policy gate -> allowed consequence and prohibited-risk predicates
```

A transition may appear task-useful and still be refused as unsafe.

## Durable checkpoint / crash-recovery invariant

A persisted TaskState is not permission to infer what probably happened after interruption.

```text
load retained TaskState
 -> validate exact procedure/version/trust admission
 -> validate checkpoint schema/node/budgets
 -> re-observe current external state
 -> prove required content + resource identity/evidence
 -> exactly one known continuation is authorized
      -> resume
    otherwise
      -> ABSTAIN/escalate
```

A verifier result not durably checkpointed does not become remembered success after restart. Ambiguous mid-transition crash state is never guessed through. Rollback/removal requires current ownership evidence, not byte similarity alone.

## Relationship to existing components

The Control Plane does not replace accepted components:

- `semantic-projection` remains the truthful Chat-facing boundary, not the workflow brain;
- `runtime/windows` remains Windows observation/authorization/actuation/verifier capability code;
- Windows `DesktopState` remains the accepted native Windows state representation;
- Browser structure-first semantic/vision routing remains capability-specific implementation;
- OpenAdapt Flow `ProgramGraph` remains the qualified procedural IR candidate;
- OpenAdapt Capture remains the qualified human/demo capture candidate;
- adapted SkillLibrary mechanics may support version/provenance/regression lifecycle;
- LFM2.5-VL remains bounded perception proposal only;
- Filesystem/Playwright remain focused capabilities.

`COMPUTER_USE_ARCHITECTURE.md` defines how these capability-specific pieces should converge on common long-horizon contracts without creating a generic agent gateway.

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
- silently turn a single demonstration into permanent trust;
- treat environmental UI/tool content as authority over user intent or policy.

## Stage mapping

Current release-critical order:

```text
26.2E real application E2E                         ACCEPTED
 -> 26.3A verified procedure runtime              ACCEPTED
 -> 26.3B Verification Kernel + Finish Gate       NEXT
 -> 26.3C WorkingState + typed recovery + LoopGuard
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

## Future Track P — Local Planner / Offline Autonomy

A local general planner is retained as future optional research, not current production architecture.

Earliest prerequisite: verified procedure-state data from Stage 26.3/26.4 and a measured reason ordinary ChatGPT is insufficient.

```text
P0 shadow planner
   -> sees structured state
   -> proposal only
   -> no authorization / no actuation

P1 bounded subtask planner
   -> explicitly scoped task classes
   -> deterministic Control Plane remains authoritative

P2 optional local general-planner mode
   -> only after measured parity/safety/resource evidence
   -> never silently replaces ChatGPT default
```

Even in P2, the planner remains above the same capability policy, verification, Finish Gate and safety boundaries.

## Terminology rule

Use these terms consistently:

- **general planner / planner:** open-ended strategy and task interpretation; currently ordinary ChatGPT only;
- **deterministic Control Plane:** execution state/policy/procedure/verification/recovery/finish machinery;
- **WorkingState:** structured long-horizon operational state, never private reasoning;
- **transition verifier:** verifies one expected action effect;
- **Finish Gate:** independently verifies task-level completion;
- **LoopGuard:** detects bounded repeated/no-effect/oscillating execution;
- **specialist model:** bounded perception or structured proposal; non-authorizing;
- **future local planner:** optional Track P research.

Do not use `Control Plane` as a synonym for `local planner`.

# Deterministic Local Control Plane

## Status

**AUTHORITATIVE ARCHITECTURAL DIRECTION.** Stage 26.3A physically accepted the first deterministic multi-transition procedure slice. Stage 26.3B generalizes verification/completion; Stage 26.3C follows with project-owned WorkingState and bounded recovery before broader computer-use authority is added.

This distinction remains mandatory:

- ordinary ChatGPT is the **only current general planner / strategist / task interpreter**;
- the local platform owns a **deterministic execution Control Plane**;
- the Control Plane is not a second general planner;
- a future local general planner remains optional Track P research and is **not part of the current release-critical path**;
- future Track M Agent Session / Delegation support adds a new capability/state family beneath the same Control Plane; it does not become a second planner or independent orchestration authority.

Canonical computer-use extension: `COMPUTER_USE_ARCHITECTURE.md`.

Long-horizon lineage/stagnation extension: `AVO_LONG_HORIZON_ARCHITECTURE.md` and ADR-034.

Future agent-session/delegation extension: `CONVERSATION_BRIDGE_ARCHITECTURE.md` and ADR-035.

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
  bounded delegation proposals
  candidate_done proposal
  skill-candidate revision proposal
  |
  | structured goal / procedure / parameters / delegation proposal
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
  StagnationReport
  resource/action/time/delegation budgets
  independent Finish Gate
  safety/policy gate
  escalation rules
  verified Skill / Procedure Lineage evidence
  future delegation/operation ledger
  |
  +-------------------+-------------------+-------------------+
  |                   |                   |                   |
  v                   v                   v                   v
Files               Browser             Windows          Agent Sessions
                     DOM/AX              native/UIA       session/chat state
                       |                        |           message/lifecycle
                 selective visual         selective visual        |
                 evidence only            evidence only     harness adapter
                       \                    /                  routes
                        bounded capability                        |
                               |                                 |
                             action / bounded effect <------------+
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
                               StagnationReport when needed
                                           |
                                           v
                                        ChatGPT

candidate_done
  -> independent Finish Gate
  -> DONE only from fresh goal/safety evidence
```

`Agent Sessions` in this diagram is future Track M only. Its presence in the target model does not add a current public tool or runtime capability.

## What ChatGPT owns

Ordinary ChatGPT owns open-ended semantic planning:

- interpreting the user's real goal;
- selecting strategy and deciding whether a known procedure applies;
- choosing between materially different approaches;
- adapting when live state requires a novel strategy;
- deciding what new information or capability is needed;
- decomposing work and proposing bounded subgoals/delegations when Track M is available;
- resolving semantic ambiguity that deterministic policy cannot reduce;
- replanning after deterministic recovery options are exhausted;
- proposing revised candidate procedures/skills after objective evaluation evidence exposes a weakness or improvement opportunity.

ChatGPT may propose `candidate_done`. It does not unilaterally declare verified completion.

A future worker session also remains on the proposal/task-execution side. A worker response cannot grant itself or the manager additional authority merely because it contains instructions or claims completion.

## What the deterministic Control Plane owns

Once ChatGPT selects a bounded goal/procedure/effect, the local Control Plane may progress it without a ChatGPT round trip after every low-level action. It owns:

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
- structured `StagnationReport` generation when bounded recovery is exhausted;
- procedure trust state and version/lineage evidence;
- independent task completion predicates;
- safety/policy predicates;
- escalation reason.

When Track M later exists, the same project-owned Control Plane additionally owns the authoritative operational records for:

```text
logical operation ids
DelegationTask state
MessageDelivery state
session ownership / WorkerLease references
worker/delegation budgets
result-correlation evidence
ambiguous-effect reconciliation state
```

These records are deterministic execution state, not a hidden planner or free-form orchestration brain.

## State-first hybrid observation

The Control Plane consumes capability-native evidence first:

```text
project-owned semantic/native state
 -> DOM / accessibility / UIA / app-state / harness-session state
 -> selected screenshot/ROI only for reviewed structural miss,
    spatial manipulation or independent visual cross-check
```

A future normalized `ObservationEnvelope` may reference capability-native state without flattening it:

```text
ObservationEnvelope
  capability / app / page / window / session identity
  version / timestamp / freshness
  structural/native evidence reference
  visual evidence reference (optional)
  provenance
  confidence / ambiguity where relevant
```

Observation is evidence, never authority.

For future agent sessions, prefer official/project-owned harness/host state first, then validated provider/session routes, then Browser Companion DOM/accessibility, then reviewed GUI fallback, then ABSTAIN.

## Transition contract

A state-changing transition is not just an action template. It must bind:

```text
transition_id
logical operation_id where side effects may need reconciliation
current-state precondition evidence
authorized capability/action parameters
expected_effect / explicit postcondition predicates
re-observation scope
verification policy
recovery/reconciliation policy
budget impact
```

Normal progression:

```text
ChatGPT selects bounded operation/procedure P
 -> load exact operation/procedure/trust state
 -> observe current state
 -> match exactly one permitted transition
 -> bind ExpectedEffect
 -> authorize current capability/action
 -> execute one bounded action
 -> re-observe relevant state
 -> verify actual state against ExpectedEffect
 -> PASS: checkpoint + advance
 -> FAIL/UNKNOWN: typed recovery/reconciliation or ABSTAIN/escalate
```

`delivery != success` remains a non-negotiable invariant.

For future Track M this means, for example:

```text
message transport acknowledgement != verified message delivery
verified message delivery != worker turn started
worker turn started != delegation complete
latest worker response != result of this delegation unless correlation is proven
session-create timeout != permission to create another session blindly
```

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

### Stage 26.3B foundation

The shared internal verification foundation implements:

```text
ObservationRef
  capability + subject + stream_id + monotonic sequence + fingerprint
ObservationSnapshot
  bounded immutable normalized evidence
ExpectedEffect
  bounded equals/present/absent predicates
verification
  PASS | FAIL | UNKNOWN
```

Freshness requires the same observation stream/capability/subject and a strictly higher sequence. Stale, mismatched-stream, ambiguous or incomplete required evidence yields `UNKNOWN` rather than guessed success.

Normalized evidence is bounded plain data and detached from caller mutation; arbitrary custom comparison/executable objects are not admitted into the verifier.

Future entity-creation effects may use an operation-scoped subject such as:

```text
capability = agent_sessions
subject = session-create:<operation_id>
```

so BEFORE/AFTER observations remain on one verifiable stream even when the created session id does not exist before the action. The Verification Kernel itself should not gain vendor-specific thread/project logic.

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
required artifact/application/browser/session state
required delegation/result-correlation state where applicable
unresolved ambiguity/confirmation state
safety/policy predicates
```

Completion checks bind to one explicit `evidence_batch_id`. Goal/safety/constraint/freshness results used for one decision must be observation-bound and belong to that same evidence collection. Unbound or old/mixed-batch PASS receipts become `UNKNOWN` for completion.

A file merely existing is not sufficient when content/identity/structure matters. A browser click succeeding is not sufficient when server-side or DOM state defines completion. A produced artifact is not sufficient when required semantic correctness remains unverified. A worker saying "done" is likewise not sufficient when the user's task requires independently observable computer/artifact/application state.

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
retry/recovery/reconciliation history
resource/action/time budgets
active capability/grant references
procedure id/version/node + optional external checkpoint reference
```

Stage 26.3C must remain useful without Track M, but should avoid hard-coding `one task -> one procedure -> one executor`. Future-compatible optional references should allow:

```text
subgoal
  subgoal_id
  status
  actor_ref                   optional
  delegation_ref              optional
  execution_environment_ref   optional
  budget_ref                  optional
  evidence_refs

delegations[]                 optional/future
capability_grant_refs[]
```

`actor_ref` is a planner-neutral reference. It may later identify the current manager, a procedure runtime, an external worker session or another admitted actor without making that actor an authority source.

WorkingState must not contain hidden model chain-of-thought.

Selected ROI visual evidence may be referenced when operationally useful, subject to capture privacy/retention policy. Episodic memory may retrieve verified procedures/trajectories or selected historical session evidence, but historical experience remains non-authorizing and current state outranks it.

AVO-style persistent-memory lessons are adopted only through this structured boundary: durable evaluation evidence, compact failure summaries, lineage/version metadata and verified progress may survive context boundaries; private hidden reasoning does not become stored execution state.

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

Future Track M may add narrower classes such as:

```text
session_unavailable
delivery_refused
delivery_held
result_correlation_ambiguous
operation_outcome_unknown
worker_stalled
delegation_duplicate_suspected
ownership_unproven
```

Capabilities may define narrower subtypes, but every recoverable failure must map to a reviewed bounded transition, reconciliation step or escalation.

Default recovery ladder:

```text
re-observe
 -> refresh/re-resolve target
 -> reconcile ambiguous logical operation when required
 -> retry only when new evidence proves retry safety
 -> alternate admitted modality/capability
 -> predeclared local recovery branch
 -> ChatGPT replan / user clarification / ABSTAIN
```

No recovery step grants broader authority than the original task/procedure/delegation and current capability policy.

### Ambiguous side-effect invariant

A mutating timeout/error must be classified rather than treated as ordinary failure:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

For `OUTCOME_UNKNOWN`, deterministic reconciliation by stable logical `operation_id` precedes retry. If authoritative evidence cannot establish whether the original effect occurred, remain `UNKNOWN` and stop/escalate rather than risk a duplicate effect.

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

Future Track M extends, rather than replaces, this state with orchestration/delegation dimensions such as:

```text
worker_count
spawn_depth
children_per_worker
active_delegations
unresolved_worker_count
messages_per_worker
cross_session_message_budget
session_creation_budget
duplicate_delegation_fingerprints
total delegated action/time/resource cost
```

A duplicate delegation fingerprint may include worker session, subgoal, HandoffPack hash and expected-result contract. An ambiguous acknowledgement must enter reconciliation before an equivalent delegation is sent again.

The first multi-worker topology should default to `max_spawn_depth = 1`. Recursive worker spawning is a later separately admitted capability, not implicit inheritance from the manager.

## StagnationReport

When LoopGuard concludes that deterministic recovery has plateaued, escalation should carry enough evidence for the general planner to change strategy without replaying the entire raw history.

Target report:

```text
StagnationReport
  task_id / subgoal_id
  actor/delegation identity where applicable
  verified progress vector
  repeated state/action/delegation fingerprints
  no-effect / retry / oscillation counters
  attempted typed recovery/reconciliation classes
  fresh evidence references
  exhausted + remaining budgets
  admitted alternatives already tried
  unresolved failure class / ambiguity
```

Normal boundary:

```text
LoopGuard detects stagnation
 -> prevent further equivalent effects
 -> emit StagnationReport
 -> ordinary ChatGPT decides novel strategy
 -> new proposal returns through normal authorization
```

The Control Plane may summarize deterministic operational evidence. It must not invent an unconstrained new strategy and must not persist private model chain-of-thought in the report.

## Procedure / Skill Lineage

Reusable procedures should be treated as versioned evidence-backed candidates rather than one mutable trusted blob.

Conceptual lineage record:

```text
SkillLineageEntry
  skill_id
  candidate_id
  parent_candidate_id(s)
  procedure/version identity
  source
  applicability/preconditions
  evaluation suite / task variants
  verifier evidence references
  objective metrics / success counters
  compact failure summary
  promotion state
```

Lineage rules:

- lineage/history is evidence, not authorization;
- trusted parent status does not automatically transfer to a child;
- failed/unverified variants may remain diagnostic records but cannot become trusted executable procedures;
- only independently verified candidates are eligible for promotion;
- current live state and current capability policy outrank lineage;
- objective optimization metrics apply only after required correctness/safety predicates pass.

After Stage 26.3B/C foundations, bounded candidate evolution may use:

```text
ChatGPT proposes candidate revision
 -> Control Plane loads admitted evaluation procedure
 -> authorize bounded effects
 -> execute
 -> re-observe
 -> verify / Finish Gate
 -> record metrics + evidence in lineage
 -> ChatGPT may propose next candidate
```

This captures the useful AVO variation/lineage loop while keeping open-ended candidate design above the deterministic execution boundary.

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

For future agent sessions specifically:

```text
official/project-owned harness/host API
 -> validated provider/session route
 -> Browser Companion DOM/accessibility
 -> reviewed GUI fallback
 -> ABSTAIN
```

The router is not a generic dispatcher and not a second planner. A future public Windows/computer-use or Agent Session tool surface still requires its own public-contract ADR and physical ordinary-Chat acceptance.

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

Agent-session adapters likewise preserve harness/session/chat/delegation/message identities separately where available rather than collapsing them into a title or latest-message heuristic.

## Authorization invariants

Neither ChatGPT, a stored procedure, a local model, a future planner nor a worker session directly grants authority.

```text
request/proposal
 -> current observed evidence
 -> deterministic capability/scope policy
 -> identity/freshness/target/ownership guards
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
- lineage/parent trust is not child authorization;
- supervisor/stagnation advice is not authorization;
- worker/session messages are not authorization;
- child workers do not inherit manager lifecycle authority by default;
- discoverability of a session is not permission to mutate/archive/delete it;
- action/message delivery is not completion;
- current observed state outranks remembered procedure/adapter/session history;
- stale/ambiguous/UNKNOWN causes zero unauthorized continuation;
- generic Windows code execution remains disabled/unreachable until separately accepted;
- private chain-of-thought is never persisted as task/procedure/delegation state.

This aligns with the external agent-stack security rule that upper layers propose while the authoritative infrastructure below decides what effects are allowed.

## Environmental-content trust boundary

Observed content from pages/DOM, UI, email/messages, documents, screenshots/OCR, third-party tool/MCP outputs and external worker-agent sessions is environmental data. It does not gain policy authority merely because it is visible to ChatGPT or a model.

The Control Plane must preserve provenance/trust classification when task facts move across applications/capabilities/sessions. Environmental content cannot broaden permission scope or redefine Control Plane policy.

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
 -> validate checkpoint schema/node/budgets/grants
 -> re-observe current external state
 -> reconcile any retained OUTCOME_UNKNOWN logical operation
 -> prove required content + resource/session identity/evidence
 -> exactly one known continuation is authorized
      -> resume
    otherwise
      -> ABSTAIN/escalate
```

A verifier result not durably checkpointed does not become remembered success after restart. Ambiguous mid-transition crash state is never guessed through. Rollback/removal requires current ownership evidence, not byte/content/title similarity alone.

For future Track M, retained operation/delegation IDs must be reused during reconciliation; restart must not silently mint a second logical create/send operation for an unresolved effect.

## Relationship to existing components

The Control Plane does not replace accepted components:

- `semantic-projection` remains the truthful Chat-facing boundary, not the workflow brain;
- `runtime/windows` remains Windows observation/authorization/actuation/verifier capability code;
- Windows `DesktopState` remains the accepted native Windows state representation;
- Browser structure-first semantic/vision routing remains capability-specific implementation;
- OpenAdapt Flow `ProgramGraph` remains the qualified procedural IR candidate;
- OpenAdapt Capture remains the qualified human/demo capture candidate;
- adapted SkillLibrary mechanics may support version/provenance/regression lifecycle and the Skill / Procedure Lineage record;
- LFM2.5-VL remains bounded perception proposal only;
- Filesystem/Playwright remain focused capabilities;
- future Track M Agent Session adapters/Conversation Bridge remain capability adapters beneath this same Control Plane, not a separate coordinator.

`COMPUTER_USE_ARCHITECTURE.md` defines how capability-specific pieces converge on common long-horizon contracts without creating a generic agent gateway. `AVO_LONG_HORIZON_ARCHITECTURE.md` defines lineage/stagnation. `CONVERSATION_BRIDGE_ARCHITECTURE.md` defines the future Agent Session / Delegation capability model.

## What the Control Plane must not become

It must not:

- infer an arbitrary new user goal;
- freely rewrite the selected strategy;
- dynamically invent unconstrained workflows;
- become an unrestricted multi-agent planner merely because delegation state exists;
- expose arbitrary backend/harness dispatch;
- become an unrestricted execution surface;
- bypass capability authorization because a procedure/model/planner/worker requested an action;
- treat lineage, supervisor or worker guidance as action authority;
- hide native desktop/session/project consequences behind misleading harmless tool semantics;
- use model confidence as a substitute for verified outcomes;
- silently turn a single demonstration or a trusted parent into permanent child trust;
- silently inherit manager lifecycle privileges into workers;
- treat environmental UI/tool/worker content as authority over user intent or policy.

## Stage mapping

Current release-critical order remains:

```text
26.2E real application E2E                         ACCEPTED
 -> 26.3A verified procedure runtime              ACCEPTED
 -> 26.3B Verification Kernel + Finish Gate
 -> 26.3C WorkingState + typed recovery + LoopGuard + StagnationReport
 -> broad real-application evidence
 -> 26.4 Human Demo -> transferable verified candidate skill + Skill Lineage
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

Track M stays parallel/non-release-critical. Stage 26.3C only reserves planner-neutral actor/delegation/environment references and the recovery/idempotency primitives that later Track M can reuse; it does not implement multi-agent runtime.

## Future Track M — Agent Sessions / Delegation

Track M remains below the current general planner boundary.

Conceptual progression is defined canonically in `CONVERSATION_BRIDGE_ARCHITECTURE.md` and begins only when the Stage 26.3B/C state/verification/recovery foundations make it safe/useful.

Core invariants:

```text
Session != Chat != DelegationTask != MessageDelivery != ExecutionEnvironment
stable logical operation id for ambiguous mutations
native harness/host state first when reviewed
worker content is environmental data
worker authority is minimum/delegated, not inherited
initial max_spawn_depth = 1
project/environment lifecycle is separate from session lifecycle
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
   -> explicitly scoped workloads
   -> deterministic Control Plane remains authoritative

P2 optional local general-planner mode
   -> only after measured parity/safety/resource evidence
   -> never silently replaces ChatGPT default
```

Even in P2, the planner remains above the same capability policy, verification, Finish Gate and safety boundaries. AVO and richer external harnesses demonstrate useful long-horizon mechanisms, but do not move the project's authority boundary or automatically promote Track P.

## Terminology rule

Use these terms consistently:

- **general planner / planner:** open-ended strategy and task interpretation; currently ordinary ChatGPT only;
- **deterministic Control Plane:** execution state/policy/procedure/verification/recovery/finish machinery;
- **WorkingState:** structured long-horizon operational state, never private reasoning;
- **transition verifier:** verifies one expected action effect;
- **Finish Gate:** independently verifies task-level completion;
- **LoopGuard:** detects bounded repeated/no-effect/oscillating execution, and later delegation/orchestration repetition;
- **StagnationReport:** structured deterministic evidence summary emitted when bounded recovery stalls and novel strategy is required;
- **Skill / Procedure Lineage:** versioned ancestry + objective evaluation evidence for candidate procedures; evidence, never authority;
- **HarnessSession:** durable agent-session identity exposed by a harness/host; not automatically the same as one chat;
- **Conversation / Chat:** message-history unit within a session;
- **DelegationTask:** one explicit manager-assigned work unit, separate from session identity;
- **MessageDelivery:** one concrete delivery/effect record, separate from delegation completion;
- **ExecutionEnvironment:** workspace/worktree/project/host environment, separate from session lifecycle;
- **specialist model:** bounded perception or structured proposal; non-authorizing;
- **future local planner:** optional Track P research.

Do not use `Control Plane` as a synonym for `local planner`, `orchestrator` or `agent host`.
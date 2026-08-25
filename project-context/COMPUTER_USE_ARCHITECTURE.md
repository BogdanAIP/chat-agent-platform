# Computer-Use Architecture

Status: **AUTHORITATIVE ARCHITECTURAL DIRECTION / IMPLEMENTATION STAGED**.

This document promotes the 2026-08-24 Stage 26.3A ordinary-Chat research run into project architecture. It does not make external papers or benchmarks authoritative over repository evidence. Instead, it records which externally observed mechanisms were independently checked and which project decisions follow from them.

The source research artifact was produced during physical Stage 26.3A session:

```text
STAGE26_3A_CHAT_E2E_E4F49B4AD4CB4DABA07A9F01A5575255
```

The accepted project formula is:

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> capability-aware bounded action
 -> post-action re-observation
 -> explicit transition verification
 -> typed bounded recovery / LoopGuard
 -> structured active working state
 -> independent task finish gate
 -> separate safety gate
 -> Control Plane authorization remains authoritative
```

This extends the existing architecture. It does not replace the accepted six-tool semantic surface, the Windows `DesktopState`/UIA/VLM stack, or the deterministic Control Plane.

---

# 1. Evidence review

The following claims from the Stage 26.3A research were independently checked against the public paper/project sources available on 2026-08-24.

## ComponentBench

Sources:

- https://arxiv.org/abs/2608.18307
- https://www.componentbench.com/

Verified:

- 97 canonical UI component types and 2,910 programmatically verified tasks;
- human reference trajectories/efficiency baselines;
- strong dependence on observation/action interface;
- component families such as drag/drop, precision controls and editors remain diagnostic failure classes.

Project consequence: component-level diagnostics should be a regression layer between atomic grounding tests and long-horizon E2E. Observation/action interface is an architectural variable, not merely a model prompt choice.

## OSWorld 2.0

Source:

- https://osworld-v2.xlang.ai/

Verified:

- 108 long-horizon workflows;
- median skilled-human operation time around 1.6 hours;
- hundreds of agent actions/tool calls;
- performance degrades sharply as task horizon increases;
- representative failures include stale internal state, missed dynamic updates, hidden-state recovery failures, constraint drift and skipped verification.

Project consequence: improving grounding alone is insufficient. Long tasks require structured state, freshness/provenance, checkpoints, progress tracking, bounded search and objective completion predicates.

## OSWorld-G / Jedi

Source:

- https://osworld-grounding.github.io/

Verified:

- OSWorld-G contains 564 annotated grounding samples;
- categories include text matching, element recognition, layout understanding and fine-grained manipulation;
- Jedi contains 4M synthesized grounding examples.

Project consequence: grounding should expose target identity/category/confidence/ambiguity rather than only coordinates. Spatial manipulation remains a specialist capability below policy/authorization.

## UI-Mate / OSWorkerBench

Sources:

- https://arxiv.org/abs/2608.15930
- https://ui-mate.github.io/
- https://github.com/Tencent/UI-Mate

Verified:

- a closed-loop task/environment/rollout/verifier training stack;
- multimodal demonstrations are converted into subtask-level workflows instead of rigid action replay;
- live UI remains authoritative and the agent re-plans when the target diverges from the demonstration;
- OSWorkerBench contains 100 long-horizon office tasks across 41 applications with dedicated demonstration settings.

Project consequence: Stage 26.4 must compile demonstrations into advisory subgoals + verifiable completion criteria, not macros. Demonstrated low-level actions and historical coordinates never outrank current state.

## StateAct

Source:

- https://arxiv.org/abs/2607.22798

Verified:

- the main agent operates on program state while GUI interaction is delegated only where required;
- an independent finish gate checks structural output failures such as missing/unsaved/wrong-path artifacts;
- a code-only variant underperforms the hybrid configuration, so state access does not eliminate GUI needs.

Project consequence: preserve the idea of state grounding without copying unrestricted code/program-state authority. Project-owned bounded semantic adapters remain the state channel; GUI remains selective fallback; task completion needs a gate distinct from action delivery and planner confidence.

## MementoGUI

Source:

- https://arxiv.org/abs/2605.18652

Verified:

- long-horizon GUI control is formulated as active memory control;
- working memory selectively preserves task-relevant textual summaries plus ROI-level visual evidence;
- episodic memory retrieves reusable verified trajectories through learned selection.

Project consequence: do not replay unbounded screenshot/history context. Start with deterministic structured WorkingState and verified episodic procedure evidence; learned memory selection is deferred until the project has enough verified traces to justify it.

## HiViG

Source:

- https://arxiv.org/abs/2606.11078

Verified:

- macro-action history summarizes completed achievements;
- a visually grounded critic checks proposed raw coordinates against the current screenshot before execution;
- the mechanism is specifically useful for catching execution/grounding errors.

Project consequence: pre-execution visual critique is useful for uncertain coordinate, destructive or otherwise consequential GUI actions, not for every cheap semantic read.

## WebArena

Source:

- https://arxiv.org/abs/2307.13854

Verified:

- realistic functional websites and long-horizon web tasks;
- evaluation focuses on functional correctness of the resulting state.

Project consequence: browser acceptance should prefer final predicates/system-of-record state over action-sequence similarity.

## BrowserGym ecosystem

Source:

- https://arxiv.org/abs/2412.05467

Verified:

- unified observation/action spaces and a common harness across multiple web benchmarks.

Project consequence: benchmark-specific adapters belong below a normalized project evaluation protocol. Benchmark APIs must not become the product-facing agent architecture.

## ENVS / OSWorld-Noisy

Source:

- https://arxiv.org/abs/2606.22948

Verified:

- training-time search branches behaviorally distinct GUI actions in live environments and verifies successful leaves;
- OSWorld-Noisy evaluates recoverable interruptions such as refocus/dismiss/wait/recover.

Project consequence: verified branching is useful for training/evaluation, but production must use bounded known alternatives and a recovery state machine rather than broad speculative side effects.

## Hybrid GUI-MCP

Sources:

- https://arxiv.org/abs/2608.03327
- https://github.com/redai-infra/hybrid-routing-agent

Verified:

- the same MCP tool availability can help one policy and hurt another;
- tool selection/integration semantics are a bottleneck;
- a successful tool result can make subsequent screenshots redundant, and context policy materially affects cost/performance.

Project consequence: capability availability is not a routing decision. A project-owned router must choose modalities by explicit preconditions/evidence and avoid redundant visual context after a verified semantic result.

## MobileWorldSafety

Source:

- https://arxiv.org/abs/2608.17659

Verified:

- 142 risk tasks across real Android applications;
- environmental injection uses untrusted application/tool content to induce unsafe behavior;
- final-state risk indicators and a two-stage evaluator distinguish safety failure from capability failure.

Project consequence: UI/DOM/email/page/tool-output content is **environmental data, not authority**. Task-success verification and safety/policy verification are separate concerns.

---

# 2. Decisions promoted into the architecture

## 2.1 State-first hybrid observation

The normal preference order is:

```text
project-owned semantic/native state
 -> structural DOM/AX/UIA/app adapter evidence
 -> selected screenshot/ROI evidence only when needed
```

Pixels are not forbidden. They are selective evidence for spatial, visual-only, structure-missing or cross-check cases.

The Windows `DesktopState` remains the accepted Windows state representation. Future cross-capability integration should introduce a small normalized envelope rather than replacing capability-native state:

```text
ObservationEnvelope
  capability / app / page / window identity
  observation version + timestamp/freshness
  structural evidence reference
  selected visual evidence reference (optional)
  provenance / source
  confidence / ambiguity where applicable
```

This is a target schema, not yet a public Chat-facing tool schema.

## 2.2 One mutating transition = bounded action + expected effect + re-observation + verification

Every state-changing transition admitted into the deterministic Control Plane must define:

```text
precondition/current-state evidence
expected_effect / postcondition predicate(s)
authorized bounded action
re-observation scope
verification result = PASS | FAIL | UNKNOWN
```

Delivery receipts remain evidence of delivery only. They never imply success.

The active Stage 26.3B foundation now gives this contract an internal deterministic representation: stream-bound `ObservationRef`, immutable bounded normalized `ObservationSnapshot`, declarative `ExpectedEffect` predicates and explicit `PASS | FAIL | UNKNOWN` results. This is foundation code only; capability adapters and production-procedure migration remain staged.

## 2.3 Independent finish gate

Transition verification and task completion are different layers.

The planner may propose:

```text
candidate_done
```

Only an independent completion gate may produce:

```text
DONE
```

The finish gate evaluates explicit goal predicates against fresh evidence and must not rely solely on the planner's self-assessment or the historical action sequence.

Minimum completion dimensions:

```text
goal predicates satisfied
constraint consistency
required freshness/reconciliation completed
no unresolved required ambiguity/confirmation
required safety predicates satisfied
```

The active Stage 26.3B foundation requires completion verification receipts to be tied to concrete observations and to one explicit `evidence_batch_id`; unbound or mixed/older batch PASS receipts become `UNKNOWN` rather than being composed into `DONE`.

For file tasks completion may require path + existence + identity/content/hash/structure. For browser/app tasks it may require URL/document/server-side/app state. Complex procedures may require a conjunction of checkpoint predicates.

## 2.4 Structured WorkingState, not raw history replay

Long-horizon state should preserve operational facts, not hidden reasoning.

Target WorkingState fields:

```text
user constraints
current subgoals / progress
verified completed achievements
authoritative facts + provenance + freshness
open questions / ambiguities
current observation/evidence references
expected vs observed state deltas
retry/recovery history
resource/action/time budgets
```

ROI visual evidence may be retained only when operationally useful and under the same privacy/retention rules as other capture data.

Episodic memory may contain verified trajectories/procedures with applicability evidence. A raw successful trajectory is not automatically a trusted reusable skill.

## 2.5 Typed recovery + LoopGuard

Recovery must be explicit state, not an unconstrained `try again` loop.

Initial common failure vocabulary:

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

Capability-specific failures may extend this vocabulary, but must map to a bounded recovery or escalation decision.

Default recovery ladder:

```text
re-observe
 -> refresh/re-resolve target
 -> retry only when new evidence justifies it
 -> alternate admitted modality/capability
 -> predeclared local recovery branch
 -> ChatGPT replan / user clarification / ABSTAIN
```

LoopGuard target evidence:

```text
fingerprint(relevant_state, intended_subgoal, action_signature)
no_effect_count
action-family retry count
oscillation window (A -> B -> A -> B)
subgoal budget
global task budget
recovery escalation level
verified progress vector
```

Repeating an identical state/action fingerprint without new evidence or progress must not continue indefinitely.

## 2.6 Capability-aware routing

Backend/tool availability is not sufficient reason to choose it.

Routing decisions must use capability/precondition evidence:

```text
exact safe semantic/native operation available
 -> use it

structure unavailable/insufficient for a reviewed case
 -> request selected visual/GUI grounding evidence

uncertain/ambiguous/high-consequence result
 -> additional verification or ABSTAIN
```

The router must remain deterministic/policy-bounded for admitted cases. It must not become another general planner or generic backend dispatcher.

## 2.7 Grounding returns identity evidence, not only coordinates

A common future grounding proposal should be able to carry:

```text
semantic target identity
role/name/state where available
bounding region / coordinates when required
source = structural | visual | hybrid
observation/frame binding
confidence
ambiguity evidence
```

Existing Browser and Windows grounders remain capability-specific implementations. Do not build a generic service merely for architectural symmetry before a measured integration need exists.

## 2.8 Environmental content is untrusted data

Text or instructions observed inside:

```text
web pages / DOM
email/messages
application UI
files/documents being processed
third-party MCP/tool output
screenshots/OCR
```

must not be allowed to redefine user intent, Control Plane policy, permission scope or safety rules merely because the planner can read them.

Task-success verification and safety verification are separate:

```text
task verifier: did the requested outcome occur?
safety/policy gate: was the transition allowed and did it avoid prohibited consequence?
```

A task can be capability-successful and safety-failed; architecture and evaluation must preserve that distinction.

---

# 3. What is deliberately NOT adopted

The research does **not** authorize the following changes:

- screenshot-only computer use as the normal control loop;
- unrestricted code/program-state access from StateAct;
- exposing raw UIA/DOM/backend graphs as hundreds of ChatGPT tools;
- generic `tool_invoke`, backend dispatch or unrestricted execution surfaces;
- blind absolute-coordinate replay from demonstrations;
- replaying every screenshot/action in long-horizon context;
- learned memory/router/critic components before project traces demonstrate a measured need;
- mass speculative environment branching in production;
- a critic/model verdict as authorization or final task completion;
- exact future Windows public tool names without a separate public-contract ADR and physical ordinary-Chat acceptance.

The current six-tool public surface remains accepted until a later reviewed capability contract changes it.

---

# 4. Stage mapping

## Stage 26.3B — Verification Kernel + Finish Gate — ACTIVE

Current foundation:

```text
ObservationRef / ObservationSnapshot
same-stream/capability/subject freshness
bounded immutable normalized evidence
ExpectedEffect / declarative predicates
PASS | FAIL | UNKNOWN
evidence_batch_id-bound Finish Gate
separate task completion and safety/policy evidence
```

Remaining Stage 26.3B work includes truthful file/browser/Windows observation adapters, migration of accepted procedure checks onto the kernel, cross-capability completion predicates where needed and physical acceptance once production procedure/action behavior changes.

Model-assisted ambiguous judging, if ever added, remains non-authorizing evidence and must not replace system/native predicates when available.

## Stage 26.3C — WorkingState + Typed Recovery + LoopGuard

Implement:

```text
structured WorkingState v1
facts + provenance + freshness
progress/checkpoint vector
failure taxonomy
no-effect / repeated-state detection
oscillation detection
retry/action/time/resource budgets
recovery escalation state
```

This generalizes the bounded retry/checkpoint mechanics already proved by Stage 26.3A.

## Stage 26.4 — Demonstration -> Transferable Verified Candidate Skill

Compile demonstrations into:

```text
subtask goals
verifiable completion criteria
advisory action/target evidence
applicability/precondition evidence
```

At replay, live state is authoritative. Historical coordinates/action sequences are not executable authority. One demonstration remains at most CANDIDATE until replay/regression/variant evidence justifies promotion.

## Stage 26.5 — Hybrid Computer-Use Integration

After verifier/recovery/memory foundations are available, integrate Browser and Windows under common control-loop contracts:

```text
normalized ObservationEnvelope
capability-aware routing
common grounding proposal fields
semantic/native first
selective visual fallback
component-level regression diagnostics
cross-app state/provenance handling
```

Stage 26.5 does not automatically add public tools. A truthful Windows/computer-use Chat-facing surface still requires the separate ADR/schema/security/physical-acceptance gate already required by ADR-024.

---

# 5. Evaluation direction

External benchmarks are evidence sources and optional evaluation harnesses, not automatic release gates.

The project should build a layered evaluation strategy:

```text
component/primitive diagnostics
 -> capability integration tests
 -> recovery/noisy-state fixtures
 -> long-horizon verified procedures
 -> selected external benchmark runs when reproducible and useful
```

Useful references:

- ComponentBench-style component diagnostics for route/interaction failure families;
- BrowserGym/WebArena-style normalized browser evaluation and functional correctness;
- OSWorld 2.0-style long-horizon state/freshness/hidden-state cases;
- OSWorld-Noisy-style interruption/recovery cases;
- MobileWorldSafety-style environmental injection and final-state safety predicates.

Benchmark-specific optimizations must not leak into production policy unless they generalize to a project-owned invariant.

---

# 6. Implementation order

```text
26.3A verified procedure runtime                         ACCEPTED
 -> 26.3B Verification Kernel + independent Finish Gate ACTIVE
 -> 26.3C WorkingState + typed recovery + LoopGuard
 -> 26.4 demonstration -> verified candidate skill
 -> 26.5 hybrid computer-use integration
 -> 27 distribution/maintenance
 -> 28 clean-user E2E / stable release
```

This order intentionally solves long-horizon correctness before broadening raw GUI authority.

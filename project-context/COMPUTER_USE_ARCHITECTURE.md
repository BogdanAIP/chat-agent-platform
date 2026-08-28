# Computer-Use Architecture

Status: **AUTHORITATIVE ARCHITECTURAL DIRECTION / IMPLEMENTATION STAGED**.

This document owns the durable state-first computer-use contract. Detailed dated research evidence remains useful reference but does not own current stage status or release order.

External research inputs reviewed for this direction include ComponentBench, OSWorld 2.0, OSWorld-G/Jedi, UI-Mate/OSWorkerBench, StateAct, MementoGUI, HiViG, WebArena, BrowserGym, ENVS/OSWorld-Noisy, Hybrid GUI-MCP and MobileWorldSafety. Their benchmark numbers are evidence inputs, not project release gates.

## Accepted formula

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> capability-aware bounded action
 -> fresh post-action re-observation
 -> explicit ExpectedEffect verification
 -> reconcile ambiguous mutating outcome before retry
 -> typed bounded recovery / LoopGuard / budgets
 -> structured WorkingState
 -> independent Finish Gate
 -> separate safety/policy gate
 -> Control Plane authorization remains authoritative
```

This extends the accepted six-tool/product architecture; it does not authorize screenshot-only control, raw code execution, generic backend dispatch or a second local planner.

## Evidence lessons promoted into architecture

### State/interface quality matters

External GUI research repeatedly shows that observation/action representation materially changes performance. Project consequence:

- prefer semantic/native structure when reliable;
- preserve target/subject/frame identity rather than only coordinates;
- keep component-level diagnostics between primitive tests and long-horizon E2E;
- final functional state matters more than action-sequence similarity.

### Long horizon needs explicit state and finish criteria

Long tasks fail through stale state, hidden-state changes, constraint drift, missed updates and premature completion.

Project consequence:

- use structured WorkingState, provenance/freshness and checkpoints;
- treat planner `candidate_done` as proposal only;
- require independent Finish Gate evidence;
- bound recovery and repetition.

### Demonstrations are advisory, not macros

Demonstration research supports subgoal/workflow transfer with live-state replanning rather than rigid action replay.

Project consequence:

- Stage 26.4 compiles demos into candidate subgoals/verifiers/applicability evidence;
- live state outranks historical coordinates/actions;
- one successful trajectory is at most a candidate skill.

### Visual evidence is selective

Vision is useful for structural misses, spatial manipulation and independent cross-checks. It remains evidence, not authority.

A model/critic may reject or propose an uncertain target, but deterministic identity/freshness/authorization and Verification Kernel rules remain authoritative.

### Fresh visual post-action verification

A structurally correct state is not always a visually correct user result. When an `ExpectedEffect`, task predicate or acceptance condition includes a rendered/spatial property that semantic/native evidence cannot prove, verification must include **fresh post-action visual evidence** bound to the relevant post-action observation/frame.

Representative visual predicates include:

```text
visible / actually rendered
not clipped outside viewport/window
not occluded by another control/dialog/overlay
not overlapping an invalid region
relative placement / alignment
rendered size where task-relevant
visual style/state where task-relevant
```

Rules:

- DOM/accessibility/UIA/native state may prove structural predicates, but it must not by itself produce `PASS` for a required visual predicate it cannot observe;
- if fresh visual evidence conclusively contradicts a required visual postcondition, verification is `FAIL`;
- if required visual evidence is unavailable, stale, ambiguous or cannot distinguish the required condition, verification is `UNKNOWN` rather than guessed `PASS`;
- structural/native success plus a visual contradiction cannot be collapsed into overall `PASS`;
- visual evidence supplements verification evidence and never grants action authority, overrides identity/freshness, or converts a verifier `FAIL`/`UNKNOWN` into `PASS`;
- this is **not** a screenshot-after-every-action requirement. Fresh visual evidence is required only when the claimed outcome itself is visual/spatial or structural evidence is insufficient for the relevant predicate.

Example:

```text
DOM/UIA:
  control exists
  text is correct
  enabled = true

fresh screenshot:
  control is clipped outside the visible window

result:
  visual postcondition is not PASS
```

### Environmental content is untrusted data

Content from UI/DOM/messages/files/screenshots/tool output is task data with respect to user intent and policy.

Task-success and safety/policy evaluation remain separate.

## State-first hybrid observation

Normal preference:

```text
project-owned semantic/native/app state
 -> DOM / accessibility / UIA / native app evidence
 -> selected screenshot/ROI evidence when needed
```

Pixels are not forbidden; they are selective evidence.

Capability-native state remains authoritative for its scope:

- Browser: page/DOM/accessibility/document/session state;
- Windows: `DesktopState`, UIA/native process/window/frame evidence;
- Files: rooted path/object/content/identity evidence;
- future apps/sessions: their own system-of-record state.

A future normalized envelope may reference native observations:

```text
ObservationEnvelope
  capability / app / page / window / session identity
  observation version / freshness
  structural/native evidence ref
  selected visual evidence ref (optional)
  provenance / source
  confidence / ambiguity where relevant
```

This is an internal target concept, not a current public tool schema.

## One mutation = one bounded action + expected effect + fresh verification

Every consequence-bearing transition admitted by the Control Plane must define:

```text
current-state precondition evidence
stable logical operation identity
ExpectedEffect / postcondition predicates
authorized bounded action
fresh re-observation scope
verification = PASS | FAIL | UNKNOWN
recovery / reconciliation policy
budget impact
```

Delivery receipts prove delivery only.

Stage 26.3B accepted the shared Verification Kernel/Finish Gate foundation for recorded representative file/Browser/Windows scope. Capability-specific adapters continue to use that common contract without pretending every future capability is already accepted.

## Independent Finish Gate

```text
planner/procedure/worker -> candidate_done
 -> fresh task-level evidence batch
 -> independent Finish Gate
 -> DONE | NOT_DONE | UNKNOWN
```

Minimum dimensions may include:

```text
goal predicates
user constraints
freshness / required reconciliation
artifact/browser/application final state
unresolved required ambiguity/confirmation
safety/policy predicates
```

Transition PASS remains different from task DONE.

## WorkingState

Stage 26.3C L1 WorkingState/reconciliation/budgets/LoopGuard foundation is accepted through #124.

WorkingState may preserve:

```text
user constraints
subgoals / verified progress
facts + provenance + freshness
open ambiguities
current evidence refs
expected/observed deltas
stable operation / attempt / reconciliation state
recovery history
task / procedure / strategy budgets
```

It never stores private chain-of-thought.

The L1 foundation does not automatically prove restart-safe effects for every production consumer; path-specific integration still needs acceptance.

## Typed recovery / reconciliation

Recovery is explicit state, not unconstrained retry.

```text
fresh re-observe
 -> classify failure/outcome
 -> reconcile ambiguous logical operation before retry
 -> re-resolve target
 -> retry only when current evidence permits it
 -> alternate already-admitted modality
 -> predeclared recovery branch
 -> StagnationReport / ChatGPT replan / clarification / ABSTAIN
```

Representative failure classes include missing/ambiguous target, stale state, no/partial effect, unexpected dialog, navigation change, tool unavailable, permission denial, unsafe transition and external dynamic change.

`OUTCOME_UNKNOWN` never means “try again blindly”.

## LoopGuard

LoopGuard detects repeated equivalent physical intents, no-effect retries, oscillation and exhausted budgets.

Relevant state includes:

```text
physical/logical attempt fingerprint
verified progress vector
no-effect / retry counts
oscillation window
task / procedure / strategy budgets
recovery escalation state
```

On stagnation, the deterministic layer stops further equivalent effects and emits diagnostic StagnationReport data to the ordinary-ChatGPT planner.

## Capability-aware routing

Availability is not routing authority.

```text
exact safe semantic/native route proven
 -> use it

structure insufficient for reviewed case
 -> selected visual/GUI evidence route

ambiguous/high-consequence state
 -> stronger evidence / reconciliation / ABSTAIN
```

Routing remains deterministic/policy-bounded for admitted cases; it must not become a hidden general planner or generic backend dispatcher.

## Grounding evidence

A useful grounding proposal may carry:

```text
semantic target identity
role/name/state where available
bounding region / coordinates only when required
source = structural | visual | hybrid
observation/frame binding
confidence
ambiguity evidence
```

Coordinates alone are not durable authority when stronger identity evidence exists.

## Browser / Windows integration

Existing Browser and Windows implementations remain capability-specific.

The accepted Browser L3 backend is headless Playwright/Chrome on target Windows. Existing Windows foundations use DesktopState/native/UIA evidence and selected visual fallback.

Future 26.5 hybrid integration may normalize common envelope/routing/recovery semantics, but does not require one universal runtime class or automatically add public tools.

## Deliberately not adopted

This architecture does **not** authorize:

- screenshot-only computer use as normal loop;
- unrestricted StateAct-like code/program-state authority;
- raw hundreds-of-tools UIA/DOM/backend exposure;
- generic `tool_invoke`/backend dispatch;
- blind absolute-coordinate demonstration replay;
- unbounded screenshot/action history replay;
- learned memory/router/critic components without measured need;
- mass speculative side effects in production;
- model/critic verdict as authorization or task completion;
- arbitrary local Python/shell execution;
- future Windows/public tool names without separate contract/security/physical acceptance.

## Current staged mapping

Release order belongs to `ROADMAP.md`; this section only maps architectural adoption:

```text
26.3A procedure runtime                         accepted
26.3B Verification Kernel + Finish Gate         accepted for recorded scope
26.3C WorkingState/LoopGuard L1 foundation      accepted; production recovery integration active
26.4 demonstration -> verified candidate skill future
26.5 hybrid computer-use integration            future
```

Future implementation mechanisms are subject to fresh applicable Stage Research and `ARCHITECTURE_REUSE_BASELINE.md`; this architecture document does not pre-authorize a specific persistence/recovery framework.

## Evaluation direction

Use layered evidence:

```text
primitive/component diagnostics
 -> capability integration tests
 -> recovery/noisy-state fixtures
 -> long-horizon verified procedures
 -> selected external benchmark runs when reproducible/useful
```

Benchmark-specific optimizations must not enter product policy unless they generalize to a project-owned invariant.
# Capability Registry + Event / Policy Hooks Architecture

## Status

**PROVISIONAL AUTHORITATIVE FUTURE ARCHITECTURE / ADR-037.**

This document defines a common discovery and event-policy substrate for future Files / Browser / Windows / Agent Sessions / Skills / Connectors / Scheduled Tasks without changing current runtime authority, the six-tool ordinary-Chat surface, or the release-critical Stage 26 sequence.

It is architecture only until the staged implementation and acceptance gates described below are satisfied.

Canonical surrounding boundaries remain:

- `ARCHITECTURE.md` — component and authority boundaries;
- `CONTROL_PLANE.md` — deterministic execution / verification / recovery / Finish Gate authority;
- `COMPUTER_USE_ARCHITECTURE.md` — state-first computer-use loop;
- `CONVERSATION_BRIDGE_ARCHITECTURE.md` — Track M Agent Session / Delegation;
- `AVO_LONG_HORIZON_ARCHITECTURE.md` — WorkingState / stagnation / skill-lineage direction;
- `SECURITY_POLICY.md` — authorization and environmental-content trust;
- `ROADMAP.md` — implementation order.

---

# Why this layer exists

The project already has a strong lower execution boundary:

```text
ordinary ChatGPT
 -> deterministic Control Plane
 -> bounded capability action
 -> fresh re-observation
 -> ExpectedEffect
 -> PASS | FAIL | UNKNOWN
 -> independent Finish Gate
```

What is missing is a truthful product/runtime layer that answers two different questions without exposing raw backend catalogs:

```text
What capabilities exist / are healthy / are eligible?

What typed lifecycle event just occurred, and which deterministic policy
must observe/block/annotate/reconcile it?
```

Without that layer, future Skills, Agent Sessions, Connectors, Scheduled Tasks and deliverable workflows risk each inventing their own discovery, event, hook and policy semantics.

The external 2026-08 QwenWork review reinforces the product value of this separation:

- Agent Sessions are the primary work surface;
- Skills provide reusable methods;
- Connectors provide authorized external capabilities;
- Hooks expose session/tool/subagent lifecycle events;
- Scheduled Tasks create independent runs/sessions.

Reference documentation:

- https://docs.qwenwork.ai/product-introduction
- https://docs.qwenwork.ai/desktop/skills
- https://docs.qwenwork.ai/desktop/connectors
- https://docs.qwenwork.ai/desktop/hooks
- https://docs.qwenwork.ai/web/scheduled-tasks

These are architecture/reference inputs only. QwenWork is not a runtime dependency, authority source, compatibility target or acceptance oracle for this project.

---

# Core decision

Add two project-owned internal primitives beneath the planner and above/beside concrete adapters:

```text
CapabilityRegistry

TypedEventBus + PolicyHooks
```

Target placement:

```text
                         USER
                           |
                           v
                  ordinary ChatGPT
                  GENERAL PLANNER
                           |
                           v
                  Task / AgentSession
                           |
                 WorkingState references
                           |
              +------------+-------------+
              |                          |
              v                          v
       CapabilityRegistry          TypedEventBus
              |                          |
      discovery / health           typed lifecycle
      eligibility metadata              events
              |                          |
              +------------+-------------+
                           |
                           v
              deterministic Control Plane
              authorization / ExpectedEffect
              Verification Kernel / recovery
              independent Finish Gate
                           |
          +----------------+----------------+
          |                |                |
        Files            Browser          Windows
          |                |                |
          +------- future adapters --------+
          |        Agent Sessions          |
          |        Connectors              |
          |        Skills/Procedures       |
          |        ScheduledTask runs      |
          +--------------------------------+
```

Neither primitive is a planner.

Neither primitive may turn descriptive metadata, events, model output, worker output or third-party tool catalogs into action authority.

---

# 1. CapabilityRegistry

## Purpose

`CapabilityRegistry` is the project-owned source of **descriptive capability discovery and current capability state**.

It lets higher layers ask questions such as:

```text
Which accepted capability can read a spreadsheet?
Which browser capability is healthy?
Does this task have any admitted way to update a Windows form?
Which session adapter supports read-only observation vs message transport?
Which Skill requirements cannot currently be satisfied?
```

It does **not** provide generic arbitrary dispatch.

## Descriptor model

Target descriptor shape:

```text
CapabilityDescriptor
  capability_id
  kind
  provider
  version

  description
  operations[]

  availability_state
  health_state
  trust_state
  acceptance_scope

  consequence_classes[]
  required_grant_types[]

  observation_support[]
  mutation_support[]
  verification_profiles[]

  lifecycle_scope
  source_provenance_ref
  adapter_ref
```

IDs are project-owned stable semantic identifiers. Provider/backend identity remains separate.

Example distinction:

```text
capability_id = browser.semantic
provider      = pinned-playwright-adapter

capability_id = agent_sessions.message_transport
provider      = browser-companion:chatgpt-web
```

The planner should reason about admitted capability semantics, not raw backend function names.

## Availability is not authority

ADR-017 remains binding:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

The registry may truthfully report `AVAILABLE` or `ACTIVE` state, but only the deterministic Control Plane may authorize a concrete effect for the current task/grant/evidence.

Therefore:

```text
registry match != route decision
registry availability != authorization
registry health != trust
registry descriptor != public Chat tool
```

## Registry sources

Future descriptors may be supplied by:

```text
project-owned built-in capabilities
project-owned adapters
accepted internal extension adapters
reviewed third-party MCP backends behind semantic projection
future Agent Session adapters
future app-specific connectors
verified SkillPackages / Procedures as requirements and reusable methods
```

Raw third-party MCP/tool catalogs are not copied directly into the registry as trusted semantic capabilities. They require a project-owned adapter/descriptor and reviewed consequence/verification mapping.

## Skills are not capabilities by default

A Skill is a reusable method and may depend on capabilities.

Target relationship:

```text
SkillPackage
  requires -> CapabilityDescriptor refs
  invokes  -> admitted Procedures / semantic operations
  produces -> expected deliverable/effect contracts
```

A Skill cannot grant missing capabilities merely because its instructions request them.

## Discovery behavior

Future discovery may support:

```text
list admitted capabilities
filter by semantic operation
filter by consequence class
filter by current health/availability
resolve Skill requirements
explain why a capability is unavailable or unauthorized
```

Discovery is read-only descriptive state.

No `invoke(capability_id, arbitrary_json)` or equivalent generic Chat-facing meta-tool is accepted by this ADR.

---

# 2. TypedEventBus

## Purpose

The event bus provides a single typed lifecycle stream for internal coordination, observability and policy interception.

It is **not** a completion oracle.

Canonical rule:

```text
event
 -> optional deterministic policy handling
 -> fresh authoritative re-observation when state matters
 -> Verification Kernel
 -> PASS | FAIL | UNKNOWN
```

Event delivery alone never proves the external effect happened.

## Initial event families

The target vocabulary should remain small and semantic. Candidate families:

```text
TaskStarted
TaskStateChanged

CapabilityObserved
CapabilityHealthChanged
CapabilityAuthorizationEvaluated

TransitionProposed
BeforeTransition
TransitionDelivered
TransitionVerified
TransitionPassed
TransitionFailed
TransitionUnknown

RecoveryStarted
RecoveryAttempted
RecoveryExhausted
LoopGuardTriggered
StagnationReported

BeforeFinish
FinishPassed
FinishRejected
FinishUnknown

ProcedureStarted
ProcedureCheckpointed
ProcedureCompleted
ProcedureFailed

SkillCandidateCreated
SkillEvaluationRecorded
SkillPromoted
SkillQuarantined

DelegationCreated
MessageDeliveryObserved
WorkerResultCorrelated
DelegationCompleted
DelegationFailed

SessionObserved
SessionLifecycleRequested
SessionLifecycleVerified

ScheduledTaskTriggered        future
ScheduledTaskRunCreated       future
ScheduledTaskRunCompleted     future

DeliverableRegistered        future
DeliverableVerified          future
```

Not every event is implemented in one stage. The vocabulary is introduced only with the capability that can truthfully emit it.

## Event envelope

Target envelope:

```text
EventEnvelope
  event_id
  event_type
  occurred_at

  task_ref
  session_ref                 optional
  actor_ref                   optional
  capability_ref              optional
  transition_ref              optional
  operation_ref               optional
  delegation_ref              optional

  evidence_refs[]
  working_state_version       optional
  registry_version            optional

  payload                     bounded typed data
  provenance
```

Events contain bounded operational metadata only.

Never persist private chain-of-thought in events.

Environmental text copied into an event remains environmental data under ADR-033.

## Delivery semantics

Event delivery must distinguish at least:

```text
accepted
processed
handler_failed
outcome_unknown
```

A handler timeout must not be silently treated as policy success.

Events that may affect authority or safety require deterministic ordering and a defined fail-closed policy.

Telemetry-only handlers may fail independently without changing task authority.

---

# 3. PolicyHooks

## Purpose

`PolicyHooks` are project-owned deterministic handlers registered for specific typed events.

They provide extension seams without turning the Control Plane into hard-coded per-capability branching.

Example:

```text
BeforeTransition
 -> consequence policy hook
 -> grant-scope hook
 -> target identity/freshness hook
 -> ALLOW | BLOCK | REQUIRE_REOBSERVE | ESCALATE
```

## Hook result model

Target result:

```text
HookDecision
  decision = ALLOW | BLOCK | ANNOTATE | REQUIRE_REOBSERVE | REQUEST_REPLAN
  reason_code
  annotations
  evidence_refs[]
```

Only explicitly policy-authoritative hook classes may return `ALLOW/BLOCK` for their owned policy scope.

A hook cannot:

- grant a capability that is not already admitted by policy;
- widen a grant lifetime/scope;
- convert verifier `FAIL` or `UNKNOWN` into `PASS`;
- convert Finish Gate `NOT_DONE/UNKNOWN` into `DONE`;
- invent a new user goal;
- execute arbitrary backend actions as a side effect of observation-only events;
- treat webpage/file/worker text as higher-priority policy instructions.

## No arbitrary shell-hook baseline

The initial project architecture deliberately does **not** copy unrestricted shell-script hooks from external products.

Baseline handlers are:

```text
project-owned
registered
versioned
bounded-input
bounded-output
deterministically classified
```

A future user-extension hook mechanism would be a separate consequence/security boundary and would require explicit filesystem/process/network grants plus physical acceptance.

---

# 4. Relationship to WorkingState — Stage 26.3C

WorkingState remains the durable project-owned operational state.

The EventBus is not WorkingState and must not become a replay-log substitute for current truth.

Recommended seams:

```text
WorkingState
  ...existing fields...
  active_capability_refs[]
  active_grant_refs[]
  registry_snapshot_ref       optional
  last_verified_event_refs[]  bounded optional references
  retry/recovery history
```

Events may trigger WorkingState updates after the relevant authoritative observation/verification succeeds.

Example:

```text
TransitionDelivered
 -> re-observe
 -> TransitionVerified(PASS)
 -> checkpoint WorkingState
 -> emit TransitionPassed
```

Not:

```text
TransitionDelivered
 -> assume success
 -> checkpoint success
```

## 26.3C implementation boundary

26.3C may introduce the smallest typed internal event seam needed for:

```text
verification results
recovery
LoopGuard
Finish Gate
```

It may also define a read-only `CapabilityDescriptor` schema if useful for planner-neutral WorkingState and recovery routing.

26.3C must **not** detour into marketplace UX, scheduled automation, connector breadth or Track M runtime.

---

# 5. Relationship to verified Skills — Stage 26.4

QwenWork-style `SKILL.md` ergonomics are useful, but project trust remains stronger and separate.

Target project package:

```text
SkillPackage/
  SKILL.md
  manifest.json
  procedures/
  resources/
  tests/
```

Target `manifest.json` semantics:

```text
skill_id
version
description
triggers
required_capabilities[]
required_grant_types[]
procedure_refs[]
expected_outputs[]
verification_profile_refs[]
lineage_ref
trust_status
```

Lifecycle:

```text
demo / authored method
 -> CANDIDATE
 -> independent replay / regression / variant evidence
 -> trusted SkillPackage
 -> stale / quarantined / superseded
```

The registry exposes the Skill's requirements and trust state; it does not bypass promotion evidence.

Relevant events may later include candidate creation, evaluation, promotion and quarantine.

---

# 6. Relationship to Track M Agent Sessions

ADR-035 already requires event-driven monitoring while preserving fresh re-observation.

ADR-037 gives that direction a common internal substrate.

Examples:

```text
native worker event arrives
 -> MessageDeliveryObserved
 -> fresh Session/Conversation observation
 -> verify intended message state

worker idle/completion signal arrives
 -> re-observe exact session/chat/work-unit
 -> correlate result to delegation_id
 -> Verification Kernel / Finish predicates
```

The event bus does not weaken ADR-035 identity rules:

```text
session_id != delegation_id
message delivery != worker completion
worker completion != manager task DONE
```

CapabilityRegistry may expose truthful Track M sub-capabilities such as:

```text
agent_sessions.observe
agent_sessions.message_transport
agent_sessions.lifecycle
```

with provider-specific adapters hidden behind project-owned descriptors.

---

# 7. Relationship to Connectors / internal Extension Manager

Future Connectors should register project-owned semantic capabilities rather than dump raw provider tools into the planner.

Target flow:

```text
third-party backend / MCP / provider API
 -> reviewed adapter
 -> CapabilityDescriptor
 -> project semantic operation
 -> Control Plane authorization
 -> bounded effect
 -> verification
```

1MCP remains optional internal Extension Manager infrastructure. It may help discover/start/health-check backends, but it does not own the CapabilityRegistry trust state or action authorization.

Backend health changes may emit typed events that trigger recovery/re-resolution, but a health event is not proof of task progress.

---

# 8. Future ScheduledTask architecture

Scheduled Tasks are useful only after WorkingState/grant/lifecycle foundations are stable.

Target object:

```text
ScheduledTask
  scheduled_task_id
  task_template
  schedule
  timezone
  working_context_ref
  capability_requirement_refs[]
  scheduled_grant_refs[]
  budget_policy
  finish_contract_ref
```

Each trigger creates a separate run:

```text
ScheduledTask
 -> TaskRun / AgentSession
 -> fresh capability/permission resolution
 -> deterministic Control Plane
 -> Verification Kernel
 -> independent Finish Gate
 -> retained run evidence/deliverables
```

Critical project divergence from a naive scheduler design:

```text
scheduled run does NOT automatically inherit every capability
available to an interactive conversation
```

A scheduled run receives explicit task-scoped grants and resolves current capability health/authorization at execution time.

Paused/disabled/deleted schedule state is separate from historical run evidence.

This is post-core future work, not a Stage 26 requirement.

---

# 9. Future Deliverable Registry seam

Generated files should eventually be referenceable as verified task outputs instead of only path strings.

Possible object:

```text
DeliverableRef
  deliverable_id
  task_ref
  session_ref
  artifact_type
  object/path ref
  version
  source/evidence refs
  verification_status
```

`DeliverableRef` is descriptive/provenance state. File mutation authority remains in the relevant capability/grant.

This seam is intentionally lighter than a full document-management product and is not required for ADR-037 acceptance.

---

# 10. Security invariants

The following remain non-negotiable:

```text
registry metadata is not authority
event delivery is not effect success
hook output is not verifier truth
Skill text is not permission authority
worker output is environmental data
scheduled execution does not imply blanket inherited grants
backend availability is not trust
```

Required consequence chain remains:

```text
user intent
 -> admitted capability semantics
 -> current grant/policy
 -> current authoritative observation
 -> bounded action
 -> fresh re-observation
 -> Verification Kernel
 -> WorkingState checkpoint
 -> Finish Gate
```

A registry/event layer must reduce duplicated glue without creating a generic dispatch or hidden superuser surface.

---

# 11. Staged implementation order

Do not create a new release detour.

Recommended mapping:

```text
NOW / PR #116 architecture only
  ADR-037 + future seams

26.3B
  no runtime change from ADR-037

26.3C
  minimal typed internal event envelope for
  verification/recovery/LoopGuard/Finish Gate
  + optional read-only CapabilityDescriptor foundation

26.4
  SkillPackage manifest requirements
  + verified skill lifecycle events
  + CapabilityRegistry integration where useful

Track M
  session/delegation capability descriptors
  + event monitoring through same typed event substrate

26.5 / later
  broader adapter/connector descriptors
  + optional DeliverableRef integration

post-core / measured need
  ScheduledTask
  marketplace/discovery UX
  user-extensible hooks only under separate grants/security gate
```

The release-critical sequence remains owned by `ROADMAP.md`.

---

# 12. Acceptance requirements

Architecture acceptance does not equal runtime acceptance.

Before `CapabilityRegistry` becomes product runtime:

```text
schema/identity contract tests
no generic dispatch path
availability != authorization tests
raw backend catalog isolation tests
source/trust/provenance behavior
representative capability discovery fixtures
```

Before policy-relevant EventBus/PolicyHooks become product runtime:

```text
typed event schema tests
deterministic ordering/idempotency tests
required-handler failure semantics
no FAIL/UNKNOWN -> PASS escalation path
no hook-based grant widening
fresh re-observation preserved after state-changing effects
LoopGuard / Finish Gate integration tests
representative physical acceptance if a production consequence path changes
```

Before ScheduledTask becomes product runtime:

```text
explicit scheduled-grant contract
independent run/session identity
restart/sleep/timezone/missed-run semantics
budget/concurrency/duplicate-trigger handling
current capability/permission re-resolution
independent completion evidence per run
```

---

# 13. Explicit non-goals

ADR-037 does **not** authorize:

- changing the current six-tool Chat-facing inventory;
- a generic `capability_invoke` / raw tool dispatcher;
- exporting arbitrary MCP catalogs to ChatGPT;
- arbitrary shell/Python hooks;
- automatic permission inheritance from Skills, Sessions or Scheduled Tasks;
- automatic self-modification or skill promotion without evidence;
- a second general planner;
- replacing WorkingState with an event log;
- replacing Verification Kernel or Finish Gate with hook callbacks;
- implementing QwenWork compatibility or copying its runtime.

The goal is a small project-owned substrate that lets future product layers grow without weakening the verified execution architecture.
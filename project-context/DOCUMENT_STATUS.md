# Documentation Status Map

## Purpose

This file prevents older stage/research documents from overriding the live architecture merely because they contain words such as `ACTIVE`, `CURRENT`, `NEXT`, `DRAFT`, `rerun required`, or an old future-stage number.

Before using any document as current architecture, resolve live GitHub state and apply this status map.

## Source-of-truth order

```text
current code/tests/CI/physical evidence
 > CONTINUATION_CONTEXT.md / START_HERE.md / CURRENT_STATE.md
 > ARCHITECTURE.md / CONTROL_PLANE.md / COMPUTER_USE_ARCHITECTURE.md / ROADMAP.md
 > reviewed architecture extensions such as AVO_LONG_HORIZON_ARCHITECTURE.md
   and CONVERSATION_BRIDGE_ARCHITECTURE.md
 > current policy/catalog docs
 > EVIDENCE_INDEX.md for exact accepted evidence navigation
 > active stage contract
 > accepted historical stage evidence
 > old research/handoffs
```

A status/planning phrase inside a historical file describes the time that revision was written. It is not a live roadmap instruction.

## Documentation separation rule

```text
ARCHITECTURE.md / CONTROL_PLANE.md / COMPUTER_USE_ARCHITECTURE.md
  = durable boundaries and invariants

reviewed architecture-extension documents
  = source-specific or future-track mechanisms already mapped into ADRs/canonical architecture;
    they cannot override the canonical documents or claim implementation acceptance

CURRENT_STATE.md / ROADMAP.md
  = current accepted boundary, active work, current residual risks

EVIDENCE_INDEX.md
  = exact accepted heads, physical result locations and scoped measurements

STAGE*.md / historical handoffs
  = detailed qualification design and attempt history
```

Do not copy complete physical dumps into durable architecture documents. Promote generalized architecture/safety lessons; keep exact accepted heads and evidence locators in the evidence/stage records.

## Root documents

| File | Status | Use |
|---|---|---|
| `AGENTS.md` | AUTHORITATIVE ENTRY | Fresh-session rules, source order and current boundaries. |
| `README.md` | CURRENT PRODUCT OVERVIEW | Human-facing architecture/status summary. |
| `SECURITY.md` | CURRENT SECURITY OVERVIEW | Repository/product security boundary. |
| `LICENSE` | AUTHORITATIVE LEGAL | MIT license. |

`.github/PULL_REQUEST_TEMPLATE.md` is a current process template and must track architecture/document-consistency checks.

## Authoritative live context

| File | Status | Use |
|---|---|---|
| `CONTINUATION_CONTEXT.md` | AUTHORITATIVE LIVE SNAPSHOT | Fast continuation after resolving live GitHub state. |
| `START_HERE.md` | AUTHORITATIVE ENTRY | Read order and operating constraints. |
| `CURRENT_STATE.md` | AUTHORITATIVE CURRENT STATE | Accepted boundary, active work and residual risks. Stage 26.3A is accepted/merged; 26.3B is active. |
| `ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURE | Durable component/layer/authority boundaries. |
| `CONTROL_PLANE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | General planner vs deterministic execution state/policy, verification, recovery, completion, stagnation escalation and procedure-lineage evidence. |
| `COMPUTER_USE_ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | State-first hybrid observation, capability routing, ExpectedEffect verification, WorkingState, LoopGuard, Finish Gate and environmental-content trust boundary. Implementation is staged. |
| `AVO_LONG_HORIZON_ARCHITECTURE.md` | REVIEWED ARCHITECTURAL EXTENSION | NVIDIA AVO/persistent-memory/supervision/lineage review; project consequences are promoted through ADR-034, Control Plane and Roadmap. Does not claim runtime acceptance or override canonical architecture. |
| `CONVERSATION_BRIDGE_ARCHITECTURE.md` | PROVISIONAL FUTURE ARCHITECTURE / TRACK M | CtxPort-derived open-ended conversation adapter registry/profile/hooks, GenericChatAdapter fallback, Browser Companion boundary, ConversationSnapshot/HandoffPack contracts and verified worker-handoff direction. Not implemented, not release-critical, no public-tool expansion. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence + optional/future tracks. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | Which documents may define current state. |
| `EVIDENCE_INDEX.md` | AUTHORITATIVE EVIDENCE NAVIGATION | Exact accepted heads, result locators and scoped measurements. |

## Current policy / design governance

| File | Status | Use |
|---|---|---|
| `CONSTRAINTS.md` | CURRENT POLICY | Hard project constraints. |
| `DECISIONS.md` | CURRENT ADR INDEX | Decisions governing development. ADR-031 = optional internal Extension Manager; ADR-032 = state-first hybrid computer-use loop; ADR-033 = environmental content is data, not authority; ADR-034 = verified skill lineage and stagnation escalation; ADR-035 = bounded provider-open Conversation Bridge / future Track M direction. |
| `DEVELOPMENT_PRINCIPLES.md` | CURRENT POLICY | Development/acceptance principles. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Trust/authorization/privacy/environmental-content/safety boundaries. |
| `COST_POLICY.md` | CURRENT POLICY | Baseline cost/subscription constraints. |
| `MODULE_CATALOG.md` | CURRENT CATALOG | Accepted/current/future capability status. |
| `MODULE_SELECTION_POLICY.md` | CURRENT POLICY | Selection/promotion rules including Extension Manager boundary. |
| `EXTENSION_MANAGER.md` | CURRENT OPERATING CONTRACT | Optional 1MCP Extension Manager role and lifecycle/promotion boundary. |
| `TYPED_CAPABILITY_PROJECTION.md` | CURRENT CAPABILITY CONTRACT | Historical typed five-tool foundation plus accepted canonical six-tool surface; `procedure_run` remains typed/bounded, not generic execution. |
| `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md` | CURRENT TEMPORARY MIGRATION COMPATIBILITY | Exact bounded historical inbound alias families only; aliases are not published tools and cannot repair ChatGPT-side app snapshot/permission state before MCP invocation. |
| `TRANSPORT_SUPERVISOR.md` | ACCEPTED CURRENT RELIABILITY FOUNDATION | Self-healing Secure MCP Tunnel lifecycle, layered health and bounded recovery accepted through #94 and low-power Manual/Automatic refinements merged through #100. |
| `TRANSPORT_SUPERVISOR_IMPLEMENTATION_NOTES.md` | ACCEPTED QUALIFICATION NOTES | Transport Supervisor v1 implementation/qualification contract. |
| `TRANSPORT_SUPERVISOR_REBOOT_EVIDENCE.md` | ACCEPTED PHYSICAL EVIDENCE | Exact Windows reboot/logon evidence. |
| `TRANSPORT_SUPERVISOR_ATTEMPT_HISTORY.md` | HISTORICAL QUALIFICATION ATTEMPT LOG | Historical diagnostics only. |
| `VISION.md` | CURRENT PRODUCT DIRECTION | Long-term product direction; subordinate to architecture/roadmap for exact stage status. |
| `HANDOFF_TEMPLATE.md` | CURRENT PROCESS TEMPLATE | Required future handoff fields. |
| `KNOWN_ISSUES.md` | CURRENT ISSUE INDEX | Current unresolved issues + explicitly closed history. |

## Stage 26.3 current/accepted documents

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | CURRENT STAGE 26.3 DESIGN CONTRACT | Verified Procedure Runtime, candidate-first procedural trust and deterministic progression invariants. |
| `STAGE26_3A_IMPLEMENTATION_NOTES.md` | ACCEPTED STAGE 26.3A IMPLEMENTATION/EVIDENCE NOTES | Canonical six-tool runtime, checkpoint/resume, identity rules and accepted physical boundary. |
| `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` | ACCEPTED STAGE 26.3A PUBLIC-SURFACE CONTRACT | `procedure_run` is part of the accepted normal semantic six-tool surface; no separate qualification profile remains. |
| `STAGE26_3B_VERIFICATION_KERNEL.md` | ACTIVE STAGE 26.3B IMPLEMENTATION CONTRACT | Verification Kernel foundation plus current PR #102 file/artifact adapter and accepted-procedure migration. New exact-head hosted CI, physical integration evidence and later capability adapters remain; no Stage 26.3B acceptance claim yet. |

Stage 26.3A is accepted/merged through PR #92, and the Stage 26.3B kernel foundation is merged through PR #99. Current release-critical implementation is PR #102: the file/artifact observation adapter and migration of the accepted procedure are implemented. Because #102 was rebased onto the current documentation line, its new exact head still needs hosted CI and the ordinary-Chat physical completion + zero-overwrite regression; Browser/Windows adapters and cross-capability predicates also remain before Stage 26.3B can be accepted. Stage 26.3C then adds WorkingState + typed recovery + LoopGuard + StagnationReport, and Stage 26.4 adds verified candidate-skill lineage/evolution.

Track M Conversation Bridge work is explicitly **parallel/future**. ADR-035 and `CONVERSATION_BRIDGE_ARCHITECTURE.md` define a provider-open Adapter Registry + declarative profiles/hooks + `GenericChatAdapter`/GUI fallback architecture, but they do not alter the current Stage 26 critical path or imply that authenticated user-browser multi-chat control is implemented.

Current normal transport/extension invariants:

```text
public semantic inventory = exactly six tools
normal semantic binding = direct-stdio
normal semantic 1MCP dependency = none
persistent tunnel source = state/tunnel.json
legacy local-1mcp.yaml = migration fallback / optional extension path only
1MCP = optional internal Extension Manager
```

## Accepted foundation documents — historical evidence

The files below preserve stage-specific evidence/design from their own time. Old planning/status prose cannot override live context.

| File | Status | Important note |
|---|---|---|
| `BRIDGE_ACCEPTANCE.md` | ACCEPTED HISTORICAL FOUNDATION | Evidence log intentionally points current architecture elsewhere. |
| `DIRECT_SEMANTIC_TUNNEL.md` | ACCEPTED HISTORICAL FOUNDATION | Stage 24.1 transport evidence; historical tool counts are stage-scoped. |
| `STAGE22_LEGACY_REDUCTION.md` | ACCEPTED HISTORICAL STAGE | References then-current architecture only. |
| `STAGE24_LEAST_PRIVILEGE.md` | ACCEPTED HISTORICAL STAGE | Opening “current Stage 24” wording is historical. |
| `STAGE25_1_VISION_INTEGRATION.md` | ACCEPTED HISTORICAL STAGE | Accepted Stage 25.1 evidence. |
| `STAGE26_1A_OPENADAPT_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | Historical qualification evidence. |
| `STAGE26_1B_OPENADAPT_CAPTURE_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | Accepted capture evidence. |
| `STAGE26_1C_WINDOWS_EXECUTOR_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | Final accepted physical head `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`; #83 merged. |
| `STAGE26_1D_WINDOWS_HOT_RUNTIME_BENCHMARK.md` | ACCEPTED HISTORICAL STAGE | Physical benchmark evidence. |
| `STAGE26_1E_WINDOW_SCOPED_UIA_RESOLVER.md` | ACCEPTED HISTORICAL STAGE | Physical resolver evidence. |
| `STAGE26_2A_PRODUCTION_WINDOWS_RUNTIME.md` | ACCEPTED HISTORICAL STAGE | Stage 26.2A accepted/merged #87. |
| `STAGE26_2B_DESKTOP_OBSERVATION.md` | ACCEPTED HISTORICAL STAGE | Accepted/merged #88. |
| `STAGE26_2C_DESKTOP_GROUNDER.md` | ACCEPTED HISTORICAL STAGE | Accepted/merged #89. |
| `STAGE26_2D_WINDOWS_VISION_ROUTING.md` | ACCEPTED HISTORICAL STAGE | Physical head `1c74713edcd6321d5583a39234929169e68b5ac1`; #90 merged. |
| `STAGE26_2E_REAL_APPLICATION_E2E.md` | ACCEPTED HISTORICAL EVIDENCE | Physical runtime/qualification head `457db0b634f2e47f53d41e359a238840fa3ca2ee`; isolated VS Code gate passed. |

Exact physical data in historical documents remains valid only for the scoped code/head/test it names. Historical five-tool counts do not define the current accepted six-tool inventory.

Historical references placing 1MCP in the normal bridge path remain valid only for their own stage and do not override current direct-stdio normal transport.

## Research / superseded planning documents

| File | Status | Notes |
|---|---|---|
| `ACTIVE_VISUAL_GROUNDING.md` | HISTORICAL RESEARCH / STAGE 25 DESIGN | Old visual-grounding implementation order is historical. |
| `LOCAL_SPECIALIST_INFERENCE.md` | HISTORICAL RESEARCH / SPECIALIST TRACK | Current specialist/planner boundary is governed by `CONTROL_PLANE.md` and current catalog. |
| `STAGE25_MODEL_PROFILES.md` | HISTORICAL RESEARCH | Old profile selection notes are not current runtime. |
| `STAGE25_TARGET_BENCHMARKS.md` | HISTORICAL EVIDENCE/RESEARCH | Preserve measurements; opening ACTIVE wording is date-scoped. |
| `STAGE25_CHAT_HANDOFF_2026-08-17.md` | HISTORICAL HANDOFF | Explicitly obsolete continuation guidance. |

The Stage 26.3A locally generated `gui-agent-research.md` is **research evidence**, not a repository source of truth. Its independently checked/generalized conclusions have been promoted into `COMPUTER_USE_ARCHITECTURE.md`, ADR-032/033, `CONTROL_PLANE.md`, `CURRENT_STATE.md`, `ROADMAP.md` and `SECURITY_POLICY.md`.

The 2026-08-25 NVIDIA AVO review is recorded in `AVO_LONG_HORIZON_ARCHITECTURE.md`. It is a **reviewed architecture extension**, not physical evidence. Its adopted mechanisms are promoted through ADR-034 into `CONTROL_PLANE.md` and `ROADMAP.md`; source-specific claims in that review cannot override current code/tests/CI/physical evidence or the canonical architecture documents.

The 2026-08-25 CtxPort review is recorded as project-specific future architecture in `CONVERSATION_BRIDGE_ARCHITECTURE.md` and ADR-035. CtxPort remains an external MIT implementation/reference source; its presence or absence is not runtime evidence, and Track M remains non-release-critical until separately implemented and physically qualified. Its adapter registry/declarative-profile/open-ended-provider lessons are architecture references, not a reason to vendor CtxPort as a required runtime.

## Architecture terminology all future docs must preserve

### Current general planner

```text
ordinary ChatGPT
```

Owns open-ended goal interpretation, strategy, procedure selection and novel-state adaptation.

### Deterministic local execution Control Plane

```text
TaskState / WorkingState
ProgramGraph progression
capability policy / authorization
ExpectedEffect + transition verifier
checkpoints
bounded typed recovery + LoopGuard
StagnationReport escalation
resource/action/time budgets
independent Finish Gate
safety/policy gate
Skill / Procedure Lineage evidence
```

May advance known authorized+verified procedure transitions without a ChatGPT round trip after every low-level action. It is not a second general planner. `StagnationReport` carries structured deterministic evidence back to the planner when bounded recovery stalls; it does not add local open-ended strategy.

### State-first hybrid computer use

```text
semantic/native state first
 -> selective visual evidence
 -> bounded action
 -> fresh re-observation
 -> transition verification
 -> bounded recovery
 -> independent completion
```

### Optional internal Extension Manager

```text
1MCP or qualified replacement
 -> extension discovery / aggregation
 -> enable-disable / lazy lifecycle
 -> health / restart
 -> selected third-party MCP backends
```

It is not the normal semantic transport, does not own the persistent tunnel anchor, does not grant trust/authorization and does not directly publish raw backend catalogs.

### Future Conversation Bridge / Track M

```text
Browser Companion in authenticated user browser
 -> open-ended Conversation Adapter Registry
 -> declarative provider/application profiles + small reviewed hooks
 -> GenericChatAdapter DOM/accessibility fallback
 -> selected GUI/visual fallback or ABSTAIN
 -> ConversationObserver / bounded ConversationActuator
 -> ConversationSnapshot
 -> WorkingState-derived HandoffPack
 -> verified Manager -> Worker handoff
```

It is a future parallel layer, not a current planner, not a replacement for the isolated Browser capability, not a public-tool expansion and not evidence that multi-chat orchestration is implemented. Credentials remain inside the browser-companion boundary and worker content remains environmental data. Provider/application identity is not the same as model identity, and new AI services should normally require a profile/hook rather than a core architecture change.

### Future local planner

Optional Track P research only after verified data/need:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general-planner mode
```

Even if later accepted it remains above deterministic capability authorization, transition verifier, Finish Gate and safety boundaries.

## Maintenance rule

Any architecture-changing PR must audit/update this map when it:

- changes authoritative document names/read order;
- closes/opens an active stage;
- changes general-planner or Control Plane responsibility;
- changes computer-use observation/verification/recovery/completion boundaries;
- changes skill/procedure lineage or long-horizon stagnation-escalation semantics;
- changes the Extension Manager/persistent tunnel boundary;
- changes Conversation Bridge / authenticated-browser / adapter-registry / multi-chat handoff boundaries;
- promotes a research track into the release-critical roadmap;
- changes the public Chat-facing capability surface.

# Documentation Status Map

## Purpose

This file prevents older stage/research documents from overriding the live architecture simply because they contain words such as `ACTIVE`, `CURRENT`, `NEXT`, `DRAFT`, `rerun required`, or an old future-stage number.

Before using any document as current architecture, resolve live GitHub state and apply this status map.

## Source-of-truth order

```text
current code/tests/CI/physical evidence
 > CONTINUATION_CONTEXT.md / START_HERE.md / CURRENT_STATE.md
 > ARCHITECTURE.md / CONTROL_PLANE.md / ROADMAP.md
 > current policy/catalog docs
 > EVIDENCE_INDEX.md for exact accepted evidence navigation
 > active stage contract
 > accepted historical stage evidence
 > old research/handoffs
```

A status/planning phrase inside a historical file describes the time that document/revision was written. It is not a live roadmap instruction.

## Documentation separation rule

```text
ARCHITECTURE.md / CONTROL_PLANE.md
  = durable boundaries and invariants

CURRENT_STATE.md / ROADMAP.md
  = current accepted boundary, active work, current residual risks

EVIDENCE_INDEX.md
  = exact accepted heads, physical result locations and scoped measurements

STAGE*.md / historical handoffs
  = detailed qualification design and attempt history
```

Do not copy full physical result dumps into durable architecture documents. Promote only the generalized invariant learned from evidence.

## Root documents

| File | Status | Use |
|---|---|---|
| `AGENTS.md` | AUTHORITATIVE ENTRY | Fresh-session rules/source order/current boundaries. |
| `README.md` | CURRENT PRODUCT OVERVIEW | Human-facing architecture/status summary. |
| `SECURITY.md` | CURRENT SECURITY OVERVIEW | Repository/product security boundary. |
| `LICENSE` | AUTHORITATIVE LEGAL | MIT license. |

`.github/PULL_REQUEST_TEMPLATE.md` is a current process template and must track architecture/document-consistency checks.

## Authoritative live context

| File | Status | Use |
|---|---|---|
| `CONTINUATION_CONTEXT.md` | AUTHORITATIVE LIVE SNAPSHOT | Fast continuation after resolving live GitHub state. Current Stage 26.3A semantic candidate = exactly six public tools; normal semantic is direct-stdio; 1MCP is optional internal Extension Manager infrastructure. |
| `START_HERE.md` | AUTHORITATIVE ENTRY | Read order and operating constraints. |
| `CURRENT_STATE.md` | AUTHORITATIVE CURRENT STATE | Accepted boundary, active gate, residual risks. Current candidate semantic inventory = six tools; persistent tunnel source = neutral `state/tunnel.json`. |
| `ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURE | Durable component/layer/authority boundaries, including the optional Extension Manager boundary. |
| `CONTROL_PLANE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | General planner vs deterministic execution Control Plane vs future planner. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence + optional/future tracks. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | Which documents can define current state. |
| `EVIDENCE_INDEX.md` | AUTHORITATIVE EVIDENCE NAVIGATION | Exact accepted physical/target heads, result locators and scope. |

## Current policy / design governance

| File | Status | Use |
|---|---|---|
| `CONSTRAINTS.md` | CURRENT POLICY | Hard project constraints. |
| `DECISIONS.md` | CURRENT ADR INDEX | Decisions governing current development. ADR-031 defines 1MCP as an optional replaceable internal Extension Manager rather than normal semantic critical-path infrastructure. |
| `DEVELOPMENT_PRINCIPLES.md` | CURRENT POLICY | Development/acceptance principles. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Detailed trust/authorization/privacy boundaries. |
| `COST_POLICY.md` | CURRENT POLICY | Baseline cost/subscription constraints. |
| `MODULE_CATALOG.md` | CURRENT CATALOG | Accepted/current/future capability status. |
| `MODULE_SELECTION_POLICY.md` | CURRENT POLICY | Selection/promotion rules, including the internal Extension Manager boundary for future MCP backends. |
| `EXTENSION_MANAGER.md` | CURRENT OPERATING CONTRACT | Defines the optional 1MCP Extension Manager role, opt-in install/status/remove flow, tunnel migration boundary, CI separation and future MCP backend promotion path. |
| `TYPED_CAPABILITY_PROJECTION.md` | CURRENT STAGE 26.3A CANDIDATE CONTRACT | Historical typed five-tool foundation plus current canonical six-tool candidate surface; `procedure_run` is typed/bounded, not generic execution. |
| `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md` | CURRENT TEMPORARY MIGRATION COMPATIBILITY | Exact five historical `_1mcp_` inbound aliases only. Current canonical candidate inventory is six tools; aliases are not published and do not create a five-tool mode. |
| `TRANSPORT_SUPERVISOR.md` | ACCEPTED CURRENT RELIABILITY FOUNDATION | Self-healing Secure MCP Tunnel lifecycle, layered health, bounded recovery, Windows persistence and persistent desired-state separation accepted through #94. |
| `TRANSPORT_SUPERVISOR_IMPLEMENTATION_NOTES.md` | ACCEPTED QUALIFICATION NOTES | Transport Supervisor v1 qualification contract/status. |
| `TRANSPORT_SUPERVISOR_REBOOT_EVIDENCE.md` | ACCEPTED PHYSICAL EVIDENCE | Exact Windows reboot/logon evidence. |
| `TRANSPORT_SUPERVISOR_ATTEMPT_HISTORY.md` | HISTORICAL QUALIFICATION ATTEMPT LOG | Historical diagnostics only. |
| `VISION.md` | CURRENT PRODUCT DIRECTION | Long-term product direction; subordinate to architecture/roadmap on exact stage status. |
| `HANDOFF_TEMPLATE.md` | CURRENT PROCESS TEMPLATE | Required future handoff fields. |
| `KNOWN_ISSUES.md` | CURRENT ISSUE INDEX | Current unresolved issues + explicitly closed history. |

## Active stage contract

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | ACTIVE STAGE 26.3 CONTRACT / DESIGN | Verified Procedure Runtime / deterministic Control Plane, candidate-first procedural trust and progression invariants. |
| `STAGE26_3A_IMPLEMENTATION_NOTES.md` | ACTIVE STAGE 26.3A IMPLEMENTATION NOTES | Canonical six-tool runtime, checkpoint/resume, filesystem identity and physical acceptance boundary. |
| `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` | ACTIVE STAGE 26.3A PUBLIC-SURFACE CONTRACT | `procedure_run` is permanently part of the current candidate ordinary semantic six-tool surface; no separate qualification profile remains. |

The first Stage 26.3 physical vertical slice must remove intermediate user command entry:

```text
one user goal
 -> ordinary Chat procedure selection
 -> normal six-tool semantic route
 -> local deterministic multi-transition execution
 -> verified completion OR ABSTAIN/escalation
```

Current transport/extension invariants for that slice:

```text
normal semantic binding = direct-stdio
normal semantic 1MCP dependency = none
persistent tunnel source = state/tunnel.json
legacy local-1mcp.yaml = migration fallback / optional extension path only
1MCP = optional internal Extension Manager
```

Hosted acceptance for current code must prove the normal bootstrap does not require a 1MCP/npx preflight and that its smoke test exercises `semantic` + `direct-stdio`, not the historical `reference`/1MCP route.

## Accepted foundation documents — historical evidence

The files below preserve stage-specific evidence/design from their own time. Their old planning/status prose cannot override live context.

| File | Status | Important note |
|---|---|---|
| `BRIDGE_ACCEPTANCE.md` | ACCEPTED HISTORICAL FOUNDATION | Evidence log intentionally points current architecture elsewhere. |
| `DIRECT_SEMANTIC_TUNNEL.md` | ACCEPTED HISTORICAL FOUNDATION | Stage 24.1 transport decision/evidence. Historical public inventory counts remain scoped to that stage. |
| `STAGE22_LEGACY_REDUCTION.md` | ACCEPTED HISTORICAL STAGE | References the then-current 1MCP architecture. |
| `STAGE24_LEAST_PRIVILEGE.md` | ACCEPTED HISTORICAL STAGE | Opening “current Stage 24” wording is historical. |
| `STAGE25_1_VISION_INTEGRATION.md` | ACCEPTED HISTORICAL STAGE | Accepted Stage 25.1 evidence. |
| `STAGE26_1A_OPENADAPT_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | Historical qualification evidence. |
| `STAGE26_1B_OPENADAPT_CAPTURE_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | Accepted capture evidence. |
| `STAGE26_1C_WINDOWS_EXECUTOR_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | Final accepted physical head is `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`; #83 merged. |
| `STAGE26_1D_WINDOWS_HOT_RUNTIME_BENCHMARK.md` | ACCEPTED HISTORICAL STAGE | Physical benchmark evidence. |
| `STAGE26_1E_WINDOW_SCOPED_UIA_RESOLVER.md` | ACCEPTED HISTORICAL STAGE | Physical resolver evidence. |
| `STAGE26_2A_PRODUCTION_WINDOWS_RUNTIME.md` | ACCEPTED HISTORICAL STAGE | Stage 26.2A accepted/merged as #87. |
| `STAGE26_2B_DESKTOP_OBSERVATION.md` | ACCEPTED HISTORICAL STAGE | Accepted/merged #88. |
| `STAGE26_2C_DESKTOP_GROUNDER.md` | ACCEPTED HISTORICAL STAGE | Accepted/merged #89. |
| `STAGE26_2D_WINDOWS_VISION_ROUTING.md` | ACCEPTED HISTORICAL STAGE | Exact physical head `1c74713edcd6321d5583a39234929169e68b5ac1`; #90 merged. |
| `STAGE26_2E_REAL_APPLICATION_E2E.md` | ACCEPTED HISTORICAL EVIDENCE | Exact physical runtime/qualification head `457db0b634f2e47f53d41e359a238840fa3ca2ee`; isolated VS Code real-app gate passed. |

Exact physical data inside historical documents remains valid only for the scoped code/head/test it names. Historical five-tool counts remain valid evidence for those exact earlier stages but do not define the current Stage 26.3A candidate inventory.

Historical references that place 1MCP in the normal bridge path remain valid only for their own stage. They do not override the current direct-stdio normal route or ADR-031.

## Research / superseded planning documents

| File | Status | Notes |
|---|---|---|
| `ACTIVE_VISUAL_GROUNDING.md` | HISTORICAL RESEARCH / STAGE 25 DESIGN | Old visual-grounding implementation order is historical. |
| `LOCAL_SPECIALIST_INFERENCE.md` | HISTORICAL RESEARCH / SPECIALIST TRACK | Current specialist/planner boundary is `CONTROL_PLANE.md`/`MODULE_CATALOG.md`. |
| `STAGE25_MODEL_PROFILES.md` | HISTORICAL RESEARCH | Old profile selection notes are not current runtime. |
| `STAGE25_TARGET_BENCHMARKS.md` | HISTORICAL EVIDENCE/RESEARCH | Preserve measurements; opening ACTIVE wording is date-scoped. |
| `STAGE25_CHAT_HANDOFF_2026-08-17.md` | HISTORICAL HANDOFF | Explicitly obsolete continuation guidance. |

## Architecture terminology all future docs must preserve

### Current general planner

```text
ordinary ChatGPT
```

Owns open-ended goal interpretation, strategy, procedure selection and novel-state adaptation.

### Deterministic local execution Control Plane

```text
TaskState
ProgramGraph state/progression
capability policy / authorization
checkpoints
verifier/postconditions
bounded retry/recovery
resource/action/time budgets
escalation
```

May advance known authorized+verified procedure transitions without a ChatGPT round trip after every low-level action. It is not a second general planner.

### Optional internal Extension Manager

```text
1MCP or qualified replacement
 -> extension discovery / aggregation
 -> enable-disable / lazy lifecycle
 -> health / restart
 -> selected third-party MCP backends
```

It is not the normal semantic transport, does not own the persistent tunnel anchor, does not grant trust/authorization and does not expose raw extension tool catalogs directly to ordinary ChatGPT.

### Future local planner

Optional Track P research only after verified data/need:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general-planner mode
```

Even if later accepted it remains behind deterministic capability authorization/verifier boundaries.

## Maintenance rule

Any architecture-changing PR must audit/update this map when it:

- changes authoritative document names/read order;
- closes/opens an active stage;
- changes general-planner or Control Plane responsibility;
- changes the 1MCP/Extension Manager boundary or persistent tunnel source;
- promotes a research track into the release-critical roadmap;
- changes the public Chat-facing capability surface.

Any accepted physical gate must update `EVIDENCE_INDEX.md`. Durable architecture docs should record only the invariant learned from evidence, not the complete historical result dump.

Do not rewrite historical physical evidence merely to make old prose look current. Preserve evidence and make its authority/status explicit here and in current context.

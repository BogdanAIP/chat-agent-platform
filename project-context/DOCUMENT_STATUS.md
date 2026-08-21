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
 > active stage contract
 > accepted historical stage evidence
 > old research/handoffs
```

A status/planning phrase inside a file classified below as historical describes the time that document/revision was written. It is **not** a live roadmap instruction.

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
| `CONTINUATION_CONTEXT.md` | AUTHORITATIVE LIVE SNAPSHOT | Fast continuation after resolving live GitHub state. |
| `START_HERE.md` | AUTHORITATIVE ENTRY | Read order and current operating constraints. |
| `CURRENT_STATE.md` | AUTHORITATIVE CURRENT STATE | Accepted evidence, active gate, residual risks. |
| `ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURE | Current component/layer boundaries. |
| `CONTROL_PLANE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | General planner vs deterministic execution Control Plane vs future planner. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence + optional/future tracks. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | Which documents can define current state. |

## Current policy / design governance

| File | Status | Use |
|---|---|---|
| `CONSTRAINTS.md` | CURRENT POLICY | Hard project constraints. |
| `DECISIONS.md` | CURRENT ADR INDEX | Decisions governing current development. |
| `DEVELOPMENT_PRINCIPLES.md` | CURRENT POLICY | Development/acceptance principles. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Detailed trust/authorization/privacy boundaries. |
| `COST_POLICY.md` | CURRENT POLICY | Baseline cost/subscription constraints. |
| `MODULE_CATALOG.md` | CURRENT CATALOG | Accepted/current/future capability status. |
| `MODULE_SELECTION_POLICY.md` | CURRENT POLICY | Selection/promotion rules. |
| `TYPED_CAPABILITY_PROJECTION.md` | ACCEPTED CURRENT FOUNDATION | Five-tool semantic projection + separation from procedure Control Plane. |
| `TRANSPORT_SUPERVISOR.md` | PLANNED CROSS-CUTTING RELIABILITY DESIGN | Self-healing Secure MCP Tunnel lifecycle, layered health, bounded recovery and Windows persistence plan; not accepted runtime yet. |
| `TRANSPORT_SUPERVISOR_IMPLEMENTATION_NOTES.md` | ACTIVE QUALIFICATION NOTES | Branch-scoped first implementation slice and physical-gate scope; subordinate to the canonical design and not accepted evidence until qualification passes. |
| `VISION.md` | CURRENT PRODUCT DIRECTION | Long-term product direction; subordinate to architecture/roadmap on exact stage status. |
| `HANDOFF_TEMPLATE.md` | CURRENT PROCESS TEMPLATE | Required future handoff fields. |
| `KNOWN_ISSUES.md` | CURRENT ISSUE INDEX | Current unresolved issues + explicitly closed history. |

## Active stage contract

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | ACTIVE STAGE 26.3 CONTRACT / DESIGN | Verified Procedure Runtime / deterministic Control Plane, candidate-first procedural trust and progression invariants. |

The first Stage 26.3 physical vertical slice must remove intermediate user command entry: one user goal -> ordinary Chat procedure selection -> local deterministic multi-transition execution -> verified completion or ABSTAIN/escalation.

## Accepted foundation documents — historical evidence

The files below preserve stage-specific evidence/design from their own time. Their old planning/status prose cannot override live context.

| File | Status | Important note |
|---|---|---|
| `BRIDGE_ACCEPTANCE.md` | ACCEPTED HISTORICAL FOUNDATION | Evidence log intentionally points current architecture elsewhere. |
| `DIRECT_SEMANTIC_TUNNEL.md` | ACCEPTED HISTORICAL FOUNDATION | Stage 24.1 transport decision/evidence. |
| `STAGE22_LEGACY_REDUCTION.md` | ACCEPTED HISTORICAL STAGE | References the then-current 1MCP architecture; direct stdio later became normal public path. |
| `STAGE24_LEAST_PRIVILEGE.md` | ACCEPTED HISTORICAL STAGE | Opening “current Stage 24” wording is historical. |
| `STAGE25_1_VISION_INTEGRATION.md` | ACCEPTED HISTORICAL STAGE | Accepted Stage 25.1 evidence. |
| `STAGE26_1A_OPENADAPT_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | “product integration not started” describes that stage, not current state. |
| `STAGE26_1B_OPENADAPT_CAPTURE_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | Accepted capture evidence. |
| `STAGE26_1C_WINDOWS_EXECUTOR_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE | **Its opening DRAFT/rerun-required label is an old intermediate revision.** Final accepted physical head is `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`; #83 merged. |
| `STAGE26_1D_WINDOWS_HOT_RUNTIME_BENCHMARK.md` | ACCEPTED HISTORICAL STAGE | Physical benchmark evidence. |
| `STAGE26_1E_WINDOW_SCOPED_UIA_RESOLVER.md` | ACCEPTED HISTORICAL STAGE | Physical resolver evidence. |
| `STAGE26_2A_PRODUCTION_WINDOWS_RUNTIME.md` | ACCEPTED HISTORICAL STAGE | **Its opening ACTIVE/DRAFT label is historical.** Stage 26.2A was accepted/merged as #87. |
| `STAGE26_2B_DESKTOP_OBSERVATION.md` | ACCEPTED HISTORICAL STAGE | Accepted/merged #88. |
| `STAGE26_2C_DESKTOP_GROUNDER.md` | ACCEPTED HISTORICAL STAGE | Accepted/merged #89. |
| `STAGE26_2D_WINDOWS_VISION_ROUTING.md` | ACCEPTED HISTORICAL STAGE | **Its opening ACTIVE/qualification-required label is historical.** Exact physical head `1c74713edcd6321d5583a39234929169e68b5ac1` passed and #90 merged. |
| `STAGE26_2E_REAL_APPLICATION_E2E.md` | ACCEPTED HISTORICAL EVIDENCE | Exact physical runtime/qualification head `457db0b634f2e47f53d41e359a238840fa3ca2ee` passed the isolated VS Code real-app gate with one guarded Unicode action, independent file verification and full rollback. |

Exact physical data inside historical documents remains valid only for the scoped code/head/test it names. Do not reinterpret synthetic cases as physical evidence.

## Research / superseded planning documents

| File | Status | Notes |
|---|---|---|
| `ACTIVE_VISUAL_GROUNDING.md` | HISTORICAL RESEARCH / STAGE 25 DESIGN | Opening ACTIVE wording and old 3B/Mark-Grid implementation order are historical; accepted target later became 450M F16 bounded specialist path. |
| `LOCAL_SPECIALIST_INFERENCE.md` | HISTORICAL RESEARCH / SPECIALIST TRACK | Opening ACTIVE/PROVISIONAL and LM Studio candidate discussion are historical. Current specialist/planner boundary is `CONTROL_PLANE.md`/`MODULE_CATALOG.md`. |
| `STAGE25_MODEL_PROFILES.md` | HISTORICAL RESEARCH | Opening active benchmark wording and old 3B profile are not current selected runtime. |
| `STAGE25_TARGET_BENCHMARKS.md` | HISTORICAL EVIDENCE/RESEARCH | Preserve measurements; opening ACTIVE EVIDENCE is date-scoped. |
| `STAGE25_CHAT_HANDOFF_2026-08-17.md` | HISTORICAL HANDOFF | Its “active development handoff for next conversation” is explicitly obsolete. |

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

May advance known authorized+verified procedure transitions without a ChatGPT round trip after every low-level action. It is **not** a second general planner.

### Future local planner

Optional Track P research only after verified data/need:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general-planner mode
```

Even if later accepted it remains behind deterministic capability authorization/verifier boundaries and does not silently replace ChatGPT default.

## Maintenance rule

Any architecture-changing PR must audit/update this map when it:

- changes authoritative document names/read order;
- closes/opens an active stage;
- changes general-planner or Control Plane responsibility;
- promotes a research track into the release-critical roadmap;
- changes the public Chat-facing capability surface.

Do not rewrite historical physical evidence merely to make old prose look current. Preserve evidence and make its authority/status explicit here and in current context.

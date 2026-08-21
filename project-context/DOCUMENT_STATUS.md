# Documentation Status Map

## Purpose

This file prevents older stage/research documents from overriding the live architecture simply because they contain words such as `ACTIVE`, `CURRENT`, `NEXT`, or an old stage number.

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

`ACTIVE`, `NEXT`, or `CURRENT` text inside a file classified below as historical describes the time that document was written. It is **not** a live roadmap instruction.

## Root documents

| File | Status | Use |
|---|---|---|
| `AGENTS.md` | AUTHORITATIVE ENTRY | Fresh-session rules/source order/current boundaries. |
| `README.md` | CURRENT PRODUCT OVERVIEW | Human-facing architecture/status summary. |
| `SECURITY.md` | CURRENT SECURITY OVERVIEW | Repository/product security boundary. |
| `LICENSE` | AUTHORITATIVE LEGAL | MIT license. |

## Authoritative live context

| File | Status | Use |
|---|---|---|
| `CONTINUATION_CONTEXT.md` | AUTHORITATIVE LIVE SNAPSHOT | Fast current continuation after resolving live GitHub state. |
| `START_HERE.md` | AUTHORITATIVE ENTRY | Read order and current operating constraints. |
| `CURRENT_STATE.md` | AUTHORITATIVE CURRENT STATE | Accepted evidence, active gate, residual risks. |
| `ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURE | Current component/layer boundaries. |
| `CONTROL_PLANE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | General-planner vs deterministic local execution Control Plane vs future local planner. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence + optional/future research tracks. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | Which files may define current state vs historical evidence. |

## Current policy / design governance

| File | Status | Use |
|---|---|---|
| `CONSTRAINTS.md` | CURRENT POLICY | Hard project constraints. |
| `DECISIONS.md` | CURRENT ADR INDEX | Decisions governing current development; Git history retains superseded ADR detail. |
| `DEVELOPMENT_PRINCIPLES.md` | CURRENT POLICY | Development/acceptance principles. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Detailed trust/authorization/privacy boundaries. |
| `COST_POLICY.md` | CURRENT POLICY | Baseline cost/subscription constraints. |
| `MODULE_CATALOG.md` | CURRENT CATALOG | Accepted/current/future capability status. |
| `MODULE_SELECTION_POLICY.md` | CURRENT POLICY | How future components are selected/promoted. |
| `TYPED_CAPABILITY_PROJECTION.md` | ACCEPTED CURRENT FOUNDATION | Current five-tool semantic-projection contract and relationship to the separate Control Plane. |
| `VISION.md` | CURRENT PRODUCT DIRECTION | Long-term product direction; subordinate to architecture/roadmap on exact stage status. |
| `HANDOFF_TEMPLATE.md` | CURRENT PROCESS TEMPLATE | What a future handoff must state. |
| `KNOWN_ISSUES.md` | CURRENT ISSUE INDEX | Only unresolved current architecture issues plus explicitly closed history. |

## Active stage contract

| File | Status | Use |
|---|---|---|
| `STAGE26_2E_REAL_APPLICATION_E2E.md` | ACTIVE STAGE CONTRACT | Exact isolated VS Code real-app qualification contract until Stage 26.2E closes. |

When 26.2E closes, change its status in this map to `ACCEPTED HISTORICAL EVIDENCE` and name the next active stage contract.

## Accepted foundation documents — historical evidence

The following preserve exact stage-specific decisions/evidence. Their old `NEXT`, `ACTIVE`, `CURRENT`, future-stage numbering, or implementation-order text is **historical** and cannot override live context:

| File | Status |
|---|---|
| `BRIDGE_ACCEPTANCE.md` | ACCEPTED HISTORICAL FOUNDATION |
| `DIRECT_SEMANTIC_TUNNEL.md` | ACCEPTED HISTORICAL FOUNDATION |
| `STAGE22_LEGACY_REDUCTION.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE24_LEAST_PRIVILEGE.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE25_1_VISION_INTEGRATION.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_1A_OPENADAPT_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_1B_OPENADAPT_CAPTURE_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_1C_WINDOWS_EXECUTOR_QUALIFICATION.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_1D_WINDOWS_HOT_RUNTIME_BENCHMARK.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_1E_WINDOW_SCOPED_UIA_RESOLVER.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_2A_PRODUCTION_WINDOWS_RUNTIME.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_2B_DESKTOP_OBSERVATION.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_2C_DESKTOP_GROUNDER.md` | ACCEPTED HISTORICAL STAGE |
| `STAGE26_2D_WINDOWS_VISION_ROUTING.md` | ACCEPTED HISTORICAL STAGE |

Exact physical evidence in these files remains valid for the scoped code/head it names. Only their old planning/status prose is historical.

## Research / superseded planning documents

These are useful references but must not define current architecture/status:

| File | Status | Notes |
|---|---|---|
| `ACTIVE_VISUAL_GROUNDING.md` | HISTORICAL RESEARCH / STAGE 25 DESIGN | Old model/profile/status sections are superseded by accepted Stage 25.2 + later architecture. |
| `LOCAL_SPECIALIST_INFERENCE.md` | HISTORICAL RESEARCH / SPECIALIST TRACK | Specialist/tiny-model research reference; current specialist/planner boundaries are in `CONTROL_PLANE.md`/`ROADMAP.md`. |
| `STAGE25_MODEL_PROFILES.md` | HISTORICAL RESEARCH | Old candidate/model profiles; not current selected runtime. |
| `STAGE25_TARGET_BENCHMARKS.md` | HISTORICAL EVIDENCE/RESEARCH | Preserve measurements; do not use as current roadmap. |
| `STAGE25_CHAT_HANDOFF_2026-08-17.md` | HISTORICAL HANDOFF | Dated snapshot only. |
| `STAGE26_PROCEDURAL_MEMORY.md` | CURRENT PROCEDURAL DESIGN | Rewritten/synchronized to current 26.3/Control Plane architecture; older Git revisions are superseded. |

## Architecture terminology that all future docs must preserve

### Current general planner

```text
ordinary ChatGPT
```

Owns open-ended user-goal interpretation, strategy, procedure selection and novel-state adaptation.

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

Do not “fix” historical physical evidence to match new architecture language. Preserve evidence and update its classification/current authority instead.

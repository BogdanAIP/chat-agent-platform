# Documentation Status Map

## Purpose

This file defines **which document owns which kind of project truth**. It must not become another current-state snapshot.

Always resolve live `main`, relevant open PRs/exact heads, current code/tests, hosted CI and required physical evidence before acting. When prose disagrees with live code/evidence, live code/evidence wins.

## Source-of-truth order

Use the narrowest owner for the question:

```text
current code/tests/current hosted CI/current physical evidence
  > CURRENT_STATE.md for accepted/current boundary and immediate work
  > ROADMAP.md for release-stage order
  > PROJECT_RISKS.md for ranked project risk
  > architecture/security/policy owner documents for durable boundaries
  > BENCHMARK_EVALUATION_STRATEGY.md for cross-capability external-evaluation method
  > ARCHITECTURE_REUSE_BASELINE.md for prior reuse/project-owned role lineage used by stage-research
  > EVIDENCE_INDEX.md for exact accepted evidence navigation
  > accepted Stage/qualification records for detailed historical evidence
  > reviewed external/research references
  > old handoffs / superseded stage prose
```

A document being authoritative for one role does not make every historical sentence inside it a live-state claim. Exact implementation status belongs in `CURRENT_STATE.md`; exact accepted heads/paths belong in `EVIDENCE_INDEX.md`; release ordering belongs in `ROADMAP.md`.

## Separation rules

```text
START_HERE.md
  = fresh-session entry/read order

CONTINUATION_CONTEXT.md
  = concise orientation aid subordinate to CURRENT_STATE/live GitHub

CURRENT_STATE.md
  = single live accepted boundary + immediate critical path + active PR/design snapshot

ROADMAP.md
  = single owner of release sequence and stage-level completion conditions

PROJECT_RISKS.md
  = single ranked risk register

BENCHMARK_EVALUATION_STRATEGY.md
  = cross-capability external benchmark ladder, frequency, adapter-integrity, provenance and holdout rules

ARCHITECTURE.md / CONTROL_PLANE.md / COMPUTER_USE_ARCHITECTURE.md
  = durable product/execution boundaries

SECURITY_POLICY.md / SECURITY.md
  = security/authority/trust boundaries

ARCHITECTURE_REUSE_BASELINE.md
  = canonical prior component/reuse/project-owned role lineage for Stage Research comparison

MODULE_CATALOG.md
  = current capability inventory/reference; not release-order or acceptance-evidence owner

MODULE_SELECTION_POLICY.md
  = current component/reuse selection policy

KNOWN_ISSUES.md
  = unresolved current limitations; not risk ranking or roadmap

TECH_DEBT.md
  = existing compromises with explicit close conditions

EVIDENCE_INDEX.md
  = exact accepted physical/target evidence navigation

STAGE*.md / qualification records
  = implementation/qualification lineage for their recorded scope, not current status unless explicitly designated active
```

Do not duplicate full risk rankings, active PR snapshots, exact accepted SHAs, machine-local evidence paths or active design detail across multiple live documents.

## Root documents

| File | Status | Owns |
|---|---|---|
| `AGENTS.md` | **AUTHORITATIVE DEVELOPMENT ENTRY** | bootstrap, research gate, development/merge/document discipline |
| `README.md` | **CURRENT PRODUCT OVERVIEW** | human-facing product summary; deliberately no live stage snapshot |
| `SECURITY.md` | **CURRENT SECURITY OVERVIEW** | public repository/product security summary |
| `LICENSE` | **AUTHORITATIVE LEGAL** | license |

## Live project/state documents

| File | Status | Owns |
|---|---|---|
| `START_HERE.md` | **AUTHORITATIVE CONTINUATION ENTRY** | minimum fresh-session read path |
| `CURRENT_STATE.md` | **AUTHORITATIVE CURRENT STATE** | accepted/current boundary, immediate work and active PR/design snapshot |
| `CONTINUATION_CONTEXT.md` | **CURRENT CONTINUATION AID** | concise orientation only; subordinate to live GitHub and `CURRENT_STATE.md` |
| `ROADMAP.md` | **AUTHORITATIVE ROADMAP** | release-critical sequence and stage-level completion conditions |
| `PROJECT_RISKS.md` | **AUTHORITATIVE RISK REGISTER** | ranked risks and close conditions |
| `TECH_DEBT.md` | **AUTHORITATIVE TECH-DEBT REGISTER** | existing implementation/process compromises |
| `KNOWN_ISSUES.md` | **CURRENT LIMITATION REGISTER** | unresolved limitations/issues that are not necessarily ranked risks or debt |
| `EVIDENCE_INDEX.md` | **AUTHORITATIVE EVIDENCE NAVIGATION** | exact accepted physical/target heads, result locators and scoped measurements |
| `DOCUMENT_STATUS.md` | **AUTHORITATIVE DOCUMENT MAP** | document ownership/status only |

## Current architecture / policy owners

| File | Status | Owns |
|---|---|---|
| `ARCHITECTURE.md` | **AUTHORITATIVE ARCHITECTURE** | durable component and authority boundaries |
| `CONTROL_PLANE.md` | **AUTHORITATIVE EXECUTION ARCHITECTURE** | planner vs deterministic execution/state/verification/recovery/completion boundary |
| `COMPUTER_USE_ARCHITECTURE.md` | **AUTHORITATIVE ARCHITECTURAL DIRECTION** | state-first hybrid computer-use contract |
| `SECURITY_POLICY.md` | **AUTHORITATIVE CURRENT POLICY** | trust, authorization, environmental-content and consequence boundaries |
| `CONSTRAINTS.md` | **CURRENT CONSTRAINTS** | project-wide hard constraints consistent with `AGENTS.md` and accepted architecture |
| `DEVELOPMENT_PRINCIPLES.md` | **CURRENT DEVELOPMENT PRINCIPLES** | stable engineering principles; subordinate to `AGENTS.md` where process wording differs |
| `COST_POLICY.md` | **CURRENT COST POLICY** | baseline no-extra-subscription/cost boundary |
| `MODULE_SELECTION_POLICY.md` | **AUTHORITATIVE MODULE-SELECTION POLICY** | external-component selection/adaptation/reuse rules |
| `MODULE_CATALOG.md` | **CURRENT CAPABILITY CATALOG** | capability/component inventory and role/status reference; live evidence still wins |
| `BENCHMARK_EVALUATION_STRATEGY.md` | **AUTHORITATIVE CROSS-CAPABILITY EVALUATION STRATEGY** | external benchmark ladder, domain-harness selection, run frequency, adapter integrity, provenance and dev/regression/holdout rules |
| `ARCHITECTURE_REUSE_BASELINE.md` | **AUTHORITATIVE RESEARCH COMPARISON BASELINE** | prior selected external/project-owned role lineage for applicable `stage-research` |
| `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | **AUTHORITATIVE INTEGRATION DIRECTION** | detailed OpenAdapt/UFO reuse boundaries; does not own active PR state or release order |
| `REAL_TASK_ACCEPTANCE.md` | **AUTHORITATIVE ACCEPTANCE CONTRACT** | L1/L2/L3 evidence depth and real-task rules |
| `SOURCE_PROVENANCE_ACCEPTANCE.md` | **AUTHORITATIVE PHYSICAL-PROVENANCE METHOD** | exact executed-source/install/runtime binding |
| `MUTATION_ASSURANCE.md` | **CURRENT ASSURANCE DIRECTION** | guarantee mutation/adversarial assurance and CAP-M families |
| `TRANSPORT_SUPERVISOR.md` | **CURRENT TRANSPORT RELIABILITY OWNER** | accepted supervisor desired-state/recovery/ownership boundary |
| `EXTENSION_MANAGER.md` | **CURRENT OPTIONAL-EXTENSION REFERENCE** | optional 1MCP Extension Manager role; never baseline transport/authority |
| `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md` | **CURRENT COMPATIBILITY REFERENCE** | frozen ChatGPT action/schema compatibility and migration limits |

## Evaluation-strategy discovery rule

`BENCHMARK_EVALUATION_STRATEGY.md` is read when a capability becomes externally evaluable, when a benchmark adapter/harness is proposed, when a capability/stage is being closed with public-comparative evidence, or when a major release/architecture change should be compared against prior CAP results.

It does not own current stage scheduling and does not force every benchmark to run after every PR. `ROADMAP.md` still owns order; benchmark selection and frequency follow the evaluation strategy only when the corresponding capability is honestly available.

## Provisional/future architecture

These documents define reviewed future boundaries but **do not add current runtime/public authority by themselves**:

| File | Status |
|---|---|
| `CONVERSATION_BRIDGE_ARCHITECTURE.md` | **PROVISIONAL FUTURE ARCHITECTURE / ADR-035 / Track M** |
| `BROWSER_HARNESS_ARCHITECTURE.md` | **PROVISIONAL FUTURE ARCHITECTURE / ADR-036** |
| `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` | **PROVISIONAL FUTURE ARCHITECTURE / ADR-037** |

`AVO_LONG_HORIZON_ARCHITECTURE.md` is a **REVIEWED EXTERNAL-MECHANISM / REFERENCE RECORD** whose accepted project consequences are promoted through ADR-034 and current owner documents. Its dated research prose is not a live implementation-status source.

## ADR / decision index

`DECISIONS.md` is the **CURRENT ADR INDEX**. Accepted decisions and durable provisional boundaries govern current design. Release-stage mapping, active PR state and exact implementation acceptance belong to their dedicated owners rather than ADR prose.

## Accepted historical / Stage records

The following are useful scoped accepted/research records but are **not current status owners**:

- `DIRECT_SEMANTIC_TUNNEL.md` — accepted Stage 24.1 direct-transport record; its historical five-tool contract was later superseded by the current six-tool surface;
- `LOCAL_SPECIALIST_INFERENCE.md` — Stage 25 local-specialist research/qualification record; current capability status belongs to `MODULE_CATALOG.md` / accepted code/evidence;
- `ACTIVE_VISUAL_GROUNDING.md` — Stage 25 visual-grounding research/benchmark record; dated provisional wording is historical;
- `STAGE26_PROCEDURAL_MEMORY.md` — accepted procedural foundation/reference;
- `STAGE26_3A_IMPLEMENTATION_NOTES.md` — accepted 26.3A record;
- `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` — accepted six-tool/procedure surface record;
- `STAGE26_3B_VERIFICATION_KERNEL.md` — accepted 26.3B contract/historical implementation record;
- `STAGE26_3B_WINDOWS_VERIFICATION.md` — accepted 26.3B Windows verification record.

Other `STAGE*.md`, dated handoffs, physical-gate failure reports and research snapshots are **HISTORICAL / REFERENCE by default** unless this map or a current owner explicitly promotes them.

Historical files may correctly contain old five-tool counts, old active-PR wording or candidate/runtime research that was true in their recorded stage. Those statements must not be read as present product state.

## Architecture reuse baseline rule

`ARCHITECTURE_REUSE_BASELINE.md` is intentionally different from `MODULE_CATALOG.md`:

- the catalog says what capability/component role exists or is planned;
- the reuse baseline preserves the **prior architecture selection lineage** that new Stage Research must explicitly keep/refine/replace/reject/defer/reuse-more;
- the baseline must not contain active release scheduling, runtime acceptance claims or transient dependency pins;
- an accepted Stage Research decision that materially changes a baseline role must update the baseline in the adopting PR before/with merge.

A historical/research document may still be linked as the detailed rationale for a baseline row; that does not promote the entire historical file to current status authority.

## Maintenance rule

Update this map only when document ownership/status changes. Do **not** update it merely because a stage advances, a PR opens/closes, a SHA changes or a qualification run completes; those facts belong to their dedicated owners.

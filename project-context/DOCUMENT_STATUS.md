# Documentation Status Map

## Purpose

Prevent stale stage/research/status prose from overriding live repository reality.

Before using any document as current truth, resolve live GitHub state.

## Source-of-truth order

```text
current code/tests/current hosted CI/current physical evidence
 > CURRENT_STATE.md / CONTINUATION_CONTEXT.md / START_HERE.md
 > PROJECT_RISKS.md for ranked engineering risk priority
 > ARCHITECTURE.md / CONTROL_PLANE.md / COMPUTER_USE_ARCHITECTURE.md / SECURITY_POLICY.md
 > BROWSER_HARNESS_ARCHITECTURE.md for ADR-036 reviewed future capability direction
 > REAL_TASK_ACCEPTANCE.md for L1/L2/L3 acceptance depth
 > ROADMAP.md
 > TECH_DEBT.md for current implementation/process debt
 > EVIDENCE_INDEX.md for accepted exact heads/evidence navigation
 > active stage contract
 > accepted historical stage evidence
 > old research/handoffs
```

When two documents disagree on whether work is implemented/accepted/current, live code and exact evidence win.

## Default classification rule

Any `project-context/*.md` document **not explicitly listed** in this status map is **HISTORICAL / REFERENCE by default** until a reviewed change explicitly promotes it into an authoritative/current category.

This is intentional: adding a research note or historical stage record must not force a central catalog update or accidentally grant that document authority over live state.

## Documentation separation rule

Architecture documents own **durable boundaries and invariants**; evidence documents own exact accepted heads and scoped proof.

```text
ARCHITECTURE / CONTROL_PLANE / COMPUTER_USE_ARCHITECTURE / SECURITY_POLICY
  = durable authority, safety and execution boundaries

BROWSER_HARNESS_ARCHITECTURE
  = reviewed ADR-036 future capability direction;
    cannot claim current runtime acceptance

REAL_TASK_ACCEPTANCE
  = durable L1/L2/L3 acceptance-depth contract;
    cannot by itself claim a specific physical task passed

CURRENT_STATE
  = concise live accepted/current boundary and next work

CONTINUATION_CONTEXT / START_HERE
  = fresh-session continuation/read order

PROJECT_RISKS
  = single authoritative ranked risk table, mitigation and close conditions

ROADMAP
  = single owner of the explicit release-stage order and acceptance objectives

TECH_DEBT
  = single inventory of current implementation/process debt;
    not feature backlog or project-risk ranking

EVIDENCE_INDEX
  = exact accepted evidence navigation

STAGE*.md
  = active detailed implementation contract or historical qualification record
```

Do not copy the full risk table into other documents. Do not copy the full release-stage sequence into multiple live status documents. Do not copy detailed physical dumps into durable architecture docs.

## Root documents

| File | Status | Use |
|---|---|---|
| `AGENTS.md` | AUTHORITATIVE ENTRY | Development/merge/authority rules. |
| `README.md` | CURRENT PRODUCT OVERVIEW | Human-facing summary. |
| `SECURITY.md` | CURRENT SECURITY OVERVIEW | Repository/product security boundary. |
| `LICENSE` | AUTHORITATIVE LEGAL | MIT license. |

## Authoritative live context

| File | Status | Use |
|---|---|---|
| `CONTINUATION_CONTEXT.md` | AUTHORITATIVE LIVE SNAPSHOT | Exact continuation point after resolving live GitHub. |
| `START_HERE.md` | AUTHORITATIVE ENTRY | Read order and current focus. |
| `CURRENT_STATE.md` | AUTHORITATIVE CURRENT STATE | Accepted/current implementation boundary and immediate critical path. |
| `PROJECT_RISKS.md` | AUTHORITATIVE RISK REGISTER | Ranked project risks, scores, evidence, mitigation and close conditions. |
| `ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURE | Durable component/authority boundaries. |
| `CONTROL_PLANE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | Planner vs deterministic execution/verification/recovery/completion boundary. |
| `COMPUTER_USE_ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | State-first hybrid computer-use contract. |
| `BROWSER_HARNESS_ARCHITECTURE.md` | PROVISIONAL FUTURE ARCHITECTURE / ADR-036 | Site Capability Profiles, trusted-site full-browser direction, candidate helpers/domain knowledge and separately scoped Local Execution Kernel/Python authority. No current runtime/public-tool authority expansion. |
| `REAL_TASK_ACCEPTANCE.md` | AUTHORITATIVE ACCEPTANCE-DIRECTION CONTRACT | Defines L1 primitive, L2 workflow and L3 real user-task evidence; representative L3 is required before a major capability path is treated as proven for realistic autonomous use. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Trust/authorization/privacy/environmental-content/safety boundaries. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Single owner of release-critical sequence and acceptance objectives. |
| `TECH_DEBT.md` | AUTHORITATIVE TECHNICAL DEBT REGISTER | Existing temporary compatibility, hardening, reproducibility and repository-hygiene debt with priority and close conditions. Future features/stages do not belong here. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | This source map and default classification rule. |
| `EVIDENCE_INDEX.md` | AUTHORITATIVE EVIDENCE NAVIGATION | Exact accepted heads and scoped evidence locations. |
| `DECISIONS.md` | CURRENT ADR INDEX | Current architectural decisions including ADR-036. |

## Current Stage 26.3 documents

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | CURRENT 26.3 DESIGN CONTRACT | Verified procedure/candidate trust foundations. |
| `STAGE26_3A_IMPLEMENTATION_NOTES.md` | ACCEPTED 26.3A RECORD | Accepted canonical six-tool implementation/evidence. |
| `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` | ACCEPTED 26.3A SURFACE CONTRACT | `procedure_run` in the six-tool surface. |
| `STAGE26_3B_VERIFICATION_KERNEL.md` | ACTIVE 26.3B IMPLEMENTATION CONTRACT | Shared Verification Kernel; accepted file integration; Browser observation foundation; physically accepted/merged `web_open` verification; `web_interact` verification is active in draft PR #111. |

## Current implementation snapshot

At the 2026-08-26 post-PR-#110 point:

```text
Stage 26.3A                                      ACCEPTED / MERGED #92
Verification Kernel foundation                  MERGED #99
file/artifact integration                       PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                  MERGED #106
production web_open verification                PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                  MERGED #110
web_interact verification                       ACTIVE DRAFT PR #111; hosted CI green, physical gate pending
Browser L3 real-task harness                    STACKED DRAFT PR #112
Windows/application/process verifier            REMAINING 26.3B
WorkingState + recovery + LoopGuard              26.3C TARGET
```

PR #107 was physically accepted on exact head `64184713e97bf2e150614cd93c77509c244cddec`. Exact gate details belong in the PR/evidence records, not duplicated here.

PR #111 is a clean one-commit runtime/test diff on post-#110 `main`; its final hosted CI is green and target-Windows ordinary-Chat physical interaction acceptance remains required before merge.

PR #112 is intentionally stacked on #111 so it does not alter #111's exact head. It adds the first randomized stateful Browser L3 harness and the L1/L2/L3 acceptance contract. After #111 merges, #112 must be replayed on accepted `main` before its own physical L3 evidence is collected.

## Real-task acceptance boundary

The project now distinguishes:

```text
L1 primitive / contract proof
L2 multi-step component workflow
L3 ordinary user goal + independent final state
```

L1/L2 remain mandatory for diagnosis and regression. L3 is required to prevent architecture from advancing solely on laboratory-style tests.

L3 harness state may be independently observable by the Finish Gate, but mutation must still occur through the accepted product capability surface rather than a hidden test/admin API.

## ADR-036 boundary

The 2026-08-26 Browser Harness review is recorded in `BROWSER_HARNESS_ARCHITECTURE.md` and ADR-036.

It adopts this future authority split:

```text
restricted browser by default
 -> user-owned Site Capability Profile
 -> trusted-site full-browser authority only inside reviewed origin/network scope

separate Local Execution Grant
 -> task-scoped Python/program authority
 -> explicit filesystem/network/process/resource scope
```

Important invariants:

- trusted destination never means trusted page instructions;
- Browser/site trust never automatically grants Windows/filesystem/Python authority;
- local execution trust never automatically grants arbitrary authenticated-browser authority;
- generated helpers remain candidate lineage until separately tested/promoted;
- current six-tool surface and runtime authority are unchanged by ADR-036 itself;
- any later material authority expansion also requires representative L3 evidence, not only primitive contract tests.

## Future tracks

`CONVERSATION_BRIDGE_ARCHITECTURE.md` / Track M, Browser Harness-derived full-browser work, Local Execution Kernel work, and local-planner Track P remain future/parallel unless promoted by the authoritative Roadmap/stage contracts. They do not override the current release-critical sequence.

## Current normal transport invariants

```text
public semantic inventory = exactly six tools
normal semantic binding = direct stdio
normal semantic 1MCP dependency = none
1MCP = optional internal Extension Manager
ordinary ChatGPT = only current general planner
```

## Maintenance rule

Update this map when a reviewed change:

- changes authoritative document names/read order;
- changes general-planner or Control Plane responsibility;
- changes computer-use observation/verification/recovery/completion boundaries;
- changes L1/L2/L3 real-task acceptance requirements;
- changes Browser Harness-derived Site Capability Profiles, browser network trust or Local Execution Grant boundaries;
- changes which document owns project risk, technical debt or release order;
- promotes a research/future track into current implementation authority;
- changes the public Chat-facing capability surface.

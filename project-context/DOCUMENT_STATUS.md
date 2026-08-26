# Documentation Status Map

## Purpose

Prevent stale stage/research/status prose from overriding live repository reality. Before using any document as current truth, resolve live GitHub state.

## Source-of-truth order

```text
current code/tests/current hosted CI/current physical evidence
 > CURRENT_STATE.md / CONTINUATION_CONTEXT.md / START_HERE.md
 > PROJECT_RISKS.md for ranked engineering risk priority
 > ARCHITECTURE.md / CONTROL_PLANE.md / COMPUTER_USE_ARCHITECTURE.md / SECURITY_POLICY.md
 > REAL_TASK_ACCEPTANCE.md for L1/L2/L3 acceptance depth
 > SOURCE_PROVENANCE_ACCEPTANCE.md for physical source-byte binding
 > EXTERNAL_EXECUTION_REUSE_STRATEGY.md for OpenAdapt/UFO integration boundaries
 > active Stage 26.3 contracts
 > BROWSER_HARNESS_ARCHITECTURE.md for ADR-036 reviewed future direction
 > ROADMAP.md
 > TECH_DEBT.md
 > EVIDENCE_INDEX.md
 > accepted historical stage evidence
 > old research/handoffs
```

When documents disagree on whether work is implemented/accepted/current, live code and exact evidence win.

Any `project-context/*.md` document not explicitly listed here is **HISTORICAL / REFERENCE by default** until reviewed promotion.

## Documentation separation rule

```text
architecture/policy docs
  = durable authority, safety and execution boundaries

CURRENT_STATE
  = concise live accepted/current boundary and next work

CONTINUATION_CONTEXT / START_HERE
  = fresh-session continuation/read order

PROJECT_RISKS
  = single authoritative ranked risk table

ROADMAP
  = single owner of explicit release-stage order

REAL_TASK_ACCEPTANCE
  = durable L1/L2/L3 acceptance contract

SOURCE_PROVENANCE_ACCEPTANCE
  = physical acceptance binding between exact head and actual executed source bytes

EXTERNAL_EXECUTION_REUSE_STRATEGY
  = durable OpenAdapt/UFO reuse boundary; external mechanics never replace project authority/verification/completion

TECH_DEBT
  = current implementation/process debt

EVIDENCE_INDEX
  = accepted exact-head/evidence navigation

STAGE*.md
  = active implementation contract or historical qualification record
```

Do not copy full risk rankings, physical dumps or release-stage detail across many live documents.

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
| `CONTINUATION_CONTEXT.md` | AUTHORITATIVE LIVE SNAPSHOT | Continuation point after resolving live GitHub. |
| `START_HERE.md` | AUTHORITATIVE ENTRY | Read order and current focus. |
| `CURRENT_STATE.md` | AUTHORITATIVE CURRENT STATE | Accepted/current boundary and immediate critical path. |
| `PROJECT_RISKS.md` | AUTHORITATIVE RISK REGISTER | Ranked risks, evidence, mitigation and close conditions. |
| `ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURE | Durable component/authority boundaries. |
| `CONTROL_PLANE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | Planner vs deterministic execution/verification/recovery/completion boundary. |
| `COMPUTER_USE_ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | State-first hybrid computer-use contract. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Trust/authorization/privacy/environmental-content/safety boundaries. |
| `REAL_TASK_ACCEPTANCE.md` | AUTHORITATIVE ACCEPTANCE-DIRECTION CONTRACT | L1 primitive, L2 workflow and L3 real-task evidence. |
| `SOURCE_PROVENANCE_ACCEPTANCE.md` | AUTHORITATIVE PHYSICAL-ACCEPTANCE METHODOLOGY | Requires clean-tree/source-hash binding so exact-head evidence proves the bytes actually executed. |
| `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | AUTHORITATIVE INTEGRATION DIRECTION | OpenAdapt as procedure/effect-evidence substrate; UFO as selective Windows/Office component source; project Control Plane/Kernel/Finish Gate remain authoritative. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence and acceptance objectives. |
| `BROWSER_HARNESS_ARCHITECTURE.md` | PROVISIONAL FUTURE ARCHITECTURE / ADR-036 | Future Site Capability/full-browser/helper/Local Execution direction; no current authority by itself. |
| `TECH_DEBT.md` | AUTHORITATIVE TECHNICAL DEBT REGISTER | Existing implementation/process debt. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | This map. |
| `EVIDENCE_INDEX.md` | AUTHORITATIVE EVIDENCE NAVIGATION | Accepted exact heads/evidence locations. |
| `DECISIONS.md` | CURRENT ADR INDEX | Current architectural decisions. |

## Current Stage 26.3 documents

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | CURRENT 26.3 DESIGN CONTRACT | Verified procedure/candidate trust foundations. |
| `STAGE26_3A_IMPLEMENTATION_NOTES.md` | ACCEPTED 26.3A RECORD | Accepted canonical six-tool implementation/evidence. |
| `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` | ACCEPTED 26.3A SURFACE CONTRACT | `procedure_run` in the six-tool surface. |
| `STAGE26_3B_VERIFICATION_KERNEL.md` | ACTIVE 26.3B IMPLEMENTATION CONTRACT | Shared Verification Kernel, accepted file/Browser integrations and active Windows integration. |
| `STAGE26_3B_WINDOWS_VERIFICATION.md` | ACTIVE 26.3B WINDOWS CONTRACT | PR #114 Windows `DesktopState` shared-kernel identity/final-state verification and physical qualification contract. |

## Current implementation snapshot

At the 2026-08-26 post-PR-#113 point:

```text
Stage 26.3A                                      ACCEPTED / MERGED #92
Verification Kernel foundation                  MERGED #99
file/artifact integration                       PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                  MERGED #106
production web_open verification                PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                  MERGED #110
production web_interact verification            PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance                 PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verifier     ACTIVE DRAFT PR #114
Windows/application L3                          NEXT AFTER #114 ACCEPTANCE
WorkingState + recovery + LoopGuard              26.3C TARGET
OpenAdapt procedure/effect-evidence spike        AFTER 26.3C CORE SHAPE
selective UFO Office adapters                    LATER 26.5-ALIGNED WORK
```

PR #113 physical Browser L3 evidence included one target save, one target audit mutation, external `FINISH_GATE=done` and `NON_TARGET_MUTATION=none` on exact physical head `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf`.

The new Source Provenance contract records that PR #113's functional/final-state evidence remains accepted for its historical scope, while its source cleanliness was not proved by the older gate. Before Stage 26.3B is fully closed, repeat one representative Browser L3 under the new clean-tree/source-hash methodology rather than pretending the older gate proved it.

PR #114 adds no public Chat/MCP tool and no Windows action authority. It adapts accepted `DesktopState` evidence to the shared Verification Kernel with mandatory continuity of Windows session, application/executable identity, PID, process generation, HWND and coordinate space. `window_instance` remains validated for internal consistency on each observation but is not required to remain equal when a legitimate title change changes its canonical digest. Physical target qualification is required on the final exact source-provenance-bound head before merge.

## External execution reuse boundary

The project may reuse mature external mechanics without importing a second authority stack:

```text
OpenAdapt
  = internal procedure compiler/runtime/checkpoint/teach/effect-evidence substrate
  != project WorkingState owner
  != project PASS/DONE authority

UFO
  = selective UIA/Win32/COM/Office adapter source
  != HostAgent/AppAgent/Galaxy production planner stack

project Control Plane
  = authority + WorkingState + recovery/budgets
project Verification Kernel
  = PASS | FAIL | UNKNOWN
project Finish Gate
  = DONE | NOT_DONE | UNKNOWN
```

Canonical detail: `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`.

## Real-task acceptance boundary

```text
L1 primitive / contract proof
L2 multi-step component workflow
L3 ordinary user goal + independent final state
```

L1/L2 remain mandatory for diagnosis/regression. L3 prevents architecture from advancing solely on laboratory-style tests. Independent Finish Gate evidence must not be planner-writable and mutation must occur through the accepted product capability surface rather than a hidden test/admin API.

Every future release-critical physical gate must also satisfy `SOURCE_PROVENANCE_ACCEPTANCE.md`; L3 proves behavior, while source provenance proves what bytes were actually under test.

## ADR-036 boundary

Future authority split remains:

```text
restricted browser by default
 -> user-owned Site Capability Profile
 -> trusted-site full-browser authority only inside reviewed origin/network scope

separate Local Execution Grant
 -> task-scoped Python/program authority
 -> explicit filesystem/network/process/resource scope
```

Trusted destination never means trusted instructions. Browser trust does not automatically grant Windows/filesystem/Python authority; local execution trust does not grant authenticated-browser authority. Material authority expansion requires its own acceptance and representative L3 evidence.

## Current normal transport invariants

```text
public semantic inventory = exactly six tools
normal semantic binding = direct stdio
normal semantic 1MCP dependency = none
1MCP = optional internal Extension Manager
ordinary ChatGPT = only current general planner
```

## Maintenance rule

Update this map when a reviewed change alters authoritative document names/read order, planner/Control Plane responsibility, computer-use observation/verification/recovery/completion boundaries, source-provenance requirements, external execution reuse boundaries, L1/L2/L3 requirements, Browser/Local Execution authority, risk/debt/release ownership, future-track promotion, or the public Chat-facing capability surface.

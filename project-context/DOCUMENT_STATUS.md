# Documentation Status Map

## Purpose

Prevent stale stage/research/status prose from overriding live repository reality. Before using any document as current truth, resolve live GitHub state.

## Source-of-truth order

```text
current code/tests/current hosted CI/current physical evidence
 > CURRENT_STATE.md / CONTINUATION_CONTEXT.md / START_HERE.md
 > PROJECT_RISKS.md for ranked engineering risk priority
 > ARCHITECTURE.md / CONTROL_PLANE.md / COMPUTER_USE_ARCHITECTURE.md / SECURITY_POLICY.md
 > ARCHITECTURE_REUSE_BASELINE.md for prior component/reuse role lineage used by stage research
 > CONVERSATION_BRIDGE_ARCHITECTURE.md for ADR-035 future Agent Session / Delegation architecture
 > CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md for ADR-037 future discovery/event-policy substrate
 > REAL_TASK_ACCEPTANCE.md for L1/L2/L3 acceptance depth
 > SOURCE_PROVENANCE_ACCEPTANCE.md for physical source-byte binding
 > EXTERNAL_EXECUTION_REUSE_STRATEGY.md for OpenAdapt/UFO integration boundaries
 > MUTATION_ASSURANCE.md for guarantee mutation/adversarial assurance direction
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
  = durable boundaries and invariants for authority, safety and execution

ARCHITECTURE_REUSE_BASELINE
  = canonical prior decision/reuse lineage for comparison by future Stage Research

CURRENT_STATE
  = concise live accepted/current boundary and immediate critical path

CONTINUATION_CONTEXT / START_HERE
  = fresh-session continuation/read order

PROJECT_RISKS
  = single authoritative ranked risk table

ROADMAP
  = single owner of explicit release-stage order

EVIDENCE_INDEX
  = exact accepted heads, local result locators and scoped measurements

MUTATION_ASSURANCE
  = guarantee-oriented mutation/adversarial policy and permanent defect-class catalog

STAGE*.md
  = active implementation contract or historical qualification record
```

Do not copy full risk rankings, exact acceptance dumps, local paths or release-stage detail across many live documents. Live context should point to `EVIDENCE_INDEX.md` for exact evidence.

`ARCHITECTURE_REUSE_BASELINE.md` must not become a second module catalog or roadmap. It records which architectural role was previously assigned to which selected external mechanism or project-owned boundary, what was intended to be reused, and why. Fresh Stage Research may keep, refine, replace, reject, defer, or reuse more of that choice when current evidence justifies it.

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
| `ARCHITECTURE_REUSE_BASELINE.md` | AUTHORITATIVE RESEARCH COMPARISON BASELINE | Prior selected component/project-owned role lineage that applicable Stage Research must compare before silently duplicating or replacing a mechanism. |
| `CONVERSATION_BRIDGE_ARCHITECTURE.md` | PROVISIONAL AUTHORITATIVE FUTURE ARCHITECTURE / ADR-035 | Agent Session / Delegation object model and cross-provider Browser Companion/native routing. No current runtime authority by itself. |
| `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` | PROVISIONAL AUTHORITATIVE FUTURE ARCHITECTURE / ADR-037 | Capability discovery + typed event/policy-hook substrate. No current runtime authority by itself. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Trust/authorization/privacy/environmental-content/safety boundaries. |
| `REAL_TASK_ACCEPTANCE.md` | AUTHORITATIVE ACCEPTANCE-DIRECTION CONTRACT | L1 primitive, L2 workflow and L3 real-task evidence. |
| `SOURCE_PROVENANCE_ACCEPTANCE.md` | AUTHORITATIVE PHYSICAL-ACCEPTANCE METHODOLOGY | Clean-tree/source/install binding so evidence proves bytes actually executed. |
| `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | AUTHORITATIVE INTEGRATION DIRECTION | OpenAdapt/UFO integration boundaries; project authority remains authoritative. |
| `MUTATION_ASSURANCE.md` | AUTHORITATIVE ASSURANCE DIRECTION | CAP-M guarantee mutants, adversarial behavioral cases and 26.3C CAP-M7 obligations. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence plus parallel future tracks. |
| `BROWSER_HARNESS_ARCHITECTURE.md` | PROVISIONAL FUTURE ARCHITECTURE / ADR-036 | Future Site Capability/full-browser/helper/Local Execution direction; no current authority by itself. |
| `TECH_DEBT.md` | AUTHORITATIVE TECHNICAL DEBT REGISTER | Existing implementation/process debt. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | This map. |
| `EVIDENCE_INDEX.md` | AUTHORITATIVE EVIDENCE NAVIGATION | Exact accepted heads and scoped evidence locations. |
| `DECISIONS.md` | CURRENT ADR INDEX | Architectural decisions including ADR-035/036/037. |

## Stage 26.3 document status

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | ACCEPTED FOUNDATION / REFERENCE | Verified procedure/candidate trust foundations. |
| `STAGE26_3A_IMPLEMENTATION_NOTES.md` | ACCEPTED 26.3A RECORD | Accepted canonical six-tool implementation/evidence. |
| `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` | ACCEPTED 26.3A SURFACE CONTRACT | `procedure_run` in the six-tool surface. |
| `STAGE26_3B_VERIFICATION_KERNEL.md` | ACCEPTED 26.3B CONTRACT / HISTORICAL IMPLEMENTATION RECORD | Shared Verification Kernel and file/Browser/Windows integration lineage. 26.3B is no longer the active stage. |
| `STAGE26_3B_WINDOWS_VERIFICATION.md` | ACCEPTED 26.3B WINDOWS RECORD / CONTRACT | PR #114 Windows `DesktopState` shared-kernel lineage; #115 supplies representative application L3. |

Stage 26.3B is accepted for the recorded representative scope after #118. New work belongs to Stage 26.3C rather than continuing to label `STAGE26_3B_VERIFICATION_KERNEL.md` as an active implementation contract.

## Current implementation snapshot

Resolve live `main` for the exact commit. Current semantic state is:

```text
Stage 26.3A                                      ACCEPTED / MERGED #92
Verification Kernel foundation                  MERGED #99
file/artifact integration                       PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                  MERGED #106
production web_open verification                PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                  MERGED #110
production web_interact verification            PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance                 PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verifier     PHYSICAL ACCEPTED / MERGED #114
Windows/application L3                          PHYSICAL ACCEPTED / MERGED #115
CAP-M0 mutation assurance                       ACCEPTED / MERGED #117
Track M + ADR-037 docs                          MERGED #116 / FUTURE AUTHORITY ONLY
Browser stronger-provenance repeat              PHYSICAL ACCEPTED / MERGED #118
adversarial assurance plan                      MERGED #119
Stage 26.3B                                     ACCEPTED / CLOSED FOR RECORDED SCOPE
WorkingState + recovery/reconciliation/LoopGuard STAGE 26.3C CURRENT TARGET
Track M Agent Session / Delegation              PARALLEL FUTURE ARCHITECTURE / NO RUNTIME AUTHORITY
CapabilityRegistry + TypedEventBus/PolicyHooks  FUTURE ARCHITECTURE / NO RUNTIME AUTHORITY
OpenAdapt procedure/effect-evidence spike       AFTER 26.3C CORE SHAPE
```

Exact physical acceptance heads and result paths are indexed in `EVIDENCE_INDEX.md` rather than duplicated here.

## Browser accepted-scope note

The accepted Browser L3 route is target-Windows headless Playwright/Chrome through the semantic Browser capability. It does not by itself prove visible headed browser-window control on the Windows desktop.

The stronger #118 acceptance also established that independent audit/Finish Gate evidence outranks planner self-report. Earlier invalid physical attempts exposed harness/runtime defects and were rejected, then converted into permanent assurance direction in `MUTATION_ASSURANCE.md`.

## Track M / ADR-035 boundary

Track M is future architecture only and adds no current public tool/runtime authority.

Canonical identities:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Browser Companion is the primary cross-provider web adapter family. `GenericChatAdapter` owns common extraction/normalization/fallback; thin provider adapters remain for exact selectors, identity and quirks. Stronger reviewed native routes are preferred per exact target where available.

## Capability Registry + Event / Policy Hooks / ADR-037 boundary

Canonical invariants:

```text
CapabilityRegistry
  = semantic discovery / availability / health / trust metadata
  != authorization
  != generic dispatch

TypedEventBus
  = typed lifecycle/observation trigger stream
  != proof that an external effect succeeded
  != WorkingState source of truth

PolicyHooks
  = registered bounded deterministic handlers
  != second planner
  != verifier / Finish Gate replacement
```

26.3C may add only minimal internal seams useful for WorkingState/recovery/LoopGuard/Finish Gate.

## Maintenance rule

Update this map when a reviewed change alters authoritative document names/read order, planner/Control Plane responsibility, architecture reuse baseline ownership or comparison semantics, computer-use or Agent Session observation/verification/recovery/completion boundaries, capability discovery/event-policy architecture, mutation/adversarial assurance semantics, source-provenance requirements, external execution reuse boundaries, L1/L2/L3 requirements, Browser/Local Execution authority, risk/debt/release ownership, future-track promotion, or the public Chat-facing capability surface.

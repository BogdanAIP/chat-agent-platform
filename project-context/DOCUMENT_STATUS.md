# Documentation Status Map

## Purpose

Prevent stale stage/research/status prose from overriding live repository reality. Before using any document as current truth, resolve live GitHub state.

## Source-of-truth order

```text
current code/tests/current hosted CI/current physical evidence
 > CURRENT_STATE.md / CONTINUATION_CONTEXT.md / START_HERE.md
 > PROJECT_RISKS.md for ranked engineering risk priority
 > ARCHITECTURE.md / CONTROL_PLANE.md / COMPUTER_USE_ARCHITECTURE.md / SECURITY_POLICY.md
 > CONVERSATION_BRIDGE_ARCHITECTURE.md for ADR-035 future Agent Session / Delegation architecture
 > CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md for ADR-037 future discovery/event-policy substrate
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
  = durable boundaries and invariants for authority, safety and execution

CONVERSATION_BRIDGE_ARCHITECTURE
  = durable future Track M Agent Session / Delegation object model,
    adapter/routing, ownership, idempotency, correlation and staged acceptance direction

CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE
  = durable future capability discovery + typed event/policy-hook substrate,
    including WorkingState/Skill/Track M/ScheduledTask integration seams

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
  = exact accepted heads and scoped evidence navigation

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
| `ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURE | Durable component/authority boundaries, including future Agent Sessions beside core capabilities. |
| `CONTROL_PLANE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | Planner vs deterministic execution/verification/recovery/completion boundary, including future delegation/operation state seams. |
| `COMPUTER_USE_ARCHITECTURE.md` | AUTHORITATIVE ARCHITECTURAL DIRECTION | State-first hybrid computer-use contract. |
| `CONVERSATION_BRIDGE_ARCHITECTURE.md` | PROVISIONAL AUTHORITATIVE FUTURE ARCHITECTURE / ADR-035 | Agent Session / Delegation object model, native-harness-first adapters, Conversation Bridge fallback, ownership/idempotency/correlation and M0-M8 direction. No current runtime authority by itself. |
| `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` | PROVISIONAL AUTHORITATIVE FUTURE ARCHITECTURE / ADR-037 | Project-owned CapabilityRegistry plus TypedEventBus/PolicyHooks, with strict availability-vs-authorization, event-vs-verification and staged Skill/Track M/ScheduledTask integration. No current runtime authority by itself. |
| `SECURITY_POLICY.md` | CURRENT POLICY | Trust/authorization/privacy/environmental-content/safety boundaries, including future worker/session authority. |
| `REAL_TASK_ACCEPTANCE.md` | AUTHORITATIVE ACCEPTANCE-DIRECTION CONTRACT | L1 primitive, L2 workflow and L3 real-task evidence. |
| `SOURCE_PROVENANCE_ACCEPTANCE.md` | AUTHORITATIVE PHYSICAL-ACCEPTANCE METHODOLOGY | Requires clean-tree/source-hash binding so exact-head evidence proves the bytes actually executed. |
| `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | AUTHORITATIVE INTEGRATION DIRECTION | OpenAdapt as procedure/effect-evidence substrate; UFO as selective Windows/Office component source; project Control Plane/Kernel/Finish Gate remain authoritative. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence plus parallel Track M M0-M8 progression. |
| `BROWSER_HARNESS_ARCHITECTURE.md` | PROVISIONAL FUTURE ARCHITECTURE / ADR-036 | Future Site Capability/full-browser/helper/Local Execution direction; no current authority by itself. |
| `TECH_DEBT.md` | AUTHORITATIVE TECHNICAL DEBT REGISTER | Existing implementation/process debt. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | This map. |
| `EVIDENCE_INDEX.md` | AUTHORITATIVE EVIDENCE NAVIGATION | Exact accepted heads and scoped evidence locations. |
| `DECISIONS.md` | CURRENT ADR INDEX | Current architectural decisions including ADR-035/036/037. |

## Current Stage 26.3 documents

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | CURRENT 26.3 DESIGN CONTRACT | Verified procedure/candidate trust foundations. |
| `STAGE26_3A_IMPLEMENTATION_NOTES.md` | ACCEPTED 26.3A RECORD | Accepted canonical six-tool implementation/evidence. |
| `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` | ACCEPTED 26.3A SURFACE CONTRACT | `procedure_run` in the six-tool surface. |
| `STAGE26_3B_VERIFICATION_KERNEL.md` | ACTIVE 26.3B IMPLEMENTATION CONTRACT | Shared Verification Kernel and accepted file/Browser/Windows integration direction. |
| `STAGE26_3B_WINDOWS_VERIFICATION.md` | ACCEPTED 26.3B WINDOWS VERIFIER RECORD / CONTRACT | PR #114 Windows `DesktopState` shared-kernel identity/final-state verification and physical qualification lineage. |

Live PR #115 and its acceptance assets currently own the representative Windows/application L3 implementation details; do not rewrite #115 from stale prose in older stage documents.

## Current implementation snapshot

At the 2026-08-27 documentation synchronization point:

```text
main                                              cc0fa3d1b7afe9d833334ae68482d2d3dca4b818
Stage 26.3A                                      ACCEPTED / MERGED #92
Verification Kernel foundation                  MERGED #99
file/artifact integration                       PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                  MERGED #106
production web_open verification                PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                  MERGED #110
production web_interact verification            PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance                 PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verifier     ACCEPTED / MERGED #114
Windows/application L3                          ACTIVE DRAFT PR #115
WorkingState + recovery + LoopGuard              26.3C TARGET
Track M Agent Session / Delegation               PARALLEL FUTURE ARCHITECTURE / NO RUNTIME AUTHORITY
CapabilityRegistry + TypedEventBus/PolicyHooks   FUTURE ARCHITECTURE / ADR-037 / NO RUNTIME AUTHORITY
OpenAdapt procedure/effect-evidence spike        AFTER 26.3C CORE SHAPE
selective UFO Office adapters                    LATER 26.5-ALIGNED WORK
```

PR #113 physical Browser L3 evidence included one target save, one target audit mutation, external `FINISH_GATE=done` and `NON_TARGET_MUTATION=none` on exact physical head `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf`.

The Source Provenance contract records that PR #113's functional/final-state evidence remains accepted for its historical scope, while its source cleanliness was not proved by the older gate. Before Stage 26.3B is fully closed, repeat one representative Browser L3 under the new clean-tree/source-hash methodology rather than pretending the older gate proved it.

PR #114 adds no public Chat/MCP tool and no new Windows action authority. It is now accepted/merged for the recorded shared-kernel verification scope.

PR #115 builds the representative Windows/application L3 on top of #114 through a bounded registered procedure, fresh Windows observations/shared-kernel transition verification, external independent Finish Gate and source/install/runtime provenance. It remains draft until hosted and target-Windows physical evidence are complete on one final exact head.

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

Canonical routing:

```text
official/project-owned harness API / local host protocol
 -> validated provider/session native route
 -> Browser Companion + GenericChatAdapter DOM/accessibility
 -> reviewed GUI/visual fallback
 -> ABSTAIN
```

Key boundaries:

- `session_id` is not `delegation_id`;
- HandoffPack is task data, not permission authority;
- queued send is distinct from stronger steer/interrupt effects;
- delivery is not worker completion or task DONE;
- worker result requires delegation/work-unit correlation;
- stable logical operation id + reconciliation precede retry after ambiguous mutation;
- session discoverability is not lifecycle ownership;
- workers do not inherit manager lifecycle authority;
- initial multi-worker topology defaults to `max_spawn_depth = 1`;
- project/workspace/worktree lifecycle is a separate stronger consequence class;
- Stage 26.3C reserves only compatible state/recovery seams, not Track M runtime.

Canonical detail: `CONVERSATION_BRIDGE_ARCHITECTURE.md` and ADR-035.

## Capability Registry + Event / Policy Hooks / ADR-037 boundary

ADR-037 is future shared infrastructure only and adds no current public tool/runtime authority.

Canonical invariants:

```text
CapabilityRegistry
  = descriptive semantic discovery / availability / health / trust metadata
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

Key boundaries:

- `AVAILABLE -> ACTIVE -> AUTHORIZED` remains authoritative; registry availability cannot skip authorization;
- raw MCP/provider catalogs are not promoted directly to planner-visible trusted capabilities;
- event delivery triggers fresh authoritative re-observation where effect state matters;
- hook output cannot widen grants or convert `FAIL/UNKNOWN` to `PASS` or `NOT_DONE/UNKNOWN` to `DONE`;
- initial hooks are project-owned registered handlers, not arbitrary shell/Python scripts;
- Skills reference required capabilities/grants; Skill text cannot create missing authority;
- Stage 26.3C may add only the minimal typed event/read-only descriptor seams useful for recovery/LoopGuard/Finish Gate;
- Scheduled Tasks remain later work and must use explicit scheduled-run grants rather than inheriting every interactive capability.

Canonical detail: `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` and ADR-037.

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

Future Track M real authenticated mutations require the same acceptance philosophy, including exact worker/session identity, intended-only message/delegation/session mutation, result correlation, bounded fan-out and independent final-state evidence.

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

Update this map when a reviewed change alters authoritative document names/read order, planner/Control Plane responsibility, computer-use or Agent Session observation/verification/recovery/completion boundaries, capability discovery/event-policy architecture, source-provenance requirements, external execution reuse boundaries, L1/L2/L3 requirements, Browser/Local Execution authority, risk/debt/release ownership, future-track promotion, or the public Chat-facing capability surface.
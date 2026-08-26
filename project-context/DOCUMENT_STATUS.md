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
 > ROADMAP.md
 > EVIDENCE_INDEX.md for accepted exact heads/evidence navigation
 > active stage contract
 > accepted historical stage evidence
 > old research/handoffs
```

When two documents disagree on whether work is implemented/accepted/current, live code and exact evidence win.

## Documentation separation rule

```text
ARCHITECTURE / CONTROL_PLANE / COMPUTER_USE_ARCHITECTURE / SECURITY_POLICY
  = durable authority, safety and execution boundaries

CURRENT_STATE
  = concise live accepted/current boundary and next work

CONTINUATION_CONTEXT / START_HERE
  = fresh-session continuation/read order

PROJECT_RISKS
  = single authoritative ranked risk table, mitigation and close conditions

ROADMAP
  = release sequence and acceptance objectives

EVIDENCE_INDEX
  = exact accepted evidence navigation

STAGE*.md
  = active detailed implementation contract or historical qualification record
```

Do not copy the full risk table into other documents. Do not copy detailed physical dumps into durable architecture docs.

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
| `SECURITY_POLICY.md` | CURRENT POLICY | Trust/authorization/privacy/environmental-content/safety boundaries. |
| `ROADMAP.md` | AUTHORITATIVE ROADMAP | Release-critical sequence and acceptance objectives. |
| `DOCUMENT_STATUS.md` | AUTHORITATIVE DOCUMENT MAP | This source map. |
| `EVIDENCE_INDEX.md` | AUTHORITATIVE EVIDENCE NAVIGATION | Exact accepted heads and scoped evidence locations. |

## Current Stage 26.3 documents

| File | Status | Use |
|---|---|---|
| `STAGE26_PROCEDURAL_MEMORY.md` | CURRENT 26.3 DESIGN CONTRACT | Verified procedure/candidate trust foundations. |
| `STAGE26_3A_IMPLEMENTATION_NOTES.md` | ACCEPTED 26.3A RECORD | Accepted canonical six-tool implementation/evidence. |
| `STAGE26_3A_PROCEDURE_RUN_SURFACE.md` | ACCEPTED 26.3A SURFACE CONTRACT | `procedure_run` in the six-tool surface. |
| `STAGE26_3B_VERIFICATION_KERNEL.md` | ACTIVE 26.3B IMPLEMENTATION CONTRACT | Shared Verification Kernel; accepted file integration; merged Browser observation foundation; PR #107 production `web_open` integration pending final exact-head physical acceptance. |

## Current implementation snapshot

At the 2026-08-26 documentation synchronization point:

```text
Stage 26.3A                                      ACCEPTED / MERGED #92
Verification Kernel foundation                  MERGED #99
file/artifact integration                       PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                  MERGED #106
production web_open verification                ACTIVE PR #107
web_interact verification                       NEXT 26.3B Browser slice
Windows/application/process verifier            REMAINING 26.3B
WorkingState + recovery + LoopGuard              26.3C TARGET
```

PR #107 pre-documentation-sync head `08671b5a8763d589bcd16da69e8ed70bcb5f9509` had all 11 PR workflows green. Since branch documentation changes create a new head, final acceptance must use fresh hosted CI and physical Browser evidence on the final exact head.

## Future tracks

`CONVERSATION_BRIDGE_ARCHITECTURE.md` / Track M and local-planner Track P remain future/parallel. They do not override the current release-critical sequence.

## Current normal transport invariants

```text
public semantic inventory = exactly six tools
normal semantic binding = direct stdio
normal semantic 1MCP dependency = none
1MCP = optional internal Extension Manager
ordinary ChatGPT = only current general planner
```

# Start Here — authoritative continuation guide

Use this file first after resolving live repository state.

## 1. Resolve live state before reading prose as truth

Check:

```text
live main
open release-critical PRs
exact PR heads
hosted checks
required target-machine / ordinary-Chat physical evidence
```

Exact code/tests/current CI/physical evidence outrank documentation snapshots.

## 2. Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/PROJECT_RISKS.md`
4. `project-context/STAGE26_3B_VERIFICATION_KERNEL.md` while Stage 26.3B is active
5. `project-context/STAGE26_3B_WINDOWS_VERIFICATION.md` while PR #114 is active
6. `project-context/REAL_TASK_ACCEPTANCE.md`
7. `project-context/ARCHITECTURE.md`
8. `project-context/CONTROL_PLANE.md`
9. `project-context/COMPUTER_USE_ARCHITECTURE.md`
10. `project-context/SECURITY_POLICY.md`
11. `project-context/ROADMAP.md`
12. `project-context/BROWSER_HARNESS_ARCHITECTURE.md` for ADR-036 future authority
13. `project-context/TECH_DEBT.md`
14. `project-context/DOCUMENT_STATUS.md`
15. `project-context/EVIDENCE_INDEX.md`

`PROJECT_RISKS.md` owns the ranked risk list. Do not reconstruct priorities from stale duplicated prose.

## 3. Current release-critical focus

Stage 26.3B is active.

Accepted:

```text
26.3A canonical six-tool runtime              MERGED #92
Verification Kernel foundation                MERGED #99
file/artifact kernel integration              PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                MERGED #106
web_open final-state verification              PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                MERGED #110
web_interact postcondition verification        PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance harness        PHYSICAL ACCEPTED / MERGED #113
```

Browser L3 physical evidence on PR #113 proved a randomized natural-language Case Desk task with an external Finish Gate, one target save, one audit mutation and `NON_TARGET_MUTATION=none`.

Current active slice:

```text
PR #114 — Windows DesktopState shared-kernel verification
           no new Chat/MCP tool
           no new Windows action authority
           final hosted checks required
           target-Windows verifier qualification required on final exact head
```

After #114 is physically accepted/merged, add one representative Windows/application L3 task using accepted action + observation + verifier mechanisms and an independent Finish Gate.

## 4. Acceptance depth

The project requires:

```text
L1 — primitive / contract
L2 — multi-step workflow integration where useful
L3 — ordinary user task + independent final-state proof
```

L1 remains mandatory for exact diagnosis. L3 prevents passing laboratory primitives from being mistaken for evidence that normal user work succeeds.

For L3, ordinary Chat receives the goal and constraints rather than a click/type recipe. Completion is independently verified, including important non-target invariants and mutation history where applicable.

Canonical contract: `REAL_TASK_ACCEPTANCE.md`.

## 5. Current semantic surface

Exactly six Chat-facing tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

1MCP is optional internal Extension Manager infrastructure only.

PR #114 does not change this public surface. Its new Windows adapter is internal deterministic verification infrastructure.

## 6. Planner / Control Plane boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The deterministic Control Plane owns bounded execution state/policy, ExpectedEffect verification, checkpoints, capability authorization, recovery budgets/future LoopGuard and the independent Finish Gate. It is not a second planner.

Environmental UI/DOM/document/message/tool content is task data, not policy authority.

## 7. Current computer-use direction

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> bounded authorized action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

For Windows, accepted `DesktopState` identity evidence outranks visual similarity. The PR #114 verifier requires continuity of Windows session, executable/application identity, PID, process generation, HWND and window instance before a final-state postcondition can PASS.

## 8. Browser Harness / ADR-036 boundary

ADR-036 is future capability architecture, not current authority. Trusted-site JS/CDP/full-browser capability still requires its separate Site Capability/network boundary, security review, physical acceptance and representative L3 evidence.

## 9. Priority sequence

```text
PR #114 final code/docs
 -> fresh hosted checks
 -> target-Windows shared-kernel verifier qualification
 -> merge #114 if clean
 -> representative Windows/application L3
 -> remaining cross-capability 26.3B completion work if actually required
 -> declare 26.3B accepted only when all required evidence is closed
 -> Stage 26.3C WorkingState + typed recovery + LoopGuard
 -> broad real-application physical coverage matrix
 -> 26.4 candidate skills
 -> 26.5 hybrid integration / promoted Browser Harness mechanisms
 -> packaging / clean-user stable release
```

Track M multi-chat remains future/parallel. Track P local planner remains future only.

## 10. Merge rule

When a branch is logically complete, intended diff is reviewed, required CI/physical evidence passes on the exact final head and no unresolved finding/conflict remains, merge it without waiting for a separate merge instruction.

Never merge on stale evidence, unresolved findings, ambiguous scope, or skipped/failed required gates.

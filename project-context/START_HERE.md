# Start Here — authoritative continuation guide

Use this file first after resolving live repository state.

## 1. Resolve live state before reading prose as truth

Check:

```text
live main
open release-critical PRs
exact PR heads
hosted checks
required target-machine/ordinary-Chat physical evidence
```

Exact code/tests/current CI/physical evidence outrank documentation snapshots.

## 2. Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/PROJECT_RISKS.md`
4. `project-context/STAGE26_3B_VERIFICATION_KERNEL.md` while Stage 26.3B is active
5. `project-context/REAL_TASK_ACCEPTANCE.md`
6. `project-context/ARCHITECTURE.md`
7. `project-context/CONTROL_PLANE.md`
8. `project-context/COMPUTER_USE_ARCHITECTURE.md`
9. `project-context/SECURITY_POLICY.md`
10. `project-context/ROADMAP.md`
11. `project-context/BROWSER_HARNESS_ARCHITECTURE.md` when working on ADR-036 future authority
12. `project-context/TECH_DEBT.md` for maintenance debt
13. `project-context/DOCUMENT_STATUS.md`
14. `project-context/EVIDENCE_INDEX.md` for exact accepted evidence

Do not maintain competing risk rankings in multiple documents. `PROJECT_RISKS.md` is authoritative for score/priority/close conditions.

## 3. Current release-critical focus

Stage 26.3B is active.

Accepted:

```text
26.3A canonical six-tool runtime             MERGED #92
Verification Kernel foundation               MERGED #99
file/artifact kernel integration             PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation               MERGED #106
web_open final-state verification             PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs               MERGED #110
web_interact postcondition verification       PHYSICAL ACCEPTED / MERGED #111
```

Current:

```text
PR #113 — clean post-#111 Browser L3 real-task acceptance harness
           fresh hosted checks required on final exact head
           ordinary-Chat target-Windows Case Desk L3 + external Finish Gate pending

PR #112 — historical stacked draft superseded by #113
```

The first Browser L3 task is now the active release-critical gate. It must pass before proceeding to Windows/application/process verification.

## 4. Acceptance depth

The project requires three complementary levels:

```text
L1 — primitive / contract
L2 — multi-step workflow integration
L3 — ordinary user task + independent final-state proof
```

L1 stays mandatory for exact diagnosis. L3 prevents laboratory tests from being mistaken for evidence that the agent can perform normal user work.

For L3, give ordinary ChatGPT the user goal and constraints, not a click/type recipe. Verify the final persisted state independently and check important non-target invariants and mutation history.

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

1MCP is optional internal Extension Manager infrastructure, not baseline transport or authority.

## 6. Planner / Control Plane boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The deterministic Control Plane owns bounded execution state/policy:

```text
TaskState / future WorkingState
capability policy + authorization
ExpectedEffect/postconditions
fresh verification
checkpoints
recovery budgets / future LoopGuard
independent Finish Gate
safety/policy result
```

It may advance already-defined authorized+verified transitions. Novel strategy stays above that boundary.

## 7. Current computer-use direction

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> bounded action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

Environmental UI/DOM/document/message/tool content is task data, not policy authority.

## 8. Browser Harness / ADR-036 boundary

ADR-036 records future capability architecture; it does not itself grant new runtime authority or change the six-tool surface.

Before trusted-site JS/CDP/full-browser authority is accepted, the Browser Site Capability / network boundary must be implemented, tested and physically accepted. TD-001 tracks that prerequisite debt. Any material widened authority also requires representative L3 evidence.

## 9. Priority sequence

```text
freeze final PR #113 head
 -> fresh hosted checks
 -> prepare randomized Case Desk run
 -> ordinary-Chat Browser L3 real-task gate
 -> external Finish Gate
 -> merge #113 if clean
 -> Windows/application/process verification
 -> representative Windows/application L3
 -> close remaining Stage 26.3B gates
 -> Stage 26.3C WorkingState + typed recovery + LoopGuard
 -> broad real-application physical coverage matrix
 -> 26.4 candidate skills
 -> 26.5 hybrid integration / promoted Browser Harness mechanisms
 -> packaging / clean-user stable release
```

Track M multi-chat remains future/parallel. Track P local planner is **future only**. Neither may displace unfinished prerequisites.

## 10. Merge rule

When a branch is logically complete, intended diff is reviewed, required CI/physical evidence passes on the exact head and no unresolved finding/conflict remains, merge it without waiting for a separate merge command.

Never merge on stale evidence, unresolved review findings, ambiguous scope or required skipped/failed gates.

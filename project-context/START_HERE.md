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
5. `project-context/ARCHITECTURE.md`
6. `project-context/CONTROL_PLANE.md`
7. `project-context/COMPUTER_USE_ARCHITECTURE.md`
8. `project-context/SECURITY_POLICY.md`
9. `project-context/ROADMAP.md`
10. `project-context/BROWSER_HARNESS_ARCHITECTURE.md` when working on ADR-036 future authority
11. `project-context/TECH_DEBT.md` for maintenance debt
12. `project-context/DOCUMENT_STATUS.md`
13. `project-context/EVIDENCE_INDEX.md` for exact accepted evidence

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
```

Current:

```text
PR #110 — documentation/ADR-036/technical-debt synchronization
PR #111 — production web_interact postcondition verification (draft)
```

PR #107 was physically accepted on its exact pre-merge head and is already in `main`. Do not repeat its gate as current work.

PR #111 is the active release-critical Browser slice. It requires fresh hosted CI and an ordinary-Chat target-Windows physical interaction regression on the final exact head before merge.

## 4. Current semantic surface

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
 -> direct stdio semantic launcher
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

1MCP is optional internal Extension Manager infrastructure, not baseline transport or authority.

## 5. Planner / Control Plane boundary

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

A planner-neutral adapter contract is a tracked risk mitigation target after WorkingState stabilizes; it is not a reason to build a second planner now.

## 6. Current computer-use direction

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

## 7. Browser Harness / ADR-036 boundary

ADR-036 records future capability architecture; it does not itself grant new runtime authority or change the six-tool surface.

Current Stage 26.3B acceptance remains focused on verification. Browser Harness-derived mechanisms align with later work as follows:

```text
26.3C -> trust/grant lifetime state
26.4  -> generated helper candidate lineage
26.5  -> trusted-site full-browser / Browser Companion integration
```

Before trusted-site JS/CDP/full-browser authority is accepted, the Browser Site Capability / network boundary must be implemented, tested and physically accepted. TD-001 tracks that prerequisite debt.

## 8. Priority sequence

```text
finish/synchronize PR #110
 -> final exact-head hosted CI for PR #111
 -> ordinary-Chat target-Windows web_interact physical gate
 -> merge #111 if clean
 -> remaining Stage 26.3B Windows/application/process verification
 -> Stage 26.3C WorkingState + typed recovery + LoopGuard
 -> broad real-application physical coverage matrix
 -> 26.4 candidate skills
 -> 26.5 hybrid integration / promoted Browser Harness mechanisms
 -> packaging / clean-user stable release
```

Track M multi-chat and Track P local planner remain parallel/future and must not displace unfinished prerequisites.

## 9. Merge rule

When a branch is logically complete, intended diff is reviewed, required CI/physical evidence passes on the exact head and no unresolved finding/conflict remains, merge it without waiting for a separate merge command.

Never merge on stale evidence, unresolved review findings, ambiguous scope or required skipped/failed gates.

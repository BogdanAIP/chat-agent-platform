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
10. `project-context/DOCUMENT_STATUS.md`
11. `project-context/EVIDENCE_INDEX.md` for exact accepted evidence

Do not maintain competing risk rankings in multiple documents. `PROJECT_RISKS.md` is authoritative for score/priority/close conditions.

## 3. Current release-critical focus

Stage 26.3B is active.

Accepted:

```text
26.3A canonical six-tool runtime             MERGED #92
Verification Kernel foundation               MERGED #99
file/artifact kernel integration             PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation               MERGED #106
```

Active:

```text
PR #107 — production web_open final-state verification
```

The pre-documentation-sync head `08671b5a8763d589bcd16da69e8ed70bcb5f9509` had all 11 PR workflows green. Because documentation synchronization changes the branch head, resolve the final exact head and require hosted CI on that exact head before the ordinary-Chat target-Windows physical Browser gate.

Do not merge PR #107 until that physical gate passes and no unresolved finding remains.

Next functional slice after #107: `web_interact` click/type/control-result verification.

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

## 7. Priority sequence

```text
finish PR #107 exact-head hosted + physical gate
 -> remaining Stage 26.3B verification integration
 -> Stage 26.3C WorkingState + typed recovery + LoopGuard
 -> broad real-application physical coverage matrix
 -> 26.4 candidate skills
 -> 26.5 hybrid integration
 -> packaging / clean-user stable release
```

Track M multi-chat and Track P local planner remain parallel/future and must not displace unfinished prerequisites.

## 8. Merge rule

When a branch is logically complete, intended diff is reviewed, required CI/physical evidence passes on the exact head and no unresolved finding/conflict remains, merge it without waiting for a separate merge command.

Never merge on stale evidence, unresolved review findings, ambiguous scope or required skipped/failed gates.

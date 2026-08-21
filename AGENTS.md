# Agent Entry Point

This repository is designed to be continued safely from a fresh ordinary ChatGPT session.

## Read first

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/START_HERE.md`
3. `project-context/CURRENT_STATE.md`
4. `project-context/ARCHITECTURE.md`
5. `project-context/CONTROL_PLANE.md`
6. `project-context/ROADMAP.md`
7. `project-context/DOCUMENT_STATUS.md`
8. `project-context/MODULE_CATALOG.md`
9. `project-context/KNOWN_ISSUES.md`
10. active Stage 26.3 contract/design, currently `project-context/STAGE26_PROCEDURAL_MEMORY.md`
11. accepted Stage 26.2E evidence in `project-context/STAGE26_2E_REAL_APPLICATION_E2E.md` when exact real-app details are needed
12. older stage/research documents only as historical evidence when `DOCUMENT_STATUS.md` classifies them that way

## Source-of-truth order

When documents disagree:

1. current code/tests + exact current PR/CI/physical target evidence;
2. `CONTINUATION_CONTEXT.md`, `START_HERE.md`, `CURRENT_STATE.md`;
3. `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `ROADMAP.md`;
4. current policy/catalog docs and active stage contract;
5. accepted historical stage evidence;
6. old research/handoffs.

`DOCUMENT_STATUS.md` classifies every `project-context/*.md` file. Old `ACTIVE`, `NEXT`, `CURRENT` or future-stage prose inside a document classified as historical is not a live roadmap instruction.

Always resolve live `main` and relevant PR heads before branching/editing. A documentation SHA is a snapshot, not a permanently current integration line.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources for development, review, orchestration or execution unless the user explicitly re-enables them later.

## Current architecture boundary

Ordinary ChatGPT is the **only current general planner/intelligence layer**. The local platform owns a **deterministic execution Control Plane** for state, selected procedure progression, authorization, verification, checkpoints, bounded recovery and resource budgets.

```text
ordinary ChatGPT
  general goal interpretation / strategy / adaptation
        |
        v
local deterministic Control Plane
  TaskState / ProgramGraph state
  policy / authorization
  checkpoints / verifier / bounded recovery / budgets
        |
        v
focused Files / Browser / Windows capabilities
```

The Control Plane may advance already-selected known procedure transitions without returning to ChatGPT after every low-level action, but it must ABSTAIN/escalate when live state is novel, ambiguous, stale, incompatible or requires a new strategy.

Do **not** confuse a deterministic Control Plane with a second general planner. Read `project-context/CONTROL_PLANE.md` before changing this boundary.

## Public semantic contract

Current Chat-facing tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Normal path:

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused backends/adapters
```

1MCP remains internal replaceable diagnostic/adaptive/aggregation infrastructure. `semantic-projection` remains a deterministic truthful capability boundary; it is not the procedure Control Plane.

Any Stage 26.3 public procedure surface must be introduced explicitly through a dedicated truthful typed contract/ADR. Never hide Windows/procedure consequences behind `web_interact`, generic `tool_invoke`, shell/Python execution or an opaque workflow dispatcher.

## Non-negotiable invariants

- ordinary ChatGPT is the only **current general** planner/intelligence;
- a focused deterministic local execution Control Plane is allowed/desired and is the active Stage 26.3 direction;
- no current second local general planner/autonomous strategy brain;
- model/procedure/planner output never self-authorizes an action;
- observation is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not completion evidence;
- stale/ambiguous/UNKNOWN evidence causes zero mutation;
- no generic hidden `tool_invoke`, shell/Python executor or unbounded workflow dispatcher;
- private chain-of-thought is never persisted;
- prefer qualified upstream mechanisms plus the smallest project-owned deterministic policy/state seams.

## Accepted Windows foundation

Accepted/merged through Stage 26.2D:

```text
#83 26.1C typed executor
#84 26.1D latency baseline
#85 26.1E window-scoped UIA
#86 context synchronization
#87 26.2A production Windows runtime
#88 26.2B DesktopState
#89 26.2C native Grounder
#90 26.2D deterministic structure-first UIA -> vision routing
```

Stage 26.2E real-app E2E is physically accepted on exact runtime/qualification head:

`457db0b634f2e47f53d41e359a238840fa3ca2ee`

Accepted result:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448`

It proved one isolated real VS Code text-edit task with exact hidden Monaco focus identity, one-shot window-scoped focused keyboard guard, exactly one guarded Unicode delivery, independent file SHA-256 verification and full rollback. It is not universal Windows accuracy.

## Current critical path

```text
26.2E real application E2E — ACCEPTED
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration — ACTIVE
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postconditions
    -> checkpoint/recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27/28 release work
```

The first Stage 26.3 physical vertical slice must specifically prove:

```text
one user goal
 -> ordinary ChatGPT selects a bounded known procedure
 -> local Control Plane executes multiple current-state-authorized + verified transitions
 -> no intermediate PowerShell copy/paste by the user
 -> verified completion OR deterministic ABSTAIN/escalation
```

The user must no longer be treated as a routine command relay. Use the user only for irreducible target-machine/ordinary-Chat permission/setup gates that the available tool surface genuinely cannot perform itself.

## Future local planner

A local general planner is not banned forever. It is explicit future optional **Track P — Local Planner / Offline Autonomy** in `ROADMAP.md`/`CONTROL_PLANE.md`.

It begins shadow/proposal-only after verified procedure-state data and measured need exist, remains behind deterministic Control Plane authorization/verifier boundaries, and is not a Stage 27/28 release prerequisite.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable acceptance checks are satisfied, merge it without waiting for a separate merge command.

Do not auto-merge on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

## Development workflow

- inspect live repository/PR/CI state before editing;
- preserve exact physical evidence heads;
- distinguish synthetic/policy tests from physical evidence;
- never invent measured counters;
- keep `main` as integration line and never force-push it;
- use the user only for irreducible target-machine/ordinary-Chat gates;
- actively reduce manual user command relay when the platform has enough capability to do the work itself;
- keep continuation/architecture/control-plane/document-status docs synchronized at architecture-changing points.

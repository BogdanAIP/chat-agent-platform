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
10. active stage document, currently `project-context/STAGE26_2E_REAL_APPLICATION_E2E.md`
11. older stage/research documents only as historical evidence when `DOCUMENT_STATUS.md` classifies them that way

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

Ordinary ChatGPT is the **only current general planner/intelligence layer**. The local platform is expected to own a **deterministic execution Control Plane** for state, selected procedure progression, authorization, verification, checkpoints, bounded recovery and resource budgets.

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

## Non-negotiable invariants

- ordinary ChatGPT is the only **current general** planner/intelligence;
- a focused deterministic local execution Control Plane is allowed/desired and is the Stage 26.3 direction;
- no current second local general planner/autonomous workflow brain;
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

Integration `main` when 26.2E started:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted Stage 26.2D head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

This remains bounded controlled-WinForms evidence, not universal Windows accuracy.

## Current critical path

```text
26.2E real application E2E
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postconditions
    -> checkpoint/recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27/28 release work
```

While 26.2E is active, branch `chat/stage26-2e-vscode-real-app-e2e` uses isolated VS Code + one disposable TEMP artifact. Read its stage document before changing the physical contract.

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
- keep continuation/architecture/control-plane/document-status docs synchronized at architecture-changing points.

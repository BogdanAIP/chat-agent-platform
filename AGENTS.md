# Agent Entry Point

This repository is designed to be continued safely from a fresh ordinary ChatGPT session.

## Read first

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/START_HERE.md`
3. `project-context/CURRENT_STATE.md`
4. `project-context/ARCHITECTURE.md`
5. `project-context/CONTROL_PLANE.md`
6. `project-context/ROADMAP.md`
7. `project-context/MODULE_CATALOG.md`
8. `project-context/KNOWN_ISSUES.md`
9. active stage document, currently `project-context/STAGE26_2E_REAL_APPLICATION_E2E.md`
10. older stage/research documents only as historical evidence when needed

## Source-of-truth order

When documents disagree:

1. current code/tests + exact current PR/CI/physical target evidence;
2. `CONTINUATION_CONTEXT.md`, `START_HERE.md`, `CURRENT_STATE.md`;
3. `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `ROADMAP.md`, `MODULE_CATALOG.md`, `KNOWN_ISSUES.md`;
4. active/accepted stage documents;
5. `DECISIONS.md`, `DEVELOPMENT_PRINCIPLES.md`, security/constraint policies;
6. historical research/handoffs/older revisions.

Always resolve live `main` and relevant PR heads before branching/editing. A documentation SHA is a snapshot, not a permanently current integration line.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources for development, review, orchestration or execution unless the user explicitly re-enables them later.

## Current architecture boundary

Ordinary ChatGPT is the **only current general planner/intelligence layer**. The local platform is expected to own a **deterministic execution Control Plane** for state, procedure progression, authorization, verification, checkpoints, bounded recovery and resource budgets.

Those are different roles:

```text
ordinary ChatGPT
  general goal interpretation / strategy / adaptation
        |
        v
local deterministic Control Plane
  TaskState / ProgramGraph state
  policy + authorization
  checkpoints + bounded retry/recovery
  verifier/postconditions
        |
        v
focused Files / Browser / Windows capabilities
```

The deterministic Control Plane may advance already-selected, already-defined procedure transitions without returning to ChatGPT after every low-level action, but it must ABSTAIN/escalate when the live state is novel, ambiguous, stale, incompatible or requires a new strategy.

Do **not** confuse this with a second general planner. Read `project-context/CONTROL_PLANE.md` before changing this boundary.

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

1MCP remains internal replaceable diagnostic/adaptive/aggregation infrastructure. `semantic-projection` remains deterministic and truthful; it is not the Control Plane or a hidden workflow brain.

## Non-negotiable invariants

- ordinary ChatGPT is the only **current general** planner/intelligence;
- a focused deterministic local Control Plane is allowed and is the Stage 26.3 direction;
- no current second local general planner/autonomous workflow brain;
- model/procedure/planner output never self-authorizes an action;
- observation is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not completion evidence;
- stale/ambiguous/UNKNOWN evidence causes zero mutation;
- generic hidden `tool_invoke`, shell/Python execution and unbounded workflow dispatch remain outside the product boundary;
- private chain-of-thought is never persisted;
- prefer qualified upstream mechanisms plus the smallest project-owned deterministic policy/state seams.

## Accepted Windows foundation

Stage 26.1B Capture and Stage 26.1C-E executor/UIA qualification are accepted. Stage 26.2A production Windows runtime, 26.2B DesktopState, 26.2C native Grounder and 26.2D structure-first Windows vision routing are accepted and merged through PR #90.

Stage 26.2D integration `main` when 26.2E started:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted Stage 26.2D head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

This evidence remains bounded controlled-WinForms evidence, not universal Windows accuracy.

## Current critical path

```text
Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime / deterministic Control Plane integration
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27/28 release work
```

While Stage 26.2E is active, the qualification branch is `chat/stage26-2e-vscode-real-app-e2e`. It uses an isolated VS Code profile and one disposable TEMP artifact. Read the active stage document before changing the physical contract.

## Future local planner

A local general planner is not banned forever. It is explicitly a future optional **Track P — Local Planner / Offline Autonomy** in `ROADMAP.md` and `CONTROL_PLANE.md`.

It may be researched only after verified procedure-state data and measured need exist. It begins shadow/proposal-only, remains behind the deterministic Control Plane authorization/verifier boundary, and is not a Stage 27/28 release prerequisite.

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
- never claim a target path passed unless that exact path ran;
- keep continuation/architecture/control-plane docs synchronized at architecture-changing points.
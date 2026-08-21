# Start Here — authoritative continuation guide

Use this file first in a fresh ordinary ChatGPT session after resolving live repository state.

## Resolve live repository state first

Never treat a documentation SHA as permanently current. Resolve live `main`, then inspect open PR heads relevant to the task.

## Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/CONTROL_PLANE.md`
5. `project-context/ROADMAP.md`
6. `project-context/MODULE_CATALOG.md`
7. `project-context/KNOWN_ISSUES.md`
8. active stage document as needed

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

Historical stage/research documents preserve evidence and may contain old `current`/`next` wording. They must not override the files above.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them later.

## Planner / Control Plane boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The local platform is expected to implement a **deterministic execution Control Plane** that owns:

```text
TaskState
selected ProgramGraph/procedure state
capability policy + authorization
checkpoints
verifier/postconditions
bounded retry/recovery
resource/action/time budgets
escalation reason
```

That Control Plane may continue a known, already-selected procedure through multiple current-state-authorized and verified transitions without asking ChatGPT after every low-level action. It must escalate when the environment requires a new strategy or is stale/unknown/ambiguous/incompatible.

This is not a second general planner. See `CONTROL_PLANE.md`.

A future local general planner remains in optional Track P and starts shadow/proposal-only after verified procedure-state data and measured need exist.

## Normal path and public contract

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused local capabilities
```

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. `semantic-projection` is not the procedure Control Plane and may not become an opaque workflow dispatcher.

## Accepted Windows foundation

Accepted/merged sequence:

```text
#83 26.1C typed executor
#84 26.1D latency baseline
#85 26.1E window-scoped UIA
#86 context synchronization
#87 26.2A production Windows runtime
#88 26.2B DesktopState
#89 26.2C native Desktop Grounder
#90 26.2D deterministic structure-first vision routing
```

Stage 26.2D integration `main` when 26.2E started:

`42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted 26.2D head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-routing-qualification\routing-20260820-085625`

This is controlled WinForms evidence, not broad application accuracy.

## Active work — Stage 26.2E real application E2E

Active branch at this snapshot:

`chat/stage26-2e-vscode-real-app-e2e`

Qualification application: isolated VS Code with only a specifically prefixed TEMP root, isolated user-data/extensions and one disposable `.txt`.

Before the one allowed guarded Unicode delivery, the driver requires exact Code.exe PID/HWND/DesktopState, focused-editor evidence, deliberate verifier mismatch -> ABSTAIN with zero action, then **fresh pre-action DesktopState with the same exact window identity and the same focused-editor observation fingerprint**, followed by the native foreground/hit-test guard.

Completion requires exact autosaved file size/SHA-256, same current window identity, workspace containing only the expected artifact, exact-window cleanup, **natural CLI exit** and TEMP-root rollback. Forced CLI terminate/kill is cleanup-only and makes acceptance fail.

Read `STAGE26_2E_REAL_APPLICATION_E2E.md` before changing this gate.

## Current critical path

```text
26.2E real application E2E
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postconditions
    -> checkpoint/recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27/28 distribution and clean-user release
```

Future local planner/offline autonomy is **not deleted from the roadmap**; it is Track P after verified data/need, not a prerequisite for the current stable release.

## Merge policy

Once a branch is logically complete, intended diff is verified, required physical/CI tests pass and applicable acceptance gates pass, merge it without waiting for a separate merge command.

Stop on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

## Non-negotiable rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic local execution Control Plane is allowed/desired;
- no current local general planner/autonomous workflow brain;
- model/procedure/planner/observation proposal is not authorization;
- current observed state outranks remembered history;
- verification controls completion;
- stale/ambiguous/UNKNOWN fails closed;
- never persist private chain-of-thought;
- raw desktop capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- release-grade Python/model/OpenAdapt reproducibility is required before stable distribution.

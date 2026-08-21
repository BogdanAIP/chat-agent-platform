# Continuation Context — read this first in a fresh chat

This file is intentionally compact. Resolve live GitHub state before acting because `main` and PR heads can move after this snapshot.

## Repository

`BogdanAIP/chat-agent-platform`

## Operating rules

- Use ordinary ChatGPT + GitHub + the project's local/connected tools.
- Do **not** use Codex or ChatGPT Work resources unless the user explicitly re-enables them.
- Ordinary ChatGPT is the **only current general planner/intelligence**.
- A **deterministic local execution Control Plane is part of the target architecture**; it is not a second planner.
- The Control Plane owns TaskState, selected ProgramGraph progression, authorization, checkpoints, verifier/postconditions, bounded recovery and resource budgets.
- A known selected procedure may advance through several independently authorized/verified transitions without returning to ChatGPT after every low-level action.
- Novel strategy, stale/ambiguous/UNKNOWN/incompatible state -> ABSTAIN/escalate to ChatGPT.
- Current public semantic tools remain exactly `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`.
- Model/procedure/planner/observation output is evidence/proposal, never authorization by itself.
- Current state outranks remembered/history state.
- Delivery is not completion; explicit verification controls completion.
- Generic Windows code execution remains disabled/unreachable.
- When a branch is logically complete, intended diff is reviewed, required physical/CI gates pass and no unresolved issue remains, merge it without waiting for a separate `сливай` command.

Canonical architecture distinction: `project-context/CONTROL_PLANE.md`.

## Current integration line at this snapshot

Stage 26.2D was merged as PR #90.

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

PR #90 exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-routing-qualification\routing-20260820-085625`

Stage 26.2D proved one controlled structure-first Windows visual-fallback action with current request/UIA/process/window/frame evidence, fresh re-observation, native foreground/hit-test guard, one bounded delivery and correct fail-closed negative cases. It is not broad Windows-app accuracy.

## Active work

**Stage 26.2E — first real application E2E**

Active branch:

`chat/stage26-2e-vscode-real-app-e2e`

The test uses only:

`%TEMP%\chat-agent-stage26e-vscode-<guid>`

with isolated VS Code user-data/extensions and one unique empty `.txt`.

The one allowed mutation is guarded Unicode text delivery. Before it, the driver requires exact Code.exe PID/HWND/DesktopState, focused editor, native guard and a deliberate verifier mismatch -> FAIL -> ABSTAIN with zero action. Immediately before typing it must take a **fresh DesktopState** proving the same window identity and **the same focused-editor observation fingerprint**, then rerun the native foreground/hit-test guard.

Completion requires exact autosaved file size/SHA-256, same current window identity, workspace containing only the expected artifact, exact qualification-window cleanup, **natural CLI exit**, TEMP cleanup and rollback. Forced CLI terminate/kill is cleanup-only and must fail acceptance.

A physical GUI qualification has **not yet been accepted** at this snapshot.

Read `STAGE26_2E_REAL_APPLICATION_E2E.md` for the exact gate.

## Correct roadmap after 26.2E

```text
26.2E real application E2E
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postconditions
    -> checkpoint/recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 distribution/maintenance
 -> 28 clean-user E2E/stable release
```

Do **not** replace 26.3 with a local general LLM planner. 26.3 is where the deterministic local Control Plane is integrated around ProgramGraph/live state/authorization/verifier.

## Future local planner

The local planner idea is retained deliberately as **Track P — Local Planner / Offline Autonomy** after verified procedure-state data and measured need exist.

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general-planner mode
```

It is not current release-critical work. Even a future planner remains above the same deterministic Control Plane authorization/verifier layer and cannot grant itself authority.

## Fresh-chat startup procedure

1. Resolve live `main` and open PR heads.
2. Read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `ROADMAP.md` and the active stage document.
3. Treat older stage documents as historical evidence if their `current`/`next` wording conflicts with live state.
4. Prefer exact code/tests/current CI/physical evidence over prose.
5. Continue the current release-critical stage instead of restarting architecture discussion.

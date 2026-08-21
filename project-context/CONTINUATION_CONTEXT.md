# Continuation Context — read this first in a fresh chat

This file is intentionally compact. Resolve live GitHub state before acting because `main` and PR heads can move after this snapshot.

## Repository

`BogdanAIP/chat-agent-platform`

## Operating rules

- Use ordinary ChatGPT + GitHub + the project's local/connected tools.
- Do **not** use Codex or ChatGPT Work resources unless the user explicitly re-enables them.
- Ordinary ChatGPT remains the only general planner/intelligence layer.
- Do not add a second autonomous planner/control-plane brain or generic hidden dispatcher.
- Current public semantic tools remain exactly `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`.
- Model/procedure/observation output is evidence/proposal, never authorization by itself.
- Current state outranks remembered/history state.
- Delivery is not completion; explicit verification controls completion.
- Stale/ambiguous/UNKNOWN evidence fails closed with zero mutation.
- Generic Windows code execution remains disabled/unreachable.
- When a branch is logically complete, intended diff is reviewed, required physical/CI gates pass and no unresolved issue remains, merge it without waiting for a separate `сливай` command.

## Current integration line at this snapshot

Stage 26.2D was merged as PR #90.

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

PR #90 exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-routing-qualification\routing-20260820-085625`

Key Stage 26.2D evidence:

```text
NATIVE_POINT_GUARD_PREFLIGHT_PASS=True
NATIVE_POINT_GUARD_WRONG_WINDOW_REFUSAL_PASS=True
NATIVE_POINT_GUARD_DELIVERY_PASS=True
VISION_DISABLED_ABSTAIN_PASS=True
ROLE_CONFLICT_ABSTAIN_PASS=True
NEGATIVE_ZERO_ACTION_PASS=True
POSITIVE_ROUTE_STATUS=delivered
POSITIVE_ROUTE_REASON=vision-zero-exact-delivered
POSITIVE_CONSISTENCY_IOU=0.34455881673798816
FRESH_REOBSERVATION_PASS=True
GUARDED_CLICK_RECEIPT_PASS=True
FIXTURE_START_POSTCONDITION_PASS=True
FIXTURE_NO_EXTRA_MUTATION_PASS=True
SINGLE_ACTION_PASS=True
STRUCTURAL_EXECUTOR_CALLS=0
COORDINATE_EXECUTOR_CALLS=1
GROUNDER_CALLS=1
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
PASS=True
```

The two exact-window screenshots around inference had the same SHA-256:

`f318c355d0f180968c030cbd25b23947791cb146d5ba8b5a11a1ad7b5e87012f`

## Active work

**Stage 26.2E — first real application E2E**

Active branch at this snapshot:

`chat/stage26-2e-vscode-real-app-e2e`

This stage deliberately uses an isolated VS Code qualification task, not a new agent planner.

The test creates only disposable data under:

`%TEMP%\chat-agent-stage26e-vscode-<guid>`

It launches VS Code with isolated `--user-data-dir`, `--extensions-dir`, disabled extensions, and one unique empty `.txt` file. It may perform exactly one guarded Unicode text delivery after exact PID/HWND/focused-control/native-point guards pass. Completion is independently verified from the saved file size/SHA-256 and the workspace must contain only that expected artifact. A deliberate wrong verifier expectation must map to ABSTAIN before action. Then the exact qualification window and the isolated TEMP root must be cleaned up.

Current branch assets include:

```text
scripts/stage26-vscode-real-app-e2e.py
scripts/stage26-vscode-real-app-e2e.ps1
tests/test_stage26_2e_vscode_real_app_e2e.py
project-context/STAGE26_2E_REAL_APPLICATION_E2E.md
project-context/CONTINUATION_CONTEXT.md
```

CI must parse the new PowerShell harness and run the source/contract tests. A physical GUI qualification has **not yet been accepted** at the time this snapshot was written.

Read `project-context/STAGE26_2E_REAL_APPLICATION_E2E.md` for the exact acceptance contract.

## Correct roadmap after 26.2E

```text
26.2E real application E2E
 -> 26.3 Verified Procedure Runtime
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 distribution/maintenance
 -> 28 clean-user E2E/stable release
```

Do **not** replace Stage 26.3 with a local generic `Agent Control Plane`/Planner. That earlier idea conflicts with the repository architecture. Procedure runtime is non-agentic support for ordinary ChatGPT: load applicable ProgramGraph, observe current state, resolve a bounded next transition, authorize, execute, verify, then advance/recover/ABSTAIN.

## Fresh-chat startup procedure

1. Resolve live `main`.
2. Inspect open PRs, especially the Stage 26.2E branch/PR if still active.
3. Read this file, `CURRENT_STATE.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `STAGE26_2E_REAL_APPLICATION_E2E.md`.
4. Prefer exact code/tests/current CI/physical evidence over stale prose.
5. Continue the current release-critical stage instead of restarting architecture discussion.
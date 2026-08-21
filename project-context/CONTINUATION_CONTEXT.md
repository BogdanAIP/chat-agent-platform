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
- Current public semantic tools remain exactly `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact` until a dedicated contract/ADR changes them.
- Model/procedure/planner/observation output is evidence/proposal, never authorization by itself.
- Current state outranks remembered/history state.
- Delivery is not completion; explicit verification controls completion.
- Generic Windows code execution remains disabled/unreachable.
- When a branch is logically complete, intended diff is reviewed, required physical/CI gates pass and no unresolved issue remains, merge it without waiting for a separate `сливай` command.

Canonical architecture distinction: `project-context/CONTROL_PLANE.md`.

## Accepted Windows integration line before 26.3

Stages through 26.2D were merged as PRs #83–#90. Stage 26.2E is physically accepted on PR #91.

Exact physically accepted Stage 26.2E runtime/qualification head:

`457db0b634f2e47f53d41e359a238840fa3ca2ee`

Physical result directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448`

Accepted evidence includes:

```text
WINDOW_BINDING_PASS=True
DESKTOP_OBSERVATION_PASS=True
FOCUSED_EDITOR_PRECONDITION_PASS=True
FOCUSED_EDITOR_ROLE=textbox
FRESH_PRE_ACTION_STATE_PASS=True
NATIVE_POINT_GUARD_PASS=True
KEYBOARD_FOCUS_GUARD_MODE=window_scoped_focused_observation_fingerprint
KEYBOARD_FOCUS_GUARD_ARMED_PASS=True
KEYBOARD_FOCUS_GUARD_PASS=True
MISMATCH_PROBE_VERIFICATION_STATUS=fail
MISMATCH_PROBE_DECISION=abstain
MISMATCH_PROBE_ZERO_ACTION_PASS=True
GUARDED_KEYBOARD_DELIVERY_PASS=True
KEYBOARD_ACTION_COUNT=1
COMPLETION_VERIFICATION_STATUS=pass
COMPLETION_VERIFICATION_PASS=True
CURRENT_STATE_VERIFICATION_PASS=True
WORKSPACE_EXPECTED_ONLY_PASS=True
KEYBOARD_FOCUS_GUARD_ARMS=1
KEYBOARD_FOCUS_GUARD_CALLS=1
KEYBOARD_FOCUS_GUARD_PASSES=1
KEYBOARD_FOCUS_GUARD_FAILURES=0
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
CLEANUP_REVALIDATION_PASS=True
APPLICATION_CLEANUP_PASS=True
CLI_PROCESS_RETURNCODE=0
CLI_PROCESS_EXIT_PASS=True
FORCED_CLI_CLEANUP=False
APP_ROOT_CLEANUP_PASS=True
ROLLBACK_PASS=True
STAGE26_2E_REAL_APPLICATION_E2E_RESULT=PASSED
QUALIFICATION_EXIT_CODE=0
```

The accepted real-app finding is that Monaco's real keyboard target may be an intentionally hidden/zero-size accessibility `textbox`. The production path now separates exact semantic focus identity from top-level foreground/window geometry and rechecks the exact hidden focused fingerprint inside the guarded request.

One successful VS Code task is not broad desktop accuracy.

## Active work

**Stage 26.3 — Verified Procedure Runtime / deterministic Control Plane integration**

The next acceptance target is deliberately user-facing: stop using the user as the operator who copies intermediate PowerShell commands.

Target flow:

```text
user states one goal once
 -> ordinary ChatGPT chooses an applicable bounded known procedure + parameters
 -> local deterministic Control Plane
      loads ProgramGraph
      binds TaskState/checkpoint
      observes current state
      resolves exactly one permitted known transition
      authorizes the action
      executes a typed/scoped capability
      re-observes
      verifies the postcondition
      checkpoints and advances
      repeats while state remains known/permitted and budgets allow
 -> verified completion
    OR deterministic ABSTAIN/escalation
```

First physical Stage 26.3 acceptance should require:

```text
ONE user goal
 -> NO intermediate PowerShell copy/paste
 -> multiple independently authorized + verified transitions
 -> independent final postcondition
 -> evidence returned to Chat
```

Negative acceptance must prove stale/unexpected/ambiguous intermediate state causes zero unauthorized continuation and an explicit escalation reason.

Do **not** replace 26.3 with a local general LLM planner. 26.3 is deterministic local execution around ProgramGraph/live state/authorization/verifier. A true local general planner remains optional future Track P.

## Stage order

```text
26.2E real application E2E — ACCEPTED
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane — ACTIVE
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postconditions
    -> checkpoint/recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 distribution/maintenance
 -> 28 clean-user E2E/stable release
```

## Future local planner

Track P remains future optional research after verified procedure-state data and measured need exist:

```text
P0 shadow/proposal-only
 -> P1 bounded subtask planner
 -> P2 optional local general-planner mode
```

Even then it stays above the same deterministic authorization/verifier boundary.

## Fresh-chat startup procedure

1. Resolve live `main` and open PR heads.
2. Read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `ROADMAP.md`, `DOCUMENT_STATUS.md` and the active Stage 26.3 contract/design.
3. Treat `STAGE26_2E_REAL_APPLICATION_E2E.md` as accepted historical evidence for exact head `457db0b...`.
4. Prefer exact code/tests/current CI/physical evidence over prose.
5. Continue the current release-critical Stage 26.3 instead of restarting architecture discussion.

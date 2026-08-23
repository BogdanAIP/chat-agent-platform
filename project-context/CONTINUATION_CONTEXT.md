# Continuation Context — read this first in a fresh chat

This file is intentionally compact. Resolve live GitHub state before acting because `main` and PR heads can move after this snapshot.

## Repository

`BogdanAIP/chat-agent-platform`

## Current integration snapshot — 2026-08-23

Transport Supervisor v1 was accepted and merged as PR #94. The Stage 26.3A branch has been integrated on top of that accepted foundation without force-push.

```text
accepted main foundation after #94:
2f33997d3fbaa1fc52d437c00be7f16e55bdde5e

Stage 26.3A exact hosted-qualified code head:
e4507dbe6dc07e182313769ebe833dd1e6801572
```

All ten pull-request-triggered hosted workflows were green on `e4507dbe6dc07e182313769ebe833dd1e6801572`, including `ci`, `Stage 26.3A Procedure Qualification`, Direct Semantic Tunnel Acceptance, semantic/profile regressions, CodeQL and Secret History Scan.

Documentation commits after that exact code head do not themselves constitute new physical evidence. Before any physical qualification, resolve the live PR #92 head and require the intended exact SHA.

Stage 26.3A is **not physically accepted yet**. Remaining physical gates:

1. exact-head target-Windows direct-tunnel qualification;
2. ordinary ChatGPT one-goal E2E with no intermediate PowerShell copy/paste;
3. independent final artifact verification through `workspace_read`;
4. incompatible/pre-existing state -> structured ABSTAIN with zero unauthorized continuation/overwrite.

## Operating rules

- Use ordinary ChatGPT + GitHub + the project's local/connected tools.
- Do **not** use Codex or ChatGPT Work resources unless the user explicitly re-enables them.
- Ordinary ChatGPT is the **only current general planner/intelligence**.
- A **deterministic local execution Control Plane is part of the target architecture**; it is not a second planner.
- The Control Plane owns TaskState, selected ProgramGraph progression, authorization, checkpoints, verifier/postconditions, bounded recovery and resource budgets.
- A known selected procedure may advance through several independently authorized/verified transitions without returning to ChatGPT after every low-level action.
- Novel strategy, stale/ambiguous/UNKNOWN/incompatible state -> ABSTAIN/escalate to ChatGPT.
- Current normal public semantic tools remain exactly `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`; Stage 26.3A adds `procedure_run` only in the isolated qualification profile.
- Model/procedure/planner/observation output is evidence/proposal, never authorization by itself.
- Current state outranks remembered/history state.
- Delivery is not completion; explicit verification controls completion.
- Generic Windows code execution remains disabled/unreachable.
- When a branch is logically complete, intended diff is reviewed, required physical/CI gates pass and no unresolved issue remains, merge it without waiting for a separate merge command.

Canonical architecture distinction: `project-context/CONTROL_PLANE.md`.

## Accepted Windows integration through Stage 26.2E

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

The accepted real-app finding is that Monaco's real keyboard target may be an intentionally hidden/zero-size accessibility `textbox`. The production path separates exact semantic focus identity from top-level foreground/window geometry and rechecks the exact hidden focused fingerprint inside the guarded request.

One successful VS Code task is not broad desktop accuracy.

## Accepted Transport Supervisor v1 foundation

PR #94 is merged into `main`. Accepted physical evidence includes owned-tunnel kill recovery, external network disconnect/reconnect, Modern Standby sleep/resume, reboot/logon, fresh ordinary-Chat post-reboot semantic E2E, idle resource/recovery latency, console-free Scheduled Task launch and persistent desired-state/runtime-owner separation.

The normal Windows lifecycle therefore now includes persistent user desired state, a single console-free supervisor process, bounded recovery and direct semantic route health. Exact physical SHAs/result locators remain in `EVIDENCE_INDEX.md` and transport evidence documents.

## Active work

**Stage 26.3 — Verified Procedure Runtime / deterministic Control Plane integration**

The immediate candidate is Stage 26.3A `verified_workspace_artifact_v1`, exposed only through the separate `procedure-qualification` profile as `procedure_run`. The normal semantic profile remains five canonical tools.

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

First physical Stage 26.3 acceptance requires:

```text
ONE user goal
 -> NO intermediate PowerShell copy/paste
 -> multiple independently authorized + verified transitions
 -> independent final postcondition
 -> evidence returned to Chat
```

Negative acceptance must prove stale/unexpected/ambiguous or pre-existing incompatible state causes zero unauthorized continuation and an explicit escalation reason.

Do **not** replace 26.3 with a local general LLM planner. 26.3 is deterministic local execution around ProgramGraph/live state/authorization/verifier. A true local general planner remains optional future Track P.

## Stage order

```text
26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane — ACTIVE
    -> 26.3A hosted qualification — GREEN; physical one-goal gate NEXT
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

1. Resolve live `main`, PR #92 head and current checks.
2. Read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `ROADMAP.md`, `DOCUMENT_STATUS.md`, `EVIDENCE_INDEX.md` and the active Stage 26.3A notes/contracts.
3. Treat Stage 26.2E and Transport Supervisor evidence as accepted only for their exact recorded physical heads.
4. Treat `e4507dbe6dc07e182313769ebe833dd1e6801572` as the exact hosted-qualified Stage 26.3A code head after integration with #94; do not infer physical acceptance from it.
5. Prefer exact code/tests/current CI/physical evidence over prose.
6. Continue the current Stage 26.3A physical qualification instead of restarting architecture discussion.

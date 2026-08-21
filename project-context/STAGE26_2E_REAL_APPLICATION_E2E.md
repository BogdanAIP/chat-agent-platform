# Stage 26.2E — First Real Application E2E

## Status

**ACCEPTED — physical qualification passed on exact runtime/qualification head `457db0b634f2e47f53d41e359a238840fa3ca2ee`.**

Base integration line when this stage started:

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

Qualification branch / PR:

`chat/stage26-2e-vscode-real-app-e2e` / PR #91

Stage 26.2D was physically accepted and merged as PR #90. Stage 26.2E preserved its structure/freshness/native-guard invariants and extended the Windows path to one real medium-complexity application.

## Why this stage existed

The Windows capability had already been proven on controlled fixtures. Before deterministic procedure Control Plane integration, the platform needed one real application task with:

- a disposable artifact;
- deterministic before/after evidence;
- one bounded mutation;
- current-state verification;
- recoverable mismatch -> ABSTAIN;
- clean rollback;
- no user workspace/profile mutation.

This is an application E2E gate, not a general-planner implementation and not a claim of universal desktop accuracy.

## Selected qualification application

VS Code was used because it is a real medium-complexity Windows application while allowing strong isolation:

```text
%TEMP%\chat-agent-stage26e-vscode-<guid>\
  workspace\
    chat-agent-stage26e-<random>.txt
  user-data\
    User\settings.json
  extensions\
```

Launch contract:

```text
--wait
--new-window
--disable-extensions
--user-data-dir <isolated user-data>
--extensions-dir <isolated extensions>
--goto <disposable file>:1:1
```

VS Code is a qualification application, not a permanent architectural dependency.

## Focus model learned from physical evidence

Real VS Code/Monaco intentionally exposes the current keyboard input as a hidden accessibility input. On the accepted Windows build the exact focused target was:

```text
role = textbox
name = <exact randomized qualification filename>
visible = False
bounds = 0 x 0
focused = True
enabled = True
```

Therefore visible control geometry is not part of semantic keyboard-target identity. The accepted contract separates:

1. **semantic keyboard target** — exact current hidden Monaco textbox identity, bound to the exact randomized file and DesktopState observation fingerprint;
2. **top-level native window guard** — a point inside the exact bound VS Code window used only to prove current foreground/root HWND/PID and frame context;
3. **one-shot focused keyboard guard** — immediately inside the guarded keyboard request, the production window-scoped resolver consumes an explicitly armed target and performs a fresh exact-window DesktopState observation. It requires the same PID, HWND, process generation, window title, exact focused observation fingerprint, role and name before authorizing the existing guarded Unicode input path.

The point is never treated as geometry for the hidden Monaco textbox. No `TreeWalker` ancestor reconstruction is required for authorization.

## Safety boundary

The run may perform exactly one intended mutation: guarded Unicode text delivery into the focused editor of the isolated VS Code window.

Before any mutation the driver proves:

1. application root is a specifically prefixed child of OS TEMP;
2. target file is a new empty disposable file;
3. no pre-existing window contains the unique qualification filename;
4. exactly one visible VS Code top-level window with that filename exists;
5. PID/HWND/executable/process-generation identity bind to that exact window;
6. production DesktopState observation succeeds;
7. the exact focused hidden Monaco textbox is uniquely identified by current UIA evidence;
8. native foreground + `WindowFromPoint`/root-HWND/PID guard succeeds for the exact bound window;
9. ephemeral win_agent is loopback-only, authenticated and has no legacy exec capability;
10. a deliberately wrong artifact expectation produces verifier `FAIL`, maps to `ABSTAIN`, and action count remains zero;
11. **after the mismatch probe and immediately before typing, a fresh DesktopState still matches the same exact window identity and the same focused-editor observation fingerprint**;
12. the native top-level window guard is repeated;
13. the exact hidden focus target is armed one-shot in `WindowScopedUiaResolver` and must pass exactly once during the guarded keyboard request.

Only then may the accepted guarded keyboard path run:

```text
arm_focused_keyboard_target
 -> arm_guarded_keyboard
 -> guarded_keyboard_frame
 -> expected_frame_sha256
 -> focused-at-point request intercepted by armed window-scoped focus guard
 -> fresh exact-window DesktopState + focused fingerprint verification
 -> type_text_guarded(unique marker)
```

No clipboard, PyAutoGUI, `SetForegroundWindow`, generic shell execution, structural click, coordinate click, key press or scroll was added to this gate.

## Why the fresh focused-control recheck is required

A root-window foreground guard alone cannot detect a focus change **inside the same VS Code HWND**. The fresh DesktopState closes that gap by requiring the exact focused editor observation fingerprint accepted before mutation. The armed focus guard repeats this semantic identity check inside the guarded request before physical input.

If the focused control changes, the run fails closed before text delivery.

## Completion verification

Delivery receipt is not completion.

The run waits for isolated VS Code autosave and independently verifies the disposable file:

```text
exists = true
size = exact UTF-8 marker byte length
sha256 = exact expected marker digest
```

The production `verify_expected_fields` baseline decides PASS/FAIL/UNKNOWN. Non-PASS does not advance.

The run then re-observes the same PID/HWND/window identity and requires the disposable workspace snapshot to contain exactly one file: the target file with the expected digest.

Measured evidence includes:

- zero mutation on deliberate mismatch probe;
- fresh same-window/same-focused-editor evidence immediately before mutation;
- exactly one armed keyboard focus guard call and pass;
- exactly one registered guarded keyboard delivery;
- exact bound process/window identity;
- native top-level window guard;
- independent file postcondition;
- workspace contains only the expected artifact.

## Rollback and process cleanup

A cached numeric HWND is never sufficient cleanup authority by itself. Immediately before `WM_CLOSE`, the driver re-enumerates current visible windows by the run's randomized qualification filename and freshly validates the candidate process as `Code.exe`. When a bound HWND/PID/process-generation identity is available, those values constrain the fresh match as well.

`WM_CLOSE` is permitted only when cleanup has exactly one current matching qualification window and exactly one freshly validated candidate. A missing, changed or ambiguous identity fails closed rather than posting to a stale/reused HWND.

The VS Code CLI process started with `--wait` must exit naturally with return code `0`. Forced terminate/kill is **failure cleanup** only and can never satisfy acceptance.

Acceptance requires:

```text
CLEANUP_REVALIDATION_PASS=True
APPLICATION_CLEANUP_PASS=True
CLI_PROCESS_RETURNCODE=0
CLI_PROCESS_EXIT_PASS=True
FORCED_CLI_CLEANUP=False
APP_ROOT_CLEANUP_PASS=True
ROLLBACK_PASS=True
```

## Accepted physical evidence

Exact physically tested head:

`457db0b634f2e47f53d41e359a238840fa3ca2ee`

Physical result directory reported by the accepted run:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448`

Key evidence:

```text
PROJECT_HEAD=457db0b634f2e47f53d41e359a238840fa3ca2ee
TEMP_CONTAINMENT_PASS=True
APPLICATION_DISCOVERY_PASS=True
DRIVER_PASS=True
ISOLATED_PROFILE_PASS=True
DISPOSABLE_WORKSPACE_PASS=True
WINDOW_BINDING_PASS=True
DESKTOP_OBSERVATION_PASS=True
FOCUSED_EDITOR_PRECONDITION_PASS=True
FOCUSED_EDITOR_ROLE=textbox
FRESH_PRE_ACTION_STATE_PASS=True
NATIVE_POINT_GUARD_PASS=True
KEYBOARD_FOCUS_GUARD_MODE=window_scoped_focused_observation_fingerprint
KEYBOARD_FOCUS_GUARD_ARMED_PASS=True
KEYBOARD_FOCUS_GUARD_PASS=True
AGENT_LOOPBACK_PASS=True
AGENT_AUTH_REQUIRED_PASS=True
LEGACY_CAPABILITY_ABSENT_PASS=True
BASELINE_VERIFICATION_STATUS=pass
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

The run also recorded `ERROR=None`, `PASS=True` and no resolver failure stage/detail.

## What this stage proves / does not prove

It proves the accepted observation/hidden-focus authorization/guarded-input/verifier stack can complete and roll back one real VS Code task under this exact bounded contract.

It does **not** prove universal Windows application accuracy, arbitrary desktop authority, or autonomous procedure execution across multiple transitions.

## Next release-critical stage

**Stage 26.3 — Verified Procedure Runtime / deterministic local execution Control Plane integration.**

Ordinary ChatGPT remains the only current general planner. Stage 26.3 must let a selected procedure progress deterministically through known authorized+verified transitions without ChatGPT micromanaging every low-level action.

The first user-value acceptance should remove the user from the role of PowerShell operator: one ordinary-Chat goal should select a bounded known procedure, let the local Control Plane execute its verified transitions, and return verified completion or ABSTAIN/escalation without requiring the user to paste intermediate commands.

A true local general planner is not inserted here; it remains future optional Track P research after verified data/need. See `CONTROL_PLANE.md`, `STAGE26_PROCEDURAL_MEMORY.md` and `ROADMAP.md`.

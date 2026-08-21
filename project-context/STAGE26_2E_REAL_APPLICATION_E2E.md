# Stage 26.2E — First Real Application E2E

## Status

**ACTIVE / physical qualification not yet accepted.**

Base integration line when this stage started:

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

Active branch:

`chat/stage26-2e-vscode-real-app-e2e`

Stage 26.2D is physically accepted and merged as PR #90. This stage must not weaken its structure/freshness/native-guard invariants.

## Why this stage exists

The Windows capability has been proven on controlled fixtures. Before deterministic procedure Control Plane integration, the platform needs one real medium-complexity application task with:

- a disposable artifact;
- deterministic before/after evidence;
- one bounded mutation;
- current-state verification;
- recoverable mismatch -> ABSTAIN;
- clean rollback;
- no user workspace/profile mutation.

This is an application E2E gate, not a general-planner implementation and not a claim of global desktop accuracy.

## Selected qualification application

VS Code is the qualification candidate because it is a real medium-complexity Windows application while allowing a strongly isolated disposable test:

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

VS Code is one qualification application, not a permanent architectural dependency.

## Safety boundary

The run may perform exactly one intended mutation: guarded Unicode text delivery into the focused editor of the isolated VS Code window.

Before any mutation the driver must prove:

1. application root is a specifically prefixed child of OS TEMP;
2. target file is a new empty disposable file;
3. no pre-existing window contains the unique qualification filename;
4. exactly one visible VS Code top-level window with that filename exists;
5. PID/HWND/executable identity bind to that exact window;
6. production DesktopState observation succeeds;
7. one enabled/visible focused **editor** control is uniquely identified by current UIA evidence;
8. native foreground + `WindowFromPoint`/root-HWND/PID guard succeeds at that control;
9. ephemeral win_agent is loopback-only, authenticated and has no legacy exec capability;
10. a deliberately wrong artifact expectation produces verifier `FAIL`, maps to `ABSTAIN`, and action count remains zero;
11. **after the mismatch probe and immediately before typing, a fresh DesktopState must still match the same exact window identity and the same focused-editor observation fingerprint**;
12. the native foreground/hit-test guard is repeated against that fresh pre-action state.

Only then may the accepted guarded keyboard path run:

```text
arm_guarded_keyboard
 -> guarded_keyboard_frame
 -> expected_frame_sha256
 -> type_text_guarded(unique marker)
```

No clipboard, PyAutoGUI, `SetForegroundWindow`, generic shell execution, structural click, coordinate click, key press or scroll is added to this gate.

## Why the fresh focused-control recheck is required

A root-window foreground guard alone cannot detect a focus change **inside the same VS Code HWND** (for example editor -> search/command palette/notification). The fresh DesktopState closes that gap by requiring the exact focused editor observation fingerprint that was accepted before mutation.

If the focused control changes, the run must fail closed before text delivery.

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

No constant `false_action_count=0` or `unrelated_window_action_count=0` is accepted as evidence. The measurable evidence is instead:

- zero mutation on deliberate mismatch probe;
- fresh same-window/same-focused-editor evidence immediately before mutation;
- exactly one registered guarded keyboard delivery;
- exact bound process/window identity;
- native point guard;
- independent file postcondition;
- workspace contains only the expected artifact.

## Rollback and process cleanup

The exact qualification window is closed with `WM_CLOSE`; the harness does not use `SetForegroundWindow`, `taskkill` or a generic process-execution endpoint as the normal success path.

The VS Code CLI process started with `--wait` must exit naturally after the exact qualification window closes.

If the CLI fails to exit, terminate/kill may be used only as **failure cleanup** to avoid leaving the test process behind. That fallback must set:

```text
FORCED_CLI_CLEANUP=True
CLI_PROCESS_EXIT_PASS=False
```

and the qualification must remain FAILED.

After window/process cleanup, the specifically prefixed TEMP application root is recursively removed. Python and PowerShell independently validate TEMP containment before recursive cleanup.

Acceptance requires:

```text
APPLICATION_CLEANUP_PASS=True
CLI_PROCESS_EXIT_PASS=True
FORCED_CLI_CLEANUP=False
APP_ROOT_CLEANUP_PASS=True
ROLLBACK_PASS=True
```

## Acceptance target

A physical PASS must include at least:

```text
TEMP_CONTAINMENT_PASS=True
APPLICATION_DISCOVERY_PASS=True
ISOLATED_PROFILE_PASS=True
DISPOSABLE_WORKSPACE_PASS=True
WINDOW_BINDING_PASS=True
DESKTOP_OBSERVATION_PASS=True
FOCUSED_EDITOR_PRECONDITION_PASS=True
NATIVE_POINT_GUARD_PASS=True
AGENT_LOOPBACK_PASS=True
AGENT_AUTH_REQUIRED_PASS=True
LEGACY_CAPABILITY_ABSENT_PASS=True
BASELINE_VERIFICATION_STATUS=pass
MISMATCH_PROBE_VERIFICATION_STATUS=fail
MISMATCH_PROBE_DECISION=abstain
MISMATCH_PROBE_ZERO_ACTION_PASS=True
FRESH_PRE_ACTION_STATE_PASS=True
GUARDED_KEYBOARD_DELIVERY_PASS=True
KEYBOARD_ACTION_COUNT=1
CURRENT_STATE_VERIFICATION_PASS=True
COMPLETION_VERIFICATION_STATUS=pass
COMPLETION_VERIFICATION_PASS=True
WORKSPACE_EXPECTED_ONLY_PASS=True
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
APPLICATION_CLEANUP_PASS=True
CLI_PROCESS_EXIT_PASS=True
FORCED_CLI_CLEANUP=False
APP_ROOT_CLEANUP_PASS=True
ROLLBACK_PASS=True
STAGE26_2E_REAL_APPLICATION_E2E_RESULT=PASSED
```

If target VS Code exposes an unexpected focused UIA role/name, the first run must fail before mutation and preserve diagnostics. Broaden only from observed evidence, not speculation.

## What this stage does not prove

One successful VS Code task does not prove universal Windows application accuracy or arbitrary desktop authority. It proves only the accepted observation/guarded-input/verifier stack can complete and roll back one real application task under this exact bounded contract.

## Architecture relationship

The next release-critical stage is **Stage 26.3 — Verified Procedure Runtime / deterministic local execution Control Plane integration**.

Ordinary ChatGPT remains the only current general planner. Stage 26.3 should let a selected procedure progress deterministically through known authorized+verified transitions without ChatGPT micromanaging every action.

A true local general planner is not inserted here; it remains future optional Track P research after verified data/need. See `CONTROL_PLANE.md` and `ROADMAP.md`.

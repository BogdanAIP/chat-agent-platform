# Stage 26.2E — First Real Application E2E

## Status

**ACTIVE / physical qualification not yet accepted.**

Base integration line when this stage started:

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

Active branch:

`chat/stage26-2e-vscode-real-app-e2e`

Stage 26.2D is already physically accepted and merged as PR #90. This stage must not weaken its structure/freshness/native-guard invariants.

## Why this stage exists

The Windows capability has been proven on controlled WinForms fixtures. Before procedural runtime integration, the platform needs one real medium-complexity application task with:

- a disposable artifact;
- deterministic before/after evidence;
- one bounded mutation;
- current-state verification;
- recoverable mismatch -> ABSTAIN;
- clean rollback;
- no user workspace/profile mutation.

This is an application E2E gate, not a new planner and not a claim of global desktop accuracy.

## Selected qualification application

VS Code is the qualification candidate because it is a real medium-complexity Windows application while still allowing a strongly isolated disposable test:

```text
%TEMP%\chat-agent-stage26e-vscode-<guid>\
  workspace\
    chat-agent-stage26e-<random>.txt
  user-data\
    User\settings.json
  extensions\
```

The harness launches `Code.exe` with:

```text
--wait
--new-window
--disable-extensions
--user-data-dir <isolated user-data>
--extensions-dir <isolated extensions>
--goto <disposable file>:1:1
```

The repository does not make VS Code a permanent architecture dependency. It is one qualification application selected for this gate.

## Safety boundary

The run may perform exactly one intended mutation: guarded Unicode text delivery into the focused editor of the isolated VS Code window.

The driver must prove before mutation:

1. application root is a specifically prefixed child of the OS TEMP directory;
2. target file is a new empty disposable file;
3. no pre-existing window contains the unique qualification filename;
4. one visible VS Code top-level window with that unique filename exists;
5. PID/HWND and executable identity bind to that exact window;
6. DesktopState observation succeeds through the production window-scoped resolver;
7. one enabled/visible focused editor-like UIA control is present;
8. native foreground + `WindowFromPoint` guard succeeds at that control;
9. ephemeral win_agent is loopback-only, authenticated and has no legacy exec capability;
10. a deliberately wrong artifact expectation produces verifier `FAIL`, maps to `ABSTAIN`, and action count remains zero.

Only then may the harness call the already accepted guarded keyboard path:

```text
arm_guarded_keyboard
 -> guarded_keyboard_frame
 -> expected_frame_sha256
 -> type_text_guarded(unique marker)
```

No clipboard, PyAutoGUI, `SetForegroundWindow`, generic shell execution, structural click, coordinate click, key press or scroll is added to this gate.

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

- exactly one registered guarded keyboard delivery;
- exact bound process/window identity;
- native point guard before mutation;
- independent file postcondition;
- workspace contains only the expected artifact;
- zero action on the deliberate mismatch probe.

## Rollback

The exact qualification window is closed with `WM_CLOSE`; the harness does not call `SetForegroundWindow`, `taskkill` or a generic process-execution endpoint.

After the isolated VS Code window exits, the specifically prefixed TEMP application root is recursively removed. Both Python and PowerShell layers validate TEMP containment before recursive cleanup.

Acceptance requires:

```text
APPLICATION_CLEANUP_PASS=True
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
APP_ROOT_CLEANUP_PASS=True
ROLLBACK_PASS=True
STAGE26_2E_REAL_APPLICATION_E2E_RESULT=PASSED
```

If VS Code exposes an unexpected focused UIA role/name, the run must fail before mutation and preserve diagnostics. The contract should then be changed only from observed real evidence, not by broadening target acceptance speculatively.

## What this stage does not prove

One successful VS Code task does not prove universal Windows application accuracy. It proves that the accepted Windows observation/guarded-input/verifier stack can complete and roll back one real application task under a bounded isolated contract.

## After acceptance

The next release-critical stage remains **Stage 26.3 — Verified Procedure Runtime**. Do not insert a second local general planner/control-plane brain. Ordinary ChatGPT remains the only general planning/intelligence layer.
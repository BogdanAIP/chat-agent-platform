# Stage 26.2B — Desktop Observation / DesktopState

Status: **ACCEPTED ON TARGET**

Introduced by PR #88. Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Physical evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-observation-qualification\observation-20260819-184904\result.json`

Stage 26.2A moved the accepted Windows resolver, bounded actuation and minimal verifier into maintained `runtime/windows`. Stage 26.2B adds the read-only state representation required before desktop visual grounding or procedural integration.

## Goal

Create one canonical, bounded, non-authorizing `DesktopState` for an exact process/window.

Evidence priority remains:

```text
1. Win32 identity
2. UIA/native structure
3. screenshot digest
4. VLM later, only as proposal evidence
```

No pixel/model result may outrank contradictory Win32/UIA identity.

## Production surface

Added:

`runtime/windows/observation.py`

Exports:

- `Rect`
- `ControlObservation`
- `EvidenceProvenance`
- `DesktopState`
- `build_desktop_state(...)`
- `observe_bound_window(...)`

The runtime package still exposes no new public Chat/MCP tool.

## Canonical state

The state carries:

```text
schema_version
session_id
application_identity
executable_name
process_id
process_generation
window_handle
window_instance
window_title
window_bounds
coordinate_space
focused_control
controls[]
visible_text
observed_capabilities[]
screenshot_digest
frame_digest
observed_at
observation_source[]
provenance[]
freshness_evidence
```

`coordinate_space` is explicitly `screen_physical_px`.

## Identity and freshness

Win32 process evidence includes target PID, Windows session id, executable basename, SHA-256 identity of the normalized executable path rather than persisting the full path, and process creation time as `process_generation`.

`window_instance` binds process generation, HWND and observed window title. `frame_digest` binds the current structural snapshot plus screenshot digest when screenshot evidence is present.

The contract is deliberately conservative. Later routing may add stronger before/after freshness probes, but it must not reinterpret these evidence fields as authorization.

## Controls

UIA descendants are observed only inside the already accepted PID/HWND-bound exact window. The scan remains bounded to 512 controls.

Per control:

```text
role
name
automation_id
bounds
enabled
visible
focused
observation_fingerprint
```

`observation_fingerprint` is an evidence digest only. It is **not** the executor authorization fingerprint and must never substitute for independent action re-resolution/fingerprint checks.

## Visible text

Visible non-empty UIA names are deduplicated into `visible_text`, bounded to 32,768 characters. Hidden controls are not promoted into visible text.

## Screenshot handling

`build_desktop_state(...)` accepts optional PNG bytes only to bind their SHA-256 digest into the state. Screenshot bytes are not retained by `DesktopState`.

The physical qualification captured the exact observed window rectangle with pinned `mss==10.2.0`, then passed those bytes into the second structural observation with provenance `mss_exact_bound_window`. The qualification persisted JSON state/digests, not screenshot PNG bytes.

Future runs use `mss.MSS()`; the deprecated `mss.mss()` call observed during the accepted target run was removed after review without changing production observer code.

## Observation is not authorization

`observed_capabilities` describes evidence sources such as:

```text
win32_identity
uia_structure
uia_focus_state
screenshot_digest
```

It deliberately contains no click/type/scroll/continue/complete authority.

Stage 26.2B production observer does not call `runtime/windows/actuation.py`, `WindowsBackend.act_*`, win_agent input routes, shell/subprocess/generic exec, or VLM inference. This read-only boundary is enforced by code review and CI source-boundary tests.

## Deterministic tests

CI locks deterministic state/digest construction, process-generation freshness, control-state/bounds fingerprints, focused-control binding, hidden-text exclusion, evidence-only capabilities, optional screenshot semantics, 512-control ceiling, required identity/freshness fields, exact-window resolver reuse, absence of action/generic-exec channels, exact-window screenshot bounding and PowerShell parsing.

## Physical target qualification

Harness:

`scripts/stage26-desktop-observation-qualification.ps1`

Driver:

`scripts/stage26-desktop-observation-qualification.py`

The harmless WinForms fixture is reused. The accepted target run:

1. waited for the fixture to publish its exact PID;
2. bound `WindowScopedUiaResolver` to that PID;
3. observed an initial structural `DesktopState`;
4. captured only that exact window rectangle through pinned `mss`;
5. observed a second `DesktopState` carrying the screenshot digest;
6. verified identity stability, expected controls, screenshot/freshness fields and bounded scan;
7. closed only the qualification-owned fixture.

Physically measured acceptance evidence:

```text
FLOW_PIN_PASS=True
WINDOWS_RUNTIME_PIN_PASS=True
SAME_IDENTITY_PASS=True
CONTROL_CONTRACT_PASS=True
SCREENSHOT_DIGEST_PASS=True
FRESHNESS_CONTRACT_PASS=True
BOUNDED_CONTROL_COUNT_PASS=True
WINDOW_ENUM_CALLS=2
WINDOW_NAME_MATCH_COUNT=2
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
CHROME_PROCESS_COUNT_BEFORE=11
CHROME_PROCESS_COUNT_AFTER=11
CHROME_SURVIVAL_PASS=True
FIXTURE_KILLED=False
FIXTURE_CLEANUP_PASS=True
DRIVER_ERROR=<null>
ERROR=<null>
STAGE26_2B_DESKTOP_OBSERVATION_RESULT=PASSED
```

## Acceptance-evidence correction after self-review

The first qualification driver also printed `OBSERVATION_ONLY_PASS=True` and `ACTION_COUNT=0` / `FALSE_ACTION_COUNT=0` / `UNRELATED_WINDOW_ACTION_COUNT=0`. Self-review found those values were constants in the harness, not instrumented action counters. They are therefore **not used as physical acceptance evidence**.

The misleading counters were removed. Future qualification results bind SHA-256 digests of observer/driver sources and report only measurements the harness actually derives. The read-only claim is supported separately by direct code review and CI source-boundary tests showing that neither production observer nor qualification driver exposes or invokes an executor/actuation channel.

This correction does not change the physically tested production observer head `dcf20a7...` or invalidate the actually measured identity/control/screenshot/freshness/binding/cleanup evidence.

## Non-goals

This stage does not add public `desktop_*` Chat tools, semantic-projection Windows routing, VLM Grounder, action authorization based on `DesktopState`, procedural runtime or real-application accuracy claims.

Stage 26.2C may consume exact-window PNG + `DesktopState` UIA evidence through a proposal-only desktop Grounder seam.

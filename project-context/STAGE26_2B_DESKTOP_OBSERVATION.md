# Stage 26.2B — Desktop Observation / DesktopState

Status: **DRAFT / CI + PHYSICAL TARGET QUALIFICATION REQUIRED**

Base `main` at branch creation:

`d044926846d9c2e198c906ff5174308da0974b03`

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

`coordinate_space` is explicitly:

`screen_physical_px`

## Identity and freshness

Win32 process evidence includes:

- target process id;
- Windows session id;
- executable basename;
- SHA-256 identity of the normalized executable path rather than persisting the full path;
- process creation time as `process_generation`.

`window_instance` binds process generation, HWND and observed window title. `frame_digest` binds the current structural snapshot plus screenshot digest when screenshot evidence is present.

The initial Stage 26.2B contract is deliberately conservative. Later routing may add stronger before/after freshness probes, but it must not weaken or reinterpret these evidence fields as authorization.

## Controls

UIA descendants are observed only inside the already accepted PID/HWND-bound exact window. The scan remains bounded to the Stage 26.1E ceiling of 512 controls.

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

`observation_fingerprint` is an evidence digest only. It is **not** the executor authorization fingerprint and must never be accepted as a substitute for independent action re-resolution/fingerprint checks.

## Visible text

Visible non-empty UIA names are deduplicated into `visible_text`, bounded to 32,768 characters. Hidden controls are not promoted into visible text.

## Screenshot handling

`build_desktop_state(...)` accepts optional PNG bytes only to bind their SHA-256 digest into the state. Screenshot bytes are not retained by `DesktopState`.

The physical qualification captures the exact observed window rectangle with pinned `mss==10.2.0`, then passes those bytes into the second structural observation with provenance:

`mss_exact_bound_window`

The qualification persists only JSON state/digests, not the screenshot PNG.

## Observation is not authorization

`observed_capabilities` describes available evidence sources such as:

```text
win32_identity
uia_structure
uia_focus_state
screenshot_digest
```

It deliberately contains no `click`, `type`, `scroll`, `continue` or `complete` authority.

Stage 26.2B does not call:

- `runtime/windows/actuation.py`;
- `WindowsBackend.act_*`;
- `win_agent` input routes;
- shell/subprocess/generic exec;
- VLM inference.

## Deterministic tests

CI locks:

- deterministic state/digest construction for identical evidence;
- process-generation freshness changes;
- control-state/bounds changes alter observation fingerprints;
- focused-control fingerprint binding;
- hidden-text exclusion and visible-text deduplication;
- evidence-only `observed_capabilities`;
- optional screenshot semantics;
- 512-control hard ceiling;
- required identity/freshness fields;
- exact-window resolver reuse with no Desktop root walk;
- no action/generic-exec channel;
- read-only physical driver contract;
- exact-window screenshot bounding;
- PowerShell parsing for current Stage 26 Windows harnesses.

## Physical target qualification

Harness:

`scripts/stage26-desktop-observation-qualification.ps1`

Driver:

`scripts/stage26-desktop-observation-qualification.py`

The harmless existing WinForms fixture is reused. The driver:

1. waits for the fixture to publish its exact PID;
2. binds `WindowScopedUiaResolver` to that PID;
3. observes an initial structural `DesktopState`;
4. captures only that exact window rectangle through pinned `mss`;
5. observes a second `DesktopState` carrying the screenshot digest;
6. verifies identity stability, expected controls, screenshot/freshness fields and bounded scan;
7. performs zero actions;
8. closes only the qualification-owned fixture.

Required physical gates:

```text
FLOW_PIN_PASS=True
WINDOWS_RUNTIME_PIN_PASS=True
SAME_IDENTITY_PASS=True
CONTROL_CONTRACT_PASS=True
SCREENSHOT_DIGEST_PASS=True
FRESHNESS_CONTRACT_PASS=True
BOUNDED_CONTROL_COUNT_PASS=True
OBSERVATION_ONLY_PASS=True
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
ACTION_COUNT=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
CHROME_SURVIVAL_PASS=True
FIXTURE_KILLED=False
FIXTURE_CLEANUP_PASS=True
DRIVER_ERROR=<null>
ERROR=<null>
STAGE26_2B_DESKTOP_OBSERVATION_RESULT=PASSED
```

## Non-goals

This stage does not add:

- public `desktop_*` Chat tools;
- semantic-projection Windows routing;
- VLM Grounder;
- action authorization based on `DesktopState`;
- procedural memory/runtime;
- real-application accuracy claims.

After Stage 26.2B target acceptance, Stage 26.2C may consume exact-window PNG + `DesktopState` UIA evidence through a proposal-only desktop Grounder seam.

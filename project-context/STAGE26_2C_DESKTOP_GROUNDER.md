# Stage 26.2C — Native Desktop LFM2.5-VL Grounder

Status: **ACTIVE / CI + PHYSICAL TARGET QUALIFICATION REQUIRED**

Base `main` at branch creation:

`784d0d44adada85a2f7253de7280e94f3cd16bf2`

## Goal

Add a proposal-only desktop visual grounder for one exact Windows window without exposing a new public Chat/MCP tool and without authorizing or executing an action.

The accepted Stage 25 local runtime is reused:

```text
llama.cpp build 10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
127.0.0.1:3068
CPU 8 threads
ctx 2048
```

Browser `production_policy` is deliberately not reused as Windows authorization.

## Production seam

`runtime/windows/grounder.py`

```text
locate_desktop_target(
  client,
  window_png,
  target_text,
  desktop_state,
  optional bounded UIA evidence
) -> GrounderProposal | None
```

`None` is ABSTAIN. Contract/provider failures raise `DesktopGrounderError`; callers must treat that as zero mutation.

## Exact-frame binding

Before inference:

- `DesktopState.coordinate_space` must be `screen_physical_px`;
- `DesktopState.screenshot_digest` must exist;
- SHA-256 of the exact PNG must equal that digest;
- PNG dimensions must exactly equal `DesktopState.window_bounds` width/height.

This binds the model proposal to the same observed window frame. Stage 26.2D will still require a fresh re-observation before any action.

## Coordinate contract

Model output is interpreted in:

`window_physical_px`

The adapter deterministically translates it to:

`screen_physical_px`

using the exact current `DesktopState.window_bounds.left/top` offset.

Browser `css_viewport` coordinates are not accepted or reused.

## Proposal fields

The proposal binds:

```text
target_text
window point + region
screen point + region
window_physical_px
screen_physical_px
frame_digest
screenshot_digest
window_instance
process_id
window_handle
bounded UIA evidence digest
method
consistency_iou
latency
confidence = null
confidence_basis = uncalibrated-model-proposal
```

`consistency_iou` is diagnostic evidence, not calibrated model confidence. No confidence number is invented before the adversarial dataset in Stage 26.2D.

## Model behavior

The adapter reuses the accepted native-bbox inventory + zoom mechanism:

- target-blind inventory for exact readable labels;
- zero matching labels -> ABSTAIN;
- multiple matching labels -> ABSTAIN;
- one candidate -> bounded zoom refinement;
- malformed/provider result -> error / zero mutation.

The model never clicks.

## Deterministic CI gates

Tests require:

- screenshot digest mismatch rejects before any model call;
- image dimensions match exact observed window;
- window-local coordinates translate correctly to physical screen coordinates;
- absent and ambiguous inventory cases ABSTAIN;
- UIA evidence is bounded;
- proposal keeps confidence explicitly uncalibrated;
- no action/actuation/WindowsBackend/shell channel exists in the grounder;
- browser CSS coordinate/promotion policy is not reused;
- physical harness restores the pre-existing local vision runtime state.

## Physical target qualification

Harness:

`scripts/stage26-desktop-grounder-qualification.ps1`

Driver:

`scripts/stage26-desktop-grounder-qualification.py`

The harmless WinForms fixture is observed through the production `DesktopState` path. The harness starts the already-reviewed local vision runtime only if needed and restores its prior running/stopped state afterward.

Required target gates:

```text
VISION_READY_PASS=True
VISION_RESTORED_PASS=True
SAME_FRAME_BINDING_PASS=True
COORDINATE_CONTRACT_PASS=True
TARGET_POINT_INSIDE_UIA_PASS=True
TARGET_EVIDENCE_BINDING_PASS=True
ABSENT_TARGET_ABSTAIN_PASS=True
STALE_FRAME_REJECTION_PASS=True
PROPOSAL_ONLY_CONTRACT_PASS=True
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
FIXTURE_KILLED=False
FIXTURE_CLEANUP_PASS=True
DRIVER_ERROR=<null>
ERROR=<null>
STAGE26_2C_DESKTOP_GROUNDER_RESULT=PASSED
```

No action-count field is used as evidence because this stage has no executor/actuation channel; the read-only/proposal-only boundary is enforced by code review and CI source-boundary tests.

## Non-goals

This stage does not add:

- public `desktop_*` tools;
- semantic/UIA -> vision routing;
- action authorization;
- click/type/scroll execution;
- calibrated confidence;
- cross-application accuracy claims;
- procedural runtime.

After target acceptance, Stage 26.2D integrates deterministic UIA -> visual fallback routing, freshness authorization and the adversarial accuracy suite.

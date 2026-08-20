# Stage 26.2C — Native Desktop LFM2.5-VL Grounder

Status: **ACCEPTED — physical target qualification passed**

Base `main` at branch creation:

`784d0d44adada85a2f7253de7280e94f3cd16bf2`

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

## Goal

Add a proposal-only desktop visual grounder for one exact Windows window without exposing a new public Chat/MCP tool and without authorizing or executing an action.

Accepted local runtime reused:

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

Primary internal result:

```text
ground_desktop_target(...) -> DesktopGroundingResult
```

Compatibility seam:

```text
locate_desktop_target(...) -> GrounderProposal | None
```

The explicit result preserves `proposal | abstain`, a reason and bounded diagnostics. The compatibility wrapper returns `None` on ABSTAIN. Provider/contract failures raise `DesktopGrounderError`; callers must treat that as zero mutation.

## Exact-frame binding

Before inference:

- `DesktopState.coordinate_space` must be `screen_physical_px`;
- `DesktopState.screenshot_digest` must exist;
- SHA-256 of the exact PNG must equal that digest;
- PNG dimensions must exactly equal `DesktopState.window_bounds` width/height.

The proposal binds to session/application/process/window identity, `frame_digest`, `screenshot_digest`, PID, HWND, process generation and optional bounded UIA evidence digest. Stage 26.2D must still re-observe freshness before action.

## Coordinate contract

Model output is interpreted in `window_physical_px` and deterministically translated to `screen_physical_px` with the current window origin. Browser `css_viewport` coordinates are not accepted or reused.

## Label policy

Text routing is fail-closed:

1. exact normalized inventory label match first;
2. only after `inventory-absent`, a desktop-only ordinal alias may remove one leading UI order marker such as `1.` or `2)`;
3. the resulting label must match exactly one already-observed inventory label;
4. zero or multiple alias candidates remain ABSTAIN;
5. no general fuzzy, Levenshtein or semantic-similarity matching is used.

This policy was introduced from physical evidence where the rendered target was `1. Benchmark start` and LFM2.5-VL read the same button as `Benchmark start`.

## Diagnostics

Bounded diagnostics include the exact decision, inventory/pass2 detection counts and parsed labels. They do not expose an action channel or raw model authority. The physical harness also persists the exact-window PNG separately as local sensitive evidence.

## Physical acceptance

Result directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054`

Exact screenshot:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\exact-window.png`

Screenshot SHA-256:

`b32ea145964c64de783077ed43ebc70839fab882bfd83c24931ee0f7fee8d95a`

Accepted result:

```text
VISION_READY_PASS=True
VISION_RESTORED_PASS=True
POSITIVE_GROUNDER_STATUS=proposal
POSITIVE_GROUNDER_REASON=grounder-accepted-ordinal-alias-proposal-only
POSITIVE_DECISION=accepted
POSITIVE_INVENTORY_DETECTION_COUNT=2
POSITIVE_INVENTORY_MATCH_COUNT=1
POSITIVE_INVENTORY_LABELS_JSON=["Benchmark start","Guarded list click + scroll"]
POSITIVE_PASS2_DETECTION_COUNT=1
POSITIVE_PASS2_LABELS_JSON=["Benchmark start"]
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
QUALIFICATION_EXIT_CODE=0
```

Source bindings:

```text
observer sha256 = b4f84d92a0e5aaf30f0d562ea55e6c3bc402d5d0c7ce3358946e0ec81377fda1
grounder sha256 = 0910bd0221a805609e5a1f6f32017ff6bed50e281cd7c44247b2352caa32327c
driver sha256   = cd4619f0ec5e21c030b43736107c7dc42795e49430c9ec84ad68cff826e64777
```

The decisive positive gate is `TARGET_POINT_INSIDE_UIA_PASS=True`: the local VLM proposed a point from pixels and that point fell inside independently observed current UIA bounds for the intended control.

## Qualification history

Three earlier runs were intentionally retained as evidence rather than hidden:

- `75db0b1...`: harness passed UIA AccessibleName rather than rendered text and exposed a stale `$LASTEXITCODE` lifecycle bug;
- `1d95d675...`: rendered text was used and lifecycle restore passed, but the API still collapsed abstain causes;
- `a08ac167...`: diagnostics showed the model detected `Benchmark start` while the requested rendered label was `1. Benchmark start`; absent-target and stale-frame gates already passed.

Those findings produced the bounded diagnostics and ordinal-only alias policy used by the accepted head.

## Non-goals / scope

Stage 26.2C does not add:

- public `desktop_*` tools;
- action authorization;
- click/type/scroll execution;
- calibrated confidence;
- cross-application accuracy claims;
- procedural runtime.

This is controlled WinForms target evidence, not general Windows accuracy.

## Next

Stage 26.2D integrates deterministic native/UIA -> visual fallback routing, fresh same-window/same-frame authorization and an adversarial accuracy suite before any broad desktop claim or coordinate action path is promoted.

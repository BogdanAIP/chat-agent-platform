# Stage 26.1B — Real bounded Windows Capture qualification

Status: **ACCEPTED / EXACT-HEAD REAL WINDOWS TARGET PASSED / MERGED VIA PR #81**

Branch base resolved from live `main` after merged Stage 26.1A:

`17380af312feb56c22cd196b2b4adb85f96ce304`

Stage 26.1A already proved exact-source OpenAdapt Flow/Capture installation and the model-free tutorial. Stage 26.1B asks a narrower new question:

> Can pinned OpenAdapt Capture record a real physical-user interaction in one harmless Windows window, preserve correct raw Windows UIA/window evidence, convert it into a Flow recording under an explicit remote-client surface contract and compile it without touching unrelated user applications or invoking the still-unaccepted Windows executor?

## Product boundary

This is **recording/conversion/compiler qualification only**.

It does not:

- integrate OpenAdapt into production `semantic-projection`;
- expose any new public Chat tool;
- use OpenAdapt `WindowsBackend` for replay;
- start the OpenAdapt Windows agent;
- call `/execute_windows` or any equivalent generic code execution;
- synthesize user input;
- automate a real user workload;
- claim arbitrary Windows application support.

Ordinary ChatGPT remains the only planner/intelligence.

## Exact upstream pins

Inherited from `config/stage26-openadapt-lock.json`:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Python requirement remains `3.12.x` for this exact Flow pin.

### Managed FFmpeg qualification asset

Capture's exact pinned `CaptureSession.get_frame_at()` reads video evidence; still-image-only capture is therefore not a faithful adapter qualification path for this pin.

Stage 26.1B uses the OpenAdapt Desktop-managed Windows FFmpeg artifact referenced by the pinned Desktop manifest rather than a random system FFmpeg:

```text
source repo: OpenAdaptAI/openadapt-desktop
source commit: 86b1da232d88537e5e4b92ec23571008ed7ff81f
manifest: src-tauri/ffmpeg-runtime-manifest.json
runtime: 8.1.2-r1
target: x86_64-pc-windows-msvc
license: LGPL-2.1-or-later
```

Archive plus `ffmpeg.exe` and `ffprobe.exe` SHA-256 values are lock-pinned and verified before recording. The harness also verifies the required non-GPL/no-network build properties and required capture encoders/muxers.

## Why physical user input is required

Pinned OpenAdapt Capture deliberately filters injected mouse/keyboard input.

Therefore a synthetic `SendInput`/automation test would not honestly qualify the recorder path. Stage 26.1B uses a dedicated harmless WinForms fixture and asks the user to perform a tiny physical sequence only inside that fixture.

No actual work application is used.

## Qualification fixture

One dedicated WinForms window is created with a unique per-run `Form.Text` title and native accessibility names.

The controls remain disabled until OpenAdapt Recorder reports READY.

After READY, perform exactly:

1. click the fixture's start button;
2. type exactly `CAPTURE_OK` into the fixture text box;
3. press `Enter` in that text box;
4. physically scroll the fixture list with the mouse wheel;
5. click the fixture finish button.

The fixture enables Finish only after it has independently observed the expected sequence.

Do not switch to or interact with unrelated windows during this short capture interval.

## Recorder configuration

Qualification-only recorder settings:

```text
capture_video = true
capture_audio = false
capture_images = false
capture_window_data = false
capture_structural_observations = true
capture_browser_events = false
capture_full_video = false
screen_capture_fps = 4
window = unique fixture title
ffmpeg / ffprobe = exact lock-pinned OpenAdapt managed runtime
```

The test preserves the raw capture, converted Flow recording and compiled bundle under one explicit local run directory for inspection. The temporary Python venv and managed FFmpeg runtime are removed after the run unless `-KeepEnvironment` is explicitly used.

## Upstream surface and structural contract

Pinned Flow 1.31.0 has two separate facts that Stage 26.1B must not conflate.

### 1. Window-scoped Capture uses the remote-client pixel contract

A window-scoped Capture session is represented in one window's pixel coordinate space. Flow's adapter records that window identity and the compiled workflow is expected to remain:

```text
backend_hints.backend = rdp
surface = rdp
```

Stage 26.1B must **not** force `target_surface="windows"` and must not claim native-Windows replay from this compiled bundle.

### 2. Local UIA suppression is controlled by explicit replay substrate

Pinned `openadapt_flow.desktop_record.record_desktop_capture()` calls the Capture adapter with structural inclusion controlled by `backend_kind`:

```text
include_structural = backend_kind not in ("rdp", "citrix")
```

Therefore **window scope by itself is not the suppression switch**.

For the Stage 26.1B conversion we deliberately pass:

```text
backend_kind = rdp
```

This is not a claim that the WinForms fixture is remotely hosted. It is an explicit statement about the **converted bundle's replay substrate contract**: local Windows UIA must not be promoted into an RDP/client-window bundle. Raw Capture UIA is inspected independently before conversion acceptance.

The intended two-layer evidence is therefore:

```text
raw OpenAdapt Capture
  -> native Windows UIA MUST exist for the qualification-owned fixture

explicit RDP Flow conversion
  -> structural_event_count = 0
  -> compiled_structural_count = 0
  -> surface = rdp
```

## Raw UIA containment contract

OpenAdapt Capture's structural schema includes native identity fields beyond text labels:

- `process.process_id`;
- `process.process_name`;
- `window.native_window_handle`;
- `window.title`.

The qualification must bind structural evidence to the **qualification-owned fixture process and captured HWND when those fields are available**.

It must not classify an observation as foreign solely because a UIA title string differs from `Form.Text`. WinForms may expose `AccessibleName` as the top-level accessibility title.

Containment therefore follows these rules:

- explicit PID mismatch -> FAIL;
- explicit captured-HWND mismatch -> FAIL;
- matching owned PID and/or matching captured HWND, with no explicit mismatch -> contained;
- no strong native identity at all -> not accepted as contained;
- textual title remains diagnostic evidence, not the sole security boundary.

The driver preserves per-observation PID/HWND/title diagnostics in `driver-result.json`.

## First real target run — 2026-08-18

The first physical Windows qualification was run against exact PR head:

`2e0b3bf3205eb9ee36449f6674c30a9d6ed81520`

The user sequence was independently confirmed by the fixture and by Capture/Flow:

```text
FIXTURE_SEQUENCE_PASS=True
REQUIRED_KINDS_PASS=True
EXPECTED_TEXT_PASS=True
EXPECTED_KEY_PASS=True
VIDEO_EVIDENCE_PASS=True
WINDOW_SCOPE_PASS=True
FFMPEG_RUNTIME_PASS=True
CHROME_SURVIVAL_PASS=True
FIXTURE_CLEANUP_PASS=True
```

Raw Capture observed all required action classes, including click/type/key/scroll.

The run failed for two harness assumptions:

### Harness defect A — UIA title alias misclassified as foreign

Observed:

```text
RAW_STRUCTURAL_ACTION_COUNT=9
FOREIGN_STRUCTURAL_WINDOW_COUNT=9
RAW_UIA_EVIDENCE_PASS=False
```

The recorded UIA top-level title was:

```text
Stage 26 capture qualification fixture
```

That string is the fixture's own WinForms `AccessibleName`, while the old driver compared it only to the unique `Form.Text` title. All nine observations were therefore incorrectly labelled foreign even though they came from the fixture.

Correction: containment now uses native PID/HWND identity and records title only as diagnostic evidence.

### Harness defect B — structural suppression was assumed from window scope alone

Observed:

```text
STRUCTURAL_EVENT_COUNT=4
COMPILED_STRUCTURAL_COUNT=4
COMPILED_SURFACE=rdp
SURFACE_CONTRACT_PASS=True
WINDOW_SCOPED_STRUCTURAL_SUPPRESSION_PASS=False
```

Inspection of the exact pinned Flow source showed why: `record_desktop_capture()` suppresses structural evidence only when `backend_kind` is explicitly `rdp` or `citrix`. The old Stage 26.1B driver omitted `backend_kind`.

Correction: Stage 26.1B now passes `backend_kind="rdp"` explicitly, preserving raw Windows UIA while requesting the intended UIA-free RDP conversion.

### Classification of the first run

The first run is retained as **valid real-target evidence of a harness defect**, not as operator failure and not as accepted Stage 26.1B qualification.

It was not converted to PASS retroactively. The corrected harness was rerun on a new exact head and passed as documented below.

## Successful exact-head target run — 2026-08-18

The corrected second physical Windows qualification was run against exact PR head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Local acceptance artifact:

```text
%LOCALAPPDATA%\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json
```

The complete target gate passed:

```text
FFMPEG_RUNTIME_PASS=True
DRIVER_PASS=True
RAW_ACTION_COUNT=40
RAW_STRUCTURAL_ACTION_COUNT=40
FOREIGN_STRUCTURAL_WINDOW_COUNT=0
RAW_UIA_EVIDENCE_PASS=True
STRUCTURAL_EVENT_COUNT=0
WINDOW_SCOPED_STRUCTURAL_SUPPRESSION_PASS=True
VIDEO_EVIDENCE_PASS=True
WINDOW_SCOPE_PASS=True
FOREIGN_STRUCTURAL_WINDOW_PASS=True
REQUIRED_KINDS_PASS=True
EXPECTED_TEXT_PASS=True
EXPECTED_KEY_PASS=True
UIA_EVIDENCE_PASS=True
FIXTURE_SEQUENCE_PASS=True
COMPILE_PASS=True
COMPILED_STEP_COUNT=30
COMPILED_STRUCTURAL_COUNT=0
COMPILED_SURFACE=rdp
SURFACE_CONTRACT_PASS=True
NATIVE_WINDOWS_REPLAY_CLAIMED=False
REPLAY_EXECUTION=SKIPPED_UNACCEPTED_WINDOWS_EXECUTOR
BOUNDED_REPLAY_REFUSAL=True
RAW_ARTIFACT_CONTAINMENT_PASS=True
CHROME_PROCESS_COUNT_BEFORE=12
CHROME_PROCESS_COUNT_AFTER=12
CHROME_SURVIVAL_PASS=True
FIXTURE_KILLED=False
FIXTURE_CLEANUP_PASS=True
STAGE26_1B_CAPTURE_RESULT=PASSED
TEST_EXIT_CODE=0
STAGE26_1B_TARGET_RESULT=PASSED
```

This exact tested head was merged by PR #81 as squash commit:

`94681ef27286f6483e26dbc00ef22d94be3f89d6`

The larger raw/Flow action counts are retained as evidence rather than normalized away. Acceptance depends on the independently verified fixture sequence, required event/text/key evidence, strict native window/UIA containment, successful Flow conversion/compiler contract, and containment/cleanup gates.

The OpenAdapt recorder emitted timestamp-order diagnostic ERROR lines during capture, but they did not abort recording or invalidate any acceptance gate.

## Driver acceptance

The corrected real capture driver must prove all of these:

```text
fixture_sequence_pass = true
video_evidence_pass = true
window_scope_pass = true
foreign_structural_window_pass = true
raw_uia_evidence_pass = true
required_kinds_pass = true
expected_text_pass = true
expected_key_pass = true
uia_evidence_pass = true
window_scoped_structural_suppression_pass = true
compile_pass = true
surface_contract_pass = true
bounded_replay_refusal = true
native_windows_replay_claimed = false
```

Required Flow event classes:

```text
click
type
key
scroll
```

Required text/key evidence:

```text
CAPTURE_OK
Enter
```

Raw UIA acceptance requires real structural evidence from the fixture and no explicit native identity mismatch with the qualification-owned fixture.

Converted Flow structural evidence is required to be empty only because Stage 26.1B now invokes the explicit `rdp` conversion contract. It is not inferred merely from window scope.

## Replay boundary

Compiled replay is intentionally recorded as:

```text
REPLAY_EXECUTION=SKIPPED_UNACCEPTED_WINDOWS_EXECUTOR
BOUNDED_REPLAY_REFUSAL=True
```

This is a **PASS condition** for Stage 26.1B, not missing work inside this gate.

The Windows executor belongs to Stage 26.1C because its process/session/authentication/blast-radius boundary has not yet been accepted.

## Harness safety

The harness must:

- use an isolated detached test worktree when invoked from the target command;
- create an isolated Python 3.12 venv inside the qualification run;
- verify exact VCS commits via installed distribution `direct_url.json`;
- download FFmpeg only from the reviewed lock URL and verify exact hashes;
- launch only the qualification-owned fixture as a child process;
- never enumerate/terminate normal user applications;
- never kill/close Chrome;
- use only the exact fixture process object for emergency fixture cleanup;
- preserve raw/converted/compiled evidence only inside the explicit qualification run directory;
- remove venv/FFmpeg runtime after the run by default;
- leave production Chat profiles/semantic runtime/tunnel untouched.

If the fixture cannot close gracefully and must be killed, the qualification fails even though only the qualification-owned PID is eligible for that cleanup.

## Expected result artifact

```text
%LOCALAPPDATA%\ChatAgentPlatform\stage26\capture-qualification\capture-<timestamp>\result.json
```

Preserved evidence under the same run directory:

```text
raw-capture\
flow-recording\
compiled-bundle\
fixture-state.json
driver-result.json
result.json
```

These artifacts should contain only the dedicated fixture and the test value `CAPTURE_OK` when the instructions are followed. They are local raw qualification evidence and are not synced automatically.

## PASS / FAIL interpretation

### PASS

PASS means:

- pinned OpenAdapt Capture genuinely observed physical user input on the target Windows machine;
- bounded window capture did not fall back to full-screen pixels;
- raw Windows UIA evidence was captured for the qualification-owned WinForms fixture with no native identity mismatch;
- expected event classes/text/key were represented;
- explicit RDP conversion suppressed local UIA as required for that remote-client surface;
- Flow compiled the converted recording according to its declared `rdp` surface contract;
- raw artifacts stayed in the qualification directory;
- normal Chrome survived;
- the unaccepted Windows executor was not invoked.

PASS therefore **does not** mean that a native-Windows structural replay path is solved. It qualifies the recorder and the safe conversion boundary honestly.

### FAIL

A fail is valuable evidence. Do not patch around it by disabling raw UIA, widening capture to full desktop, injecting actions, forcing a false Windows surface, inserting local structural locators into an `rdp` bundle or invoking the Windows executor.

Classify the failure as one of:

- Capture startup/video provision;
- native input observation;
- window scoping;
- raw UIA structural evidence/identity;
- Capture -> Flow conversion;
- explicit RDP structural suppression;
- compiler/surface contract;
- cleanup/containment;
- harness defect.

Fix only the measured boundary and rerun exact-head acceptance.

## Next if Stage 26.1B passes

Proceed to Stage 26.1C:

1. compare OpenAdapt typed Windows agent vs a narrower native/project-owned actuator;
2. prove legacy arbitrary execution disabled/unreachable in product configuration;
3. evaluate how privacy-friendly window-scoped captured evidence should map to native Windows procedures without falsifying upstream surface/UIA provenance;
4. prototype the accepted local LFM2.5-VL F16 through the proposal-only OpenAdapt `Grounder` seam;
5. rerun stale/ambiguous/freshness/false-action acceptance.

Stage 26.3 Windows desktop surface remains **REQUIRED / DO NOT DROP** after those qualification decisions.

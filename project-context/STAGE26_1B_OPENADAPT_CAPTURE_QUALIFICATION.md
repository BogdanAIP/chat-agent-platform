# Stage 26.1B — Real bounded Windows Capture qualification

Status: **DRAFT / TARGET RUN NOT YET ACCEPTED**

Branch base resolved from live `main` after merged Stage 26.1A:

`17380af312feb56c22cd196b2b4adb85f96ce304`

Stage 26.1A already proved exact-source OpenAdapt Flow/Capture installation and the model-free tutorial. Stage 26.1B asks a narrower new question:

> Can pinned OpenAdapt Capture record a real physical-user interaction in one harmless Windows window, preserve correct raw Windows UIA/window evidence, convert it into Flow recording input and compile it according to the upstream window-scoped contract without touching unrelated user applications or invoking the still-unaccepted Windows executor?

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

One dedicated WinForms window is created with a unique per-run title and native accessibility names.

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

## Important upstream surface finding

OpenAdapt Flow 1.31.0 deliberately treats **window-scoped Capture conversion** as a remote-display client-window contract and stamps:

```text
backend_hints.backend = rdp
surface = rdp
```

This is upstream behavior, not a project rewrite.

Therefore Stage 26.1B must **not** force `target_surface="windows"`. Doing so would correctly fail because the explicit surface would contradict the converter's declared backend.

The qualification compiles the recording according to the upstream-declared `rdp` surface and records that fact.

Consequences:

- PASS proves real Windows host capture + bounded window pixels + raw Windows UIA observation + Flow conversion/compiler compatibility;
- PASS does **not** prove native-Windows replay from that privacy-friendly window-scoped bundle;
- whether the project should adapt this window-scoped evidence into a native-Windows procedure is a later design/security decision;
- native Windows executor acceptance remains Stage 26.1C / Stage 26.3 work.

Do not hide this limitation by rewriting metadata in the qualification harness.

## Important upstream structural-evidence finding

Pinned OpenAdapt Capture can attach real Windows UIA observations to native actions. The qualification fixture is a local WinForms window specifically so this raw UIA path can be measured.

However, pinned Flow 1.31.0 deliberately does **not** promote local UIA observations when converting a window-scoped recording to its `rdp`/remote-client surface. Upstream's rationale is correct for the surface it models: local UIA in a remote-client window describes the local client shell, not the controls inside the remote session.

For our local WinForms fixture this creates an important, honest distinction:

```text
raw OpenAdapt Capture
  -> real Windows UIA for the WinForms fixture MUST be present

window-scoped Flow conversion
  -> surface = rdp
  -> local UIA structural locators MUST be suppressed by current upstream semantics
```

Therefore Stage 26.1B must prove both sides independently:

```text
raw_uia_evidence_pass = true
foreign_structural_window_pass = true
structural_event_count = 0
compiled_structural_count = 0
window_scoped_structural_suppression_pass = true
```

This is **not** evidence that UIA recording failed. It is evidence that the current privacy-friendly window-scoped conversion path does not directly produce a native-Windows structural bundle.

That gap becomes explicit input to Stage 26.1C:

- either qualify/adapt a native Windows capture path that preserves UIA while maintaining acceptable privacy/scope;
- or design a narrowly justified conversion/actuator boundary without falsifying upstream provenance.

Do not patch Stage 26.1B by forcing structural locators into an `rdp` bundle.

## Driver acceptance

The real capture driver must prove all of these:

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

Raw UIA acceptance requires real structural evidence from the fixture, not just pixel coordinates. Any structural window identity that is present must resolve to the unique fixture window; foreign structural window evidence fails the run.

Converted Flow structural evidence is expected to be empty on this exact **window-scoped `rdp` contract**, by upstream design. The test records this as a separate suppression PASS rather than incorrectly treating it as missing raw UIA.

Window-scoped conversion itself also refuses out-of-window mouse actions instead of silently dropping/replaying them.

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

These artifacts should contain only the dedicated fixture and the test value `CAPTURE_OK` when the instructions are followed. They are still treated as local raw qualification evidence and are not synced automatically.

## PASS / FAIL interpretation

### PASS

PASS means:

- pinned OpenAdapt Capture genuinely observed physical user input on the target Windows machine;
- bounded window capture did not fall back to full-screen pixels;
- raw Windows UIA evidence was captured for the WinForms fixture and no foreign structural window was observed;
- expected event classes/text/key were represented;
- the window-scoped Flow adapter intentionally suppressed local UIA under its current `rdp` semantics, exactly as upstream specifies;
- Flow compiled the converted recording according to its own declared window-scoped surface contract;
- raw artifacts stayed in the qualification directory;
- normal Chrome survived;
- the unaccepted Windows executor was not invoked.

PASS therefore **does not** mean that a native-Windows structural replay path is solved. It qualifies the recorder and exposes the conversion-surface gap honestly.

### FAIL

A fail is valuable evidence. Do not patch around it by disabling raw UIA, widening capture to full desktop, injecting actions, forcing a false Windows surface, injecting structural locators into an `rdp` bundle or invoking the Windows executor.

Classify the failure as one of:

- Capture startup/video provision;
- native input observation;
- window scoping;
- raw UIA structural evidence;
- Capture -> Flow conversion;
- expected upstream structural suppression;
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

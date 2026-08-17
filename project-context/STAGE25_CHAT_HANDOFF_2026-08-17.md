# Stage 25 chat handoff — 2026-08-17

Status: **active development handoff for the next ordinary ChatGPT conversation**.

This document is intentionally concrete. Continue from the repository and PR state below instead of reconstructing the Stage 25 history from scratch.

## Project boundary

Ordinary ChatGPT remains the planner and primary intelligence. Local vision is a small bounded capability behind the existing semantic/browser architecture; it is **not** a second planner and must never click by itself.

The intended product path is:

```text
ordinary ChatGPT planner
  -> semantic DOM/accessibility path first
  -> local vision only when visual fallback is needed
  -> deterministic local adapter
  -> local llama.cpp inference
  -> typed result / ABSTAIN
  -> existing semantic browser action performs any eventual interaction
```

Do not expose a generic raw model/prompt/endpoint tool to Chat. The existing five public semantic tools stay unchanged until Stage 25 promotion:

- `workspace_read`
- `workspace_write`
- `web_open`
- `web_observe`
- `web_interact`

The first future public vision action is still expected to be a narrow `vision_analyze(operation="ground_ui", ...)`-style capability after the benchmark path is safe enough to promote.

## Earlier completed platform stages

- Stage 24 PR #66 merged to `main`, squash `175d36236f80a1f99f091d4f031a1c6255f3652b`.
- Stage 24.1 PR #70 merged to `main`, merge `df1d5e232b739b62e72ad81e5d82fd01be53e884`.
- Direct stdio semantic projection is the selected ordinary-Chat path; 1MCP remains replaceable diagnostics/aggregation infrastructure, not the critical semantic path.
- Stage 25 preparation PR #71 merged, merge `3975839eb681cf95fabb3273366884e6aecb034c`.
- Stage 25 local-vision foundation PR #72 merged, squash `07bbd195d9f9f59cc491a1ea27905fbfcbf47e85`.

## Current PR and worktree

Current open PR:

- PR: `#73` — **Stage 25: Direct vs Mark-Grid grounding benchmark**
- branch: `chat/stage25-grounding-benchmark`
- base: `main`
- last fully tested pre-handoff head: `e5b8aac732c111704a7bec02d4459fa9624a3176`
- PR was open, mergeable, not draft, not merged.
- On `e5b8aac...`, `ci`, `CodeQL Security`, and `Secret History Scan` all completed successfully.

This handoff file itself advances the PR branch after `e5b8aac...`; when the next chat starts, query GitHub for the new PR head and update the local Stage 25 worktree to that exact head before running anything.

Local normal repository:

```text
C:\Users\eahra\Documents\Codex\2026-08-07\new-chat\outputs\chat-agent-platform
```

Isolated Stage 25 benchmark worktree:

```text
C:\Users\eahra\Documents\Codex\2026-08-07\new-chat\outputs\chat-agent-platform-stage25-grounding-benchmark
```

Do not disturb the user's normal checked-out development branch. Use the isolated worktree for Stage 25 target tests.

## Target machine

Windows target:

- HP 470 G8 Notebook PC
- Intel Core i5-1135G7
- 4 physical / 8 logical CPU cores
- 7.68 GB RAM
- Intel Iris Xe, no NVIDIA
- Windows 10
- llama.cpp CPU path selected for latency on this machine

The user enabled Chrome **Memory Saver = Maximum** and wants ordinary ChatGPT in Chrome to remain usable while local vision runs. This materially improved the memory envelope and is now part of the realistic target test condition.

Never auto-kill Chrome or arbitrary user processes.

## llama.cpp runtime

Installed runtime:

- `ggml.llamacpp` via winget
- llama.cpp release/build `b10448`
- commit `ad1de39e0`
- CLI identifies `0.1.0-dev (build 10448, commit ad1de39e0)`

Current successful CPU configuration for the 450M F16 path:

```text
--device none
--gpu-layers 0
--no-mmproj-offload
--no-op-offload
--threads 8
--threads-batch 8
--fit off
--ctx-size 2048
--batch-size 128
--ubatch-size 64
--cache-type-k q8_0
--cache-type-v q8_0
--image-min-tokens 64
--image-max-tokens 256
--parallel 1
--no-ui
--offline
```

Do not assume `--image-min-tokens/--image-max-tokens` caps the whole request context. They do not prevent context overflow from a large visual crop.

## Current model selection

### Selected working candidate: LFM2.5-VL-450M F16

Verified local artifacts:

```text
%LOCALAPPDATA%\ChatAgentPlatform\stage25\models\LFM2.5-VL-450M-GGUF\LFM2.5-VL-450M-F16.gguf
bytes 711486624
sha256 f7d130500beadcbe66b78fb7b1222142ccdf4edcb2596026a7ee30b4bafe6989

%LOCALAPPDATA%\ChatAgentPlatform\stage25\models\LFM2.5-VL-450M-GGUF\mmproj-LFM2.5-VL-450m-F16.gguf
bytes 189126080
sha256 51b458cfdbc736982145a35f798ce37611af0aab639e58b33473ba0c7815fd99
```

HF revision used for the exact pair: `166cd80bbe157dc86d65f964eb8cc6a2cede62ca`.

Do **not** quantize the 450M weights yet. With Chrome Memory Saver and `ctx=2048`, F16 is currently practical on the target laptop and gives the best measured quality. Quantization is a fallback only if later real workloads prove the F16 memory envelope insufficient.

### Rejected as primary default on this laptop

- 3B: unsafe memory pressure on the 7.68 GB target; do not retry merely by lowering safety guards.
- 1.6B: resource-feasible, but direct grounding quality was poor and it hallucinated present targets. Keep only as a possible later semantic/verifier candidate if measurements justify it.

## Controlled fixture

Authoritative screenshot:

```text
%LOCALAPPDATA%\ChatAgentPlatform\stage25\runtime\native-bbox-450m-20260817-090315\fixture\fixture.png
1280 x 720
sha256 bed6a8899858c299b7ca3476affe79b87709d54c8402cb56efed0cca28f974a3
```

Fixture metadata is in:

```text
tests/fixtures/stage25_grounding_cases.json
```

Six controlled cases:

1. `labeled-primary-button` — enabled `Send`, bbox `[1056,636,1200,684]`
2. `icon-only-control` — Search icon, bbox `[32,24,64,56]`
3. `repeated-row-action` — Gamma row menu, bbox `[1180,298,1208,326]`
4. `tiny-indicator` — red alert dot, bbox `[1212,28,1224,40]`
5. `state-disambiguation` — enabled Send vs disabled Send, target bbox `[1056,636,1200,684]`
6. `absent-target` — Export CSV, no bbox

The HTML fixture really contains both an enabled `Send` and a disabled `Send`. The current target-blind inventory happened to report only the enabled visible-looking Send plus Cancel, so the state-disambiguation case passed. Do not generalize that to all duplicate-label UIs; the adapter unit test intentionally fails closed when inventory returns duplicate target labels.

## Current native-bbox adapter design on the tested head

`runtime/local_vision_adapter/native_bbox.py` currently implements:

- target-blind labeled-button inventory for cases with `target_text`;
- exact normalized label match;
- zero match -> `inventory-absent`;
- multiple matches -> `inventory-ambiguous`;
- one text match -> use inventory bbox as coarse bbox;
- non-text cases -> target-conditioned native bbox detection on full screenshot;
- context crop around coarse bbox;
- **native crop with no forced Mark-Grid 512px upscaling**;
- second native bbox refinement on crop;
- deterministic bbox center as the candidate point;
- no automatic interaction.

Important current safety flaw: `coarse_refined_iou` is diagnostic only. After earlier Send evidence showed a correct refinement at very low IoU, the code currently accepts any single second-pass detection regardless of IoU. The latest tiny-target test demonstrates that this is unsafe for non-text targets.

## Strong successful target evidence

### Text-labeled Send + absent target, Chrome open, F16, ctx=2048

Real target run with Chrome left open and Memory Saver enabled:

```text
PRE-RUN RAM_FREE_GB=1.97
VIRTUAL_FREE_GB=7.58
LOAD_SECONDS=1.89
RAM_AFTER_LOAD_GB=1.10
SAFETY_STOP=False
MIN_RAM_FREE_GB=1.00
MIN_VIRTUAL_FREE_GB=7.06
MAX_SERVER_WORKING_SET_MB=994.5
MAX_SERVER_PRIVATE_MB=502.4
CHROME_STILL_RUNNING=True
```

`labeled-primary-button`:

```text
decision=accepted
point_hit=True
false_click=False
latency=11.3912s
inventory: Send + Cancel
refined bbox ~= [1084.16,625.28,1216.64,681.6]
box_iou ~= 0.5810
center_error_px ~= 23.34
```

`absent-target`:

```text
decision=inventory-absent
abstained=True
false_click=False
latency=2.4632s
inventory contained Send + Cancel and no Export CSV
no second request
```

This is the key evidence that target-blind inventory solves the previously observed `Export CSV` hallucination for this controlled text case.

### State disambiguation, Chrome open, F16, ctx=2048

`state-disambiguation` passed:

```text
decision=accepted
point_hit=True
false_click=False
latency=11.1379s
prediction_point=(1136.0,643.2)
box_iou ~= 0.4280
center_error_px ~= 18.61
CHROME_STILL_RUNNING=True
```

Inventory returned only the enabled-looking `Send` and `Cancel`, despite the fixture also containing a disabled `Send` elsewhere. Treat this as positive fixture evidence, not proof that inventory can always distinguish enabled/disabled duplicates.

## Latest target evidence — non-text grounding (MOST IMPORTANT HANDOFF STATE)

This was the final target-machine run before handoff. Chrome remained open, F16 was used, `ctx=2048`, pre-run free RAM was `2.19 GB`, minimum observed free RAM was `1.22 GB`, and there was no memory safety stop.

The three non-text cases produced:

```text
icon-only-control:
  decision=accepted
  hit=True
  false_click=False
  latency=10.382s

repeated-row-action:
  decision=error
  abstained=True
  false_click=False
  error=request 2904 tokens exceeds ctx 2048
  latency=8.1055s

tiny-indicator:
  decision=accepted
  hit=False
  false_click=True
  latency=10.2385s
```

Summary:

```text
point_accuracy=0.3333333333333333
false_clicks=1
abstains=1
errors=1
mean_latency=9.5753s
SAFETY_STOP=False
MIN_RAM_FREE_GB=1.22
SERVER_RUNNING_AFTER_TEST=False
CHROME_STILL_RUNNING=True
```

### `icon-only-control` details

This is a genuine success for non-text visual grounding:

```text
coarse bbox ~= [0,0,102.4,36]
context crop = [0,0,308,256]
refined bbox ~= [18.48,20.48,80.08,64]
prediction=(49.28,42.24)
true bbox=[32,24,64,56]
box_iou ~= 0.3820
center_error_px ~= 2.58
coarse_refined_iou ~= 0.1767
```

### `repeated-row-action` details

The first pass was too coarse:

```text
coarse bbox = [640,360,1024,504]
context crop = [128,216,1280,648]
```

That crop is `1152 x 432`, producing a second request of **2904 tokens**, which exceeds `ctx=2048`.

This is not a RAM failure and not yet reliable evidence that the model cannot ground the Gamma menu. It is an adapter crop-budget failure. Do not solve it by blindly returning to ctx=4096; first bound/downscale the native crop.

A likely deterministic fix is to cap non-text crop dimensions / area while preserving the coarse region and nearby context. For this exact case, a width cap around `768 px` with a smaller context multiplier should still include the true right-side Gamma menu while keeping the second request below ctx=2048. Measure rather than assume the final cap.

### `tiny-indicator` details — safety bug

First pass:

```text
coarse bbox ~= [1126.4,36,1164.8,64.8]
context = [1017,0,1274,256]
```

Second pass:

```text
refined bbox ~= [1209.75,51.2,1230.31,76.8]
prediction=(1220.03,64.0)
true bbox=[1212,28,1224,40]
coarse_refined_iou=0.0
box_iou=0.0
center_error_px ~= 30.07
false_click=True
```

This proves the current rule "single refined detection => accepted; IoU only diagnostic" is unsafe for non-text tiny targets.

Do **not** globally add a high IoU threshold: text-labeled Send is correct even when coarse/refined IoU is extremely small, because the target-blind text inventory independently proves target existence. The safety rule should be target-type/adaptive.

## Recommended next implementation sequence

**Do not merge PR #73 yet.** The latest tiny-target false click is a product-safety blocker.

Proceed in this order:

1. Add a fail-closed spatial-consistency rule for **non-text** native grounding. Minimal safe version: if there is no independent text inventory and coarse/refined IoU is `<= 0`, return `inconsistent`/ABSTAIN instead of accepting a click. This would make the current tiny-indicator result safe while preserving the successful text cases and Search icon case.
2. Add deterministic crop budgeting for large non-text coarse boxes. Avoid forced upscaling; also avoid sending a 1152x432 crop when ctx=2048. Prefer bounded crop size/area or downscale-only logic. Keep enough context to reach the true candidate even when coarse bbox is offset.
3. Add/adjust unit tests covering both safety rules:
   - non-text zero-overlap refinement must fail closed;
   - text inventory path may still accept low coarse/refined IoU after inventory proof;
   - oversized native crop is bounded without changing source-coordinate mapping.
4. Wait for GitHub CI/CodeQL/secret scan on the patched head.
5. Re-run **only the three non-text fixture cases** with Chrome open, F16, ctx=2048, conservative RAM guard. Do not repeat the old six-case monolithic stress test.
6. Acceptance goal for that run:
   - Search icon: hit;
   - Gamma row menu: either hit or safe ABSTAIN, but no context error;
   - tiny indicator: hit or safe ABSTAIN, **never false click**.
7. If tiny indicator only abstains after the minimal safety patch, then evaluate one extra bounded refinement/verification pass for tiny targets before considering a second model. Do not load 450M and 1.6B simultaneously on this 8 GB machine.
8. When all six controlled cases are safe (hits where supported, ABSTAIN otherwise, zero false clicks/provider errors for accepted path), update Stage 25 docs/PR description and only then consider merging PR #73.

## Product architecture after the current evidence

The strongest current design is:

```text
ChatGPT planner
  -> semantic DOM/accessibility first
  -> visual fallback only when needed
       -> if readable text target:
            target-blind 450M button inventory
            -> exact target label match
            -> native bounded crop
            -> 450M bbox refinement
       -> else:
            450M coarse native bbox
            -> bounded crop/downscale policy
            -> 450M bbox refinement
            -> non-text spatial/verification safety gate
       -> deterministic safe point inside validated bbox
       -> ABSTAIN on absence, ambiguity, disagreement, overflow or unsafe geometry
```

Keep Mark-Grid as a research comparator/optional independent fallback, not the default path. The 450M model is explicitly trained for bbox/object grounding and is currently much more promising on this target hardware.

## Important do-not-do items

- Do not merge PR #73 while tiny-target false click is unresolved.
- Do not re-run the 3B model on this laptop by lowering RAM guards.
- Do not make 1.6B the primary locator based on size alone; its measured grounding quality was poor.
- Do not quantize 450M yet; F16 currently runs with Chrome open and acceptable memory.
- Do not restore Mark-Grid-style forced 512px crop enlargement to native bbox.
- Do not simply increase ctx to hide oversized crop behavior without first fixing crop budgeting.
- Do not use model self-reported confidence as the safety gate.
- Do not auto-click from the adapter.
- Do not add a public Chat vision action until target-machine quality/safety evidence is sufficient.

## How the next chat should start

1. Use the GitHub connector/plugin.
2. Inspect PR #73 and its current head/checks.
3. Read this handoff plus `runtime/local_vision_adapter/native_bbox.py`, `tests/test_native_bbox.py`, `tests/fixtures/stage25_grounding_cases.json`, and the latest PR comments.
4. Update the isolated local worktree to the exact current PR head before asking the user to run a target command.
5. Patch the two blockers above: non-text zero-overlap safety and bounded native crop.
6. Give the user one copy-paste PowerShell action at a time.

The user prefers concise Russian explanations and one concrete executable action per turn when local execution is required.

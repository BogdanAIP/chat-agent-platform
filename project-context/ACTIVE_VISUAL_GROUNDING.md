# Stage 25 — Active Visual Grounding

Status: **IMPLEMENTATION / BENCHMARK FOUNDATION ACTIVE / NOT YET CHAT-FACING**

Date: 2026-08-16.

## Goal

Turn local vision from one-shot screenshot description into a bounded active-perception capability while ordinary ChatGPT remains the planner.

The product rule is:

```text
semantic-first when deterministic structure exists
  -> vision fallback when pixels matter
  -> adaptive local refinement only when needed
  -> typed result or explicit abstain
```

Do **not** create a second autonomous planner inside the local model layer.

## Research baseline — Auxiliary Reasoning / Mark-Grid Scaffold

Primary research source:

- paper: `How Auxiliary Reasoning Unleashes GUI Grounding in VLMs`, arXiv `2509.11548`;
- public reference implementation: `https://github.com/liweim/AuxiliaryReasoning`;
- reference repository license: MIT.

The paper identifies a useful failure mode for general VLMs: a model may understand where a GUI target is while still performing poorly when asked to emit explicit pixel coordinates. The proposed auxiliary-reasoning methods add deterministic spatial cues to the image rather than fine-tuning the model.

The strongest reported method is **Mark-Grid Scaffold**. The published runner configuration for this method explicitly uses `num_grid=8`, `num_zone_in=1`, `with_origin_chart=True` and `enlarge=True`. It therefore performs two `8 x 8` passes: first on the overview, then on the selected crop.

The model prompt asks for exactly four IDs corresponding to the target's leftmost, topmost, rightmost and bottommost cells. A useful implementation detail from the public code is that those four IDs are then de-duplicated (`set(pred)`) and the runner takes the union of the complete rectangles of every selected cell. Stage 25 should preserve this **union-of-selected-cells** behavior in the faithful baseline rather than silently substituting stricter axis-only math.

Another important code-level detail is `enlarge=True`: the reference renderer preserves aspect ratio and only enlarges a selected crop when its shorter side is **below 512 px**. It does **not** shrink an already-larger crop to 512 px. The project keeps any exact-512/downscale policy as a separate experimental variant so benchmark B remains traceable to the reference implementation.

Reported ScreenSpot-v2 examples from the paper include:

- Gemini-2.5-Flash: Direct Prediction `5.66%` -> Mark-Grid `72.09%`;
- Gemini-3.1-Pro: Direct Prediction `11.72%` -> Mark-Grid `95.20%`.

These numbers are **paper-specific evidence, not an expected LFM2.5-VL-3B score**. Stage 25 must measure the effect on the actual target model/runtime/hardware.

Do not claim ICLR 2026 acceptance unless an authoritative conference source is separately verified. The arXiv paper and public implementation are sufficient as a reproducible research baseline.

## Product architecture

Keep one small semantic capability instead of exposing screenshot micromanagement as separate Chat tools.

Candidate Chat-facing shape:

```text
vision_analyze(
  operation = "ground_ui",
  image = <reviewed local image reference>,
  target = <natural-language target>,
  precision = "adaptive"
)
```

Internal flow:

```text
ordinary ChatGPT
  -> vision_analyze(operation=ground_ui)
  -> local vision adapter
       -> direct grounding attempt
       -> deterministic validation
       -> if sufficient: return
       -> otherwise Mark-Grid pass 1
       -> deterministic coarse crop
       -> reference-compatible enlarge-if-needed
       -> Mark-Grid pass 2
       -> deterministic source-coordinate remap
       -> validation
       -> return typed grounding OR abstain
```

ChatGPT decides **what** the user wants. The adapter decides how to perform bounded visual refinement. The local VLM must not become another task planner.

## Why Mark-Grid belongs inside the adapter

Do not expose separate public tools such as `scan_screen`, `zoom_in`, `apply_grid`, and `get_coordinates` merely to reproduce the internal perception loop. That would:

- spend extra MCP round trips;
- force ChatGPT to micromanage pixels;
- couple the public surface to one grounding strategy;
- make future runtime/model replacement harder;
- encourage unnecessary multi-pass inference on easy cases.

The public contract should remain stable even if the internal implementation later changes from Mark-Grid to another grounding strategy.

## Semantic-first, vision-when-needed

For browser content, deterministic structure remains preferable when available:

```text
Playwright / accessibility / DOM grounding
  -> exact target available? use it
  -> otherwise visual grounding fallback
```

Vision is especially valuable for canvas content, screenshots, remote desktops, image-heavy controls, maps, rendered documents, games, desktop applications, and cases where accessible semantics are missing or misleading.

A visual model should not replace a deterministic selector that already identifies the target reliably.

## Adaptive grounding policy

The first product benchmark should compare several policies rather than assuming every request needs two VLM passes.

### A. Direct

One vision call attempts a point/bounding box directly.

Use as the fast baseline and as the first attempt for `precision=adaptive`.

### B. Original Mark-Grid

Reproduce the public implementation's two-pass `8 x 8` scaffold as faithfully as practical:

1. overlay the full image with numbered row-major cells `0..63`;
2. ask for exactly four extremity cell IDs, allowing duplicates;
3. de-duplicate the returned IDs and union every selected cell rectangle into the coarse ROI;
4. crop from the source image;
5. if the crop's shorter side is below `512 px`, enlarge proportionally until it reaches the minimum; otherwise keep the crop at its existing size;
6. overlay a fresh `8 x 8` grid;
7. ask for four extremity IDs again and union their selected cells;
8. map the second-pass region back to source-image coordinates and use its center as the ScreenSpot-style click point.

Rendering compatibility tests should separately cover the reference implementation's integer/`ceil` grid behavior. Geometry tests must not depend on a model, Pillow, OpenCV or network access.

This is the evidence-backed baseline and should be implemented before modifying the algorithm.

### C. Grid -> crop -> direct bbox

After reproducing B, benchmark whether the second grid can be replaced by direct bounding-box prediction on the magnified crop. Do not assume this is better merely because it appears geometrically more precise.

### D. Candidate/landmark-assisted refinement

Only after A/B/C are measured, consider deterministic OCR/UI candidates as visual landmarks. This can combine structural evidence with VLM target understanding without making the VLM responsible for every geometric detail.

## Stop-when-good-enough

`precision=adaptive` should avoid mandatory refinement.

A direct result may be accepted only when deterministic validation says it is sufficiently unambiguous. Otherwise the adapter escalates to Mark-Grid.

Examples of escalation signals:

- malformed or missing coordinates;
- target point outside the image;
- reversed or degenerate bounding box;
- several plausible target candidates;
- tiny target relative to the current image;
- weak textual/visual evidence;
- output schema violation;
- disagreement between available deterministic candidates and the VLM result.

The adapter must support **ABSTAIN**. A false click is worse than returning that the target could not be grounded reliably.

## Stable typed result

Candidate normalized result shape:

```json
{
  "found": true,
  "target": "Send button",
  "point": { "x": 0.823, "y": 0.741 },
  "bbox": { "x1": 0.781, "y1": 0.706, "x2": 0.866, "y2": 0.779 },
  "passes": 2,
  "method": "mark_grid_8x8_two_pass",
  "confidence": "high",
  "evidence": ["visible label: Send"],
  "uncertainty": []
}
```

Use normalized source-image coordinates at the adapter boundary where practical. Pixel conversion belongs at the final action boundary that knows the exact current viewport/screen geometry.

Do not expose model identifiers, raw runtime endpoints, arbitrary prompts or unrestricted file paths in this result or request contract.

## Deterministic scaffold engine boundary

Separate image/geometry mechanics from inference:

```text
local vision adapter
  -> scaffold/geometry engine
       -> grid cell IDs and bounds
       -> reference union-of-selected-cells ROI
       -> crop/enlarge planning
       -> local-to-source coordinate remap
       -> benchmark scoring and validation
  -> provider-neutral inference boundary
       -> llama.cpp + LFM2.5-VL-3B today
       -> replaceable runtime/model later
```

The scaffold engine must be deterministic and independently testable. Do not copy the reference repository wholesale or vendor its font/model/API stack. Reimplement only the required geometry/overlay behavior under the project's own tests. Do not copy bundled font files.

## Stage 25 grounding benchmark

Before public semantic integration, build a controlled benchmark where ground truth is known independently of the VLM.

For browser fixtures, Playwright can provide authoritative `boundingBox()` values while the VLM receives only screenshot pixels plus the natural-language target.

The first deterministic fixture is now tracked under `tests/fixtures/stage25_grounding_fixture.html` with a `1280 x 720` viewport and companion metadata `tests/fixtures/stage25_grounding_cases.json`. It includes labeled, icon-only, repeated-control, tiny-target, visual-state and deliberately absent-target cases. Browser capture still has to verify the metadata against real `getBoundingClientRect()` / Playwright `boundingBox()` values before any model score is accepted.

Benchmark at least:

- ordinary labeled buttons;
- icon-only controls;
- visually similar repeated controls;
- tiny targets;
- dense tables/toolbars;
- canvas-rendered controls;
- different viewport sizes and scale factors;
- high-resolution screenshots where downsampling may hide small targets;
- deliberately absent targets to measure abstention/false positives.

Compare:

```text
A  Direct grounding
B  Original two-pass Mark-Grid
C  Grid -> crop -> direct bbox
D  Candidate/OCR-assisted refinement (only after A/B/C)
```

Required metrics:

- point-in-target accuracy as the primary ScreenSpot-style click metric;
- bounding-box overlap / IoU when a bbox is returned;
- pixel/normalized center error;
- false-click rate;
- correct-abstain and false-abstain rate;
- VLM calls per task;
- end-to-end latency;
- process working set / free-memory floor;
- malformed-response rate;
- method-specific failure notes.

Provider-neutral scoring helpers now live in `runtime/local_vision_adapter/benchmark.py`; they deliberately distinguish an absent target with correct abstention from an absent target with a false positive.

Do not select a grounding method from published Gemini/Gemma results alone.

## Current target runtime baseline

The current measured reference configuration is:

```text
runtime = llama.cpp b10448 / build 10448 / commit ad1de39e0
model = LiquidAI/LFM2.5-VL-3B-GGUF Q4_K_M
mmproj = Q8_0
main model = CPU
mmproj = CPU for fastest measured path
threads = 8
ctx = 1024 for the current controlled synthetic vision test
```

The final 6-vs-8 interleaved thread benchmark selected 8 threads provisionally: median synthetic vision latency `13.84 s`, with all six 6/8-thread runs semantically correct. This is a runtime baseline, **not a GUI-grounding quality result**.

The earlier Vulkan tests showed that 8 main-model layers on Intel Iris Xe were slower than CPU-only, while mmproj-only Vulkan reduced RAM pressure but remained slower than the CPU reference. Keep those as optional memory-pressure modes, not the default grounding path.

## Implementation state and order

Completed foundation work on `chat/stage25-local-vision-adapter`:

1. deterministic Mark-Grid grid/crop/remap primitives with independent unit tests;
2. reference-aligned union-of-selected-cells semantics and two-pass geometry contract;
3. explicit reference `enlarge=True` crop policy, separated from exact-short-side experimental resizing;
4. provider-neutral grounding metrics;
5. first controlled GUI fixture + authoritative metadata contract.

Next dependency-valid work:

1. browser-render the fixture and prove metadata boxes against Playwright/DOM geometry;
2. add the internal provider-neutral inference request/response boundary using the already-proven local llama.cpp/LFM path;
3. reproduce **Direct** and the original **two-pass Mark-Grid** on the fixture first;
4. measure LFM2.5-VL-3B A vs B on the target Windows laptop;
5. only then test C and any OCR/UI-landmark extension;
6. define the final adaptive escalation/abstain policy from measured evidence;
7. add local-path/scope, malformed-result, timeout, runtime-failure and memory-pressure tests;
8. only after those gates, add the reviewed `vision_analyze` semantic operation and run a fresh ordinary-Chat end-to-end acceptance.

## Acceptance rule

Active perception is accepted into the public Chat path only when the target-machine benchmark shows that it improves GUI grounding enough to justify its extra latency and memory cost **without increasing false-click risk**.

Until then, Mark-Grid and related active-perception methods are internal Stage 25 benchmark/adapter mechanisms, not new public tools.

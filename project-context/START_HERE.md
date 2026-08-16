# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## What the project is

`chat-agent-platform` is a thin bridge from ordinary ChatGPT Chat to local Windows capabilities through standard MCP. ChatGPT remains the planner/intelligence. The repository owns integration, lifecycle, deterministic compatibility adapters, configuration and acceptance logic, not a second AI agent platform.

## Stage 24 — DONE

Stage 24 was squash-merged to `main` on 2026-08-16 as:

`175d36236f80a1f99f091d4f031a1c6255f3652b` — `Stage 24: standalone Windows bootstrap and lifecycle manager (#66)`.

Stage 24 proved the exact five-tool semantic ordinary-Chat contract through the then-normal 1MCP transport:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

The Stage 24 1MCP path worked and remains valid acceptance evidence.

## Stage 24.1 — DONE

Stage 24.1 was squash-merged to `main` on 2026-08-16 as:

`df1d5e232b739b62e72ad81e5d82fd01be53e884` — `Stage 24.1: direct semantic tunnel A/B acceptance (#70)`.

Selected normal product path:

```text
ordinary ChatGPT Chat
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> five-tool semantic projection over stdio
      -> Filesystem MCP
      -> Playwright MCP
      -> future focused capability adapters
```

`semantic-direct` remains temporarily as a compatibility/diagnostic alias. 1MCP is **not removed**; it remains replaceable internal infrastructure for diagnostics/aggregation/adaptive experiments where its features add measured value.

Final target release acceptance also passed after merge from the stable LocalAppData installation:

```text
STAGE24_1_PERSISTENT_INSTALL=PASS
active_profile=semantic
tunnel_binding=direct-stdio
active_count=1
conflict=false
PORT_3050_LISTENER_COUNT=0
```

## Stage 25 preparation — DONE

PR #71, `Docs: close Stage 24.1 and activate Stage 25 local vision`, merged on 2026-08-16 as:

`3975839eb681cf95fabb3273366884e6aecb034c`.

That merge made Stage 25 the authoritative continuation point and preserved the runtime/model/hardware reconnaissance and benchmark evidence in project context.

## Current stage — Stage 25 local specialist inference / active visual grounding

Active branch:

`chat/stage25-local-vision-adapter`

Active PR:

`#72 — Stage 25: active visual grounding foundation`

Goal: add local model-powered perception as a bounded replaceable capability backend without creating a second planner.

Current product shape:

```text
ordinary ChatGPT planner
  -> small typed local-vision capability
  -> deterministic focused local adapter
       -> semantic-first when deterministic structure exists
       -> direct visual grounding baseline
       -> bounded Mark-Grid refinement when needed
       -> deterministic validation / explicit abstain
  -> replaceable local inference runtime
  -> replaceable local VLM
```

Read these Stage 25 documents together:

- `LOCAL_SPECIALIST_INFERENCE.md` — runtime/model/hardware evidence and acceptance gates;
- `STAGE25_TARGET_BENCHMARKS.md` — measured target-machine benchmark evidence;
- `ACTIVE_VISUAL_GROUNDING.md` — current active-perception/GUI-grounding architecture and benchmark plan.

## Current verified local VLM baseline

The preferred 3B model has successfully loaded and completed real local multimodal requests on the target Windows laptop.

Verified path:

```text
runtime = llama.cpp b10448 / build 10448 / commit ad1de39e0
model = LiquidAI/LFM2.5-VL-3B-GGUF Q4_K_M
mmproj = mmproj-LFM2.5-VL-3B-Q8_0.gguf
CPU = 11th Gen Intel Core i5-1135G7
RAM = 7.68 GB
GPU = Intel Iris Xe
main model placement = CPU
mmproj placement = CPU for fastest measured path
threads = 8
ctx = 1024 for current controlled tests
```

The exact official GGUF artifacts were downloaded and SHA256-verified before use.

A deterministic synthetic vision request correctly returned:

```text
TITLE=STAGE25 VISION TEST; CIRCLE=red; SQUARE=blue; CODE=A7-42
```

The final interleaved CPU thread benchmark selected **8 threads provisionally**:

- 6-thread median vision latency: `14.13 s`;
- 8-thread median vision latency: `13.84 s`;
- all six 6/8-thread runs were semantically correct.

This is a runtime baseline, not a GUI-grounding quality score.

### Iris Xe findings

`llama.cpp` detects Intel Iris Xe as `Vulkan0`, but measured offload modes do not beat CPU-only for latency:

- 8 main-model layers on Vulkan were substantially slower than CPU-only;
- mmproj-only Vulkan reduced RAM pressure but remained slower than CPU-only.

Keep those as optional memory-pressure/comparison modes, not the default fast path.

## Active visual grounding baseline

Research baseline:

- `How Auxiliary Reasoning Unleashes GUI Grounding in VLMs`, arXiv `2509.11548`;
- public MIT implementation: `liweim/AuxiliaryReasoning`.

The key candidate is **Mark-Grid Scaffold**. Verified code-level details from the public implementation:

- experiment uses `num_grid=8`, `num_zone_in=1`, `with_origin_chart=True`, `enlarge=True`;
- the model is asked for four extremity cell IDs and duplicates are allowed;
- the reference runner then de-duplicates those IDs and unions the complete rectangles of all selected cells;
- `enlarge=True` only upscales when the crop's shorter side is below `512 px`; it does not downscale an already-larger crop to 512.

These details define the faithful benchmark baseline. Do not silently replace them with a cleaner but different algorithm.

Current project rule:

```text
semantic-first when deterministic structure exists
  -> Direct visual grounding baseline
  -> if insufficient, bounded local refinement
  -> faithful two-pass Mark-Grid baseline
  -> deterministic validation
  -> typed grounding result OR ABSTAIN
```

Do **not** expose `scan_screen`, `zoom_in`, `apply_grid`, `get_coordinates` as separate public Chat tools merely to reproduce the perception loop. Keep refinement inside the adapter.

Candidate future public shape remains one bounded capability such as:

```text
vision_analyze(
  operation = "ground_ui",
  image = <reviewed local image reference>,
  target = <natural-language target>,
  precision = "adaptive"
)
```

No new Chat-facing action is accepted yet.

## Current implementation in PR #72

The active branch now contains:

- `project-context/ACTIVE_VISUAL_GROUNDING.md`;
- `runtime/local_vision_adapter/mark_grid.py` — deterministic row-major grid, reference union semantics, crop/enlarge policy, two-pass remap and validation;
- `runtime/local_vision_adapter/benchmark.py` — provider-neutral point-in-target, IoU, center-error, false-click and abstention scoring;
- `tests/test_mark_grid.py`;
- `tests/test_grounding_benchmark.py`;
- `tests/fixtures/stage25_grounding_fixture.html`;
- `tests/fixtures/stage25_grounding_cases.json`.

The first controlled browser fixture is fixed at `1280 x 720` and covers:

- labeled primary button;
- icon-only control;
- repeated similar row actions;
- tiny target;
- enabled-vs-disabled visual state;
- deliberately absent target for abstention/false-positive measurement.

The fixture page exposes its DOM rectangles, while the companion metadata records expected boxes. A real browser/Playwright capture must still verify those two sources agree before any model score is accepted.

The public five semantic tools remain unchanged.

## Next dependency-valid Stage 25 work

1. Let PR #72 CI verify the current deterministic geometry/metrics/fixtures.
2. Browser-render the fixture and prove every metadata box against actual DOM/Playwright geometry.
3. Add an internal provider-neutral inference request/response boundary using the already-proven local llama.cpp/LFM path.
4. Run **Direct grounding** on the controlled fixture.
5. Run the faithful **two-pass Mark-Grid** baseline on exactly the same cases.
6. Compare point-in-target accuracy, false-click/abstain behavior, latency and memory on the target Windows machine.
7. Only after Direct-vs-Mark-Grid evidence, test `grid -> crop -> direct bbox` and optional OCR/UI-landmark assistance.
8. Define adaptive escalation and abstention thresholds from measured evidence.
9. Add path/scope, malformed-result, timeout, runtime-failure and memory-pressure tests.
10. Only then version the public semantic surface, refresh/review the Chat app and run fresh ordinary-Chat E2E acceptance.

## Stage 25 quality measurements

Grounding acceptance must capture at least:

- point-in-target accuracy as the primary ScreenSpot-style click metric;
- bbox IoU when applicable;
- normalized/pixel center error;
- false-click rate;
- correct-abstain / false-abstain rate;
- VLM calls per task;
- end-to-end latency;
- process working set / free-memory floor;
- malformed-response rate.

Published Gemini/Gemma Mark-Grid gains are research evidence, not a substitute for LFM2.5-VL-3B target-machine measurement.

## Important findings to preserve

- Chat action snapshots are frozen until reviewed/refreshed; server-side tool changes do not silently replace an already-scanned snapshot.
- Concrete typed Filesystem + Playwright actions work together in one ordinary-Chat conversation.
- A larger tested action inventory showed effective snapshot pressure/truncation around 20 actions; this is measured behavior, not an official universal limit.
- The generic adaptive `tool_list` / `tool_schema` / `tool_invoke` surface is not the ordinary-Chat product contract.
- OpenAI safety is context-sensitive beyond app permission mode.
- The semantic projection must remain a small deterministic typed compatibility boundary, not a planner or generic gateway.
- Installed/source manager ownership and fail-closed handling apply to both 1MCP-backed and direct semantic managed runtimes.
- A visual model should not replace deterministic Playwright/accessibility/DOM grounding when the exact semantic target is already available.
- A failed/uncertain visual grounding request must be allowed to return **ABSTAIN** instead of inventing a click coordinate.

## Product boundary

- ordinary ChatGPT remains the intelligence/planning layer;
- local specialist models may be bounded capability backends but never the second planner;
- prefer official/vendor or mature OSS components before project-owned infrastructure;
- do not recreate a project-owned generic MCP gateway, registry, vault, job system or workflow brain;
- keep 1MCP only where its measured capabilities are useful rather than forcing it into every request path;
- keep local inference runtime and model replaceable behind a focused adapter/semantic contract;
- do not expose arbitrary model names, raw inference endpoints, raw prompts, unrestricted local paths or arbitrary remote image URLs to ordinary Chat.

## How to continue safely

Before changing code:

- inspect the active branch, PR, exact head and workflow logs;
- read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `LOCAL_SPECIALIST_INFERENCE.md`, `ACTIVE_VISUAL_GROUNDING.md`, `STAGE25_TARGET_BENCHMARKS.md` and `DEVELOPMENT_PRINCIPLES.md`;
- preserve the five-tool semantic contract and single-owner/fail-closed regressions while deliberately versioning any future vision action surface;
- distinguish CI/local deterministic tests from real target-machine model acceptance;
- use the user only for irreducible target-machine or ordinary-Chat UI gates;
- never claim an ordinary-Chat or target-machine test unless that exact path actually ran;
- preserve/reconcile local uncommitted work rather than discarding it.

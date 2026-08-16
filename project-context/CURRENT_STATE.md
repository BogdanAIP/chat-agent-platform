# Current State

## Stage 24 — complete

Stage 24 was squash-merged to `main` on 2026-08-16 as commit `175d36236f80a1f99f091d4f031a1c6255f3652b` from PR #66.

The accepted Stage 24 baseline proved the exact five-tool semantic ordinary-Chat contract through 1MCP:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

Real ordinary-Chat E2E read `SEMANTIC_FINAL_INPUT_20260816`, navigated through the actual `Learn more` link from `example.com` to IANA `Example Domains`, wrote a result file and independently read it back. This remains valid historical acceptance evidence; Stage 24's 1MCP route was not broken.

## Stage 24.1 — complete

Stage 24.1 was squash-merged to `main` on 2026-08-16 as commit `df1d5e232b739b62e72ad81e5d82fd01be53e884` from PR #70.

The accepted normal semantic path is now:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> Filesystem / Playwright / future focused adapters
```

The A/B baseline remained:

```text
Stage 24 baseline
Tunnel -> HTTP 1MCP -> stdio semantic-projection

Stage 24.1 selected path
Tunnel -> stdio semantic-projection
```

Both paths completed 3/3 healthy lifecycle cycles on the target Windows machine. Average measured timings:

| Metric | 1MCP baseline | Direct stdio |
|---|---:|---:|
| Average initial Start | 123685 ms | 5007 ms |
| Average repeated/idempotent Start | 84119 ms | 4876 ms |
| Average Stop | 23252 ms | 1043 ms |
| Port 3050 listeners while running | 1 | 0 |

Direct stdio was approximately 24.70x faster to start, 17.25x faster on repeated Start and 22.29x faster to stop in this sample with no observed reliability loss.

The direct path also passed:

- modern MCP negotiation and exact five-tool inventory;
- real Filesystem + Playwright operations and negative cases;
- hosted Secure MCP Tunnel;
- real ordinary-Chat five-tool E2E;
- first-class public-manager Start/Status/Stop/Start lifecycle;
- single-owner/fail-closed behavior;
- forced tunnel-client crash recovery;
- duplicate-free idempotent repeated Start;
- normal public `semantic` promotion smoke.

After merge, the target machine updated `%LOCALAPPDATA%\ChatAgentPlatform\app` from merged `main`. SHA256 checks matched for the installed public manager, direct controller and semantic projection. Final installed acceptance reported:

```text
STAGE24_1_PERSISTENT_INSTALL=PASS
active_profile=semantic
tunnel_binding=direct-stdio
active_count=1
conflict=false
PORT_3050_LISTENER_COUNT=0
```

`semantic-direct` remains temporarily as a compatibility/diagnostic alias. 1MCP remains in the project as replaceable internal infrastructure for adaptive lifecycle experiments, aggregation/inspection, diagnostics and future catalog work where it adds measured value.

## Stage 25 — ACTIVE: local specialist inference + local vision

Stage 25 now evaluates bounded local model inference without creating a second planner.

Current verified architecture direction:

```text
ordinary ChatGPT planner
  -> small typed local-vision capability
  -> focused local adapter
  -> LM Studio / llmster
  -> replaceable local VLM
```

### Runtime candidate

LM Studio/`llmster` remains the first runtime-manager candidate. Current official LM Studio documentation supports the capabilities Stage 25 needs:

- standalone headless `llmster` for Windows;
- `lms` CLI model discovery/load/unload/server lifecycle;
- local HTTP serving on loopback;
- OpenAI-compatible chat with images;
- model memory estimation with `lms load --estimate-only`;
- configurable GPU offload/context length;
- TTL/JIT loading and auto-unload behavior.

This makes LM Studio a strong candidate for replaceable local inference infrastructure, not product identity.

### Corrected current model candidate

Earlier project docs named `LiquidAI/LFM2.5-VL-3B`. Current official Liquid AI listings do not expose that LFM2.5 model name.

Current official LFM2.5-VL family includes:

- `LiquidAI/LFM2.5-VL-1.6B` / GGUF;
- `LiquidAI/LFM2.5-VL-450M` / GGUF.

`LiquidAI/LFM2-VL-3B` exists as the previous LFM2 generation.

Therefore the first preferred current-generation `local-vision` candidate is now `LiquidAI/LFM2.5-VL-1.6B`. The older `LFM2-VL-3B` may be benchmarked as a comparison candidate. No model/runtime is accepted until target Windows hardware evidence exists.

Liquid AI describes LFM2.5-VL-1.6B as a 32,768-context general-purpose VLM with improved high-resolution/multi-image/OCR behavior and publishes native, GGUF, ONNX and MLX forms. The model card recommends it for general vision-language workloads, OCR and document comprehension rather than knowledge-intensive tasks.

## Stage 25 acceptance work

The next implementation work should establish a replaceable runtime/model boundary and benchmark the real target machine before extending the public semantic contract.

Required evidence:

1. headless/runtime lifecycle on Windows;
2. machine-readable model discovery/status;
3. pre-load RAM/VRAM estimate;
4. explicit recorded load/offload/context settings;
5. representative UI/screenshot, OCR/document, chart/graph, multi-image comparison and frame/image tasks;
6. cold load, time-to-first-token, tokens/second, peak RAM/VRAM and unload timings;
7. JIT/TTL or explicit unload/recovery behavior without stale processes;
8. deterministic adapter behavior and negative cases;
9. a small stable typed Chat-facing local-vision capability;
10. one real ordinary-Chat end-to-end workflow.

Stage 25 must compare actual useful quality as well as speed/memory. A smaller model is not accepted merely because it runs locally.

## Findings that remain active

- Chat action snapshots are frozen until reviewed/refreshed;
- concrete typed actions are the ordinary-Chat product contract;
- generic adaptive `tool_list` / `tool_schema` / `tool_invoke` remains diagnostic infrastructure, not product surface;
- the measured large-action snapshot pressure is evidence, not a universal official constant;
- OpenAI safety can block composite workflows independently of app permission mode;
- `semantic-projection` must remain deterministic/non-agentic and must not grow into a generic gateway;
- installed/source single-owner and fail-closed behavior remain required for every managed transport;
- local specialist inference must remain a bounded replaceable capability backend, not a second planner.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`. Historical Yandex/Tailscale paths are not active product dependencies.

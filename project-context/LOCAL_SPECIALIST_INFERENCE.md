# Stage 25 — Local Specialist Inference / Local Vision

Status: **ACTIVE / PROVISIONAL**

Research refresh date: 2026-08-16.

This document records the evidence-backed Stage 25 direction. Runtime/model names are candidates, not product identity.

## Goal

Add local model-powered perception as a bounded specialist capability while ordinary ChatGPT remains the planner/orchestrator.

Target shape:

```text
ordinary ChatGPT planner
  -> truthful typed local-vision operation
  -> deterministic local-vision adapter
  -> replaceable local inference runtime
  -> replaceable local VLM
  -> typed result back to Chat
```

Do not add a second planner, autonomous agent brain, generic model router or project-owned general inference platform.

## Runtime candidate — LM Studio / llmster

LM Studio is the first runtime-manager candidate because its current official tooling covers the lifecycle requirements without requiring a bespoke model server.

Official evidence:

- Developer docs: https://lmstudio.ai/docs/developer
- Headless/llmster: https://lmstudio.ai/docs/developer/core/headless
- Local server: https://lmstudio.ai/docs/developer/core/server
- OpenAI-compatible endpoints: https://lmstudio.ai/docs/developer/openai-compat
- CLI: https://lmstudio.ai/docs/cli
- `lms load`: https://lmstudio.ai/docs/cli/local-models/load
- `lms server start`: https://lmstudio.ai/docs/cli/serve/server-start

Verified current capabilities relevant to Stage 25:

- `llmster` is a standalone headless daemon and does not require the LM Studio GUI;
- Windows headless installation is officially documented;
- `lms` can list/download/load/unload models and start/stop the local server;
- `lms load --estimate-only` estimates memory before model load and accounts for context/GPU/vision settings;
- model load accepts explicit GPU offload, context length and TTL;
- JIT loading can load a requested model on inference and auto-unload it after inactivity;
- local server binds to `127.0.0.1` by default unless explicitly changed;
- OpenAI-compatible endpoints include `/v1/models`, `/v1/responses` and `/v1/chat/completions`;
- Chat Completions supports text and images.

### Stage 25 integration rule

Prefer a local loopback API or stable machine-readable CLI boundary. Do not expose LM Studio administrative commands directly to ordinary Chat.

The adapter may use LM Studio lifecycle/model-management functionality deterministically, but the public semantic contract must remain vendor-neutral.

## Target Windows hardware reconnaissance — 2026-08-16

The first real target-machine reconnaissance reported:

```text
CPU=11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz
LOGICAL_CPUS=8
RAM_GB=7.68
GPU=Intel(R) Iris(R) Xe Graphics
WINDOWS_REPORTED_VRAM_GB=0.12
GPU_DRIVER=31.0.101.5186
```

No LM Studio/llmster installation was found in the checked standard locations, `lms` was not resolved, and no NVIDIA runtime was observed.

This target is below LM Studio's current recommended Windows baseline of 16 GB RAM and 4 GB dedicated VRAM. That is a benchmark constraint, not an automatic rejection: the first acceptance sequence must use small GGUF variants, modest context/image settings, memory estimation before every larger load, and measured process/RAM behavior.

Target-specific benchmark order is therefore:

1. `LiquidAI/LFM2.5-VL-450M-GGUF` Q4 first, to validate runtime/API/vision behavior with maximum memory margin;
2. `LiquidAI/LFM2.5-VL-1.6B-GGUF` Q4 only after estimate-only and measured free-memory checks;
3. `LiquidAI/LFM2.5-VL-3B` / GGUF only if runtime estimation and observed headroom make it safe enough to benchmark.

This small-to-large order is for the current laptop's memory safety. It is not a ranking of model quality.

Because the target GPU is Intel Iris Xe integrated graphics, Stage 25 should not assume CUDA/NVIDIA behavior or trust Windows-reported `AdapterRAM` as usable dedicated VRAM. Benchmark CPU/automatic LM Studio placement first. In parallel research, keep ONNX Runtime + Intel OpenVINO as a replaceable runtime comparison for this hardware class because OpenVINO can target Intel CPU and integrated GPU. Do not add it to the product path unless measured evidence beats or materially complements the LM Studio path.

## Official Liquid AI model release evidence

`LiquidAI/LFM2.5-VL-3B` is a real official Liquid AI release from 2026-08-12. The previous documentation edit that removed it was wrong because it relied on stale indexed model listings that had not yet incorporated the new release.

Direct official sources supplied for the release:

- Liquid AI release blog: https://www.liquid.ai/blog/lfm2-5-vl-3b
- Liquid Docs model page: https://docs.liquid.ai/lfm/models/lfm25-vl-3b
- Official Hugging Face model: https://huggingface.co/LiquidAI/LFM2.5-VL-3B
- Official WebGPU demo: https://huggingface.co/spaces/LiquidAI/LFM2.5-VL-3B-WebGPU
- Liquid AI X account: https://x.com/liquidai

The release blog explicitly announces `LFM2.5-VL-3B` and the official model repository exposes the weights under that exact identifier.

## Current candidate set

Stage 25 separates preferred model quality from target-hardware feasibility:

1. **Preferred quality candidate:** `LiquidAI/LFM2.5-VL-3B` and an official/compatible local quantization when available.
2. **Middle current-generation comparison:** `LiquidAI/LFM2.5-VL-1.6B` / GGUF.
3. **Target-first lightweight candidate:** `LiquidAI/LFM2.5-VL-450M` / GGUF Q4.

The final selected runtime/model/format may differ. No candidate is accepted from model naming, parameter count or marketing claims alone.

## Candidate public capability surface

Do not expose arbitrary `model`, `endpoint`, raw prompts or LM Studio lifecycle operations as a generic Chat tool.

Candidate semantic family:

```text
vision_analyze
vision_compare
vision_extract
vision_analyze_frames
```

Before finalizing several actions, evaluate whether one coherent `vision_analyze` operation can cover representative tasks with a truthful bounded task mode/result schema. Avoid recreating generic `tool_invoke` or `run_model(prompt, model)` behind a friendlier name.

Any exported Chat action change requires:

- schema review;
- negative tests;
- Chat app Refresh/review;
- fresh ordinary-Chat acceptance.

## Adapter responsibilities

A focused local-vision adapter may:

- verify the configured runtime is available;
- discover reviewed locally installed model variants;
- estimate memory before load;
- enforce a configured allowlist of model identifiers/formats;
- apply benchmarked context/GPU-offload/TTL settings;
- load on demand or use accepted JIT behavior;
- send image + bounded task instructions to the local inference endpoint;
- validate/normalize the result into a stable typed response;
- expose health/loaded-model/resource diagnostics;
- unload/evict according to accepted lifecycle policy.

It must not:

- decide the user's high-level goal;
- become an autonomous agent;
- download arbitrary models during a user inference call;
- expose arbitrary remote URLs or model-provider credentials;
- silently send local images/files to a cloud endpoint;
- hide unrestricted local file access inside a vision request.

## Representative target-Windows benchmark set

Stage 25 acceptance must measure quality as well as speed/memory.

### Visual/UI understanding

Use real but non-sensitive screenshots to test:

- window/application identification;
- visible controls/states;
- error dialogs/messages;
- approximate spatial relationships;
- distinguishing enabled/disabled/selected UI states.

### OCR/document comprehension

Test:

- clear printed text;
- dense tables;
- mixed labels/numbers;
- invoices/forms/report pages;
- structured extraction with a fixed schema where useful.

### Charts/graphs

Test:

- axis/legend/title recognition;
- series comparison;
- visible extrema/trends;
- reading labeled numeric values where resolution supports it;
- refusal/uncertainty when values cannot be read reliably.

### Multi-image comparison

Test:

- before/after screenshots;
- changed controls/text/layout;
- missing/added visual elements;
- consistency across two related document pages/images.

### Frame/image sequences

Test representative extracted frames rather than committing to full-video ingestion in the first runtime boundary. Measure how many frames can be processed usefully within memory/latency constraints.

## Measurements to capture

For each runtime/model/format configuration record:

- exact LM Studio/llmster/lms version;
- exact model identifier and artifact/quantization;
- context length and image-token/tiling settings where applicable;
- GPU offload setting;
- `--estimate-only` memory estimate;
- observed idle RAM/VRAM;
- observed peak RAM/VRAM during load and inference;
- cold daemon/server startup;
- cold model load time;
- time to first token;
- output tokens/sec;
- end-to-end task latency;
- unload/eviction time;
- restart/recovery after forced runtime/model failure;
- correctness score/notes for each benchmark task.

Do not select a candidate from parameter count or throughput alone.

## Stage 25 acceptance gates

1. Verify/install LM Studio or standalone llmster on target Windows and record exact versions.
2. Prove headless daemon/server start/status/stop without GUI dependency.
3. Prove machine-readable local model discovery and loaded-model status.
4. Run memory estimates before candidate load and compare with measured RAM/VRAM.
5. Benchmark the candidate model set on representative visual tasks.
6. Select runtime/model/format/load policy from measured quality + latency + memory evidence.
7. Implement the smallest deterministic vendor-neutral local-vision adapter.
8. Add lifecycle, negative, path/scope and malformed-runtime-response tests.
9. Integrate the reviewed small semantic vision action surface without regressing the existing five semantic tools.
10. Refresh/review the existing Chat app action snapshot and run one real ordinary-Chat local-vision workflow.
11. Only then accept ADR-020/ADR-022 and mark Stage 25 complete.

## Initial engineering order

Do not change the Chat-facing action surface first.

Start with target-machine runtime reconnaissance and a local benchmark harness that talks directly to the loopback runtime. Only after runtime/model evidence exists should the project add the focused semantic adapter and update the Chat app schema.

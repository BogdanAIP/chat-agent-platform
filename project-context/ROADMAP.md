# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT Chat as the intelligence layer while local capabilities remain replaceable MCP modules or focused local adapters. Scale capability count without scaling ChatGPT app/plugin count, keeping hundreds of tools permanently visible, or running every local process all the time.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Accepted 2026-08-10: Secure MCP Tunnel + official tunnel-client + local 1MCP + Sequential Thinking round trip from ordinary ChatGPT.

## Stage 22 — Remove superseded custom platform infrastructure — DONE

Removed the obsolete universal Rust/Python core, custom ingress/polling/Yandex/media platform runtime. Historical implementation remains in Git at `a446397d99276856c614bc49526cab422c7e74bd`.

## Stage 23 — Quality-first module selection — DONE

Accepted Windows candidates include Filesystem MCP `2026.7.10`, Microsoft Playwright MCP `0.0.78` and 1MCP direct baseline `0.34.4`.

## Stage 24 — Windows lifecycle + scalable typed ordinary-Chat surface — DONE

Squash-merged to `main` on 2026-08-16 as `175d36236f80a1f99f091d4f031a1c6255f3652b` from PR #66.

Accepted results include standalone Windows management, DPAPI tunnel-key storage, verified official tunnel-client, least-privilege diagnostic profiles, adaptive 1MCP diagnostic lifecycle, one authoritative manager owner, occupied-port fail-closed behavior and the exact five-tool semantic projection:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Real ordinary-Chat multi-backend E2E passed through one `Chat Local Bridge Test` app.

## Stage 24.1 — Direct semantic tunnel A/B — DONE

Squash-merged to `main` on 2026-08-16 as `df1d5e232b739b62e72ad81e5d82fd01be53e884` from PR #70.

Goal: remove the unnecessary intermediate 1MCP hop from the **normal semantic request path** while retaining 1MCP as internal replaceable infrastructure where its aggregation/lifecycle features remain useful.

Evaluated paths:

```text
A — Stage 24 baseline
Tunnel -> 1MCP -> semantic-projection

B — selected
Tunnel -> stdio semantic-projection
```

This was not a response to a proven 1MCP failure. Stage 24 proved A works. B was selected because it passed equivalent functional/reliability gates and was materially simpler/faster on the target machine.

### Stage 24.1 accepted evidence

- Windows direct semantic tunnel CI with modern MCP negotiation and exact five-tool inventory;
- target Windows direct-tunnel test with real Filesystem + Playwright and negative cases;
- existing Secure MCP Tunnel hosted direct semantic path with `DIRECT_SEMANTIC_1MCP_USED=False`;
- existing Chat app Refresh and exact same five semantic actions;
- real ordinary-Chat read -> browser observe/interact -> write -> independent read workflow;
- first-class public-manager direct profile, shared ownership/fail-closed handling and clean Start/Status/Stop/Start lifecycle;
- forced tunnel-client crash recovery and duplicate-free idempotent repeated Start;
- target A/B lifecycle comparison, 3/3 healthy cycles on both transports;
- normal public `semantic` promotion smoke;
- exact promotion-head and post-merge `main` workflows all green;
- stable LocalAppData installation updated from `main` with matching SHA256 for public manager/direct controller/semantic projection and `STAGE24_1_PERSISTENT_INSTALL=PASS`.

### Target A/B evidence

| Metric | 1MCP baseline | Direct stdio |
|---|---:|---:|
| Average initial Start | 123685 ms | 5007 ms |
| Average repeated/idempotent Start | 84119 ms | 4876 ms |
| Average Stop | 23252 ms | 1043 ms |
| Running port-3050 listener | 1 | 0 |
| Healthy lifecycle cycles | 3/3 | 3/3 |

Direct was approximately 24.70x faster to start, 17.25x faster on repeated Start and 22.29x faster to stop in this sample.

### Accepted normal semantic path

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> stdio semantic-projection
  -> task-active backends / focused adapters
```

`semantic-direct` remains temporarily as a compatibility/diagnostic alias. The legacy 1MCP-backed semantic implementation remains internal diagnostic/A-B evidence. 1MCP stays in the project.

## Stage 25 — Local specialist inference runtime + `local-vision` — ACTIVE

Goal: add local model-powered perception without adding a second planner/agent brain.

### Runtime candidate

Evaluate LM Studio/`llmster` first as replaceable local inference infrastructure.

Current official LM Studio capabilities match the required lifecycle boundary:

- Windows headless `llmster` without GUI dependency;
- `lms` model discovery/load/unload/server lifecycle;
- memory estimation before load via `lms load --estimate-only`;
- configurable GPU offload, context length and TTL;
- JIT loading and automatic eviction/unload;
- local loopback HTTP server;
- OpenAI-compatible image chat.

Benchmark model discovery, resource estimation, hardware-aware load settings, JIT/explicit load behavior, TTL/auto-evict/unload, status/metrics and clean process lifecycle.

### Model candidates

`LiquidAI/LFM2.5-VL-3B` is an official Liquid AI release from 2026-08-12. The project records direct official evidence from the Liquid AI release blog, Liquid Docs model page, official Hugging Face weights and WebGPU demo.

Stage 25 separates preferred quality from hardware-safe test order:

1. **`LiquidAI/LFM2.5-VL-3B`** — preferred quality candidate;
2. `LiquidAI/LFM2.5-VL-1.6B` — middle current-generation comparison;
3. **`LiquidAI/LFM2.5-VL-450M-GGUF` Q4** — first target-machine runtime candidate on the current laptop.

The current target has i5-1135G7, 7.68 GB RAM and Intel Iris Xe. Therefore local test order remains 450M Q4 → 1.6B Q4 → 3B only after pre-load estimate and observed free-memory checks. This is a resource-safety order, not a quality ranking.

Select actual model/format/quantization from target-machine quality + speed + memory evidence, not parameter count or assumption.

### Representative Stage 25 benchmark set

Benchmark at least:

- UI/screenshot understanding and element/state description;
- OCR and document comprehension/extraction;
- chart/graph interpretation with numeric/text labels;
- multi-image comparison and change description;
- representative video-frame/image sequence analysis;
- structured extraction where a deterministic schema is useful;
- negative/adversarial cases such as missing image, unsupported path/type, oversized inputs and malformed runtime response.

Record:

- cold runtime/model startup;
- memory estimate before load;
- measured peak RAM/VRAM;
- time to first token;
- generation tokens/sec;
- end-to-end task latency;
- unload/eviction time;
- crash/restart/cleanup behavior;
- quality/correctness on the representative benchmark set.

### Chat-facing capability boundary

Do not expose LM Studio administration or arbitrary model invocation directly to Chat.

Keep the semantic local-vision surface small. Candidate capability family:

```text
vision_analyze
vision_compare
vision_extract
vision_analyze_frames
```

Before adding several actions, test whether one coherent `vision_analyze` contract with a bounded task mode/schema can cover representative work without becoming a generic hidden invocation endpoint. Any final API must remain truthful, typed and reviewable.

Changing exported Chat actions requires Chat app Refresh/review and a new ordinary-Chat acceptance gate.

### Stage 25 gates

1. **ACTIVE:** verify/install LM Studio or standalone llmster on target Windows and capture exact runtime/CLI versions.
2. **PENDING:** prove headless daemon + local server lifecycle and machine-readable model/status discovery.
3. **PENDING:** benchmark memory estimation vs measured RAM/VRAM for selected candidate formats/quantizations.
4. **PENDING:** benchmark representative VLM quality, latency and throughput.
5. **PENDING:** select runtime/model/format policy from measurements and document rollback/replacement behavior.
6. **PENDING:** implement the smallest deterministic local-vision adapter behind the semantic boundary.
7. **PENDING:** add negative/security/process-lifecycle acceptance and keep manager single-owner rules intact where applicable.
8. **PENDING:** expose the reviewed small typed vision capability, Refresh the Chat app and run one real ordinary-Chat workflow.
9. **PENDING:** only then accept ADR-020/ADR-022 and mark Stage 25 DONE.

Stage 25 is product-complete only when one replaceable runtime/model path passes target Windows acceptance and ordinary Chat uses it in a real workflow.

## Stage 26 — Professional application capability benchmarks

Benchmark and promote real workflows for REAPER, Origin, FFmpeg, Blender and Windows UI fallback behind the stable semantic capability boundary. Adding a backend should normally require catalog/config/security/acceptance work, not a new ChatGPT app.

## Stage 27 — Distribution and maintenance hardening

After the scalable typed boundary, local inference and professional backends stabilize:

- stable release artifact;
- reproducible dependency installation/locking;
- versioned bootstrap/update/repair/doctor/uninstall;
- runtime-key rotation;
- component upgrade/rollback rules;
- idle/process lifecycle policy and diagnostics;
- thin non-agentic controller/UI.

## Definition of Done

The product succeeds when ordinary ChatGPT can use useful local capabilities through a stable standard-MCP bridge, starting only what tasks require, without a second AI planner, mandatory SaaS chain, project-owned generic gateway, one ChatGPT app per local tool, or a hard-coded local model/runtime stack.

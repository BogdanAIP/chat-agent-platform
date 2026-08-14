# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT Chat as the intelligence layer while local capabilities remain replaceable MCP modules or focused local adapters. Scale capability count without scaling ChatGPT app/plugin count, keeping hundreds of tools permanently visible, or running every local process all the time.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Accepted 2026-08-10: Secure MCP Tunnel + official tunnel-client + local 1MCP + Sequential Thinking round trip from ordinary ChatGPT.

## Stage 22 — Remove superseded custom platform infrastructure — DONE

Removed the obsolete universal Rust/Python core, custom ingress/polling/Yandex/media platform runtime. Historical implementation remains in Git at `a446397d99276856c614bc49526cab422c7e74bd`.

## Stage 23 — Quality-first module selection — DONE

Accepted Windows candidates:

- Filesystem MCP `2026.7.10`;
- Microsoft Playwright MCP `0.0.78`;
- 1MCP direct baseline `0.34.4`.

Ready-made-first candidates were recorded for REAPER, Origin, FFmpeg, Blender and Windows UI fallback.

## Stage 24 — Windows lifecycle + scalable typed ordinary-Chat capability surface — IN PROGRESS

### Completed evidence inside Stage 24

- least-privilege direct `files-readonly` and `browser-isolated` profiles;
- robust profile status/conflict recovery;
- official tunnel readiness gating and startup rollback;
- verified standalone Windows bootstrap/manager under LocalAppData;
- DPAPI runtime key handling;
- tray/controller separation and no persistent console window;
- real ordinary-Chat `files-readonly` E2E;
- real freshly scanned typed Browser E2E using `browser_navigate`;
- adaptive local/CI lifecycle acceptance for Filesystem + Playwright through the exact hash-guarded compatibility package;
- real ordinary-Chat evidence that the generic adaptive lifecycle/schema/invocation surface is blocked before MCP for consequential/generic calls and must not be promoted as the product contract;
- real combined typed Filesystem + Playwright ordinary-Chat E2E in one conversation, including scoped read/write and browser navigate/find/click;
- measured action-snapshot pressure: 34 local typed tools effectively surfaced as 20 in the tested app, while a reduced 24-tool local surface allowed the needed later browser actions to become callable after Refresh/new Chat;
- real app-permission behavior: `Allow read actions` produced one-time approval for isolated `write_file`; `Allow all actions` allowed typed read/navigate/write without confirmation;
- real context-sensitive safety behavior: one large cross-capability workflow was blocked while the same typed actions passed sequentially;
- real installed/source split-brain diagnosis on `127.0.0.1:3050`;
- functional head `64fa0a27...` adds shared manager ownership/fail-closed port handling and passes Chat Profile Acceptance, CI, module candidates, CodeQL and Secret History Scan remotely.

### Current convergence

The generic lazy meta-tool contract is no longer the expected ordinary-Chat product surface. Keep adaptive 1MCP as useful lifecycle/CI diagnostic infrastructure.

The Stage 24 product requirement is now:

```text
ordinary ChatGPT
  -> concrete typed actions with truthful schemas/semantics
  -> scalable capability selection/publication
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP / focused adapters
  -> replaceable task-active backends
```

Do not create one Chat app per backend. Do not publish hundreds of unrelated tools at once. Do not solve action-count pressure by disguising all operations behind opaque `tool_invoke`.

The exact typed scaling mechanism remains **PROVISIONAL**. The observed ~20-action snapshot behavior is empirical and must not be hard-coded as an official universal limit.

### Current gates

1. target-machine acceptance of the new single-owner installed/source manager behavior on the exact functional implementation;
2. design/implement the smallest scalable typed capability publication mechanism justified by the action-snapshot evidence;
3. prove that mechanism through real ordinary Chat with more than one backend class and without one app per backend;
4. preserve adaptive/direct regression coverage and truthful safety semantics;
5. synchronize final evidence/docs/PR description with the exact functional head.

### Stage 24 Definition of Done

1. direct reference/files/browser regressions stay green;
2. adaptive local/CI lifecycle remains green as diagnostic infrastructure;
3. generic adaptive meta-tools are not falsely promoted as the accepted ordinary-Chat surface;
4. installed/source lifecycle has one authoritative owner and cannot accept stale foreign readiness on `127.0.0.1:3050`;
5. scalable Chat-facing capability publication preserves concrete typed action schemas and truthful risk semantics;
6. real ordinary Chat can use useful typed actions from multiple backend classes through one product app without routine per-backend app creation;
7. exact final functional HEAD passes `ci`, `Chat Profile Acceptance`, CodeQL, Module Candidate Acceptance and Secret History Scan;
8. only then Stage 24 is integrated into `main`.

## Stage 25 — Local specialist inference runtime + `local-vision`

Goal: add local model-powered perception without adding a second planner/agent brain.

### Runtime-manager benchmark

Evaluate LM Studio/`llmster` first as replaceable local inference infrastructure. Required real-machine checks:

- headless/server startup and stable local API/CLI use;
- list available local models and variants;
- inspect model capabilities relevant to vision/tool use;
- `lms load --estimate-only` resource estimates before load;
- hardware-aware GPU offload/variant selection without hard-coded RAM/VRAM guesses;
- JIT loading behavior;
- TTL and auto-evict/unload behavior;
- clean process/resource lifecycle and recovery.

Do not make LM Studio mandatory product identity. Keep a runtime adapter boundary so another mature runtime can replace it if measured behavior is better.

### First vision candidate

Benchmark official `LiquidAI/LFM2.5-VL-3B` first. Liquid AI released it 2026-08-12 and publishes:

- screen/UI understanding;
- document/OCR/chart understanding;
- grounding;
- multi-image input;
- function calling/tool-use improvements;
- GGUF/llama.cpp checkpoints;
- ONNX support.

Target-machine benchmark must choose actual model variant/quantization from measurement rather than assumption. Compare quality, latency, memory and stability on representative tasks such as screenshots, Origin/desktop UI, document pages, charts and selected video frames.

### Stable capability boundary

Keep the Chat-facing vision surface small and semantic, initially targeting operations such as:

- `vision_analyze`;
- `vision_compare`;
- `vision_extract`;
- `vision_analyze_frames`.

ChatGPT remains the planner. The local model returns bounded visual analysis/extraction/grounding results.

### Stage 25 Definition of Done

1. one replaceable local runtime-manager path passes target Windows acceptance;
2. automatic model/variant selection uses measured runtime estimates and guardrails;
3. LFM2.5-VL-3B or a measured fallback passes representative vision tasks on target hardware;
4. local-vision exposes a small stable typed boundary through the bridge;
5. model/runtime can load/unload without becoming a permanently resident second agent;
6. ordinary Chat successfully uses the local-vision capability in a real workflow.

## Stage 26 — Professional application capability benchmarks

Benchmark real workflows and promote backends behind the stable capability boundary:

- REAPER: choose an immutable TwelveTake artifact and test real audio/project operations;
- Origin: choose an immutable Origin-Pro-MCP artifact and test the installed Origin; fall back to official OriginLab APIs only for measured gaps;
- FFmpeg: audit and benchmark `ffmpeg-mcp-lite==0.2.2` before writing an adapter;
- Blender: compare a reduced DCC-MCP surface with the smaller `djeada` server;
- Windows UI Automation: high-privilege fallback only where specialized APIs cannot cover the task.

Promotion of a new backend should normally require catalog/config/security/acceptance work, **not a new ChatGPT plugin/app**.

Lifecycle should follow the task: activate required backends, reuse active backends across dependent stages, stop idle backends, and allow concurrency when necessary.

## Stage 27 — Distribution and maintenance hardening

Once the scalable typed boundary, local inference and professional application backends are stable:

- first stable release artifact;
- reproducible local dependency installation/lock strategy instead of repeated registry resolution;
- versioned bootstrap/update/repair/doctor/uninstall;
- runtime-key rotation;
- manager/1MCP/tunnel-client/local-inference upgrade and rollback rules;
- idle/process lifecycle policy and diagnostics;
- keep controller/UI thin and non-agentic.

## Definition of Done

The product succeeds when ordinary ChatGPT can discover and use useful local capabilities through a stable standard-MCP bridge, starting only what tasks require, without a second AI planner, mandatory SaaS chain, project-owned generic gateway, one ChatGPT app per local tool, or a hard-coded local model/runtime stack.

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

Accepted results include:

- standalone Windows bootstrap/manager/tray under LocalAppData;
- DPAPI runtime-key storage and verified official tunnel-client;
- direct least-privilege Filesystem/Browser diagnostics;
- adaptive 1MCP lifecycle diagnostic infrastructure;
- one authoritative installed/source manager owner and occupied-port fail-closed behavior;
- measured action-snapshot pressure and rejection of opaque generic `tool_invoke` as the ordinary-Chat product surface;
- exact five-tool semantic projection: `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`;
- real ordinary-Chat multi-backend semantic E2E through one `Chat Local Bridge Test` app;
- final pre-merge head `87a8701b938a128901646d096e13142700cc109a` green across Chat Profile Acceptance, Semantic Projection Acceptance, CI, CodeQL, Module Candidate Acceptance and Secret History Scan.

Accepted Stage 24 transport baseline:

```text
ordinary ChatGPT
  -> five semantic typed actions
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP
  -> semantic-projection
  -> replaceable task-active backends
```

## Stage 24.1 — Direct semantic tunnel A/B — IN PROGRESS

Goal: determine whether the normal semantic request path can remove the intermediate 1MCP hop while retaining 1MCP as internal replaceable infrastructure where its aggregation/lifecycle features are useful.

A/B paths:

```text
A — accepted baseline
Tunnel -> 1MCP -> semantic-projection

B — candidate
Tunnel -> stdio semantic-projection
```

Candidate B is not a response to a proven 1MCP failure. Stage 24 proved Baseline A works. This stage evaluates whether B is simpler and at least as reliable.

### Implemented first gate

Branch `chat/direct-semantic-tunnel` adds:

- direct-tunnel semantic MCP acceptance with modern protocol negotiation;
- Windows PowerShell harness around official `tunnel-client dev proxy --mcp-command`;
- Windows CI that downloads and verifies official `tunnel-client v0.0.11` before exercising the direct path;
- explicit documentation preserving 1MCP as internal infrastructure.

### Stage 24.1 gates

1. Windows direct semantic tunnel CI passes.
2. Target Windows direct dev-proxy test passes with startup/operation timing captured.
3. Integrate a reversible experimental direct semantic profile into the public manager without replacing the accepted baseline.
4. Prove start/status/stop/recovery and preserve ownership/fail-closed regressions.
5. Refresh the existing Chat app and confirm the exact same five semantic actions through Candidate B.
6. Repeat the accepted real ordinary-Chat workflow: read -> browser observe/interact -> write -> independent read.
7. Compare A/B startup, first-call latency, repeated calls, restart/cleanup and diagnostics.
8. Promote B as normal `semantic` transport only if it is equivalent or better; otherwise retain A.

### Non-goals

- do not delete 1MCP from the project;
- do not turn semantic-projection into a generic gateway/registry;
- do not add a second planner;
- do not change the five-tool Chat-facing semantics merely to accommodate transport work.

## Stage 25 — Local specialist inference runtime + `local-vision`

Goal: add local model-powered perception without adding a second planner/agent brain.

Evaluate LM Studio/`llmster` first as replaceable local inference infrastructure. Benchmark model discovery, memory estimation before load, hardware-aware variant/offload selection, JIT/load behavior, TTL/auto-evict/unload and clean process lifecycle.

Benchmark `LiquidAI/LFM2.5-VL-3B` first for screen/UI understanding, OCR/document/chart work, grounding and representative image/frame tasks. Select actual model variant/quantization from target-machine measurement rather than assumption.

Keep the Chat-facing vision surface small and semantic, initially targeting operations such as `vision_analyze`, `vision_compare`, `vision_extract` and `vision_analyze_frames`.

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

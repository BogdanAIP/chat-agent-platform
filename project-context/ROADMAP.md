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

Stage 24 transport baseline was:

```text
ordinary ChatGPT
  -> five semantic typed actions
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP
  -> semantic-projection
  -> replaceable task-active backends
```

## Stage 24.1 — Direct semantic tunnel A/B — PROMOTION IN FINAL RELEASE GATE

Goal: remove the unnecessary intermediate 1MCP hop from the **normal semantic request path** while retaining 1MCP as internal replaceable infrastructure where its aggregation/lifecycle features remain useful.

Evaluated paths:

```text
A — Stage 24 baseline
Tunnel -> 1MCP -> semantic-projection

B — selected
Tunnel -> stdio semantic-projection
```

This was not a response to a proven 1MCP failure. Stage 24 proved A works. B was selected because it passed equivalent functional/reliability gates and was materially simpler/faster on the target machine.

### Stage 24.1 gates

1. **DONE:** Windows direct semantic tunnel CI with modern MCP negotiation and exact five-tool inventory.
2. **DONE:** Target Windows direct-tunnel test with real Filesystem + Playwright and negative cases.
3. **DONE:** Existing Secure MCP Tunnel hosted direct semantic path with `DIRECT_SEMANTIC_1MCP_USED=False`.
4. **DONE:** Existing Chat app Refresh and exact same five semantic actions.
5. **DONE:** Real ordinary-Chat read -> browser observe/interact -> write -> independent read workflow.
6. **DONE:** First-class public-manager direct profile, shared ownership/fail-closed handling and clean Start/Status/Stop/Start lifecycle.
7. **DONE:** Forced tunnel-client crash recovery and duplicate-free idempotent repeated Start.
8. **DONE:** Target A/B lifecycle comparison, 3/3 healthy cycles on both transports.
9. **IN PROGRESS:** promote normal public `semantic` to direct stdio, run final CI and target normal-semantic profile-routing smoke.
10. **PENDING:** merge PR #70, update the stable LocalAppData manager bundle from `main`, verify final status, then mark Stage 24.1 DONE.

The final target smoke does not repeat ordinary-Chat tool semantics unless exported actions change; that E2E already passed on the same direct server surface.

### Target A/B evidence

| Metric | 1MCP baseline | Direct stdio |
|---|---:|---:|
| Average initial Start | 123685 ms | 5007 ms |
| Average repeated/idempotent Start | 84119 ms | 4876 ms |
| Average Stop | 23252 ms | 1043 ms |
| Running port-3050 listener | 1 | 0 |
| Healthy lifecycle cycles | 3/3 | 3/3 |

Direct was approximately 24.70x faster to start, 17.25x faster on repeated Start and 22.29x faster to stop in this sample.

### Promotion boundary

Normal public `semantic` now targets:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> stdio semantic-projection
  -> task-active backends
```

`semantic-direct` remains temporarily as a compatibility/diagnostic alias. The legacy 1MCP-backed semantic implementation remains internal diagnostic/A-B evidence. Do not delete 1MCP from the project.

### Non-goals

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

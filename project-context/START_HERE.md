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

The accepted session read `SEMANTIC_FINAL_INPUT_20260816`, navigated from `example.com` through the real `Learn more` link to `Example Domains`, wrote a result file and independently read it back. The Stage 24 1MCP path worked and remains valid acceptance evidence.

## Stage 24.1 — DONE

Stage 24.1 was squash-merged to `main` on 2026-08-16 as:

`df1d5e232b739b62e72ad81e5d82fd01be53e884` — `Stage 24.1: direct semantic tunnel A/B acceptance (#70)`.

Stage 24.1 compared:

```text
A — Stage 24 baseline
Tunnel -> HTTP 1MCP -> stdio semantic-projection

B — selected
Tunnel -> stdio semantic-projection
```

Candidate B passed transport, backend, ordinary-Chat, lifecycle, ownership, crash-recovery and A/B gates. Both paths completed 3/3 healthy lifecycle cycles on the target Windows machine; direct stdio was materially faster and eliminated the normal semantic port-3050 hop.

The normal product path is now:

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

`semantic-direct` remains temporarily as a compatibility/diagnostic alias. 1MCP is **not removed**; it remains replaceable internal infrastructure for adaptive lifecycle experiments, diagnostics, aggregation/inspection and future catalog work where its features add measured value.

Final target release acceptance also passed after merge from the stable LocalAppData installation:

```text
STAGE24_1_PERSISTENT_INSTALL=PASS
active_profile=semantic
tunnel_binding=direct-stdio
active_count=1
conflict=false
PORT_3050_LISTENER_COUNT=0
```

The installed manager bundle matched merged `main` by SHA256 for the public manager, direct controller and semantic projection.

## Current stage — Stage 25 local specialist inference

Stage 25 is active.

Goal: add local model-powered perception as a bounded replaceable capability backend without creating a second planner.

Current verified candidate direction:

```text
ChatGPT planner
  -> small typed local-vision capability
  -> focused local adapter
  -> LM Studio / llmster (replaceable runtime candidate)
  -> local VLM (replaceable model candidate)
```

LM Studio/`llmster` is the first runtime-manager candidate because current official documentation supports:

- standalone headless `llmster` on Windows;
- `lms` model discovery/load/unload/server lifecycle;
- `lms load --estimate-only` memory estimation before model load;
- configurable GPU offload and context length;
- TTL/JIT load and auto-unload behavior;
- localhost HTTP serving;
- OpenAI-compatible `/v1/chat/completions` with text and images.

### Liquid AI candidates

`LiquidAI/LFM2.5-VL-3B` is an official Liquid AI release dated 2026-08-12. Direct official release evidence includes:

- `https://www.liquid.ai/blog/lfm2-5-vl-3b`;
- `https://docs.liquid.ai/lfm/models/lfm25-vl-3b`;
- `https://huggingface.co/LiquidAI/LFM2.5-VL-3B`;
- `https://huggingface.co/spaces/LiquidAI/LFM2.5-VL-3B-WebGPU`.

Stage 25 therefore treats:

- `LiquidAI/LFM2.5-VL-3B` as the preferred quality candidate;
- `LiquidAI/LFM2.5-VL-1.6B` as a middle current-generation comparison;
- `LiquidAI/LFM2.5-VL-450M` / GGUF Q4 as the first target-machine candidate on the current laptop.

The current target has 7.68 GB RAM and Intel Iris Xe, so test order is deliberately 450M Q4 → 1.6B Q4 → 3B only after pre-load estimate and measured free-memory checks. This order reflects hardware constraints, not model ranking.

No runtime/model is accepted until target-hardware measurement passes.

## Stage 25 acceptance direction

Before promoting local vision:

1. verify LM Studio/llmster installation and non-GUI lifecycle on the target Windows machine;
2. prove model discovery and machine-readable status;
3. estimate memory before load and record RAM/VRAM expectations;
4. load candidates only with explicit/recorded GPU offload/context settings and sufficient measured headroom;
5. execute representative image/OCR/document/chart/UI tasks locally;
6. measure cold load, time-to-first-token, generation speed, peak memory and unload/recovery behavior;
7. prove clean TTL/JIT or explicit unload behavior with no stale model process/state;
8. expose only a small truthful typed vision capability through the semantic boundary;
9. run one real ordinary-Chat workflow through that capability;
10. keep runtime/model swappable without changing the public semantic contract unnecessarily.

Do not turn LM Studio into the product identity or expose its administrative CLI/API directly to ordinary Chat.

## Important findings to preserve

- Chat action snapshots are frozen until reviewed/refreshed; server-side tool changes do not silently replace an already-scanned snapshot.
- Concrete typed Filesystem + Playwright actions work together in one ordinary-Chat conversation.
- A larger tested action inventory showed effective snapshot pressure/truncation around 20 actions; this is measured behavior, not an official universal limit.
- The generic adaptive `tool_list` / `tool_schema` / `tool_invoke` surface is not the ordinary-Chat product contract.
- OpenAI safety is context-sensitive beyond app permission mode.
- The semantic projection must remain a small deterministic typed compatibility boundary, not a planner or generic gateway.
- Installed/source manager ownership and fail-closed handling apply to both 1MCP-backed and direct semantic managed runtimes.

## Product boundary

- ordinary ChatGPT remains the intelligence/planning layer;
- local specialist models may be bounded capability backends but never the second planner;
- prefer official/vendor or mature OSS components before project-owned infrastructure;
- do not recreate a project-owned generic MCP gateway, registry, vault, job system or workflow brain;
- keep 1MCP only where its measured capabilities are useful rather than forcing it into every request path;
- keep local inference runtime and model replaceable behind a focused adapter/semantic contract.

## How to continue safely

Before changing code:

- inspect the active branch, PR, exact head and workflow logs;
- read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `LOCAL_SPECIALIST_INFERENCE.md` and `DEVELOPMENT_PRINCIPLES.md`;
- preserve the five-tool semantic contract and single-owner/fail-closed regressions while deliberately versioning any new vision action surface;
- run locally accessible acceptance directly;
- use the user only for real ordinary-Chat UI/custom-app or other irreducible target-machine gates;
- never claim an ordinary-Chat or target-machine test unless that exact path actually ran;
- preserve/reconcile local uncommitted work rather than discarding it.

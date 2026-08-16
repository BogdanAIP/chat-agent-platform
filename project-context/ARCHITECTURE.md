# Architecture

## Product boundary

The project is a generic bridge that lets ordinary ChatGPT Chat use local capabilities through standard MCP. ChatGPT remains the planner/orchestrator. The local bridge does not implement a second AI agent or workflow brain.

Specialized local inference is allowed as a replaceable capability backend when it performs bounded perception/extraction/classification work. A vision model may help interpret screens/documents/images, but it does not become the planner. Chat remains the brain; local specialist models are tools.

## Normal ordinary-Chat reachability path

After Stage 24.1 promotion, the normal semantic path is:

```text
ordinary ChatGPT Chat
  -> custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client
  -> direct stdio semantic-projection
      -> replaceable task-active MCP backends / focused local adapters
      -> local programs/files/devices/models
```

The semantic projection is the stable five-tool Chat-facing compatibility boundary. Direct stdio removes 1MCP only from this normal critical path.

1MCP remains replaceable internal infrastructure for adaptive lifecycle experiments, diagnostics, aggregation/inspection and future catalog/lifecycle cases where its features add measured value. Stage 24 proved the 1MCP semantic path works; Stage 24.1 selected direct stdio as a measured simplification, not a repair for a broken component.

## Chat-facing capability boundary

Real Stage 24 evidence established five constraints:

1. changing a local backend profile does not automatically replace an already-scanned Chat action snapshot;
2. ChatGPT MCP app actions behave as a frozen reviewed snapshot, so server-side tool changes require Refresh/review to change that snapshot;
3. the generic adaptive `tool_list` / `tool_schema` / `tool_invoke` + lifecycle surface works as local/CI infrastructure but is not the accepted ordinary-Chat product contract;
4. concrete typed Filesystem and Playwright actions work together through one ordinary-Chat app/conversation;
5. the tested app showed effective action-snapshot pressure/truncation around 20 tools. That is measured behavior, not an official universal constant.

Stage 24 then accepted the exact semantic surface:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Stage 24.1 repeated the same five-tool ordinary-Chat workflow through direct stdio, proving that transport can remain an implementation detail beneath the stable semantic contract.

Current scalable target:

```text
ChatGPT
  -> small stable set of concrete semantic typed actions
  -> deterministic capability projection
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> task-active backends / focused adapters
```

The capability projection is a compatibility boundary, not a planner. It may map a fixed semantic typed operation to one reviewed backend action or small deterministic backend sequence. It must not decide user goals, interpret arbitrary plans, hide heterogeneous risk behind one generic schema, or recreate `tool_invoke` under another name.

Each exposed Chat-facing action must have:

- a fixed truthful JSON schema;
- a clear semantic operation;
- a coherent consequence/authorization class;
- deterministic routing to approved backend capability;
- bounded scope and negative tests where applicable.

Direct diagnostic profiles and adaptive 1MCP remain useful infrastructure, but their raw/generic contracts are not the normal Chat-facing scaling mechanism.

## Stage 24.1 transport selection

The measured A/B paths were:

```text
A — Stage 24 baseline
Tunnel -> HTTP 1MCP -> stdio semantic-projection

B — selected
Tunnel -> stdio semantic-projection
```

Candidate B passed Windows CI, target-machine real Filesystem/Playwright and negative cases, hosted Secure MCP Tunnel, ordinary-Chat five-tool E2E, first-class public-manager lifecycle, single-owner/fail-closed handling, forced-crash recovery and duplicate-free repeated Start.

Both transports then completed 3/3 healthy lifecycle cycles on the target machine:

| Metric | 1MCP baseline | Direct stdio |
|---|---:|---:|
| Average initial Start | 123685 ms | 5007 ms |
| Average repeated/idempotent Start | 84119 ms | 4876 ms |
| Average Stop | 23252 ms | 1043 ms |
| Port 3050 listeners while running | 1 | 0 |

Direct stdio was approximately 24.70x faster to start, 17.25x faster on repeated Start and 22.29x faster to stop in this sample. This closed the transport A/B gate.

Normal public `semantic` therefore routes through direct stdio. `semantic-direct` is retained temporarily as a compatibility/diagnostic alias during migration. The legacy 1MCP-backed semantic path may remain internally reachable for diagnostics/A-B evidence but is not the normal public route.

## Capability lifecycle model

Treat capability state as three independent questions:

- **AVAILABLE:** registered/known in the local catalog;
- **ACTIVE:** backend process currently running because a task needs it;
- **AUTHORIZED:** the requested operation is within allowed scope/platform policy/confirmation policy.

Default behavior should avoid running the whole catalog. Sequential activation is resource-efficient when stages are sequential, but concurrent backend activation is allowed when the real workflow requires it.

This replaces the simplistic interpretation that Filesystem and Browser must never coexist. Real ordinary-Chat typed Filesystem + Browser use passed on synthetic scoped data through both the Stage 24 baseline and Stage 24.1 direct transport.

## OpenAI permission/safety boundary

App permission mode and local backend authorization are not the whole decision surface. Real testing showed that typed calls can pass individually while a long composite workflow may still be blocked before MCP by product safety.

Therefore the platform must not treat app permission mode as its only safety mechanism and must not infer backend failure solely from a pre-MCP safety block.

Prefer scoped resources, truthful typed actions, reversible workspaces/backups/git and consequence-based confirmation over prompting for every low-risk call.

## Diagnostic/reference profiles

- `reference`: harmless connectivity smoke through the internal 1MCP path;
- `files-readonly`: one explicit root with write-capable tools disabled;
- `browser-isolated`: isolated/headless Playwright with unsafe code/evaluate/file-upload/direct-network tools disabled;
- `semantic-direct`: temporary compatibility/diagnostic alias for the direct semantic transport;
- `adaptive`: 1MCP lifecycle/CI diagnostic infrastructure.

These provide deterministic acceptance/fallback boundaries. They are not a reason to expose one ChatGPT app per backend.

## Windows management path — ACCEPTED AND EXTENDED

```text
bootstrap
  -> verified official tunnel-client install
  -> official tunnel-client profile/config
  -> LocalAppData manager bundle

user / tray / source checkout / installed bundle
  -> shared public chat-platform.ps1 lifecycle facade
  -> one authoritative owner controller
      -> direct semantic tunnel-client + stdio projection for public semantic
      -> or 1MCP + tunnel-client for profiles that still use 1MCP
```

Rules:

- manager/tray provide lifecycle/configuration/diagnostics only;
- controller is the authoritative readiness/process interpretation;
- tray consumes manager status instead of duplicating it;
- installed runtime/config lives under `%LOCALAPPDATA%\ChatAgentPlatform\app`;
- secrets, tunnel profile, binary, logs and mutable state live outside the app bundle;
- bootstrap uses the official tunnel-client CLI/profile format;
- installed/source copies coordinate one authoritative runtime owner rather than acting as independent managers;
- shared owner state lives at `%LOCALAPPDATA%\ChatAgentPlatform\state\manager-owner.json`;
- `Status` follows the recorded owner;
- takeover stops a foreign owner before starting a new one;
- an unowned shared runtime fails closed;
- for 1MCP-backed profiles, occupied port `3050` remains part of fail-closed ownership detection;
- for direct semantic, the exact owned tunnel-client command/health state is the authoritative managed process boundary and port `3050` must remain unused.

Stage 24.1 target acceptance proved normal lifecycle, forced-crash recovery and idempotent repeated Start for the direct semantic manager without duplicate processes.

## Local specialist inference architecture — PROVISIONAL

After Stage 24.1, add specialist local inference behind a stable capability boundary, not behind Chat as another planner.

Preferred runtime-manager candidate: LM Studio/`llmster`.

Target responsibilities:

```text
local capability request
  -> model/runtime policy
  -> LM Studio / llmster
      -> discover local models/capabilities
      -> estimate RAM/VRAM before load
      -> select tested model variant / GPU offload
      -> JIT or explicit load
      -> TTL / auto-evict / unload
  -> bounded specialist inference
  -> typed result back to Chat
```

LM Studio is replaceable infrastructure, not product identity. The platform must not hard-code one model or runtime.

First preferred `local-vision` candidate: `LiquidAI/LFM2.5-VL-3B`. Candidate Chat-facing vision actions should remain few and semantic, for example `vision_analyze`, `vision_compare`, `vision_extract` and `vision_analyze_frames`. The exact API is not accepted until target-machine benchmarking proves runtime/model behavior.

## Ownership

The repository owns only thin integration assets:

- pinned MCP/runtime configuration;
- Windows lifecycle/bootstrap/tray convenience;
- compatibility and acceptance tests;
- project context/documentation;
- the smallest deterministic semantic capability projection required by the measured Chat boundary;
- focused typed adapters only for measured missing local-program/model boundaries.

The repository does **not** own by default:

- AI planner/agent runtime;
- public ingress/NAT/TLS;
- generic MCP gateway/aggregator implementation;
- generic registry/vault/job/policy/workflow platform;
- media/mastering logic as platform core;
- a bespoke general-purpose model runtime when a mature local runtime manager can satisfy the requirement.

## Component choices

- Reachability: OpenAI Secure MCP Tunnel + official `tunnel-client`.
- Normal semantic transport: direct tunnel-client stdio -> semantic projection.
- Direct accepted 1MCP runtime for internal/reference paths: `@1mcp/agent@0.34.4`.
- Adaptive diagnostic 1MCP line: exact `@1mcp/agent@0.35.0-beta.3` plus the hash-guarded compatibility package until accepted upstream behavior replaces it.
- Filesystem: `@modelcontextprotocol/server-filesystem@2026.7.10`.
- Browser: `@playwright/mcp@0.0.78`.
- Planned local inference runtime candidate: LM Studio/`llmster`.
- Planned first local vision model candidate: `LiquidAI/LFM2.5-VL-3B`.
- Modules: official/vendor MCP -> mature OSS -> local API/CLI adapter -> smallest project-owned missing adapter.

## Legacy

Pre-Stage-22 implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd` as evidence/extraction material only.

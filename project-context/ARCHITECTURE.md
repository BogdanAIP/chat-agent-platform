# Architecture

## Product boundary

The project is a generic bridge that lets ordinary ChatGPT Chat use local capabilities through standard MCP. ChatGPT remains the planner/orchestrator. The local bridge does not implement a second AI agent or workflow brain.

Specialized local inference is allowed as a replaceable capability backend when it performs bounded perception/extraction/classification work. A vision model may help interpret screens/documents/images, but it does not become the planner. Chat remains the brain; local specialist models are tools.

## Accepted reachability path

```text
ordinary ChatGPT Chat
  -> custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client
  -> local 1MCP
  -> replaceable MCP backends / focused local adapters
  -> local programs/files/devices/models
```

The first E2E reference acceptance passed on 2026-08-10.

## Chat-facing capability boundary

Real Stage 24 evidence established five constraints:

1. changing a local direct 1MCP profile does not automatically replace an already-scanned Chat action snapshot;
2. current OpenAI documentation describes ChatGPT MCP app tools as a frozen reviewed snapshot, so later server-side tool changes are not automatically enabled without Refresh/review;
3. the generic adaptive `tool_list` / `tool_schema` / `tool_invoke` + lifecycle surface works as local/CI infrastructure but was blocked before MCP for the consequential/generic ordinary-Chat calls;
4. concrete typed Filesystem and Playwright actions do work together through one ordinary-Chat app/conversation;
5. the tested app effectively truncated a larger action snapshot around 20 tools: 34 local tools surfaced as 20, while a reduced 24-tool local surface allowed later `browser_navigate`/`browser_click` to become callable after Refresh/new Chat.

The exact number is **observed behavior, not an official platform constant**.

1MCP tags, presets and runtime filtering remain useful for backend selection/lifecycle, but they do not by themselves change a frozen ChatGPT action snapshot.

OpenAI Tool Search is architecturally relevant because it supports deferred large-tool discovery in the API/Agents SDK. It is not currently documented as a capability of the ordinary-Chat custom MCP app path used by this project, so it is not a Stage 24 dependency. Re-evaluate if/when that product surface exposes it.

Current scalable target:

```text
ChatGPT
  -> small stable set of concrete semantic typed actions
  -> capability projection onto the larger approved local catalog
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> 1MCP / focused local adapters
  -> one or more task-active backends
```

The capability projection is a compatibility boundary, not a planner. It may map a fixed semantic typed operation to one reviewed backend action or small deterministic backend sequence. It must not decide user goals, interpret arbitrary plans, hide heterogeneous risk behind one generic schema, or recreate `tool_invoke` under another name.

Each exposed Chat-facing action must have:

- a fixed truthful JSON schema;
- a clear semantic operation;
- a coherent consequence/authorization class;
- deterministic routing to approved backend capability;
- bounded scope and negative tests where applicable.

Direct profiles remain accepted diagnostics/reference paths. Adaptive 1MCP remains useful lifecycle/CI infrastructure, but its generic Chat-facing contract is not the accepted product surface.

## Capability lifecycle model

Treat capability state as three independent questions:

- **AVAILABLE:** registered/known in the local catalog;
- **ACTIVE:** backend process currently running because a task needs it;
- **AUTHORIZED:** the requested operation is within allowed scope/platform policy/confirmation policy.

Default behavior should avoid running the whole catalog. Sequential activation is resource-efficient when stages are sequential, but concurrent backend activation is allowed when the real workflow requires it.

This replaces the simplistic interpretation that Filesystem and Browser must never coexist. Real ordinary-Chat typed Filesystem + Browser use has now passed on synthetic scoped data.

## OpenAI permission/safety boundary

App permission mode and local backend authorization are not the whole decision surface. Real testing showed:

- `Allow read actions` can produce a one-time approval card for `write_file`;
- `Allow all actions` allows the same typed read/navigate/write tools without confirmation;
- nevertheless, a long composite local-file -> browser -> write workflow can still be blocked by OpenAI safety even when the individual typed actions pass separately.

Therefore the platform must not treat app permission mode as its only safety mechanism and must not infer backend failure solely from a pre-MCP safety block.

Prefer scoped resources, truthful typed actions, reversible workspaces/backups/git and consequence-based confirmation over prompting for every low-risk call.

## Direct diagnostic/reference profiles

- `reference`: harmless connectivity smoke;
- `files-readonly`: one explicit root, write-capable tools disabled;
- `browser-isolated`: isolated/headless Playwright with unsafe code/evaluate/file-upload/direct-network tools disabled.

These profiles provide deterministic acceptance boundaries and fallback diagnostics. They are not the desired scaling mechanism for every future application integration.

## Windows management path — ACCEPTED

```text
bootstrap
  -> verified official tunnel-client install
  -> official tunnel-client init
  -> LocalAppData manager bundle

user / tray / source checkout / installed bundle
  -> shared public chat-platform.ps1 lifecycle facade
  -> one authoritative owner controller
  -> local 1MCP + tunnel-client processes
```

Rules:

- manager/tray provide lifecycle/configuration/diagnostics only;
- controller is the authoritative local readiness/process interpretation;
- tray consumes manager status instead of duplicating it;
- installed runtime/config lives under `%LOCALAPPDATA%\ChatAgentPlatform\app`;
- secrets, tunnel profile, binary, logs and mutable state live outside the app bundle;
- bootstrap uses the official tunnel-client CLI/profile format;
- installed/source copies coordinate one owner of the fixed `127.0.0.1:3050` MCP endpoint rather than acting as independent managers;
- shared owner state lives at `%LOCALAPPDATA%\ChatAgentPlatform\state\manager-owner.json`;
- `Status` follows the recorded owner;
- takeover stops a foreign owner before starting the new copy;
- an occupied `3050` without trustworthy owner state fails closed instead of accepting another process's health endpoint.

Target Windows acceptance on 2026-08-14 passed installed -> source -> installed takeover, cross-copy Status, foreign-owner Stop/cleanup and occupied-port fail-closed behavior. Functional head `ffcc2e407...` additionally runs a real Windows foreign-listener regression in CI and passes the full CI/profile/security suite.

## Local specialist inference architecture — PROVISIONAL

After Stage 24, add specialist local inference behind a stable capability boundary, not behind Chat as another planner.

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

First preferred `local-vision` candidate: `LiquidAI/LFM2.5-VL-3B` (official release 2026-08-12). Liquid AI positions it for screen/UI understanding, OCR/document/chart understanding, grounding, function calling and multi-image input and publishes day-one GGUF/llama.cpp and ONNX support.

Candidate stable Chat-facing vision actions should remain few and semantic, for example:

- `vision_analyze`;
- `vision_compare`;
- `vision_extract`;
- `vision_analyze_frames`.

The exact API is not accepted until target-machine benchmarking proves runtime/model behavior.

## Ownership

The repository owns only thin integration assets:

- pinned 1MCP/MCP configuration;
- Windows lifecycle/bootstrap/tray convenience;
- compatibility and acceptance tests;
- project context/documentation;
- a smallest semantic capability projection only if required by the measured Chat snapshot boundary;
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
- Direct accepted 1MCP runtime: `@1mcp/agent@0.34.4`.
- Adaptive diagnostic 1MCP line: exact `@1mcp/agent@0.35.0-beta.3` plus a hash-guarded compatibility package that restores declared disabled entries during reconciliation and refreshes the lazy backend registry after lifecycle changes. Remove the patch when an accepted upstream release covers both gaps.
- Filesystem: `@modelcontextprotocol/server-filesystem@2026.7.10`.
- Browser: `@playwright/mcp@0.0.78`.
- Planned local inference runtime candidate: LM Studio/`llmster`.
- Planned first local vision model candidate: `LiquidAI/LFM2.5-VL-3B`.
- Modules: official/vendor MCP -> mature OSS -> local API/CLI adapter -> smallest project-owned missing adapter.

## Legacy

Pre-Stage-22 implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd` as evidence/extraction material only.

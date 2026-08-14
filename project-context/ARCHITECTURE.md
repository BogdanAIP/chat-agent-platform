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

Real Stage 24 evidence established four constraints:

1. changing a local direct 1MCP profile does not automatically replace an already-scanned Chat action snapshot;
2. the generic adaptive `tool_list` / `tool_schema` / `tool_invoke` + lifecycle surface works as local/CI infrastructure but was blocked before MCP for the consequential/generic ordinary-Chat calls;
3. concrete typed Filesystem and Playwright actions do work together through one ordinary-Chat app/conversation;
4. the tested app effectively truncated a larger action snapshot around 20 tools: 34 local tools surfaced as 20, while a reduced 24-tool local surface allowed later `browser_navigate`/`browser_click` to become callable after Refresh/new Chat.

The exact number is **observed behavior, not an official platform constant**.

Current scalable target:

```text
ChatGPT
  -> concrete typed actions with truthful schemas/semantics
  -> capability selection/publication layer (PROVISIONAL)
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> 1MCP / focused local adapters
  -> one or more task-active backends
```

Do not solve action-count pressure by making one opaque generic dispatcher look harmless. If a project-owned capability projection/facade is required, it must remain the smallest fixed-schema boundary justified by measured platform behavior; it must not become a second planner, generic workflow engine or replacement MCP ecosystem.

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

## Windows management path

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
- installed/source copies must coordinate ownership of the fixed `127.0.0.1:3050` MCP endpoint rather than acting as independent managers.

Functional head `64fa0a27...` implements shared manager ownership state in `%LOCALAPPDATA%\ChatAgentPlatform\state\manager-owner.json`, delegation to a foreign owner and fail-closed handling of an occupied MCP port with no trustworthy owner. Remote Windows/CI/security checks pass; target-machine installed/source handoff acceptance remains required.

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

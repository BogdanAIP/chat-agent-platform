# Architecture

## Product boundary

The project is a generic bridge that lets ordinary ChatGPT Chat use local capabilities through standard MCP. ChatGPT remains the planner/orchestrator. The local bridge does not implement a second AI agent or workflow brain.

## Accepted reachability path

```text
ordinary ChatGPT Chat
  -> custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client
  -> local 1MCP
  -> replaceable MCP backends
  -> local programs/files/devices
```

The first E2E reference acceptance passed on 2026-08-10.

## Stable Chat-facing surface target

A real Stage 24 test proved that local backend/profile switching does not automatically replace an already-discovered Chat action snapshot. Therefore the scalable target is not one separate Chat app per local capability and not a dynamically mutating direct tool list.

Target adaptive boundary:

```text
ChatGPT
  -> stable lazy meta-tools: tool_list / tool_schema / tool_invoke
  -> limited lifecycle tools: list / status / enable / disable / reload
  -> 1MCP pre-approved backend catalog
  -> one or more task-active backends
```

The adaptive design uses 1MCP's own aggregation/lazy/lifecycle facilities. It does not justify a project-owned gateway/broker unless an upstream gap is measured and cannot be resolved otherwise.

**Status:** the runtime contract passes local Stage 24 acceptance with Filesystem and Playwright through the exact beta.3 compatibility package. Remote CI, manager integration and ordinary-Chat E2E remain before architectural acceptance. Direct profiles remain the accepted fallback/reference.

## Capability lifecycle model

Treat capability state as three independent questions:

- **AVAILABLE:** registered/known in the local catalog;
- **ACTIVE:** backend process currently running because a task needs it;
- **AUTHORIZED:** the requested operation is within the allowed scope/confirmation policy.

Default behavior should avoid running the whole catalog. Sequential activation is preferred when stages are sequential, but concurrent backend activation is allowed when the real workflow requires it.

This replaces the simplistic interpretation that Filesystem and Browser must never coexist. What remains forbidden is an unnecessarily broad, permanently active, unscoped local-data + open-network baseline.

## Direct diagnostic/reference profiles

- `reference`: harmless connectivity smoke;
- `files-readonly`: one explicit root, write-capable tools disabled;
- `browser-isolated`: isolated/headless Playwright with dangerous tools disabled.

These profiles provide deterministic acceptance boundaries and fallback diagnostics. They are not the desired scaling mechanism for every future application integration.

## Windows management path

```text
bootstrap
  -> verified official tunnel-client install
  -> official tunnel-client init
  -> LocalAppData manager bundle

user / tray
  -> chat-platform.ps1
  -> chat-platform-controller
  -> local 1MCP + tunnel-client processes
```

Rules:

- manager/tray provide lifecycle/configuration/diagnostics only;
- controller is the authoritative local readiness/process interpretation;
- tray consumes manager status instead of duplicating it;
- installed runtime/config lives under `%LOCALAPPDATA%\ChatAgentPlatform\app`;
- secrets, tunnel profile, binary, logs and mutable state live outside the app bundle;
- bootstrap uses the official tunnel-client CLI/profile format.

Adaptive manager integration is not accepted until adaptive runtime acceptance passes.

## Ownership

The repository owns only thin integration assets:

- pinned 1MCP/MCP configuration;
- Windows lifecycle/bootstrap/tray convenience;
- compatibility and acceptance tests;
- project context/documentation;
- focused adapters only for measured missing local-program boundaries.

The repository does **not** own by default:

- AI planner/agent runtime;
- public ingress/NAT/TLS;
- generic MCP gateway/aggregator implementation;
- generic registry/vault/job/policy/workflow platform;
- media/mastering logic as platform core.

1MCP is the current replaceable runtime that supplies aggregation/lazy discovery/lifecycle capabilities where accepted.

## Component choices

- Reachability: OpenAI Secure MCP Tunnel + official `tunnel-client`.
- Direct accepted 1MCP runtime: `@1mcp/agent@0.34.4`.
- Adaptive experimental 1MCP line: exact `@1mcp/agent@0.35.0-beta.3` plus a hash-guarded compatibility package that restores declared disabled entries during reconciliation and refreshes the lazy backend registry after lifecycle changes. Remove the patch when an accepted upstream release covers both gaps.
- Modules: official/vendor MCP -> mature OSS -> local API/CLI adapter -> smallest project-owned missing adapter.

## Legacy

Pre-Stage-22 implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd` as evidence/extraction material only.

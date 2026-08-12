# Architecture

## Product boundary

The project is a generic bridge that lets ordinary ChatGPT Chat use local capabilities through standard MCP. ChatGPT remains the planner/orchestrator; the local bridge does not implement a second agent.

## Accepted data path

```text
ordinary ChatGPT Chat
  -> custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client
  -> 1MCP on loopback
  -> one explicit task profile
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

The first end-to-end reference acceptance passed on 2026-08-10 with the official Sequential Thinking server.

## Windows management path

The local management plane is deliberately separate from the MCP data path:

```text
bootstrap (one-time / repair)
  -> verified official tunnel-client install
  -> official tunnel-client init
  -> LocalAppData manager bundle

user / tray
  -> chat-platform.ps1          # public serialized command facade
  -> chat-platform-controller   # internal lifecycle implementation
  -> local 1MCP + tunnel-client processes

tray
  <- Status from chat-platform.ps1
```

Rules:

- `chat-platform.ps1` serializes mutating lifecycle commands with a local named mutex; `Status` remains read-only/non-blocking;
- controller is the only authoritative implementation of platform/tunnel/profile readiness used by UI;
- tray does not inspect PIDs, process command lines or MCP/tunnel health independently;
- bootstrap installs the manager/runtime configuration under `%LOCALAPPDATA%\ChatAgentPlatform\app`, so normal use is independent of the Git checkout;
- secrets, tunnel profile, tunnel binary, logs and mutable state live outside the app bundle in separate LocalAppData paths;
- bootstrap calls official `tunnel-client init` instead of generating a project-owned tunnel profile format.

## Ownership

The repository owns only thin integration assets:

- pinned 1MCP/MCP configurations;
- Windows lifecycle/profile scripts;
- bootstrap/manager/tray convenience;
- compatibility/acceptance tests and project context;
- future focused adapters only when no acceptable ready-made MCP exists.

The repository does **not** own:

- an AI planner/agent runtime;
- public ingress or NAT/TLS;
- an MCP aggregator implementation;
- polling relay/cloud gateway;
- generic jobs/artifacts/vault/policy/workflow engines;
- media/mastering logic as platform core.

## Component choices

- **Reachability:** OpenAI Secure MCP Tunnel with official `tunnel-client`.
- **Local MCP runtime:** 1MCP is the current accepted default and remains replaceable.
- **Modules:** prefer official/vendor MCP, then mature OSS, then generic/local API adapters, then the smallest project-owned missing adapter.
- **Windows convenience:** bootstrap + serialized lifecycle facade + controller + tray; these may coordinate components but must not absorb their protocol/runtime responsibilities.

## Legacy

The pre-Stage-22 implementation remains recoverable from Git history at commit `a446397d99276856c614bc49526cab422c7e74bd`. It is evidence/extraction material, not active product code.

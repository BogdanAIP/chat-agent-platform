# Architecture

## Product boundary

The project is a generic bridge that lets ordinary ChatGPT Chat use local capabilities through standard MCP. ChatGPT remains the planner/orchestrator; the bridge does not implement a second agent.

## Accepted path

```text
ordinary ChatGPT Chat
  -> custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client
  -> 1MCP on loopback
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

The first end-to-end acceptance passed on 2026-08-10 with the official Sequential Thinking reference server.

## Ownership

The repository owns only thin integration assets:

- a small 1MCP configuration;
- Windows lifecycle scripts for the local MCP runtime;
- compatibility/acceptance documentation;
- future adapters only when no acceptable ready-made MCP exists.

The repository does **not** own:

- a generic agent runtime;
- a public ingress or NAT/TLS layer;
- an MCP aggregator implementation;
- a polling relay;
- a cloud gateway;
- generic jobs/artifacts/secrets/policy engines;
- media/mastering logic as platform core.

## Component choices

- **Reachability:** OpenAI Secure MCP Tunnel for ChatGPT. `tunnel-client` runs separately and connects outbound to OpenAI.
- **Local MCP runtime:** 1MCP is the current accepted default and remains replaceable.
- **Modules:** prefer official/vendor MCP, then mature OSS, then generic adapters, then the smallest project-owned adapter.

## Legacy

The pre-Stage-22 implementation remains recoverable from Git history at commit `a446397d99276856c614bc49526cab422c7e74bd`. It is evidence and extraction material, not active product code.

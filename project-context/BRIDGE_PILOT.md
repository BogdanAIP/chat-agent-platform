# Native Chat-to-Local Bridge Pilot — Accepted

## Purpose

Prove that ordinary ChatGPT Chat can use a local MCP module through entirely off-the-shelf bridge infrastructure.

The working legacy `Music Video MCP Yandex Test` connection was left unchanged throughout the experiment.

## Final accepted path

The original Tailscale `8443` public-endpoint experiment was replaced by the official OpenAI Secure MCP Tunnel after the ChatGPT UI exposed that supported local-server path.

Accepted on 2026-08-10:

```text
ordinary ChatGPT Chat
  -> development MCP app `Chat Local Bridge Test`
  -> OpenAI Secure MCP Tunnel
  -> official `openai/tunnel-client`
  -> http://127.0.0.1:3050/mcp
  -> 1MCP 0.34.4
  -> official Sequential Thinking server 2026.7.4
  -> response returned to ChatGPT
```

## Local runtime evidence

1MCP local health reported the reference server as ready:

```json
{
  "name": "sequential-thinking",
  "state": "ready"
}
```

The local MCP endpoint remained:

```text
http://127.0.0.1:3050/mcp
```

## Secure MCP Tunnel setup evidence

A tunnel named `Chat Local Bridge Test` was created in OpenAI Platform and attached to the target ChatGPT workspace.

The official `openai/tunnel-client` was configured to connect that tunnel to the local 1MCP Streamable HTTP endpoint.

The runtime credential uses the minimum required tunnel permissions:

```text
Tunnels: Read + Use
```

The credential value is a secret and must never be committed or documented.

The tunnel client reached `ready` before the ChatGPT connector was tested.

## ChatGPT app evidence

A new development MCP app was created with:

```text
Name: Chat Local Bridge Test
Connection: Tunnel
Tunnel: Chat Local Bridge Test
MCP authentication: none (reference server only)
```

The existing Yandex development app was not modified.

## End-to-end acceptance

From an ordinary ChatGPT conversation, the user invoked:

```text
Chat Local Bridge Test -> sequential_thinking
```

The local MCP returned:

```json
{
  "thoughtNumber": 1,
  "totalThoughts": 1,
  "nextThoughtNeeded": false,
  "branches": [],
  "thoughtHistoryLength": 1
}
```

The response was delivered back into ChatGPT.

Therefore the pilot exit gate is **passed**.

## What this proves

The project does not need to own:

- MCP transport protocol implementation;
- public NAT/TLS ingress for normal ChatGPT-local connectivity;
- a universal autonomous local agent runtime;
- a custom cloud relay for the primary path.

A mature official tunnel plus a mature local MCP runtime is sufficient for the central bridge.

## Tailscale experiment status

Tailscale Funnel remains valid historical/fallback reachability evidence.

The temporary `8443 -> 3050` route is not the accepted primary ChatGPT path and should not be used as a privileged permanent ingress.

The existing HTTPS `443` legacy/Yandex route is deliberately untouched pending a separate cleanup decision.

## Security boundary

The accepted pilot exposed only Sequential Thinking.

Do not infer that filesystem, shell, browser, local application control or secrets are automatically safe to expose. Privileged modules require Stage 24 exposure/auth/permission work.

## Next

Stage 22: classify the old custom Rust/Yandex subsystems as remove, extract, retain or archive/reference.

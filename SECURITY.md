# Security Policy

Security fixes target the current `main` branch until a versioned release policy is published.

## Reporting

Do not publish tokens, API keys, private endpoints, exploit payloads, or sensitive logs in public issues/PRs. Prefer GitHub private vulnerability reporting when available; otherwise request a private channel without including exploit details.

## Current security boundary

The normal bridge path is outbound-only from the user's machine:

```text
ChatGPT -> OpenAI Secure MCP Tunnel -> tunnel-client -> 127.0.0.1:3050/mcp -> 1MCP -> MCP modules
```

The project does not implement its own public ingress, relay, tunnel, credential vault, or generic authorization server.

Secrets, including the OpenAI tunnel runtime key, must never be committed. The runtime key used by `tunnel-client` should have only the permissions required by the tunnel runtime (`Tunnels: Read + Use`).

The shipped reference config exposes only `sequential_thinking`. Filesystem, shell, browser, environment access, local application control, credentials, and other privileged modules require a separate accepted permission profile and negative tests before being enabled.

Historical Yandex/Tailscale deployments are fallback evidence outside the active architecture and must not be treated as an authorization boundary.

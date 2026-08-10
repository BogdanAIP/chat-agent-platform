# Current State

## Accepted bridge

Stage 21 is complete. On 2026-08-10 ordinary ChatGPT Chat successfully invoked `sequential_thinking` through:

```text
ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> 1MCP
  -> Sequential Thinking
  -> result back to ChatGPT
```

This is the compatibility authority for the current project direction.

## Active repository after Stage 22

The active tree is intentionally thin:

- `runtime/mcp.json` — safe reference 1MCP config;
- `scripts/start-local-bridge.ps1` — local 1MCP lifecycle;
- `scripts/status-local-bridge.ps1`;
- `scripts/stop-local-bridge.ps1`;
- minimal Windows bridge CI;
- secret-history scan and GitHub Actions CodeQL;
- project architecture/security/roadmap documentation.

There is no project-owned universal runtime, public ingress, polling relay, Yandex deployment code, Python behavioral oracle, media/mastering core, or release pipeline for `agent-platform.exe` in the active tree.

## Legacy preservation

Nothing important was erased from history. The complete pre-cleanup implementation is recoverable at:

```text
a446397d99276856c614bc49526cab422c7e74bd
```

FFmpeg, REAPER and mastering code from that history is classified as **candidate extraction material**, not active product code. Stage 23 will first look for better ready-made MCP modules before recovering any of it.

## External fallback evidence

The older Yandex integration and Tailscale route are not active repository dependencies. They may remain externally available as rollback evidence until separately retired. Do not add new features to those paths.

## Secrets

OpenAI tunnel runtime keys and tunnel IDs are local operational data and are not stored in this repository. The runtime key should use the minimum required tunnel permissions (`Read + Use`).

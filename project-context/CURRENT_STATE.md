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

## Stage 23 module selection

Stage 23 is in progress with a hard product rule: **zero new mandatory SaaS subscriptions in the baseline path** while keeping quality as a separate hard gate.

The first candidates are intentionally isolated from the default ChatGPT-facing `runtime/mcp.json`:

- read-only scoped Model Context Protocol Filesystem server, pinned to published npm release `2026.7.10`;
- Microsoft Playwright MCP, pinned to published npm release `0.0.78`, tested in isolated/headless mode;
- TwelveTake REAPER MCP classified for real local REAPER benchmark;
- `sbroenne/mcp-windows` classified as a high-privilege Windows UI Automation fallback;
- OriginLab `originpro` selected as the preferred vendor API foundation for a future thin Origin MCP adapter.

An early candidate CI run caught that source-tree `package.json` versions can be newer than the actual published package channel. Selection policy now requires proving that an installation pin exists in npm/PyPI/GitHub Releases/vendor distribution before acceptance.

Candidate profiles live under `runtime/candidates/`. Promotion into the default tool surface waits for Stage 24 least-privilege/security acceptance.

## Legacy preservation

Nothing important was erased from history. The complete pre-cleanup implementation is recoverable at:

```text
a446397d99276856c614bc49526cab422c7e74bd
```

FFmpeg, REAPER and mastering code from that history is classified as **candidate extraction material**, not active product code. Do not recover it unless ready-made/vendor-first research leaves a measured gap.

## External fallback evidence

The older Yandex integration and Tailscale route are not active repository dependencies. They may remain externally available as rollback evidence until separately retired. Do not add new features to those paths.

## Secrets

OpenAI tunnel runtime keys and tunnel IDs are local operational data and are not stored in this repository. The runtime key should use the minimum required tunnel permissions (`Read + Use`).

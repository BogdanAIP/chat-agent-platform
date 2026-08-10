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

This is the compatibility authority for the current project direction. Ordinary Chat remains the primary intelligence surface; Work, Codex and Workspace Agents are optional consumers/accelerators rather than required architecture.

## Active repository after Stage 22

The active tree is intentionally thin. There is no project-owned universal runtime, public ingress, polling relay, Yandex deployment code, Python behavioral oracle, media/mastering core, or release pipeline for `agent-platform.exe` in the active tree.

## Stage 23 — complete

Stage 23 established the hard product rule **zero new mandatory SaaS subscriptions in the baseline path** and a supply-channel/quality/security selection process.

Two baseline modules passed real Windows acceptance through pinned `@1mcp/agent@0.34.4`:

- **Filesystem `2026.7.10` — CI-ACCEPTED.** Scoped root; create/write/edit/move hidden; real `read_text_file` call passed.
- **Microsoft Playwright MCP `0.0.78` — CI-ACCEPTED.** Isolated/headless Chrome; real navigation/content/close calls passed.

Ready-made-first application candidates are documented for REAPER, Origin, FFmpeg, Windows UI Automation and Blender. Legacy project adapters stay historical unless a measured gap remains.

## Stage 24 — in progress

Stage 24 converts accepted capabilities into explicit least-privilege task profiles for ordinary Chat.

Current profile design:

### `files-readonly`

- one Filesystem MCP server only;
- one explicit workspace directory supplied locally at start time;
- whole drives and broad/system roots are rejected;
- create/write/edit/move disabled;
- no browser capability.

### `browser-isolated`

- one Playwright MCP server only;
- isolated headless Chrome;
- no filesystem capability;
- service workers and code generation disabled;
- `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload` and direct `browser_network_request` disabled.

The profiles are deliberately **not combined**. Read-only local data plus an open network-capable browser can still form an exfiltration path under prompt injection. Capability separation is therefore the baseline security boundary.

New lifecycle scripts keep the official tunnel target at `http://127.0.0.1:3050/mcp` and switch which local 1MCP Runtime Scope owns that port:

- `scripts/start-chat-profile.ps1`;
- `scripts/status-chat-profile.ps1`;
- `scripts/stop-chat-profile.ps1`.

The profile switch is an explicit local action. Ordinary Chat cannot silently grant itself a broader profile.

Stage 24 is not accepted until both profiles pass their dedicated Windows profile CI and then each passes one harmless ordinary-Chat end-to-end call through the existing Secure MCP Tunnel. Authenticated browser reuse, filesystem writes, Windows UI control and shell access remain outside the baseline.

## Application candidates after Stage 24

- TwelveTake REAPER MCP: choose one exact immutable artifact before real REAPER benchmarking;
- Origin-Pro-MCP: source and PyPI versions currently differ, so choose one exact artifact before testing installed Origin;
- `ffmpeg-mcp-lite==0.2.2`: primary typed FFmpeg candidate, still requires path/output audit and media benchmarks;
- `sbroenne/mcp-windows`: high-privilege fallback only;
- Blender: compare a reduced DCC-MCP profile against the smaller `djeada` server.

## Legacy preservation

Nothing important was erased from history. The complete pre-cleanup implementation is recoverable at:

```text
a446397d99276856c614bc49526cab422c7e74bd
```

FFmpeg, REAPER and mastering code from that history is candidate extraction material, not active product code.

## External fallback evidence

The older Yandex integration and Tailscale route are not active repository dependencies. Do not add new features to those paths.

## Secrets

OpenAI tunnel runtime keys and tunnel IDs are local operational data and are not stored in this repository. The runtime key should use the minimum required tunnel permissions (`Read + Use`).

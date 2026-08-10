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
- TwelveTake REAPER MCP is the primary REAPER family candidate: GitHub release `v1.6.4` exists, while the PyPI evidence inspected still reports `1.6.0`; the exact artifact must be chosen and pinned before local benchmarking;
- `youngminsw/Origin-Pro-MCP` is now the primary ready-made Origin family candidate: source `0.3.1` is pinned by commit `1e9741af96c45bcac9e619c3ba32264bac6950e7`, while PyPI currently publishes `0.1.0`; those must not be treated as the same artifact;
- `kevinwatt/ffmpeg-mcp-lite==0.2.2` is verified on PyPI and is now the primary small typed FFmpeg candidate; project-owned FFmpeg code is fallback only;
- `sbroenne/mcp-windows` remains a high-privilege Windows UI Automation fallback;
- Blender selection is narrowed to a deep-but-broad `dcc-mcp/dcc-mcp-blender` candidate and a smaller `djeada/blender-mcp-server` candidate.

Candidate CI/research has already caught real integration mistakes instead of accepting README claims:

1. source-tree version strings can differ from published package versions, so the selection policy requires proving the real npm/PyPI/GitHub Release/vendor supply channel;
2. 1MCP `0.34.4` does not inherit the entire parent environment for stdio servers by default. Scoped variables must be imported deliberately; the Filesystem candidate imports only `CHAT_LOCAL_FILES_ROOT` rather than the whole Windows environment;
3. an unpinned `uvx package` command is not sufficient evidence when PyPI lags behind the upstream source/release. The chosen artifact must be explicit and reproducible.

Candidate profiles live under `runtime/candidates/`. Promotion into the default tool surface waits for real acceptance plus Stage 24 least-privilege/security review.

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

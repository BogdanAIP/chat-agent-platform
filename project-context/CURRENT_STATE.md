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

Ordinary Chat remains the primary intelligence surface. Work, Codex and Workspace Agents are optional accelerators rather than required architecture.

## Active repository

The active tree is intentionally thin. There is no project-owned universal runtime, public ingress, polling relay, Yandex deployment, media/mastering core or second AI planner.

Project-owned executable behavior is limited to Windows lifecycle/bootstrap convenience and compatibility/acceptance checks around mature components.

## Stage 23 — complete

Two baseline modules passed real Windows acceptance through pinned `@1mcp/agent@0.34.4`:

- **Filesystem `2026.7.10` — CI-ACCEPTED.** Scoped root; create/write/edit/move hidden; real `read_text_file` call passed.
- **Microsoft Playwright MCP `0.0.78` — CI-ACCEPTED.** Isolated/headless Chrome; real navigation/content/close calls passed.

Ready-made-first candidates are recorded for REAPER, Origin, FFmpeg, Windows UI Automation and Blender.

## Stage 24 — in progress

### Least-privilege profiles

`files-readonly`:

- one Filesystem MCP only;
- one explicit existing workspace root;
- whole drives and broad/system roots rejected;
- create/write/edit/move disabled;
- no browser capability.

`browser-isolated`:

- one Playwright MCP only;
- isolated headless Chrome;
- no filesystem capability;
- service workers and code generation disabled;
- unsafe code/evaluate/file-upload/direct-request tools disabled.

The profiles are deliberately not combined. Read-only local data plus an open network-capable browser can still form an exfiltration path under prompt injection.

### Lifecycle state

The local lifecycle scripts keep the official tunnel target at `http://127.0.0.1:3050/mcp` and use separate 1MCP Runtime Scopes.

Profile status is now machine-readable even when more than one known Runtime Scope is active: that condition is reported as `conflict`/`active_count > 1` so the controller can recover it instead of losing the state behind an error exit.

Idempotent 1MCP cleanup consistently accepts the known already-stopped supervisor states `3` and `7`.

### Thin Windows bootstrap/manager

The Stage 24 manager is deliberately not an agent. Its responsibilities are installation/configuration/lifecycle/diagnostics only.

Bootstrap now:

- checks PowerShell 7, Node/npm/npx and pinned 1MCP availability;
- installs reviewed official `openai/tunnel-client v0.0.11` Windows x64/ARM64 assets only after comparing the downloaded archive against the pinned reviewed SHA-256, official `SHA256SUMS.txt` and GitHub release asset digest;
- creates/reuses `local-1mcp` using the official `tunnel-client init` CLI and fixed loopback MCP URL;
- installs a verified copy of the manager scripts and runtime configs under `%LOCALAPPDATA%\ChatAgentPlatform\app` so normal use does not depend on a Git checkout;
- keeps tunnel binary/profile/state/secrets outside the app bundle;
- requests the runtime API key only when not already configured and stores it through Windows DPAPI `CurrentUser`;
- installs the desktop shortcut from the installed manager copy;
- performs a default reference-profile MCP + tunnel readiness smoke test, then stops the platform.

Tray is now UI-only. It gets authoritative status from `chat-platform-controller.ps1`; it no longer duplicates PID/process/tunnel/MCP health discovery.

Manager/profile/bootstrap changes trigger the dedicated `Chat Profile Acceptance` Windows workflow in addition to normal CI, CodeQL and secret-history scanning.

## Remaining Stage 24 gates

Before Stage 24 is accepted:

1. current manager/bootstrap CI must remain green on the final branch state;
2. the bootstrap must be exercised on the real Windows machine using the existing provisioned tunnel ID/runtime key path;
3. `files-readonly` must complete one harmless call from ordinary Chat through Secure MCP Tunnel;
4. `browser-isolated` must complete one harmless call from ordinary Chat through Secure MCP Tunnel;
5. switching profiles must be checked from the real Chat surface so the previous tool surface is no longer discoverable.

Authenticated browser reuse, filesystem writes, shell access and desktop automation remain outside the baseline.

## Application work after Stage 24

- TwelveTake REAPER MCP: select one immutable artifact before real REAPER benchmarking;
- Origin-Pro-MCP: choose one immutable published/source artifact before testing installed Origin;
- `ffmpeg-mcp-lite==0.2.2`: audit output/path behavior and benchmark real media tasks;
- Blender: compare a reduced DCC-MCP profile against the smaller `djeada` server;
- Windows MCP: high-privilege fallback only.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at:

```text
a446397d99276856c614bc49526cab422c7e74bd
```

Historical Yandex/Tailscale paths are not active product dependencies.

## Secrets

Tunnel runtime keys and tunnel IDs are local operational data and are not stored in Git. The long-lived runtime key should use only the required tunnel runtime permissions (`Read + Use`).

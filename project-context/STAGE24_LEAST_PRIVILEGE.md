# Stage 24 — Least-Privilege Ordinary Chat Profiles

## Goal

Turn the Stage 23 technical candidates into safe, explicit task profiles for the already accepted path:

```text
ordinary ChatGPT Chat
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> tunnel-client
  -> 1MCP on 127.0.0.1:3050
  -> exactly one least-privilege local task profile
```

This stage does **not** introduce Work, Codex, Workspace Agents, a second planner, a cloud browser service, or a new paid subscription.

## Security decision: do not combine Filesystem and open-web Browser by default

A read-only filesystem is still sensitive: it can reveal local data. An open browser can transmit data to remote sites. Putting both capabilities in one always-on tool surface creates a cross-tool exfiltration path if an untrusted page contains prompt injection or otherwise influences the model.

Therefore the baseline uses mutually exclusive profiles:

### `files-readonly`

- exactly one Filesystem MCP server;
- exactly one explicit existing workspace root supplied at start time;
- whole-drive roots are rejected;
- Windows, Program Files, ProgramData and the user-profile root are rejected as direct roots;
- create/write/edit/move tools are disabled at 1MCP;
- no browser server is present.

### `browser-isolated`

- exactly one Microsoft Playwright MCP server;
- headless Chrome;
- isolated browser state;
- service workers blocked;
- code generation disabled;
- `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload` and direct `browser_network_request` are disabled at 1MCP;
- no filesystem server is present.

Origin restrictions such as Playwright allowed/blocked origins may still be used as defense in depth, but upstream explicitly says origin controls are not a security boundary. The primary boundary here is capability separation.

## Why one active profile at a time

The OpenAI tunnel-client already forwards to one local MCP endpoint. The project should not add another router merely to switch tasks.

Each profile uses a separate 1MCP Runtime Scope (its own config directory), while `scripts/start-chat-profile.ps1` ensures that only one known Chat-facing scope is active on the fixed tunnel target port. Switching profile is an explicit local lifecycle action, not autonomous privilege escalation from the remote model.

This is intentional. Chat should not be able to give itself broader local access merely because a task changes.

## Lifecycle

Start read-only files access:

```powershell
.\scripts\start-chat-profile.ps1 -Profile files-readonly -FilesRoot "C:\path\to\one\workspace"
```

Start isolated browser access:

```powershell
.\scripts\start-chat-profile.ps1 -Profile browser-isolated
```

Inspect state:

```powershell
.\scripts\status-chat-profile.ps1
```

Stop all Chat-facing local 1MCP scopes:

```powershell
.\scripts\stop-chat-profile.ps1
```

The official OpenAI tunnel-client is not replaced or reimplemented by these scripts. It continues to target `http://127.0.0.1:3050/mcp`.

## Promotion criteria

A profile is accepted for ordinary Chat only after all of the following pass:

1. profile configuration is pinned to the Stage 23 accepted package version;
2. dangerous tools remain absent from actual 1MCP discovery;
3. exactly one task profile owns the Chat-facing local port;
4. local health is `ready`;
5. Secure MCP Tunnel remains ready with no new public ingress;
6. ordinary Chat can perform one harmless end-to-end call for that profile;
7. switching profile does not silently expose the other profile's tools;
8. no secret, tunnel ID or user-specific absolute path is committed.

## What Stage 24 deliberately does not do

- no permanent combined `files + browser` profile;
- no write-capable Filesystem profile;
- no authenticated browser-session reuse yet;
- no Windows desktop automation yet;
- no arbitrary PowerShell/shell tool;
- no automatic privilege/profile escalation requested by Chat;
- no mandatory paid browser/cloud service.

Later task profiles may combine capabilities only when there is a concrete workflow and a narrower boundary, such as a dedicated non-sensitive exchange directory plus an allowlisted browser destination. That must be a separate reviewed decision.

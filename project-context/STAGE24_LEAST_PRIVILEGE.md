# Stage 24 — Least-Privilege Ordinary Chat Profiles and Windows Lifecycle

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

This stage does **not** introduce Work, Codex, a second planner, a cloud browser service, a new paid subscription or a custom tunnel/runtime.

## Security decision: do not combine Filesystem and open-web Browser by default

A read-only filesystem can reveal local data. An open browser can transmit data to remote sites. Putting both capabilities in one always-on tool surface creates a cross-tool exfiltration path if an untrusted page influences the model.

Therefore the baseline uses mutually exclusive profiles.

### `files-readonly`

- exactly one Filesystem MCP server;
- exactly one explicit existing workspace root supplied locally;
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
- unsafe code/evaluate/file-upload/direct-request tools disabled at 1MCP;
- no filesystem server is present.

Origin restrictions may be defense in depth, but capability separation is the primary boundary.

## One active profile at a time

The OpenAI tunnel-client forwards to one local MCP endpoint. The project does not add another router merely to switch tasks.

Each profile uses a separate 1MCP Runtime Scope while local lifecycle ensures normal operation has one known Chat-facing owner of the fixed endpoint. Switching profile is an explicit local action, not autonomous privilege escalation requested by Chat.

A recognized multiple-scope condition is reported as machine-readable `conflict` with `active_count > 1` so the manager can clean it instead of hiding the recoverable state behind a command failure.

## Thin Windows lifecycle manager

A measured usability requirement is now part of Stage 24: the user should not need multiple terminal windows or repository-local tunnel secrets merely to start/stop the accepted bridge.

The manager boundary is:

```text
chat-platform.ps1
  -> serialized public Start/Stop/Toggle/Install/SetProfile
  -> non-blocking Status
  -> internal chat-platform-controller.ps1

chat-platform-tray.ps1
  -> UI only
  -> reads Status through chat-platform.ps1
```

Mutating operations use a Windows named mutex so tray and manual commands cannot intentionally start competing lifecycle transitions.

The tray does not implement separate process/PID/health logic. Green requires controller-reported `mcp_ready`, `tunnel_ready` and exactly one active profile.

## Bootstrap

First setup/repair is performed by:

```powershell
.\scripts\bootstrap-chat-platform.ps1
```

Bootstrap responsibilities are intentionally finite:

1. check Windows/PowerShell/Node/npm/npx and pinned 1MCP availability;
2. download the reviewed official OpenAI `tunnel-client` Windows artifact;
3. verify the fixed release tag, pinned archive SHA-256, official `SHA256SUMS.txt` and release asset digest;
4. install the binary under `%LOCALAPPDATA%\ChatAgentPlatform\bin`;
5. create/reuse `local-1mcp` with official `tunnel-client init` targeting `http://127.0.0.1:3050/mcp`;
6. copy the thin scripts and runtime configs with SHA-256 copy verification to `%LOCALAPPDATA%\ChatAgentPlatform\app`;
7. request the runtime key when missing and store it with DPAPI `CurrentUser`;
8. install the desktop shortcut from the installed app copy;
9. run a default reference MCP + tunnel readiness smoke test and stop afterward.

The installed manager must remain usable if the source Git checkout is moved or deleted.

## Promotion criteria

Stage 24 is accepted only after all applicable gates pass:

1. profile and runtime packages are pinned to accepted published versions;
2. dangerous tools remain absent from actual 1MCP discovery;
3. exactly one normal task profile owns the Chat-facing endpoint;
4. conflicting known scopes are observable and recoverable;
5. local MCP health is `ready`;
6. official tunnel `/readyz` is ready before green/start success;
7. failed startup rolls back both MCP and tunnel;
8. manager/bootstrap/profile changes trigger dedicated Windows profile acceptance;
9. bootstrap does not silently follow a moving tunnel-client `latest` artifact;
10. bootstrap installs a standalone LocalAppData manager bundle and keeps secrets outside it;
11. ordinary Chat completes one harmless `files-readonly` call through the real Secure MCP Tunnel;
12. ordinary Chat completes one harmless `browser-isolated` call through the real Secure MCP Tunnel;
13. switching profile removes the previous profile's tool surface;
14. no secret, tunnel ID or user-specific absolute path is committed.

## Deliberately outside this stage

- no permanent combined files + browser profile;
- no write-capable Filesystem profile;
- no authenticated browser-session reuse;
- no Windows desktop automation;
- no arbitrary PowerShell/shell tool;
- no autonomous remote profile escalation;
- no generic workflow/policy/secret platform;
- no mandatory paid browser/cloud service.

Later profiles may combine capabilities only for a concrete workflow with a narrower boundary and a separate reviewed decision.

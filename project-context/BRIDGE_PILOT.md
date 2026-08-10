# Native Chat-to-Local Bridge Pilot

## Purpose

Prove that ordinary ChatGPT Chat can use a local MCP module through entirely off-the-shelf bridge infrastructure.

This test must not modify the working `Music Video MCP Yandex Test` connection.

## Test path

```text
ChatGPT Chat
  -> new development MCP connection
  -> https://id182019.tailc0abda.ts.net:8443/mcp
  -> Tailscale Funnel HTTPS :8443
  -> http://127.0.0.1:3050/mcp
  -> 1MCP 0.34.4
  -> official Sequential Thinking server 2026.7.4
```

The existing Funnel HTTPS `443` route is intentionally left untouched.

## Start

From the repository root in PowerShell:

```powershell
git switch main
git pull --ff-only
.\scripts\start-chat-bridge-pilot.ps1
```

Successful local/public preparation prints:

```text
BRIDGE_PILOT_STATUS=ready
MCP_URL=https://id182019.tailc0abda.ts.net:8443/mcp
EXPECTED_TOOL=sequential_thinking
```

## ChatGPT connection

Create a **new** development MCP app/connection for this pilot.

Use:

```text
URL: https://id182019.tailc0abda.ts.net:8443/mcp
Authentication: none
```

Do not edit or remove the existing Yandex development connection.

Scan/refresh the new connection's tools. The expected tool is:

```text
sequential_thinking
```

Then invoke that tool from ordinary ChatGPT Chat with a harmless test problem.

Acceptance requires the tool result to return into the same Chat conversation.

## Stop immediately after the test

```powershell
.\scripts\stop-chat-bridge-pilot.ps1
```

Expected:

```text
BRIDGE_PILOT_STATUS=stopped
```

This disables only Funnel HTTPS `8443` and stops only the 1MCP runtime selected by `runtime/bridge-pilot/mcp.json`. It must not modify the existing HTTPS `443` Funnel route.

## Security boundary

This pilot intentionally has no MCP authentication. Its config is CI-locked to exactly one non-privileged reference server.

Do not add:

- filesystem;
- shell/PowerShell;
- browser automation;
- REAPER/FFmpeg/Origin/Blender;
- credentials/secrets;
- local program control;
- other privileged MCP servers.

The pilot profile is disposable evidence, not the future privileged runtime profile.

## If ChatGPT cannot connect

Do not write a new MCP implementation immediately.

Collect which gate failed:

1. public `/health` unreachable -> reachability/Funnel issue;
2. public health works but MCP connection scan fails -> protocol/auth/account-policy edge;
3. scan works but `sequential_thinking` is missing -> 1MCP/upstream discovery issue;
4. tool appears but call fails -> invocation/transport/runtime issue.

Then test the mature alternative appropriate to that exact failure (ToolHive and/or agentgateway) before creating project-owned compatibility code.

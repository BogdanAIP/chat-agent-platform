# Stage 4 — Codex direct Function MCP acceptance

Status: **candidate / live test pending**. This path is optional and does not block the ChatGPT Stage 4 exit gate.

## Why test it

The relay Cloud Function already implements the Streamable-HTTP-style MCP request surface used by the project:

- `initialize`;
- `ping`;
- `notifications/initialized`;
- `tools/list`;
- `tools/call`.

Application auth accepts the remote project token from `X-MCP-Token` before trying `Authorization: Bearer ...`.

Yandex Cloud Functions remove the incoming `Authorization` header before user code, which is why GPT Actions use API Gateway. That limitation does not apply to the project-specific `X-MCP-Token` header. Codex supports `env_http_headers` for remote HTTP MCP servers, so a direct public Function URL is a technically supported candidate for Codex.

Possible benefit: remove the API Gateway hop for Codex while keeping the same Function, Object Storage rendezvous, Windows relay, Project Binding and allowlist.

Do **not** call it preferred until the live test below passes.

## Security rule for the first test

Do not write the remote token into `config.toml`, Git, acceptance JSON or chat.

For the first acceptance, use the token already in the Windows clipboard only as a process environment variable for a Codex CLI process launched from the same PowerShell session.

## Candidate Codex MCP config

Read the `function_id` from local `runtime/stage4-yandex-acceptance.json` and construct:

```text
https://functions.yandexcloud.net/<function_id>
```

Add a temporary MCP entry to the local Codex configuration:

```toml
[mcp_servers.agent_platform_direct]
url = "https://functions.yandexcloud.net/<function_id>"
env_http_headers = { "X-MCP-Token" = "AGENT_PLATFORM_MCP_TOKEN" }
enabled_tools = ["local_ping", "runtime_self_test"]
startup_timeout_sec = 30
tool_timeout_sec = 180
```

`env_http_headers` maps the HTTP header name to the **name of an environment variable**, not to the secret value itself.

## One-session Windows acceptance

From PowerShell, while the GPT/Codex remote token is still in the clipboard:

```powershell
$env:AGENT_PLATFORM_MCP_TOKEN = Get-Clipboard
```

Start/confirm the local relay for the real project:

```powershell
.\target\release\agent-platform.exe --repo-root . relay start --project-id chat-agent-platform
.\target\release\agent-platform.exe --repo-root . relay status --project-id chat-agent-platform
```

Then start a **new Codex CLI process from the same PowerShell session** so it inherits `AGENT_PLATFORM_MCP_TOKEN`.

Acceptance must prove, from Codex itself:

1. MCP initialization succeeds against the direct Function URL;
2. `tools/list` exposes exactly `local_ping` and `runtime_self_test`;
3. `local_ping` returns `pong=true` and `executed_locally=true`;
4. `runtime_self_test` returns success with controlled write/read and cleanup;
5. after local `relay stop`, a retry returns `AGENT_OFFLINE` rather than creating a durable pending task.

After the test:

```powershell
Remove-Item Env:AGENT_PLATFORM_MCP_TOKEN -ErrorAction SilentlyContinue
.\target\release\agent-platform.exe --repo-root . relay stop --project-id chat-agent-platform
```

## Decision after acceptance

If direct Codex -> Function passes reliably:

- keep GPT Actions -> API Gateway as the ChatGPT path;
- allow Codex MCP -> direct Function + `X-MCP-Token` as a separate optimized ingress;
- decide a durable secret-loading mechanism for Codex without placing the token inline in `config.toml`.

If it fails because Yandex or Codex transport semantics differ from the local contract, Codex can use the already-proven API Gateway path instead. Do not add another relay/service just to preserve the direct option.
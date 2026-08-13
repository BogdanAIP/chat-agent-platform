# Security Policy — Bridge

## Trust boundaries

Normal path:

```text
ChatGPT -> OpenAI tunnel service -> official tunnel-client -> loopback 1MCP -> selected backend(s)
```

The tunnel provides authenticated reachability. It is not a substitute for backend-level least privilege.

## Security objective

Security should control consequence, scope and lifetime without making legitimate workflows impossible.

Use three states:

- **AVAILABLE:** backend is registered/approved locally;
- **ACTIVE:** backend process is running for the current task;
- **AUTHORIZED:** the requested action is within the allowed scope or has the required confirmation.

Avoid keeping a broad local-files + open-network surface permanently active. This is not a blanket prohibition on temporarily using Browser + Filesystem or multiple application backends when a concrete task needs them and their scopes are acceptable.

## Chat-facing adaptive surface

If the Stage 24 adaptive architecture is accepted, ordinary Chat may receive stable discovery/invocation meta-tools and only a narrow set of lifecycle controls for a pre-approved catalog.

Do not expose generic catalog mutation/admin operations such as arbitrary install, uninstall, update, edit or search as part of the ordinary-Chat baseline.

A backend being registered does not mean its process or every tool is authorized.

## Secrets

- `CONTROL_PLANE_API_KEY` stays local and is never repository content.
- Long-lived runtime principal uses only permissions required by tunnel runtime (`Tunnels: Read + Use`) unless a separate admin action explicitly requires more.
- Manager stores the runtime key via DPAPI `CurrentUser`; plaintext exists only as needed for child startup.
- Tunnel IDs are local operational configuration.
- Never commit secrets/tunnel IDs or place them in documentation/log screenshots.
- If exposure is suspected, rotate first.

## Bootstrap supply boundary

Accepted bootstrap must:

1. use official `openai/tunnel-client` release channel;
2. pin reviewed release tag/artifact hash;
3. verify official checksum/digest evidence;
4. verify extracted executable before installation;
5. refuse unsafe replacement while the owned binary runs;
6. create tunnel profile via official `tunnel-client init`.

Installed manager/runtime bundle is copied to `%LOCALAPPDATA%\ChatAgentPlatform\app` with verification. Secrets/profile/state/binary live separately.

## Direct reference/diagnostic profiles

`reference` exposes harmless Sequential Thinking.

`files-readonly` scopes one explicit root and removes create/write/edit/move.

`browser-isolated` uses isolated/headless Playwright and removes unsafe code/evaluate/file-upload/direct-network tools.

Their separation is conservative acceptance evidence and fallback diagnostics. It must not be misread as a permanent rule that no legitimate task may ever combine their classes of capability.

## Privileged backend promotion

Before promoting filesystem writes, shell, browser session reuse, local application control, credentials or devices:

1. minimize tools/paths/actions;
2. use scopes/allowlists where supported;
3. prove forbidden tools are absent or denied;
4. document rollback/revocation;
5. avoid secret/environment enumeration by default;
6. decide which operations can be automatic and which consequences need confirmation.

## Lifecycle integrity

- fixed tunnel target must resolve to one intended local 1MCP runtime;
- conflict state must remain observable/recoverable;
- green platform state requires MCP + tunnel readiness;
- startup failure rolls back partial lifecycle;
- task-driven backend activation must clean up idle/disabled backend processes;
- manager/tray must not invent an independent authorization or planning layer.

## External fallback paths

Historical Yandex/Tailscale routes are not active security architecture. Do not extend them and do not treat public reachability as authorization.

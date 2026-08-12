# Security Policy — Bridge

## Trust boundaries

Normal path:

```text
ChatGPT -> OpenAI tunnel service -> official tunnel-client -> loopback 1MCP -> selected MCP module
```

The tunnel provides authenticated reachability. It is not a substitute for module-level least privilege.

## Secrets

- `CONTROL_PLANE_API_KEY` stays local and is never repository content.
- The long-lived runtime principal receives only the permissions required by tunnel runtime (`Tunnels: Read + Use`) unless a separate administrative action explicitly needs more.
- The Windows manager stores the runtime key through DPAPI `CurrentUser`; the plaintext value is placed in the child tunnel process environment only for startup and then removed from the manager environment.
- Tunnel IDs are local operational configuration, not source configuration.
- Do not place secrets or tunnel IDs in Git, committed Markdown examples, logs or screenshots.
- If a secret may have been exposed, rotate it first; repository cleanup is secondary.

## Bootstrap supply boundary

The bootstrap must not silently download an arbitrary moving `latest` tunnel binary.

For an accepted tunnel-client artifact it must:

1. use the official `openai/tunnel-client` release channel;
2. pin the reviewed release tag;
3. pin the reviewed Windows archive SHA-256;
4. compare the downloaded archive with the official release checksum metadata;
5. verify the extracted executable before installation;
6. refuse to overwrite the installed binary while that binary is running;
7. create the tunnel profile through the official `tunnel-client init` surface rather than custom YAML generation.

The installed manager/runtime bundle is copied to `%LOCALAPPDATA%\ChatAgentPlatform\app` with SHA-256 copy verification. Secrets/profile/state/binary remain in separate LocalAppData directories.

## Reference profile

`runtime/mcp.json` exposes only the harmless Sequential Thinking server and is used for connectivity/smoke tests.

## Privileged profiles

Before enabling filesystem, shell, browser, local application control, credentials or devices:

1. minimize exposed tools and paths/actions;
2. add module-specific scopes/allowlists;
3. prove forbidden tools are absent from actual discovery;
4. prove denied operations fail;
5. document rollback/revocation;
6. avoid environment-variable or secret enumeration tools by default.

Filesystem and an open-web browser are not combined in the baseline because read-only local data plus network transmission is already an exfiltration boundary under prompt injection.

## Lifecycle integrity

- Only one normal Chat-facing Runtime Scope should own the fixed `127.0.0.1:3050` endpoint.
- If multiple known scopes are active, status must preserve that fact as machine-readable conflict state so local lifecycle control can recover it.
- Green UI status requires both MCP `ready` and official tunnel `/readyz` readiness.
- Tray must consume controller status rather than maintaining an independent process/health interpretation.
- Failed platform startup rolls back both tunnel and MCP profile.

## External fallback paths

Historical Yandex/Tailscale routes are not the active security architecture. Do not extend them and do not treat a public tunnel as authorization.

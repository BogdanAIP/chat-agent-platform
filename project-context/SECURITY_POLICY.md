# Security Policy — Bridge

## Trust boundaries

The normal path is:

```text
ChatGPT -> OpenAI tunnel service -> official tunnel-client -> loopback 1MCP -> selected MCP modules
```

The tunnel provides reachability and authenticated control-plane access; it is not a substitute for module-level least privilege.

## Secrets

- `CONTROL_PLANE_API_KEY` / equivalent runtime key stays local.
- Give the runtime principal only `Tunnels: Read + Use` unless a separate administrative operation requires more.
- Do not place secrets or tunnel IDs in Git, Markdown examples, logs or screenshots committed to the repo.
- If a secret may have been exposed, rotate it first; repository cleanup is secondary.

## Reference profile

`runtime/mcp.json` is intentionally limited to the harmless official Sequential Thinking server. CI fails if privileged/example modules are added to that reference profile.

## Privileged modules

Before enabling filesystem, shell, browser, local application control, credentials or devices:

1. minimize exposed tools and paths/actions;
2. verify ChatGPT permission prompts/overrides;
3. add module-specific scopes/allowlists;
4. prove denied operations fail;
5. document rollback/revocation;
6. avoid environment-variable or secret enumeration tools by default.

## External fallback paths

Historical Yandex/Tailscale routes are not the active security architecture. Do not extend them and do not treat a public tunnel as authorization.

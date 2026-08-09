# Rust relay server deployment

`relay-server` is the provider-neutral public transport for Stage 4. It is a small Rust service intended to run on an ordinary Linux VPS. The VPS does not execute local capabilities: it only authenticates callers, stores short-lived relay state in SQLite, and connects remote requests to the outbound-polling Windows agent.

## Network shape

```text
ChatGPT / MCP caller
        |
        | HTTPS + X-MCP-Token
        v
Caddy :443
        |
        | loopback HTTP
        v
relay-server 127.0.0.1:8787
        ^
        | outbound HTTPS + X-Agent-Token
        |
agent-platform.exe on Windows
```

No inbound connection to the Windows computer is required. Cloudflare, ngrok, API Gateway, Cloud Functions, Redis, and a managed database are not required.

## Host requirements

- Linux x86_64 VPS with a stable public IP.
- DNS name pointing to that IP. GPT Actions must use a normal trusted HTTPS endpoint.
- TCP 80/443 open to the internet for Caddy/ACME; SSH should be restricted according to the operator's normal policy.
- `relay-server` listens only on `127.0.0.1:8787` by default.
- Caddy is the TLS boundary. The Rust process itself does not terminate public TLS.

The service is intentionally one project per process. Run separate instances with separate tokens/database paths for unrelated projects.

## Secrets

Generate two independent high-entropy values. A simple Linux example is:

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Use one value as `RELAY_MCP_TOKEN` and the other as `RELAY_AGENT_TOKEN`. Never reuse them.

`RELAY_MCP_TOKEN` is supplied to ChatGPT/MCP callers as `X-MCP-Token` (Bearer is accepted for generic MCP clients as a compatibility path). `RELAY_AGENT_TOKEN` is stored on the Windows machine by the existing agent-platform Secret Store and is sent only as `X-Agent-Token`.

Do not enable reverse-proxy access logs unless custom secret-header redaction is configured. The supplied Caddy example intentionally has no access-log directive.

## Filesystem layout

Recommended production paths:

```text
/usr/local/bin/relay-server
/etc/agent-platform-relay/relay.env
/var/lib/agent-platform-relay/relay.sqlite3
/etc/systemd/system/agent-platform-relay.service
/etc/caddy/Caddyfile
```

Create the service account and state directory:

```bash
sudo useradd --system --home /var/lib/agent-platform-relay --shell /usr/sbin/nologin agent-relay || true
sudo install -d -o agent-relay -g agent-relay -m 0700 /var/lib/agent-platform-relay
sudo install -d -o root -g agent-relay -m 0750 /etc/agent-platform-relay
```

Install the release binary as `/usr/local/bin/relay-server` and copy `relay.env.example` to `/etc/agent-platform-relay/relay.env`. Replace every placeholder and then protect the file:

```bash
sudo chown root:agent-relay /etc/agent-platform-relay/relay.env
sudo chmod 0640 /etc/agent-platform-relay/relay.env
```

Install `agent-platform-relay.service`, reload systemd, and start the service:

```bash
sudo install -m 0644 deploy/relay-server/agent-platform-relay.service /etc/systemd/system/agent-platform-relay.service
sudo systemctl daemon-reload
sudo systemctl enable --now agent-platform-relay
sudo systemctl status agent-platform-relay --no-pager
```

The local-only health endpoint should answer before Caddy is configured:

```bash
curl --fail --silent http://127.0.0.1:8787/healthz
```

Expected shape:

```json
{"status":"ok","contract_version":"relay-server-v1"}
```

## Caddy

Replace `relay.example.com` in `Caddyfile.example` with the real DNS name and use it as the site block in `/etc/caddy/Caddyfile`. Validate and reload Caddy using the package's normal service commands.

After TLS is live:

```bash
curl --fail --silent https://relay.example.com/healthz
```

Do not expose port 8787 in the VPS firewall/security group.

## Windows agent

The existing Windows relay client already speaks this server's protocol. From the repository root, place the **agent** token in a process environment variable only for configuration:

```powershell
$root = (Get-Location).Path
$env:AGENT_PLATFORM_RELAY_TOKEN = '<RELAY_AGENT_TOKEN>'

& .\target\release\agent-platform.exe `
    --repo-root $root `
    relay configure `
    --project-id chat-agent-platform `
    --endpoint 'https://relay.example.com/' `
    --env-name AGENT_PLATFORM_RELAY_TOKEN

$env:AGENT_PLATFORM_RELAY_TOKEN = $null

& .\target\release\agent-platform.exe `
    --repo-root $root `
    relay start `
    --project-id chat-agent-platform
```

`relay configure` moves the token into the project's Secret Store and does not return the raw secret.

## GPT Action

Use `gateway/actions-openapi-relay.template.json` as the source. Replace `__RELAY_URL__` with the HTTPS origin, for example:

```text
https://relay.example.com
```

Configure GPT Action authentication as API key / custom header:

```text
X-MCP-Token: <RELAY_MCP_TOKEN>
```

The exposed operation remains `runLocalAgentTool POST /`; the remote capability allowlist is exactly `local_ping` and `runtime_self_test`.

The Rust ingress deliberately treats `X-Request-Id` as an unrelated header. A GPT-generated value such as `UUID/suffix` therefore does not enter relay task identity and cannot trigger the Yandex ingress failure that motivated this backend.

## Acceptance sequence

1. `/healthz` succeeds through public HTTPS.
2. Start the Windows relay and verify `relay status` reports it alive.
3. From GPT Action, run `local_ping` and require `pong=true` plus `executed_locally=true`.
4. Run `runtime_self_test` and require success.
5. Stop the Windows relay.
6. Repeat `local_ping` and require structured `AGENT_OFFLINE`.

Only that online + offline sequence is sufficient to replace the existing Yandex ingress as the canonical Stage 4 transport.

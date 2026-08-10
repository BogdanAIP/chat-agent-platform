# Current State — Architecture v1.6

## Snapshot

The project is a **generic bridge between ordinary ChatGPT Chat and the user's local computer**.

Accepted baseline on 2026-08-10:

```text
ordinary ChatGPT Chat
  -> development MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official `openai/tunnel-client`
  -> local MCP runtime/gateway (currently 1MCP)
  -> replaceable MCP modules/adapters
  -> local programs/files/devices
```

ChatGPT remains the intelligence/orchestration layer. Work, Codex and OpenAI model API billing are not mandatory bridge dependencies.

The previous Rust-heavy `agent-platform.exe` architecture is no longer the target universal core. Existing custom code is retained only until Stage 22 classifies it from evidence.

## Stage 21 acceptance evidence

Stage 21 is complete.

The following real end-to-end call succeeded from ordinary ChatGPT Chat:

```text
ChatGPT
  -> `Chat Local Bridge Test`
  -> OpenAI Secure MCP Tunnel
  -> tunnel-client on Windows
  -> http://127.0.0.1:3050/mcp
  -> 1MCP
  -> `sequential_thinking`
  -> response returned to ChatGPT
```

Observed returned payload:

```json
{
  "thoughtNumber": 1,
  "totalThoughts": 1,
  "nextThoughtNeeded": false,
  "branches": [],
  "thoughtHistoryLength": 1
}
```

This is the first accepted proof that ordinary ChatGPT can call a standard local MCP tool through an entirely off-the-shelf transport/runtime path without project-owned MCP protocol code.

## Accepted local runtime

Current default local runtime: **1MCP**.

Pinned accepted pilot components:

- `@1mcp/agent@0.34.4`;
- `@modelcontextprotocol/server-sequential-thinking@2026.7.4`;
- Streamable HTTP endpoint `http://127.0.0.1:3050/mcp`.

1MCP remains replaceable. ToolHive/agentgateway/Docker MCP Toolkit are not permanent dependencies and are considered only if a measured requirement justifies them.

## Accepted reachability/control-plane transport

Primary ChatGPT transport: **OpenAI Secure MCP Tunnel** using the official `openai/tunnel-client`.

The tunnel runtime uses a restricted OpenAI runtime key with only the permissions required by the tunnel client (`Tunnels Read + Use`). Runtime secrets must not be stored in git or documentation.

Tailscale is no longer required for the primary ChatGPT-to-local MCP path.

Historical/fallback reachability remains:

- Tailscale Funnel proved public HTTPS -> localhost;
- legacy Yandex/polling proved Hosted Chat -> local Windows execution;
- existing HTTPS `443` route remains untouched until a separate cleanup decision.

The temporary Funnel `8443` path is not part of the accepted primary architecture.

## Security state

The accepted Stage 21 module is intentionally harmless: Sequential Thinking only.

Do not treat successful tunnel transport as permission to expose privileged tools without a profile design. Before filesystem, shell, browser, application control, secrets or other privileged modules are added:

1. define explicit module/tool exposure profiles;
2. keep tunnel/runtime secrets outside repository files;
3. use least-privilege OpenAI tunnel permissions;
4. verify ChatGPT permission/confirmation behavior;
5. test unintended/unauthorized access paths where relevant;
6. document recovery and credential rotation.

## Existing custom implementation inventory

Still present but no longer target-by-default:

- Rust `agent-platform.exe` universal runtime;
- Project Binding and capability selection;
- policy/confirmation mechanisms;
- Windows Credential Manager Secret Store;
- ArtifactStore and JobStore;
- direct authenticated `/gpt` ingress;
- provider-neutral polling relay and Rust relay server;
- Yandex deployment adapter;
- FFmpeg, REAPER and mastering adapters/workflows;
- Python behavioral oracle.

Stage 22 must classify each as remove, extract-as-module, retain-for-measured-reason, or archive/reference.

## Repository/release state

- public MIT repository;
- Windows CI/supply-chain hardening remains active;
- existing custom Rust code still builds/tests during migration;
- first versioned public release has not yet been published;
- donation/support addresses remain intentionally pending.

## Product/account caveat

The real user ChatGPT account has now accepted and executed a custom MCP app through Secure MCP Tunnel. This is accepted evidence for this project and this account.

Do not generalize it into a promise that every ChatGPT Plus account will expose identical custom-MCP functionality indefinitely. Product packaging and public documentation can change independently of this acceptance evidence.

## Next

**Stage 22 — evidence-based legacy subsystem classification and reduction.**

No new universal transport/runtime should be implemented unless Stage 22 or later produces a concrete unmet requirement that mature components cannot satisfy.

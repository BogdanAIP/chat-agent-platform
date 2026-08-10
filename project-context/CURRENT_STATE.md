# Current State — Architecture v1.5

## Snapshot

The project is now defined as a **generic bridge between ordinary ChatGPT Chat and the user's local computer**.

Target behavior:

```text
ordinary ChatGPT Chat
  -> standard MCP
  -> mature HTTPS reachability
  -> mature local MCP runtime/gateway
  -> replaceable MCP modules
  -> local programs/files/devices
```

ChatGPT remains the intelligence/orchestration layer. Work, Codex and OpenAI API model billing are not mandatory bridge dependencies.

The previous Rust-heavy `agent-platform.exe` architecture is no longer assumed to be the permanent core. Existing code is retained as proven experimental inventory until an off-the-shelf bridge path passes real ChatGPT acceptance.

See `BRIDGE_ARCHITECTURE.md` and `ROADMAP.md`.

## Why the architecture changed

The previous implementation successfully proved difficult boundaries, but it also reproduced responsibilities now available in mature MCP infrastructure:

- MCP transport and aggregation;
- stdio/HTTP bridging;
- server process lifecycle;
- public HTTPS reachability;
- generic server/tool discovery;
- optional auth/governance layers.

The new rule is therefore **off-the-shelf first**. Project-owned code is only justified for convenience/configuration or for a specific local program that lacks an acceptable MCP adapter.

## Accepted historical evidence

### Hosted Chat can execute on the local Windows machine

On 2026-08-06 the installed ChatGPT development integration `Music Video MCP Yandex Test` successfully called `local_ping` and returned the real Windows agent response back into ChatGPT.

This proved:

```text
ChatGPT Chat
  -> installed integration
  -> remote path
  -> local Windows execution
  -> response back to ChatGPT
```

### Tailscale Funnel can reach localhost on this laptop

On 2026-08-10 the user exposed the experimental local `/gpt` ingress through Tailscale Funnel and received:

- `status = success`;
- `pong = true`;
- `executed_locally = true`.

Public origin:

```text
https://id182019.tailc0abda.ts.net
```

This proves public HTTPS reachability through Tailscale. It does not prove native MCP from ChatGPT yet.

## Current native-MCP pilot

Selected first runtime candidate: **1MCP**.

Pinned test components:

- `@1mcp/agent@0.34.4`;
- `@modelcontextprotocol/server-sequential-thinking@2026.7.4`.

The test deliberately uses a harmless official reference server rather than filesystem, shell or local-program control.

Prepared local/public path:

```text
ChatGPT development MCP connection
  -> https://id182019.tailc0abda.ts.net:8443/mcp
  -> Tailscale Funnel :8443
  -> 127.0.0.1:3050/mcp
  -> 1MCP
  -> sequential-thinking
```

Repository assets:

- `runtime/bridge-pilot/mcp.json`;
- `scripts/start-chat-bridge-pilot.ps1`;
- `scripts/stop-chat-bridge-pilot.ps1`.

The pilot uses HTTPS `8443` specifically so the existing `443` route is not modified.

## Next real acceptance gate

Run the prepared pilot on the Windows laptop, then create a **new** development MCP connection in ChatGPT rather than modifying the working Yandex integration.

Expected endpoint:

```text
https://id182019.tailc0abda.ts.net:8443/mcp
```

Expected discovered tool:

```text
sequential_thinking
```

Acceptance requires an actual tool invocation from ordinary ChatGPT Chat and a returned result.

If 1MCP fails at the ChatGPT edge, identify the exact cause before writing custom protocol code. ToolHive and agentgateway are the first mature alternatives depending on whether the gap is runtime isolation/governance or protocol/auth translation.

## Security state

The current pilot is intentionally unauthenticated and therefore must expose **only** the harmless reference server for a short test window.

Do not add filesystem, shell, browser, local application control, credentials or other privileged modules to this profile.

After the native-MCP round trip is accepted:

1. stop Funnel `8443`;
2. select/test authentication supported by both the chosen runtime and the actual ChatGPT MCP surface;
3. restrict exposed modules/tools;
4. prove unauthorized requests fail;
5. only then add privileged local modules.

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

These are not being deleted yet. After off-the-shelf MCP acceptance, each will be classified as remove, extract-as-module, retain-for-measured-reason, or archive/reference.

## Repository/release state

- public MIT repository;
- Windows CI/supply-chain hardening remains active;
- current custom Rust code continues to build/test while migration is evaluated;
- first versioned public release has not yet been published;
- donation/support addresses are still intentionally pending.

## Product risk: ChatGPT account surface

The actual user account has already demonstrated a development plugin/app with local write-capable actions in ordinary ChatGPT Chat. Public OpenAI documentation does not currently guarantee identical full-MCP behavior for every Plus account.

Therefore the real user ChatGPT surface is the compatibility acceptance authority. This project should not silently move the primary intelligence path into Work, Codex or paid API usage to paper over a plan/account limitation.

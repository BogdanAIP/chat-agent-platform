# Architecture v1.5 — Chat-to-Local Bridge

## Product boundary

The product is a **generic bridge between ordinary ChatGPT Chat and the user's local computer**.

ChatGPT remains the intelligence/orchestration layer. Local programs, files, devices and specialist workflows are replaceable MCP modules behind the bridge. REAPER, FFmpeg, Origin, Blender, browsers, CAD, local models and future tools are examples, not platform-defining subsystems.

Canonical shape:

```text
ordinary ChatGPT Chat
  -> development/installed MCP app or plugin
  -> standard MCP over HTTPS
  -> replaceable mature reachability layer
  -> replaceable mature local MCP runtime/gateway
  -> replaceable MCP server/adapter
  -> local program/file/device
```

The detailed source of truth is `project-context/BRIDGE_ARCHITECTURE.md`.

## Build-vs-buy rule

Infrastructure is **off-the-shelf first**. Do not create a second implementation of functionality already provided by a mature maintained component.

Selection order for a local capability:

1. official/vendor MCP server;
2. mature open-source MCP server;
3. existing generic MCP adapter/proxy around an API/CLI/program;
4. only then a small project-owned adapter for the missing boundary.

A project-owned adapter must be replaceable without changing the bridge itself.

## First accepted candidate stack

The first direct native-MCP pilot is deliberately simple:

```text
ChatGPT Chat
  -> HTTPS MCP
  -> Tailscale Funnel :8443
  -> 1MCP on 127.0.0.1:3050
  -> official Sequential Thinking reference server
```

Why this shape:

- Tailscale already proved public HTTPS can reach this Windows machine;
- 1MCP already owns MCP aggregation, HTTP/stdio bridging, local server lifecycle, filtering and direct Streamable HTTP `/mcp`;
- the Sequential Thinking reference server is a harmless protocol test and does not expose filesystem/program-control authority;
- port `8443` lets the native MCP experiment run beside the already-working legacy `443` route.

The pilot endpoint is expected to be:

```text
https://id182019.tailc0abda.ts.net:8443/mcp
```

## Runtime candidates

### Default pilot: 1MCP

Use 1MCP first for the one-user Windows bridge. Do not wrap it in `agent-platform.exe` merely to reproduce its runtime responsibilities.

### Fallback: ToolHive

Prefer ToolHive if stronger isolation, authorization, audit/rate limiting, registry governance or protocol-version translation becomes a measured requirement.

### Protocol/security edge: agentgateway

Use agentgateway only if an otherwise-working local runtime needs a separate protocol/auth/routing edge. Do not create two gateway layers without evidence.

### Docker MCP Toolkit

Use only when Docker Desktop itself is desired. It is not a baseline dependency for an ordinary Windows laptop.

## Reachability is not core

The bridge owns no NAT traversal, TLS certificate issuance, relay network or public DNS implementation.

Tailscale Funnel is the currently tested reachability component. Equivalent mature products remain replaceable.

A tunnel provides reachability, not authorization. Privileged MCP modules must not be publicly exposed until an authentication and authorization profile has been accepted.

## What project-owned code may remain

Only three categories are justified by default:

1. **Installer/configurator** — convenience UI/CLI to install/select a runtime, add/remove modules, start/stop bridge profiles and display health/connection URLs.
2. **Compatibility/evidence metadata** — tested combinations of ChatGPT surface, runtime, tunnel and modules.
3. **Missing program adapters** — small typed MCP adapters only where no acceptable existing server exists.

This code must not become another agent runtime.

## Existing Rust core status

The existing Rust `agent-platform.exe`, direct `/gpt` ingress, polling relay, Yandex deployment, policy/job/artifact/confirmation systems and media adapters are **retained experimental inventory**, not the v1.5 target core.

They proved useful boundaries and working local execution, but they are not allowed to justify continued custom infrastructure by inertia.

Do not delete them before the off-the-shelf bridge pilot succeeds. After acceptance, evaluate each subsystem independently:

- remove if mature infrastructure replaces it;
- extract as an optional adapter if it has unique value;
- retain only when a concrete requirement cannot be met by the selected ecosystem component.

## ChatGPT surface constraint

The intended intelligence path is ordinary ChatGPT Chat. Work, Codex and OpenAI API model billing are not mandatory bridge dependencies.

The user's actual ChatGPT surface is the acceptance authority. A development plugin/app with local write-capable tools has already worked on this account, while public OpenAI plan documentation does not guarantee identical full-MCP behavior for every Plus account. Treat this as a compatibility/product-risk item, not as a reason to move intelligence into Work or the API.

## Acceptance rule

The architecture is accepted when a module can be added/removed behind the local MCP runtime and used from ordinary ChatGPT Chat without changing the bridge core.

The first gate is therefore not new Rust code. It is a real call:

```text
ChatGPT Chat
  -> public HTTPS /mcp
  -> 1MCP
  -> official reference MCP server
  -> response back to ChatGPT Chat
```

If this fails, test mature alternatives and identify the exact compatibility gap before writing any protocol implementation.

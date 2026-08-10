# Chat-to-Local Bridge Architecture v1.5

## Product definition

The product is a **generic bridge between ordinary ChatGPT Chat and the user's local computer**.

It is not a media platform, coding agent, mastering system, browser agent, or workflow engine. Those are replaceable examples of what can be connected through the bridge.

The invariant is:

```text
ChatGPT Chat
  -> standard MCP app/plugin connection
  -> replaceable reachability layer
  -> replaceable local MCP runtime/gateway
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

The model in ordinary ChatGPT Chat remains the primary intelligence and orchestrator. Work, Codex and paid OpenAI API usage are not architectural dependencies of the bridge.

## Core rule: buy/borrow infrastructure, build only missing adapters

Do not implement protocol, routing, process supervision, MCP aggregation, tunneling, generic authorization, discovery, registry or generic tool lifecycle when a mature maintained component already provides it.

First choice order:

1. official/vendor MCP server for the target program/service;
2. mature open-source MCP server;
3. generic existing adapter/proxy around the target program/API/CLI;
4. only then a small project-owned MCP adapter for the missing local program boundary.

A project-owned adapter must be removable without changing the bridge architecture.

## Default bridge stack for the first real pilot

```text
ChatGPT Chat
  -> development MCP app/plugin
  -> HTTPS Streamable HTTP
  -> Tailscale Funnel
  -> 1MCP on 127.0.0.1:3050
  -> local stdio/HTTP MCP server
  -> local capability
```

### Why 1MCP is first

For the current one-user Windows scenario, 1MCP is the narrowest mature component found that already provides the required local runtime functions:

- standalone Windows x64 binary and npm package;
- localhost binding by default;
- aggregated Streamable HTTP endpoint at `/mcp`;
- local stdio MCP process launch;
- remote HTTP MCP attachment;
- HTTP <-> stdio bridging;
- server tags, filters and presets;
- background runtime lifecycle;
- configuration reload/lazy loading options;
- optional OAuth/enhanced security.

The bridge must not wrap these features in another custom runtime unless a measured incompatibility requires it.

### First fallback: ToolHive

Use ToolHive instead of 1MCP when one of these becomes material:

- stronger isolation is required;
- built-in authorization/audit/rate limiting is required;
- mixed old/new MCP protocol translation is required;
- MCP `2026-07-28` compatibility becomes a blocking issue for 1MCP;
- a larger managed server catalog is more important than runtime weight.

ToolHive is intentionally not the default for one laptop because its security/governance model is heavier than the first bridge pilot needs.

### Protocol-edge fallback: agentgateway

Agentgateway is a protocol/security edge candidate if the local aggregator works but the remote client requires newer MCP protocol translation, auth, routing or MCP Apps behavior. It should not be inserted by default because that would create two gateway layers before a need is demonstrated.

### Docker MCP Toolkit

Docker MCP Toolkit is useful when Docker Desktop is already a desired dependency and container isolation/catalog packaging are worth the resource cost. It is not a baseline dependency for an ordinary Windows laptop.

## Reachability is replaceable

The bridge owns no NAT traversal or public TLS stack.

Current accepted reachability component: Tailscale Funnel.

Current evidence on 2026-08-10:

- public origin `https://id182019.tailc0abda.ts.net` is working;
- direct HTTPS traffic reaches the local Windows machine;
- the existing experimental `/gpt` ingress returned `status=success`, `pong=true`, `executed_locally=true` through Funnel.

This proves Tailscale can carry traffic to localhost. It does **not** prove native ChatGPT MCP yet.

For the 1MCP pilot use Funnel HTTPS port `8443`, leaving the existing `443` route untouched until the native MCP test passes:

```text
https://id182019.tailc0abda.ts.net:8443/mcp
  -> Tailscale Funnel
  -> http://127.0.0.1:3050/mcp
```

Other mature reachability components remain allowed. The local runtime and adapters must not know which tunnel is used.

## The bridge itself should stay thin

The desired permanent project-owned surface is limited to:

### 1. Installer/configurator

A small Windows-facing layer may eventually:

- detect/install the selected MCP runtime;
- add/remove MCP modules;
- define profiles/presets;
- start/stop the bridge;
- show connection health;
- configure the selected reachability provider;
- export the one MCP URL that ChatGPT should connect to.

This layer is convenience, not a second orchestration engine.

### 2. Compatibility policy

The project may maintain a compatibility matrix describing which runtime/module/tunnel combinations were actually tested.

It must not duplicate their implementation.

### 3. Missing local adapters

If a local program has no acceptable MCP server, implement one small typed adapter for that program only.

Examples such as REAPER, FFmpeg, Origin, Blender, CAD, browsers, local models or hardware are modules, not platform subsystems.

## What is no longer target core

The following existing repository subsystems are retained only as tested experiments/reference assets until the off-the-shelf bridge is accepted or rejected:

- custom `agent-platform.exe` as a universal runtime;
- custom MCP transport implementation;
- custom `/gpt` compatibility ingress as a target interface;
- custom polling relay as a normal request path;
- Yandex gateway/function infrastructure;
- universal Project Binding/policy/job/artifact/confirmation layers as mandatory bridge architecture;
- media-specific capabilities as platform-defining features.

Do not delete them yet. First prove the replacement path. After acceptance, remove or extract only what still has independent value.

## ChatGPT subscription constraint

The product goal is specifically to use **ordinary ChatGPT Chat as the intelligence layer**, not Work/Codex as the required runtime and not OpenAI API billing as the required model path.

There is an important product-risk distinction:

- the user's current real ChatGPT account already has a development plugin/app that exposes write-capable local tools and has successfully called the local computer through the legacy Yandex path;
- current public OpenAI documentation does not guarantee full write-capable custom MCP for all Plus accounts and currently documents full MCP primarily for Business/Enterprise/Edu.

Therefore the actual user's ChatGPT surface is the acceptance authority for this project. Do not generalize the observed account behavior into a promise that every Plus account will support the same feature indefinitely.

## Pilot acceptance test

The first replacement test intentionally contains no project-owned MCP implementation.

```text
ChatGPT Chat
  -> new development MCP connection
  -> https://id182019.tailc0abda.ts.net:8443/mcp
  -> Tailscale Funnel
  -> 1MCP
  -> official MCP reference server
```

Use the official `@modelcontextprotocol/server-sequential-thinking` server for the first scan/call because it does not expose the user's filesystem, environment variables or local application control.

Acceptance requires:

1. 1MCP starts on loopback and reports its HTTP MCP URL;
2. local `/health` succeeds;
3. Funnel `8443` reaches that local runtime from public HTTPS;
4. ChatGPT can create/scan a development MCP connection against the public `/mcp` URL;
5. ChatGPT discovers the `sequential_thinking` tool;
6. a call made from ordinary Chat returns through the same path;
7. the existing Yandex/plugin route remains untouched during the experiment.

If steps 4-6 fail, determine whether the failure is ChatGPT plan/account policy, 1MCP protocol compatibility, authentication expectations, or transport behavior before writing any replacement protocol code.

## Decision ladder after the pilot

```text
1MCP works directly with ChatGPT
  -> keep 1MCP as default bridge runtime
  -> add real replaceable MCP modules

1MCP local aggregation works but ChatGPT protocol edge fails
  -> test ToolHive or agentgateway
  -> do not write our own MCP server/gateway yet

All mature runtimes fail for a specific measured reason
  -> implement only the smallest missing compatibility adapter
```

## Security sequencing

For the first pilot, expose only the harmless reference server and keep the `8443` Funnel limited to the test window.

Before exposing filesystem/program-control modules over a public Funnel, add an accepted authentication profile and tool-level restrictions using capabilities already provided by the selected runtime/host where possible.

Do not assume a tunnel is an authorization boundary.

## Definition of success

The bridge is successful when the user can add/remove a local MCP module and use it from ordinary ChatGPT Chat without changing the bridge core and without requiring Work, Codex or OpenAI API model billing.

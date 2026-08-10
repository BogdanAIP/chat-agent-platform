# Chat-to-Local Bridge Architecture v1.6

## Product definition

The product is a **generic bridge between ordinary ChatGPT Chat and the user's local computer**.

It is not a media platform, coding agent, mastering system, browser agent or workflow engine. Those are replaceable examples of capabilities that can be connected through the bridge.

The accepted invariant is:

```text
ChatGPT Chat
  -> standard MCP app/plugin connection
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> replaceable local MCP runtime/gateway
  -> replaceable MCP servers/adapters
  -> local programs/files/devices
```

The model in ordinary ChatGPT Chat remains the primary intelligence and orchestrator. Work, Codex and paid OpenAI model API usage are not architectural dependencies of the bridge.

## Core rule: borrow infrastructure, build only missing adapters

Do not implement protocol, routing, process supervision, MCP aggregation, tunneling, generic authorization, discovery, registry or generic tool lifecycle when a mature maintained component already provides it.

Choice order:

1. official/vendor implementation;
2. mature maintained open-source implementation;
3. mature generic adapter/proxy;
4. project-owned code only for the exact missing boundary.

A project-owned adapter must remain removable without changing the bridge architecture.

## Accepted default bridge stack

Accepted by real ChatGPT round trip on 2026-08-10:

```text
ordinary ChatGPT Chat
  -> development MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official `openai/tunnel-client`
  -> 1MCP on `127.0.0.1:3050`
  -> local stdio/HTTP MCP module
  -> local capability
```

The accepted pilot called the official Sequential Thinking MCP tool and returned the result to the same ChatGPT conversation.

### Why Secure MCP Tunnel is primary

The official OpenAI tunnel removes the need to expose localhost through a project-owned/public ingress for normal ChatGPT use:

- the tunnel client runs on the user's machine;
- it connects outward to the OpenAI tunnel control plane;
- the local MCP server remains on localhost/private networking;
- ChatGPT uses the tunnel selected by the development MCP app;
- runtime credentials can be restricted to `Tunnels Read + Use`.

The project must not recreate this transport unless a concrete unsupported requirement is proved.

### Why 1MCP is current default local runtime

1MCP passed the real acceptance test and already provides the required local runtime functions:

- aggregated Streamable HTTP `/mcp` endpoint;
- stdio MCP process launch;
- remote HTTP MCP attachment;
- HTTP <-> stdio bridging;
- tags/filters/presets;
- background lifecycle;
- configuration and health surfaces.

It remains replaceable rather than becoming product identity.

### Fallback candidates

Use only for measured gaps:

- **ToolHive** — stronger isolation/governance/security/runtime management;
- **agentgateway** — protocol/auth/routing edge;
- **Docker MCP Toolkit** — when Docker Desktop itself is an accepted baseline.

Do not insert multiple gateway/runtime layers pre-emptively.

## Reachability is replaceable

Primary ChatGPT reachability/control plane is now OpenAI Secure MCP Tunnel.

Tailscale remains optional/fallback evidence only. It previously proved public HTTPS -> localhost and may still be useful for independent remote-access scenarios, but it is no longer required for the primary ChatGPT MCP route.

The existing legacy HTTPS `443`/Yandex route remains untouched until a separate cleanup decision. The temporary Funnel `8443` pilot is not part of the target architecture.

## The project-owned bridge surface should stay thin

### 1. Installer/configurator

A small Windows-facing layer may eventually:

- detect/install the supported tunnel client and local MCP runtime;
- add/remove MCP modules;
- define profiles;
- start/stop/status the bridge;
- show health/ready state;
- manage non-secret configuration;
- direct secrets to OS/runtime facilities;
- export diagnostics.

This layer is convenience, not a second orchestration engine.

### 2. Compatibility matrix

Maintain evidence of which tunnel-client/runtime/module combinations were actually tested.

Do not duplicate their implementation.

### 3. Missing local adapters

If a local program has no acceptable MCP server, implement one small typed adapter for that program only.

Examples such as REAPER, FFmpeg, Origin, Blender, CAD, browsers, local models or hardware are modules, not platform subsystems.

## What is no longer target core

The following existing repository subsystems are historical/experimental inventory pending Stage 22 classification:

- custom `agent-platform.exe` as a universal runtime;
- custom MCP transport implementation;
- custom `/gpt` ingress as target interface;
- polling relay as normal request path;
- Yandex gateway/function infrastructure;
- universal Project Binding/policy/job/artifact/confirmation layers as mandatory bridge architecture;
- media-specific capabilities as platform-defining features.

Each must become remove, extract, retain or archive/reference from evidence.

## Subscription/account constraint

The accepted environment proves that this user's actual ChatGPT account can create and invoke a custom MCP app through Secure MCP Tunnel.

That is sufficient acceptance evidence for this project. It is not a guarantee that every Plus account or future ChatGPT packaging will expose identical functionality.

The project must not silently replace ordinary ChatGPT with Work/Codex/model API usage merely to avoid account-surface uncertainty.

## Security sequencing

The accepted Stage 21 test exposed only a harmless reference tool.

Before privileged modules are enabled:

1. use restricted tunnel runtime credentials;
2. define explicit module/tool exposure profiles;
3. verify ChatGPT permission/confirmation behavior;
4. test negative/unintended access paths where appropriate;
5. document secret rotation and runtime recovery;
6. add privileged modules incrementally.

Secure transport does not eliminate the need for least-privilege tool design.

## Definition of success

The bridge is successful when the user can add/remove a local MCP module and use it from ordinary ChatGPT Chat without changing the bridge core and without requiring Work, Codex or OpenAI model API billing as the normal intelligence path.

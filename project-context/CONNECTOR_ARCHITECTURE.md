# Connector Architecture v1.5

## Purpose

The connector is a thin path from ordinary ChatGPT Chat to replaceable local MCP modules. It does not own an agent runtime, cloud relay or local-program catalog.

```text
ChatGPT Chat
  -> standard MCP app/plugin connection
  -> mature HTTPS reachability
  -> mature local MCP runtime/gateway
  -> one or more replaceable MCP servers/adapters
  -> local computer
```

See `project-context/BRIDGE_ARCHITECTURE.md` for the full product boundary.

## Boundaries

### Remote protocol

Use standard MCP. Protocol negotiation, Streamable HTTP, tool discovery and generic MCP lifecycle belong to the selected maintained MCP runtime/SDK, not to project code.

### Local runtime

The default pilot runtime is 1MCP because it already exposes a unified `/mcp`, launches stdio servers, attaches HTTP servers, filters modules and manages background runtime lifecycle.

The runtime is replaceable. ToolHive is the first fallback when stronger isolation/security/governance or newer protocol translation is required. agentgateway is a protocol/security edge candidate if needed.

### Reachability

Use mature networking products. The project does not implement NAT traversal, TLS certificates, DNS, tunnel multiplexing or public relay routing.

Tailscale Funnel is the first accepted reachability component because public HTTPS to this Windows machine has already been demonstrated.

The native MCP pilot uses a second Funnel listener:

```text
https://id182019.tailc0abda.ts.net:8443/mcp
  -> Tailscale Funnel HTTPS :8443
  -> http://127.0.0.1:3050/mcp
  -> 1MCP
```

This intentionally leaves the existing HTTPS `443` route unchanged.

### Local capabilities

A local capability is a module, not a core subsystem.

Preferred order:

1. official MCP server;
2. mature third-party MCP server;
3. generic existing adapter;
4. project-owned adapter only for a measured missing boundary.

Replacing one module must not require changes to other modules or the bridge runtime.

## First pilot

The first test exposes only the official MCP Sequential Thinking reference server through 1MCP.

Repository assets:

- `runtime/bridge-pilot/mcp.json` — pinned harmless upstream module;
- `scripts/start-chat-bridge-pilot.ps1` — starts the scoped 1MCP runtime and Funnel `8443`;
- `scripts/stop-chat-bridge-pilot.ps1` — removes only Funnel `8443` and stops only the pilot runtime scope.

Expected tool:

```text
sequential_thinking
```

Expected public MCP endpoint:

```text
https://id182019.tailc0abda.ts.net:8443/mcp
```

## Security rule

Funnel is public internet reachability. It is not authorization.

The initial pilot is temporarily unauthenticated only because its sole upstream module is intentionally non-privileged and the Funnel listener is temporary.

Before adding filesystem, shell, browser, application-control, secret-bearing or other privileged modules:

- select and test an authentication mechanism supported by the chosen MCP runtime and ChatGPT surface;
- narrow the exported server/tool set;
- verify permissions/confirmation behavior in the actual ChatGPT plugin/app UI;
- test negative cases from the public endpoint;
- only then expose the privileged profile.

## Legacy connector inventory

The following are not target v1.5 request paths:

- Yandex Function/API Gateway;
- custom polling relay;
- custom `/gpt` ingress;
- project-owned MCP transport/server implementation.

They remain in the repository temporarily because they are working historical evidence and rollback material. Do not expand them.

## Acceptance ladder

```text
1MCP + Funnel + ChatGPT works
  -> adopt as default runtime path

1MCP works locally but ChatGPT edge fails
  -> identify protocol/auth/account-policy cause
  -> test ToolHive / agentgateway where relevant

mature alternatives fail for the same concrete reason
  -> implement only the smallest compatibility adapter
```

No custom protocol code is allowed merely because existing code already exists.

## Native-MCP acceptance

A real direct connector is accepted only after ordinary ChatGPT Chat:

1. scans/connects the public `/mcp` endpoint;
2. discovers the expected harmless tool;
3. invokes that tool;
4. receives the result through the same direct path.

Only after this gate should the project begin migrating real local-program modules to the new bridge.

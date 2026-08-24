# Semantic Frozen-Action Compatibility

Status: **CURRENT MIGRATION COMPATIBILITY / CANONICAL PUBLIC INVENTORY = SIX TOOLS**.

## Why this exists

PR #97 physically proved that an existing ordinary-Chat app snapshot could remain frozen on historical Stage 24 1MCP-qualified action IDs even after a UI Refresh:

```text
semantic-projection_1mcp_workspace_read
semantic-projection_1mcp_workspace_write
semantic-projection_1mcp_web_open
semantic-projection_1mcp_web_observe
semantic-projection_1mcp_web_interact
```

The direct semantic runtime already published canonical semantic names, so those frozen identifiers originally failed with JSON-RPC `Tool ... not found` before PR #97 added a narrow inbound rewrite.

That historical physical evidence is scoped to those five Stage 24 IDs. It must not be generalized into a claim that every later compatibility alias has already been physically observed from ChatGPT.

## Current canonical public inventory

The normal Stage 26.3A semantic runtime publishes exactly six canonical tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

The live MCP server is `chat-semantic-control-plane`. The launcher verifies this exact six-tool inventory before starting the working child. Legacy aliases are not published in `tools/list` and do not change the public tool count.

## Current inbound compatibility allowlist

The launcher currently accepts two exact frozen-name families and rewrites them to the six canonical names only after an inbound MCP `tools/call` reaches the launcher.

Historical semantic-projection family:

```text
semantic-projection_1mcp_workspace_read        -> workspace_read
semantic-projection_1mcp_workspace_write       -> workspace_write
semantic-projection_1mcp_web_open              -> web_open
semantic-projection_1mcp_web_observe           -> web_observe
semantic-projection_1mcp_web_interact          -> web_interact
semantic-projection_1mcp_procedure_run         -> procedure_run
```

Temporary Stage 26.3A procedure-qualification family:

```text
procedure-qualification-projection_1mcp_workspace_read  -> workspace_read
procedure-qualification-projection_1mcp_workspace_write -> workspace_write
procedure-qualification-projection_1mcp_web_open        -> web_open
procedure-qualification-projection_1mcp_web_observe     -> web_observe
procedure-qualification-projection_1mcp_web_interact    -> web_interact
procedure-qualification-projection_1mcp_procedure_run   -> procedure_run
```

Only the first five `semantic-projection_1mcp_*` mappings have the PR #97 physical ordinary-Chat evidence. The `procedure_run` aliases and the former procedure-qualification family are bounded Stage 26.3A migration compatibility for app snapshots created while the public surface was changing; they are not additional public tools or an alternative runtime mode.

The compatibility implementation must remain an exact lookup table. It must not strip arbitrary prefixes, dispatch arbitrary names, expose a generic invocation tool, or reintroduce 1MCP into the normal direct-stdio transport.

## Critical ChatGPT frozen-snapshot boundary

The launcher compatibility layer operates **after** ChatGPT has already selected an action, resolved its frozen tool definition and permissions, and emitted an MCP `tools/call` request.

Therefore the launcher can repair a stale inbound tool **name**, but it cannot repair ChatGPT-side state that fails earlier in the request lifecycle. In particular, it cannot update or authorize:

- ChatGPT's frozen snapshot of available tools and input schemas;
- the app/connector connection state;
- per-action permission or confirmation state;
- whether a newly added or changed action is enabled in the ChatGPT app snapshot;
- a reconnect/re-add flow that interrupts the current conversation stream before `tools/call` is sent.

This distinction is release-critical. A successful old frozen-name call proves only that the inbound alias reached the canonical runtime; it does not prove that the current ChatGPT app snapshot is synchronized with the six-tool server.

OpenAI documents that MCP app tool/action definitions are frozen on approval and are not automatically updated; a live definition that no longer matches that snapshot can cause tool-call errors until the app actions are refreshed/reviewed or the app is recreated/rebound as required by the product surface.

## 2026-08-24 Stage 26.3A physical observation

The normal six-tool local route was physically READY on exact candidate head `300db9956dfbdf0300ecc59f017d6f3280d4353a` with:

```text
runtime_ready=true
mcp_ready=true
tunnel_ready=true
active_profile=semantic
active_count=1
conflict=false
tunnel_binding=direct-stdio
```

A subsequent ordinary-Chat attempt successfully read the fresh Stage 26.3A challenge through `workspace_read`, then reached the ChatGPT confirmation UI for `workspace_write`. During that approval path ChatGPT transitioned into a `Connect / Add Chat Local Bridge Test` flow and the current message ended with a stream error.

Because the challenge read already reached the live semantic runtime and the local route had just passed the physical READY gate, this observation is classified as **unaccepted ChatGPT app snapshot/connection/permission-session evidence**, not as evidence that the local semantic runtime crashed. The final Stage 26.3A E2E must not be accepted from this interrupted run.

## App rebind gate before final Stage 26.3A E2E

The next final ordinary-Chat acceptance must use a deliberately synchronized app binding rather than relying on a long-lived historical snapshot.

Before starting the long autonomous task:

1. complete any ChatGPT `Connect / Add` flow outside an active tool call;
2. ensure the app is rebound/refreshed against the current Secure MCP Tunnel endpoint;
3. ensure the current app snapshot recognizes the six canonical actions, including `procedure_run`;
4. settle the intended write/modify permission policy before the long task begins, so the acceptance run is not also a permission-configuration transaction;
5. start a fresh ordinary ChatGPT conversation and run the long E2E without reconnecting or changing app permissions mid-run.

A UI Refresh alone is not sufficient migration evidence because PR #97 already proved that Refresh may leave historical action IDs frozen. A newly created or explicitly rebound app is stronger evidence.

## Historical PR #97 evidence

PR #97 accepted the migration compatibility for the five Stage 24 file/browser IDs on its own exact physical head. The ordinary-Chat evidence included:

```text
workspace_read(input.txt)
=> application-level Filesystem ENOENT rather than Tool-not-found

web_open(https://example.com)
=> success

web_observe
=> Example Domain
```

The prior routing failure `Tool semantic-projection_1mcp_* not found` was absent. That result remains valid for the exact historical scope it tested.

## Removal gate

Frozen aliases may be removed only after a separate ordinary-Chat migration test proves that a newly created or explicitly rebound ChatGPT app invokes canonical names and remains stable across read, write, browser and `procedure_run` calls.

Until that gate passes, retaining the exact allowlist is safer than breaking existing app snapshots during runtime upgrades. The aliases are migration compatibility, not the permanent product contract.

## Performance scope

The compatibility operation is a fixed exact-name lookup/rewrite before the canonical MCP call. It is not expected to be a material latency contributor compared with tunnel, browser, filesystem, grounding or model work.

Removal is governed by verified app migration and contract cleanliness, not performance.

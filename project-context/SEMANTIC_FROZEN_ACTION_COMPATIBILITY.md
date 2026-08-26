# Semantic Frozen-Action Compatibility

Status: **CURRENT MIGRATION COMPATIBILITY / CANONICAL PUBLIC INVENTORY = SIX TOOLS / APP REBIND GATE PASSED FOR STAGE 26.3A**.

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

The accepted Stage 26.3A normal semantic runtime publishes exactly six canonical tools:

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
semantic-projection_1mcp_web_observe            -> web_observe
semantic-projection_1mcp_web_interact           -> web_interact
semantic-projection_1mcp_procedure_run          -> procedure_run
```

Former Stage 26.3A procedure-qualification family:

```text
procedure-qualification-projection_1mcp_workspace_read  -> workspace_read
procedure-qualification-projection_1mcp_workspace_write -> workspace_write
procedure-qualification-projection_1mcp_web_open        -> web_open
procedure-qualification-projection_1mcp_web_observe     -> web_observe
procedure-qualification-projection_1mcp_web_interact    -> web_interact
procedure-qualification-projection_1mcp_procedure_run   -> procedure_run
```

Only the first five `semantic-projection_1mcp_*` mappings have the PR #97 physical ordinary-Chat evidence. The `procedure_run` aliases and the former procedure-qualification family remain bounded migration compatibility for app snapshots created while the public surface was changing; they are not additional public tools or an alternative runtime mode.

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

## 2026-08-26 PR #111 schema-evolution observation

The first target-Windows ordinary-Chat physical gate for PR #111 produced a second concrete frozen-snapshot failure mode on exact runtime head `1521e3128a7694be43518c3ee0188cb79f0ca0f5`.

The installed/public six-tool server on that exact head already declared `web_interact.expected` in the canonical Zod/MCP schema and the backend required that bounded ExpectedEffect for `click` / `type+submit`. However, the existing `Chat Local Bridge Test` app snapshot rejected `expected` before the call reached MCP with:

```text
Additional properties are not allowed ('expected' was unexpected)
```

Physical evidence on the same run showed:

```text
type without submit                    PASS
click without expected                 refused before delivery
click with expected                    blocked by frozen ChatGPT schema
positive checkbox expected-effect path not reachable
post-delivery wrong-expected path      not reachable
ambiguity path requiring expected      not reachable as specified
```

This is not evidence that the exact-head runtime omitted the field. It is evidence that **input-schema evolution on an existing canonical tool name is not automatically delivered into an already-bound ChatGPT app snapshot**.

Operational consequence for development/qualification:

1. after a public tool input-schema change, reconnect/re-add/rebind the ChatGPT app outside an active tool call;
2. start a fresh ordinary Chat conversation after the rebind;
3. keep connection/permission state fixed during the physical gate;
4. prove the new field is actually accepted from ordinary Chat before interpreting later gate failures as runtime failures.

A UI Refresh alone remains insufficient evidence because frozen action definitions have previously survived Refresh.

Product consequence: do not assume in-place public schema changes are migration-safe merely because the live MCP server and hosted six-tool tests are correct. Stable releases need either a proven app-schema migration/rebind flow or a separately reviewed versioning/evolution rule for public tool schemas.

## 2026-08-24 interrupted app-session observation

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

An ordinary-Chat attempt successfully read the fresh Stage 26.3A challenge through `workspace_read`, then reached ChatGPT confirmation UI for `workspace_write`. During that approval path ChatGPT transitioned into a `Connect / Add Chat Local Bridge Test` flow and the current message ended with a stream error.

Because the challenge read had already reached the live semantic runtime and the local route had just passed the physical READY gate, this was classified as **ChatGPT app snapshot/connection/permission-session evidence**, not as evidence that the local semantic runtime crashed.

## Accepted Stage 26.3A app rebind evidence

The interrupted run was not accepted. The app/session state was stabilized first:

1. `Chat Local Bridge Test` was reconnected outside an active tool call;
2. app-specific permission was set to `Allow all actions` before the long run;
3. a fresh ordinary ChatGPT conversation was started;
4. connection and permission policy were not changed during the task.

The resulting long-horizon Stage 26.3A ordinary-Chat E2E completed successfully across all six semantic capabilities, including real `workspace_write`, repeated `web_interact`, `procedure_run` completion, independent final read, a second `procedure_run` structured ABSTAIN and independent zero-overwrite verification.

This proves that a deliberately synchronized/rebound app session can execute the accepted six-tool Stage 26.3A workflow. It does **not** prove that ChatGPT sent canonical names rather than one of the exact inbound compatibility aliases, because the user-visible result does not expose the action id used by ChatGPT for every call.

Operational rule: complete app reconnect/review and settle permission policy **before** a long autonomous task. Do not make app-binding or permission changes mid-run.

A UI Refresh alone remains weaker migration evidence because PR #97 showed that Refresh may leave historical action IDs frozen.

## Historical PR #97 evidence

PR #97 accepted migration compatibility for the five Stage 24 file/browser IDs on its own exact physical head. The ordinary-Chat evidence included:

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

Frozen aliases may be removed only after a separate ordinary-Chat migration test proves that a newly created or explicitly rebound ChatGPT app actually invokes canonical names and remains stable across read, write, browser and `procedure_run` calls.

The successful Stage 26.3A rebind run is strong connection/session evidence, but it does not expose enough per-call action-id telemetry to satisfy this alias-removal gate by itself.

Until that gate passes, retaining the exact allowlist is safer than breaking existing app snapshots during runtime upgrades. The aliases are migration compatibility, not the permanent product contract.

## Performance scope

The compatibility operation is a fixed exact-name lookup/rewrite before the canonical MCP call. It is not expected to be a material latency contributor compared with tunnel, browser, filesystem, grounding or model work.

Removal is governed by verified app migration and contract cleanliness, not performance.
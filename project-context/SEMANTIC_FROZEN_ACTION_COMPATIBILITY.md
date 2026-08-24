# Semantic Frozen-Action Compatibility

Status: **PHYSICAL E2E ACCEPTED MIGRATION COMPATIBILITY / CURRENT CANONICAL CANDIDATE INVENTORY = SIX TOOLS**.

## Why this exists

A previously accepted ordinary-Chat app snapshot continued to invoke five historical Stage 24 1MCP-qualified action IDs even after Refresh:

```text
semantic-projection_1mcp_workspace_read
semantic-projection_1mcp_workspace_write
semantic-projection_1mcp_web_open
semantic-projection_1mcp_web_observe
semantic-projection_1mcp_web_interact
```

The direct semantic runtime originally rejected those frozen names with JSON-RPC `Tool ... not found` even though the corresponding canonical semantics were available.

PR #97 therefore introduced a narrow inbound compatibility rewrite for exactly those five historical IDs.

## Compatibility rule

The compatibility layer rewrites **only** those five exact frozen action IDs to their canonical equivalents on inbound `tools/call` requests.

It does not:

- publish the legacy aliases in `tools/list`;
- strip arbitrary prefixes;
- add a generic invocation tool;
- dispatch arbitrary tool names;
- reintroduce 1MCP into the normal direct semantic transport;
- create a five-tool public mode;
- alias or emulate `procedure_run`.

## Current Stage 26.3A candidate inventory

The current normal semantic candidate publishes exactly six canonical tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

The five frozen `_1mcp_` aliases exist only as inbound migration compatibility for old app snapshots. They are not part of `tools/list` and do not determine the current public tool count.

`procedure_run` is new to the Stage 26.3A candidate and has no frozen Stage 24 alias.

## Historical physical evidence

PR #97 physical acceptance remains valid for the exact historical code/head and scope it tested. It proved that old frozen ChatGPT action IDs could reach the canonical file/browser implementations without restoring raw 1MCP routing.

At that time the canonical public inventory was five tools. That historical count is evidence about the accepted migration fix at that exact point in development; it is **not** the current Stage 26.3A candidate contract.

The accepted ordinary-Chat evidence included:

```text
workspace_read(input.txt)
=> application-level Filesystem ENOENT rather than Tool-not-found

web_open(https://example.com)
=> success

web_observe
=> Example Domain
```

The prior routing failure:

```text
Tool semantic-projection_1mcp_* not found
```

was not observed.

## Current architectural scope

The normal public route remains direct stdio through the Secure MCP Tunnel and canonical semantic launcher.

For Stage 26.3A the launcher always reaches the canonical six-tool projection. The frozen compatibility table is merely an inbound name-rewrite boundary for five old file/browser aliases.

There is no runtime choice such as:

```text
legacy five-tool mode
vs
six-tool procedure mode
```

The old aliases and current six-tool inventory solve different problems and must not be conflated.

## Removal gate

The five frozen aliases may be removed only after a separate ordinary-Chat migration test proves that a newly created or explicitly rebound ChatGPT app no longer invokes any of the old `_1mcp_` IDs.

A UI Refresh alone is not sufficient evidence because prior target testing showed Refresh did not clear the stale identifiers.

Until that removal gate passes, keeping the exact allowlist is safer than breaking existing connected app snapshots during runtime upgrades.

## Performance scope

The compatibility operation is a fixed lookup/rewrite across five exact historical strings before the canonical MCP call. It is not expected to be a material latency contributor compared with tunnel, browser, filesystem, grounding or model work.

Removal is governed by verified app migration and contract cleanliness, not performance.

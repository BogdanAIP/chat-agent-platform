# Stage 24 — Semantic Typed Capability Projection

Status: **LOCAL/CI ACCEPTED; ordinary-Chat promotion pending**.

## Why this boundary exists

Real ordinary-Chat evidence established two simultaneous constraints:

1. concrete typed Filesystem + Playwright actions work through one Chat app;
2. a large direct action inventory is effectively truncated in the tested Chat app, while the app also keeps a frozen reviewed tool snapshot until Refresh/review.

1MCP tags/presets/filtering can select whole backend servers locally, but they do not create a new small fixed semantic schema set for an already-reviewed Chat app. The generic adaptive `tool_invoke` path is not the accepted product surface.

A smallest project-owned projection is therefore accepted as a measured compatibility adapter. It must remain deterministic and non-agentic.

## Non-goals

The projection is **not**:

- a planner or autonomous coordinator;
- a workflow engine;
- a generic MCP gateway replacement;
- a dynamic server/tool registry;
- an arbitrary `server + tool + args` dispatcher;
- a place to hide mixed consequence classes behind misleading annotations.

ChatGPT remains the planner. 1MCP and downstream MCPs remain replaceable infrastructure.

## Accepted Chat-facing surface

Exactly five semantic tools are in the Stage 24 candidate surface:

| Tool | Effect class | Closed downstream mapping |
|---|---|---|
| `workspace_read` | read-only, closed-world | `list_allowed_directories`, `read_text_file`, `search_files` |
| `workspace_write` | local write/overwrite | `write_file` |
| `web_open` | browser navigation, open-world | `browser_navigate` |
| `web_observe` | read-only browser observation | `browser_find`, `browser_snapshot` |
| `web_interact` | browser interaction, open-world | `browser_click`, `browser_type` |

No Chat-facing argument can select an arbitrary MCP server or arbitrary backend tool.

## Workspace boundary

`CHAT_LOCAL_FILES_ROOT` is mandatory. Chat-facing workspace paths are relative to that root.

The projection rejects:

- absolute paths;
- `..` traversal that escapes the configured root.

The official Filesystem MCP remains a second enforcement layer and receives only the resolved path plus the fixed allowlisted operation.

`workspace_read` supports only:

- `roots`;
- `read_text`;
- `search`.

`workspace_write` initially supports only create/overwrite text through Filesystem `write_file`.

## Browser boundary

The downstream Browser is exact `@playwright/mcp@0.0.78` in isolated/headless Chrome mode.

`web_open` accepts only HTTP/HTTPS URLs and rejects embedded URL credentials.

`web_observe` supports only:

- `find` by plain text or regex;
- accessibility `snapshot`.

`web_interact` supports only:

- `click`;
- `type`.

The projection does not expose or call arbitrary JavaScript/Playwright execution, file upload, direct network-body access, raw backend tool selection or catalog mutation.

## Implementation rule

The local adapter boundary is pinned to:

- `@modelcontextprotocol/server@2.0.0`;
- `@modelcontextprotocol/client@2.0.0`;
- `@modelcontextprotocol/server-filesystem@2026.7.10`;
- `@playwright/mcp@0.0.78`;
- `zod@4.4.3`.

The projection is a normal stdio MCP server. It lazily creates official `StdioClientTransport` clients for exact pinned downstream MCPs and verifies that every required allowlisted downstream tool exists before using that backend.

Downstream packages are installed once as exact dependencies of `runtime/semantic-projection`; user tool calls do not perform nested `npx` installs. 1MCP launches the prepared projection entrypoint directly with Node.

Closing the projection client must close its downstream MCP clients/processes.

## Accepted local/CI evidence

On functional head `aa6bc034c1ecb36af469ecf78959a243526e2af3`, all six PR workflows passed, including Semantic Projection Acceptance run `31809532437` and Chat Profile Acceptance run `31809532439`.

The semantic acceptance proves:

1. exactly five Chat-facing tools;
2. real Filesystem roots/read/search/write;
3. relative-path and traversal rejection;
4. real Playwright navigate/find/click/type/snapshot;
5. non-HTTP URL rejection;
6. no raw/generic tool leakage;
7. clean stdio/downstream lifecycle;
8. real 1MCP `semantic` Runtime Scope start -> ready -> exact five-tool inventory -> stop;
9. the same semantic runtime from a standalone installed-layout copy outside the source checkout;
10. public manager recognition of `semantic` with persisted `FilesRoot`, while direct/adaptive/single-owner regressions remain green.

The installed layout contains the projection source/config and installs/verifies its exact dependencies inside the installed runtime. It does not copy checkout `node_modules`.

## Remaining promotion gate

The projection is not yet Stage-24 product-accepted until **real ordinary Chat** proves the refreshed custom app exposes and can use the stable five-tool surface through the normal Secure MCP Tunnel path.

The required ordinary-Chat gate must demonstrate a useful multi-backend workflow using semantic tools such as `workspace_read` + `web_open`/`web_observe`/`web_interact` + `workspace_write`, without raw backend tools, generic `tool_invoke`, one app per backend or routine per-operation Refresh.

If that gate passes and the exact final functional head remains green with synchronized docs, Stage 24 can be accepted and merged to `main`.

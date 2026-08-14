# Stage 24 — Semantic Typed Capability Projection

Status: **EXPERIMENTAL / acceptance in progress**.

## Why this boundary exists

Real ordinary-Chat evidence established two simultaneous constraints:

1. concrete typed Filesystem + Playwright actions work through one Chat app;
2. a large direct action inventory is effectively truncated in the tested Chat app, while the app also keeps a frozen reviewed tool snapshot until Refresh/review.

1MCP tags/presets/filtering can select whole backend servers locally, but they do not create a new small fixed semantic schema set for an already-reviewed Chat app. The generic adaptive `tool_invoke` path is not the accepted product surface.

A smallest project-owned projection is therefore allowed as a measured compatibility adapter. It must remain deterministic and non-agentic.

## Non-goals

The projection is **not**:

- a planner or autonomous coordinator;
- a workflow engine;
- a generic MCP gateway replacement;
- a dynamic server/tool registry;
- an arbitrary `server + tool + args` dispatcher;
- a place to hide mixed consequence classes behind misleading annotations.

ChatGPT remains the planner. 1MCP and downstream MCPs remain replaceable infrastructure.

## Initial Chat-facing surface

Exactly five semantic tools are evaluated initially:

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

Use the official MCP TypeScript v2 split packages as the local adapter boundary:

- `@modelcontextprotocol/server@2.0.0`;
- `@modelcontextprotocol/client@2.0.0`;
- `zod@4.4.3`.

The projection is itself a normal stdio MCP server. It lazily creates official `StdioClientTransport` clients for exact pinned downstream MCPs and verifies that every required allowlisted downstream tool exists before using that backend.

Closing the projection client must close its downstream MCP clients/processes.

## Acceptance gate before manager/profile integration

The isolated projection must first pass a real Windows acceptance proving:

1. exactly five Chat-facing tools and truthful annotations;
2. no raw/generic tool leakage;
3. scoped workspace roots/read/search/write;
4. relative-path/traversal rejection;
5. local HTTP browser navigate/find/click/type/snapshot;
6. non-HTTP browser URL rejection;
7. clean stdio client/server lifecycle.

Only after this isolated adapter passes should it be integrated as a new 1MCP Chat profile and installed manager capability.

## Promotion gate

Even after local/CI acceptance, the projection remains experimental until ordinary Chat proves the stable five-tool surface can complete a real multi-backend workflow without raw backend tools, generic `tool_invoke`, one app per backend or routine per-operation Refresh.

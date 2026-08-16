# Current State

Last synchronized functional head: `aa6bc034c1ecb36af469ecf78959a243526e2af3` on 2026-08-14. On that exact functional head all six PR workflows passed: Chat Profile Acceptance `31809532439`, Semantic Projection Acceptance `31809532437`, CI `31809532435`, CodeQL Security `31809532455`, Module Candidate Acceptance `31809532466` and Secret History Scan `31809532482`. Later documentation-only commits do not imply additional runtime acceptance. Always check the current PR HEAD and workflows.

## Accepted bridge

Stage 21 is complete. On 2026-08-10 ordinary ChatGPT successfully completed:

```text
ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> 1MCP
  -> Sequential Thinking
  -> result back to ChatGPT
```

Ordinary Chat remains the primary intelligence surface. Codex/Work may accelerate development but are not required product runtime components.

## Accepted direct and typed ordinary-Chat evidence

Stage 23 accepted on Windows through pinned `@1mcp/agent@0.34.4`:

- Filesystem `2026.7.10`: scoped root and real read call;
- Playwright MCP `0.0.78`: isolated/headless browser, navigation/content/close.

Stage 24 real-machine evidence includes:

- standalone bootstrap, official tunnel-client verification, DPAPI runtime-key storage and no-console tray behavior;
- direct `files-readonly` ordinary-Chat E2E returned `CHAT_LOCAL_FILES_E2E_OK`;
- fresh-snapshot direct typed Browser E2E: `browser_navigate(https://example.com)` returned `Example Domain`;
- combined typed Filesystem + Playwright ordinary-Chat E2E in one conversation: scoped `list_allowed_directories`, `read_text_file`, `write_file`, `browser_navigate`, `browser_find`, `browser_click` all executed and the browser reached IANA `Example Domains`;
- isolated write-permission test: app mode `Allow read actions` produced a real one-time approval card for `write_file`;
- full-access control: typed `read_text_file`, `browser_navigate` and `write_file` each passed sequentially without approval.

## Chat action-snapshot findings

Changing the local direct profile does not automatically replace an already-scanned Chat action snapshot. Refresh/new Chat was required to see the new typed Browser surface.

A scaling experiment exposed 14 Filesystem + 20 Playwright tools locally (34 total). The Chat-facing app effectively surfaced 20: all 14 Filesystem plus the first 6 Playwright actions, which excluded later `browser_navigate` and `browser_click`.

After reducing Filesystem to 4 typed actions, local inventory was 24 total. A refreshed/new Chat then successfully called the needed Filesystem and Browser actions, including `browser_navigate` and `browser_click`.

Conclusion: the tested app showed an **effective action-snapshot truncation around 20 actions**. This is measured product behavior, not an officially documented universal OpenAI limit. Stage 24 must not hard-code 20 as a guaranteed platform constant.

Official OpenAI documentation also confirms that ChatGPT MCP app tool definitions use a frozen reviewed snapshot and later server-side tool changes are not automatically enabled. Therefore 1MCP tags/presets/runtime filtering are useful local mechanisms but do not by themselves solve ordinary-Chat tool-surface scaling without Refresh.

## Generic adaptive contract — runtime accepted, product surface not promoted

`runtime/chat-profiles/adaptive/mcp.json` registers Filesystem + Playwright as a pre-approved disabled catalog. Direct profiles remain on `@1mcp/agent@0.34.4`; adaptive pins `@1mcp/agent@0.35.0-beta.3`, Lazy Loading ON and Async Loading OFF through the hash-guarded `runtime/1mcp-adaptive-shim` compatibility package.

The runtime/lifecycle implementation is real and green locally/remotely: enable -> lazy discovery -> real invocation -> disable -> capability removal -> process cleanup works for Filesystem and Playwright.

However, the real ordinary-Chat generic-surface test did **not** promote this contract. The exact eight generic/lifecycle actions were visible, and read-only list/status/discovery calls reached MCP, but lifecycle calls plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

Do not claim a proven single cause for that pre-MCP block. Keep adaptive as useful diagnostic/CI lifecycle infrastructure, not the primary Chat-facing product contract.

## Semantic typed capability projection — local/CI accepted

Stage 24 now has a concrete five-tool semantic compatibility boundary:

| Tool | Closed mapping |
|---|---|
| `workspace_read` | roots / read_text / search |
| `workspace_write` | write_file |
| `web_open` | browser_navigate |
| `web_observe` | browser_find / browser_snapshot |
| `web_interact` | browser_click / browser_type |

The projection is deterministic and non-agentic. No Chat-facing argument can select an arbitrary MCP server or arbitrary downstream tool.

Workspace paths are relative to mandatory `CHAT_LOCAL_FILES_ROOT`; absolute paths and traversal outside the root are rejected. Browser navigation is restricted to HTTP/HTTPS without embedded credentials. Raw evaluate/run-code, file upload, direct network-body tools, arbitrary backend selection and catalog mutation are not exposed.

Pinned runtime dependencies are:

- `@modelcontextprotocol/server@2.0.0`;
- `@modelcontextprotocol/client@2.0.0`;
- `@modelcontextprotocol/server-filesystem@2026.7.10`;
- `@playwright/mcp@0.0.78`;
- `zod@4.4.3`.

The projection no longer performs nested `npx` installs on first user action. Its exact dependencies are prepared once in `runtime/semantic-projection`, and 1MCP launches the prepared entrypoint directly with Node.

On functional head `aa6bc034...`, Semantic Projection Acceptance proved:

- exactly five projection tools;
- real Filesystem root/read/search/write;
- path-negative cases;
- real Playwright navigate/find/click/type/snapshot;
- URL-negative cases;
- clean downstream lifecycle;
- real `semantic` 1MCP Runtime Scope start -> ready -> exact five-tool inventory -> stop;
- the same runtime from a standalone installed-layout copy outside the repository checkout.

Chat Profile Acceptance on the same head additionally proved the public manager understands `semantic`, persists `FilesRoot`, sees the ready Runtime Scope and can stop/reset it, while direct/adaptive regressions stay green.

Therefore the semantic projection is **locally/CI accepted but not yet ordinary-Chat product-promoted**.

## Composite workflow safety finding

With `Chat Local Bridge Test` set to `Allow all actions`, one long request combining local file read -> browser work -> local result write was blocked by OpenAI safety after the first harmless call. The relevant typed read, browser navigation and write actions then passed when requested separately.

Therefore:

- app permission mode is not the only OpenAI safety layer;
- a composite safety block is not sufficient evidence that a local typed tool/backend is broken;
- architecture should use truthful typed actions, scoped resources and reversible operations rather than depending on permission mode alone.

## Windows single-owner lifecycle — accepted for the measured split-brain defect

A real target-machine defect was found: an installed runtime under `%LOCALAPPDATA%\ChatAgentPlatform\app` could remain on `127.0.0.1:3050` while the source checkout reported its own known profiles stopped. A new source runtime could then read the stale runtime's health endpoint.

The public manager now uses shared `%LOCALAPPDATA%\ChatAgentPlatform\state\manager-owner.json` ownership state. Installed and source copies delegate status to the real owner, stop a foreign owner before takeover and fail closed when `3050` is occupied without trustworthy ownership.

Target Windows acceptance proved installed/source takeover in both directions, cross-copy status, delegated stop/cleanup, exactly one listener on `3050` and fail-closed rejection of an unrelated listener. Automated Windows CI also covers the foreign-listener negative path.

The measured installed/source split-brain blocker is closed.

## Current Stage 24 architecture

```text
ordinary ChatGPT
  -> five stable semantic typed actions
  -> deterministic capability projection
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP / focused adapters
  -> replaceable task-active backends
```

Do not return to one Chat app per backend. Do not promote an opaque generic `tool_invoke` solely to avoid action-count pressure. The semantic projection must remain a compatibility boundary, not a planner, workflow engine or second generic MCP platform.

Direct profiles remain diagnostics/fallback. Adaptive remains lifecycle/CI infrastructure.

## Safety model

Use three separate concepts:

```text
AVAILABLE
ACTIVE
AUTHORIZED
```

A backend can be registered without running. Start only what the task needs. Multiple backends may be active simultaneously if the workflow actually requires them. Prefer scoped roots, reversible workspaces, backups/git and consequence-based authorization over asking the user to approve every low-risk tool call.

## Remaining Stage 24 gates

1. update the target-machine installed bundle to the accepted semantic implementation and run `semantic` through the normal public manager + Secure MCP Tunnel path;
2. Refresh/Scan the existing `Chat Local Bridge Test` app and confirm ordinary Chat sees the exact five semantic actions;
3. ordinary Chat completes a useful multi-backend semantic workflow without raw backend tools, generic `tool_invoke`, one app per backend or routine per-operation Refresh;
4. synchronize final docs/PR evidence to the exact final functional head and ensure all CI/security/acceptance checks are green;
5. only then accept Stage 24 and integrate/merge to `main`.

## Work after Stage 24

Stage 25 should establish the local specialist inference runtime and first `local-vision` backend, beginning with LM Studio/`llmster` evaluation and LFM2.5-VL-3B benchmarking.

Stage 26 should benchmark professional application backends (REAPER, Origin, FFmpeg, Blender, Windows UI fallback) through the stable bridge/capability boundary.

Stage 27 should harden distribution, updates, repair, rollback and release packaging.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`. Historical Yandex/Tailscale paths are not active product dependencies.

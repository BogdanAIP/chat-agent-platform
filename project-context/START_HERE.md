# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## What the project is

`chat-agent-platform` is a thin bridge from ordinary ChatGPT Chat to local Windows capabilities through standard MCP. ChatGPT remains the planner/intelligence. The repository owns integration, lifecycle, deterministic compatibility adapters, configuration and acceptance logic, not a second AI agent platform.

Accepted reachability path:

```text
ordinary ChatGPT Chat
  -> ChatGPT custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> local 1MCP
  -> focused semantic adapter / replaceable MCP backends
  -> local files/programs/devices
```

## Current work

- active stage: **Stage 24**;
- active PR: **#66 — Stage 24: standalone Windows bootstrap and lifecycle manager**;
- active development branch: `chat/stage24-local-controller`;
- latest accepted functional head: `aa6bc034c1ecb36af469ecf78959a243526e2af3`;
- on that exact functional head all six PR workflows passed: Chat Profile Acceptance `31809532439`, Semantic Projection Acceptance `31809532437`, CI `31809532435`, CodeQL Security `31809532455`, Module Candidate Acceptance `31809532466` and Secret History Scan `31809532482`;
- on 2026-08-16 the installed target-machine bundle carrying that unchanged semantic runtime also passed the remaining real ordinary-Chat semantic promotion gate through the normal manager + Secure MCP Tunnel path.

Later documentation-only commits do not imply additional runtime acceptance. Always re-check the current PR HEAD and workflows before editing or reporting final status.

## What is already accepted

- ordinary ChatGPT -> Secure MCP Tunnel -> official tunnel-client -> 1MCP -> Sequential Thinking round trip passed on 2026-08-10;
- standalone Windows bootstrap/manager and no-console tray behavior passed on the target Windows machine;
- direct `files-readonly` ordinary-Chat E2E passed;
- direct typed `browser_navigate` ordinary-Chat E2E passed after refreshing/scanning the app in a new Chat;
- one ordinary-Chat session successfully used typed Filesystem and Playwright actions together through the same `Chat Local Bridge Test` app: scoped file read/write plus browser navigate/find/click;
- app permission mechanics were measured separately: `Allow read actions` produced a one-time approval card for isolated write; `Allow all actions` allowed sequential typed read/navigate/write without confirmation;
- installed/source manager ownership passes target-machine handoff/status/stop acceptance and fail-closed handling for an unrelated listener on fixed port `3050`;
- the fixed five-tool semantic projection passes real Filesystem + Playwright acceptance, real 1MCP profile lifecycle, public-manager recognition and standalone installed-layout execution outside the source checkout;
- the same five-tool semantic projection is now **ordinary-Chat product accepted**: in one real Chat session `workspace_read` returned `SEMANTIC_FINAL_INPUT_20260816`, browser semantic tools navigated from `example.com` through the observed `Learn more` link to IANA `Example Domains`, `workspace_write` created `result.txt`, and `workspace_read` verified the exact two-line result.

## What Stage 24 discovered

### 1. Chat action snapshots are frozen until reviewed/refreshed

Switching the local direct profile did not automatically replace an already-scanned Chat action snapshot. A fresh scan/new Chat was required to see the changed typed surface.

Current OpenAI documentation likewise describes ChatGPT MCP app tools as a frozen reviewed snapshot: later MCP tool changes are not automatically enabled. Therefore local 1MCP filtering/presets alone cannot make an already-scanned ordinary-Chat app dynamically acquire new typed tools.

During the final semantic promotion on 2026-08-16, Refresh/Create initially failed in the Chat UI while the local manager, MCP and tunnel were healthy. After the Chat app/plugin itself updated, the existing `Chat Local Bridge Test` refreshed successfully and the semantic E2E passed without changing the accepted runtime. Treat that incident as transient Chat-side compatibility evidence, not as proof of a local semantic-runtime defect.

### 2. The generic adaptive meta-tool contract is not the product surface

The adaptive runtime itself passes local/CI lifecycle tests through the hash-guarded `@1mcp/agent@0.35.0-beta.3` compatibility package. But the real ordinary-Chat test saw the eight generic/lifecycle actions and only read-only list/status/discovery calls reached the bridge. Lifecycle calls plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

Do **not** claim that one specific annotation or OpenAI rule caused the block; the exact product-admission cause was not isolated. Do not relabel the generic dispatcher as harmless merely to bypass review.

Adaptive remains lifecycle/CI diagnostic infrastructure, not the promoted Chat-facing contract.

### 3. Concrete typed multi-backend actions work, but large surfaces create pressure

A combined local runtime exposed 14 Filesystem + 20 Playwright actions. The tested Chat-facing app effectively surfaced 20 actions and omitted later Playwright actions such as `browser_navigate`/`browser_click`.

After reducing Filesystem to 4 typed actions while keeping Playwright, local inventory was 24 tools; after Refresh/new Chat, ordinary Chat could use the required Filesystem and Browser actions successfully in one conversation.

This is evidence of an **effective ~20-action snapshot truncation in the tested app configuration**, not an officially documented universal OpenAI limit. Do not hard-code 20 as a platform constant.

### 4. The measured scaling mechanism is the accepted fixed semantic projection

Stage 24 has a concrete deterministic compatibility boundary:

```text
ordinary ChatGPT
  -> workspace_read
  -> workspace_write
  -> web_open
  -> web_observe
  -> web_interact
  -> deterministic closed mappings
  -> Filesystem / Playwright MCP
```

The projection is not a planner, registry, workflow engine or renamed arbitrary dispatcher. Chat-facing arguments cannot select an arbitrary MCP server or arbitrary downstream tool.

The five-tool surface is locally/CI accepted **and** real ordinary-Chat accepted on the target machine.

### 5. OpenAI safety is context-sensitive beyond app permission mode

One long combined instruction (`local file -> browser -> write result`) was blocked by OpenAI safety after the first harmless call even with `Allow all actions`, while the relevant typed calls passed sequentially.

Therefore app permission mode is not the only authorization/safety layer. A composite safety block alone is not evidence that the local backend, tunnel or typed tool is broken.

### 6. Installed/source lifecycle split-brain is closed

The target machine originally exposed a stale installed 1MCP process under `%LOCALAPPDATA%\ChatAgentPlatform\app` listening on `127.0.0.1:3050` while the source checkout reported its own profiles stopped.

The public manager now coordinates installed/source copies through shared `manager-owner.json` state. Target acceptance proved installed -> source -> installed takeover, cross-copy Status, foreign-owner Stop/cleanup and exactly one `3050` listener. An unowned foreign listener on `3050` is rejected fail-closed rather than treated as platform health.

## Accepted semantic surface

Exactly five semantic tools are the Stage 24 product surface:

- `workspace_read` -> roots/read_text/search only;
- `workspace_write` -> scoped text create/overwrite only;
- `web_open` -> HTTP/HTTPS navigation only;
- `web_observe` -> find/snapshot only;
- `web_interact` -> click/type only.

`CHAT_LOCAL_FILES_ROOT` is mandatory. Absolute paths and traversal escaping the configured root are rejected. Browser embedded credentials and non-HTTP(S) URLs are rejected. Raw JavaScript/evaluate, upload, direct network-body tools, arbitrary server/tool selection and catalog mutation are not exposed.

The projection pins exact downstream/runtime dependencies and does not perform nested `npx` installs during user tool calls. The installed manager bundle prepares the projection dependencies in its own `%LOCALAPPDATA%` runtime and does not depend on checkout `node_modules`.

## Current Stage 24 direction

Do not return to one Chat app per backend and do not promote opaque generic `tool_invoke` as the primary Chat-facing boundary.

Current architecture:

```text
ordinary ChatGPT
  -> five stable semantic typed actions
  -> deterministic capability projection
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP / focused adapters
  -> replaceable task-active backends
```

Direct profiles remain diagnostics/fallback. Adaptive remains useful lifecycle/CI infrastructure. The semantic projection is the accepted Stage 24 product boundary.

## Acceptance ownership

Local-machine acceptance belongs to the development agent when its environment and permissions allow it. Codex should itself run Windows, CLI, process-lifecycle, local-application, MCP-backend and local integration checks instead of delegating routine local tests to the user.

Ordinary ChatGPT UI/custom-app acceptance is intentionally different. When a gate specifically requires the real ordinary-Chat user path, provide one precise test for the user and wait for the actual result.

A local MCP client, mock, Codex-only browser test or narrower integration test must never be reported as an ordinary-Chat E2E pass.

## Final Stage 24 completion gates

The functional/runtime and real ordinary-Chat gates are complete. Remaining work is repository integration only:

1. synchronize final docs/PR evidence with the exact accepted functional head and the 2026-08-16 ordinary-Chat result;
2. confirm the resulting PR HEAD is green across the final CI/security/acceptance suite;
3. then mark Stage 24 complete and merge/integrate into `main`.

## Local specialist inference after Stage 24

Stage 25 will evaluate local specialist inference without creating a second planner. LM Studio/`llmster` is the first replaceable runtime-manager candidate, and `LiquidAI/LFM2.5-VL-3B` is the first preferred `local-vision` candidate. Benchmark actual target-hardware behavior before promotion.

ChatGPT remains the intelligence layer. Local specialist models provide bounded perception/extraction, not autonomous planning.

## How to continue safely

Before changing code:

- inspect `git status`, recent commits, PR #66 and current workflow logs;
- read the files referenced by `AGENTS.md`;
- distinguish accepted evidence from target architecture and experiments;
- preserve accepted direct/adaptive/single-owner regressions;
- preserve any user local stash/backup until experimental diffs are intentionally retired;
- run locally accessible acceptance yourself rather than delegating it to the user;
- use the user only for an ordinary-Chat UI/custom-app gate or another irreducible target-machine action;
- never invent user acceptance results.

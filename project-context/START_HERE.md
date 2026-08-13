# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## What the project is

`chat-agent-platform` is a thin bridge from ordinary ChatGPT Chat to local Windows capabilities through standard MCP. ChatGPT remains the planner/intelligence. The repository owns integration, lifecycle, configuration and acceptance logic, not a second AI agent platform.

Accepted reachability path:

```text
ordinary ChatGPT Chat
  -> ChatGPT custom MCP app/plugin
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> local 1MCP
  -> replaceable MCP backends
  -> local files/programs/devices
```

## Current work

- active stage: **Stage 24**;
- active PR: **#66 — Stage 24: standalone Windows bootstrap and lifecycle manager**;
- active development branch: `chat/stage24-local-controller`;
- functional code baseline before this documentation sync: `9799bec20ffeb92eebbba5061f32dff403bbe6f4`;
- documentation-only commits after that baseline do not by themselves prove new runtime behavior.

Always re-check the current PR HEAD and CI before editing or reporting status.

## What is already accepted

- ordinary ChatGPT -> Secure MCP Tunnel -> official tunnel-client -> 1MCP -> Sequential Thinking round trip passed on 2026-08-10;
- standalone Windows bootstrap/manager and no-console tray behavior passed on the target Windows machine on 2026-08-12;
- direct `files-readonly` ordinary-Chat E2E passed: Chat read the expected marker through the real tunnel;
- direct `browser-isolated` starts locally with exactly one active profile and MCP/tunnel readiness, but the existing Chat app retained the earlier filesystem action snapshot, so the ordinary-Chat browser E2E was not completed through that stale snapshot.

## Why Stage 24 changed direction

The real Chat test showed that changing the local 1MCP profile does not automatically change the already-discovered Chat-facing action snapshot. Maintaining one separate Chat app/plugin snapshot per Filesystem, Browser, REAPER, Blender, Origin, FFmpeg, etc. does not scale.

Stage 24 therefore evaluates a stable Chat-facing 1MCP contract using Lazy Loading:

```text
tool_list
tool_schema
tool_invoke
```

plus only the lifecycle management tools required for a pre-approved local backend catalog:

```text
mcp_list
mcp_status
mcp_enable
mcp_disable
mcp_reload
```

Administrative catalog mutation such as install/uninstall/update/edit/search must not be published to ordinary Chat.

Backends start disabled and are activated according to the task. More than one backend may be active when a real workflow needs them together.

## Adaptive experiment — current exact status

`runtime/chat-profiles/adaptive/mcp.json` currently registers:

- Filesystem MCP `@modelcontextprotocol/server-filesystem@2026.7.10`;
- Playwright MCP `@playwright/mcp@0.0.78`;
- both `disabled: true` initially.

Direct profiles remain pinned to accepted `@1mcp/agent@0.34.4`. Adaptive tests exact `@1mcp/agent@0.35.0-beta.3` with Lazy Loading enabled and Async Loading disabled through a hash-guarded local compatibility package.

The previous remote CI on PR HEAD `c7af0b0...` established the unpatched baseline behavior:

- `ci`: PASS;
- `CodeQL Security`: PASS;
- `Secret History Scan`: PASS;
- `Chat Profile Acceptance / windows-profiles`: PASS;
- `Chat Profile Acceptance / adaptive-runtime`: FAIL.

That remote failure established the original technical blocker:

1. `mcp_list` correctly returned `filesystem` and `playwright` as disabled;
2. the Filesystem enable path entered backend loading;
3. temporary HTTP `503 service_unavailable` while loading is handled as transitional state;
4. after the wait window, lazy `tool_list` still returned no `read_text_file` (`tools: []`, `loading retries=49`).

Upstream diagnosis then found two exact beta.3 lifecycle gaps: synchronous backend load/unload does not refresh the lazy registry, and a disabled entry disappears from the filtered transport config before the disable handler can unload it. Beta.4 has the same relevant built files.

Commit `3b12fc98e65017d3cd931369813e130119d8d614` carries a narrow hash-guarded patch for only those gaps. On 2026-08-13 the full same-session local acceptance passed for Filesystem and Playwright, including real invocation, forbidden-tool absence, exact frozen Chat surface, disabled catalog state and backend-process cleanup. Direct files/browser regressions also passed. The exact commit then passed `adaptive-runtime`, `windows-profiles`, `ci`, module candidates, CodeQL and Secret History Scan remotely.

## Acceptance ownership

Local-machine acceptance belongs to the development agent when its environment and permissions allow it. Codex should itself run Windows, CLI, process-lifecycle, local-application, MCP-backend and local integration checks instead of delegating routine local tests to the user.

Ordinary ChatGPT UI/custom-app acceptance is intentionally different. When a final gate specifically requires the real ordinary-Chat user path, Codex should provide one precise test for the user and wait for the actual result. This avoids spending agentic limits on a UI check the user can perform cheaply while preserving an independent end-to-end validation of the product's real user path.

A local MCP client, mock, Codex-only browser test or narrower integration test must never be reported as an ordinary-Chat E2E pass. After the user reports the ordinary-Chat result, record the evidence in project context and continue development.

## Stage 24 completion order

1. obtain green remote CI/security checks for the locally accepted standalone adaptive manager/bootstrap integration;
2. preserve the exact frozen Chat-facing allowlist and runtime least-privilege checks;
3. keep direct profile regressions green;
4. keep the safe installed default `reference` until ordinary-Chat acceptance;
6. perform the real ordinary-Chat acceptance that proves backend switching/selection works without creating a new plugin or refreshing the action contract for every backend;
7. only then mark Stage 24 complete and merge/integrate into `main`.

## How to continue safely

Before changing code:

- inspect `git status`, recent commits, PR #66 and current workflow logs;
- read the files referenced by `AGENTS.md`;
- distinguish accepted evidence from target architecture and experiments;
- prefer upstream 1MCP mechanisms over a new gateway/broker;
- preserve the accepted direct profiles until adaptive is proven;
- run locally accessible acceptance yourself rather than delegating it to the user;
- use the user only for the final ordinary-Chat UI/custom-app gate when that exact path is required;
- never invent user acceptance results.

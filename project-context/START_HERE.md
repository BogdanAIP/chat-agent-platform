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
- latest functional head before this documentation sync: `64fa0a27fd4d2656d938061a61c85abb72f7b6b0`;
- on that exact head, Chat Profile Acceptance run `31776737312`, CI run `31776737308`, CodeQL run `31776737298`, Module Candidate Acceptance run `31776737301` and Secret History Scan run `31776737292` all passed.

Always re-check the current PR HEAD and CI before editing or reporting status.

## What is already accepted

- ordinary ChatGPT -> Secure MCP Tunnel -> official tunnel-client -> 1MCP -> Sequential Thinking round trip passed on 2026-08-10;
- standalone Windows bootstrap/manager and no-console tray behavior passed on the target Windows machine on 2026-08-12;
- direct `files-readonly` ordinary-Chat E2E passed;
- direct typed `browser_navigate` ordinary-Chat E2E passed after refreshing/scanning the app in a new Chat: `https://example.com` returned title `Example Domain`;
- one ordinary-Chat session successfully used typed Filesystem and Playwright actions together through the same `Chat Local Bridge Test` app: scoped file read/write plus browser navigate/find/click, ending on IANA `Example Domains`;
- with app permission mode `Allow read actions`, an isolated `write_file` produced a real one-time approval card; with `Allow all actions`, typed read/navigate/write calls passed sequentially without confirmation.

## What Stage 24 discovered

### 1. Chat action snapshots are not transparently replaced

Switching the local direct profile did not automatically replace an already-scanned Chat action snapshot. A fresh scan/new Chat was required to see the changed typed surface.

### 2. The generic adaptive meta-tool contract is not product-accepted

The adaptive runtime itself passes local/CI lifecycle tests through the hash-guarded `@1mcp/agent@0.35.0-beta.3` compatibility package. But the real ordinary-Chat test saw the eight generic/lifecycle actions and only read-only list/status/discovery calls reached the bridge. Lifecycle calls plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

Do **not** claim that one specific annotation or OpenAI rule caused the block; the exact product-admission cause was not isolated. Also do not relabel the generic dispatcher as read-only/non-destructive merely to bypass review.

### 3. Concrete typed multi-backend actions work

A combined local runtime exposed 14 Filesystem + 20 Playwright actions. The Chat-facing app effectively surfaced 20 actions: all 14 Filesystem plus the first 6 Playwright actions, leaving later `browser_navigate`/`browser_click` unavailable.

A discriminator then reduced Filesystem to 4 typed actions while keeping all 20 Playwright actions. Local inventory was 24 tools; after Refresh/new Chat, ordinary Chat could call `read_text_file`, `write_file`, `browser_navigate`, `browser_find` and `browser_click` successfully in one conversation.

This is strong evidence of an **effective ~20-action snapshot truncation in the tested app configuration**, not evidence of an officially documented universal OpenAI limit. Stage 24 must solve scalable typed capability publication without assuming the number is a guaranteed platform constant.

### 4. OpenAI safety is context-sensitive beyond app permission mode

One long combined instruction (`local file -> browser -> write result`) was blocked by OpenAI safety after the first harmless call, even with `Allow all actions`. In the same kind of Chat surface, the relevant typed `read_text_file`, `browser_navigate` and `write_file` calls then passed sequentially when requested separately.

Therefore app permission mode is not the only authorization/safety layer. Do not interpret a composite safety block as proof that the local backend, tunnel or typed tool itself is broken.

### 5. Installed/source lifecycle split-brain was real

The target machine exposed a stale installed adaptive 1MCP process under `%LOCALAPPDATA%\ChatAgentPlatform\app` that continued listening on `127.0.0.1:3050` while the source checkout reported its own profiles stopped. A new source runtime could then see the stale process's health response.

PR head `64fa0a27...` adds shared manager ownership state and fail-closed port handling so installed/source manager copies coordinate instead of independently claiming the fixed MCP port. Remote Windows/CI/security checks are green; target-machine acceptance of this exact fix still needs to run before calling the split-brain issue closed.

## Current Stage 24 direction

Do not return to one Chat app per backend and do not promote opaque generic `tool_invoke` as the primary Chat-facing boundary.

Current product requirement:

```text
ordinary ChatGPT
  -> concrete typed actions with truthful schemas/semantics
  -> scalable capability selection/publication
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP / focused adapters
  -> replaceable task-active backends
```

The exact scaling mechanism is still **PROVISIONAL**. It must preserve typed action semantics while avoiding hundreds of simultaneously published tools and routine user Refresh work.

Direct profiles remain diagnostics/fallback. Adaptive 1MCP remains useful lifecycle/CI infrastructure but its generic Chat-facing contract is not accepted.

## Local specialist inference after Stage 24

The next planned specialist capability layer is local inference without creating a second planner.

Evaluate LM Studio/`llmster` as a replaceable local model-runtime manager for:

- local model/capability discovery;
- hardware-aware resource estimation before load;
- automatic variant/GPU-offload choice;
- JIT/load/unload, TTL and memory eviction;
- stable typed capability adapters such as `local-vision`.

`LiquidAI/LFM2.5-VL-3B`, officially released 2026-08-12, is the first preferred vision candidate for screen/UI understanding, OCR/document/chart understanding, grounding and multi-image work. Liquid publishes GGUF/llama.cpp and ONNX support. It is not yet accepted on the target Windows hardware; benchmark actual quantizations/runtime behavior before promotion.

ChatGPT remains the intelligence layer. Local specialist models provide bounded perception/extraction, not autonomous planning.

## Acceptance ownership

Local-machine acceptance belongs to the development agent when its environment and permissions allow it. Codex should itself run Windows, CLI, process-lifecycle, local-application, MCP-backend and local integration checks instead of delegating routine local tests to the user.

Ordinary ChatGPT UI/custom-app acceptance is intentionally different. When a gate specifically requires the real ordinary-Chat user path, provide one precise test for the user and wait for the actual result.

A local MCP client, mock, Codex-only browser test or narrower integration test must never be reported as an ordinary-Chat E2E pass.

## Stage 24 completion order

1. preserve green direct/adaptive local and CI regression coverage;
2. verify the new single-owner manager behavior on the target Windows machine, including installed/source handoff and stale-port fail-closed behavior;
3. define and implement the smallest scalable typed Chat-facing capability mechanism justified by the observed action-snapshot behavior;
4. prove that mechanism through real ordinary Chat with more than one useful backend class;
5. keep generic adaptive/lifecycle tooling diagnostic unless a later product surface can truthfully and reliably admit it;
6. synchronize docs/PR evidence with the exact final functional head;
7. only then mark Stage 24 complete and merge/integrate into `main`.

## How to continue safely

Before changing code:

- inspect `git status`, recent commits, PR #66 and current workflow logs;
- read the files referenced by `AGENTS.md`;
- distinguish accepted evidence from target architecture and experiments;
- preserve accepted direct profiles while the scalable typed boundary converges;
- do not discard the user's existing local documentation diff: back it up and reconcile it intentionally before pulling remote documentation changes;
- run locally accessible acceptance yourself rather than delegating it to the user;
- use the user only for the final ordinary-Chat UI/custom-app gate when that exact path is required;
- never invent user acceptance results.

# Bridge Acceptance Evidence

This file contains only evidence that actually ran. Target architecture belongs in `ARCHITECTURE.md`; current unresolved work belongs in `CURRENT_STATE.md`.

## 2026-08-10 — reference E2E accepted

The user's ordinary ChatGPT surface completed:

```text
ChatGPT Chat
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> local 1MCP
  -> Sequential Thinking MCP
  -> response back to the same ChatGPT conversation
```

This proves the project does not need a custom public gateway, polling relay, VPS/Yandex backend or project-owned MCP aggregation implementation for ordinary ChatGPT ↔ local MCP reachability.

## 2026-08-12 — standalone Windows bootstrap accepted

On the target Windows machine:

- reviewed official tunnel-client artifact/profile path passed;
- standalone manager bundle under LocalAppData installed and verified;
- DPAPI-protected runtime key was reused;
- reference MCP + Secure MCP Tunnel readiness smoke passed;
- cleanup left platform stopped;
- tray remained resident without leaving a separate Windows Terminal/npm/npx console window.

## 2026-08-12 — direct files-readonly ordinary-Chat E2E accepted

The installed manager started exactly one `files-readonly` runtime with MCP and tunnel ready. Ordinary Chat through `Chat Local Bridge Test` read `hello.txt` from the single allowed root and returned exact content:

```text
CHAT_LOCAL_FILES_E2E_OK
```

This accepts the direct read-only Filesystem path.

## 2026-08-13 — adaptive runtime/lifecycle accepted locally and in CI

The hash-guarded `@1mcp/agent@0.35.0-beta.3` compatibility package passed same-session Filesystem and Playwright lifecycle acceptance:

- backend initially disabled;
- enable/load;
- lazy discovery;
- real harmless invocation;
- forbidden-tool absence;
- disable/unload;
- capability removal;
- catalog retained as disabled;
- process cleanup;
- exact frozen generic top-level surface unchanged.

The integrated manager/bootstrap path also passed Windows/profile/CI/security checks. This accepts adaptive **runtime mechanics**, not the generic ordinary-Chat product contract.

## 2026-08-13 — generic adaptive ordinary-Chat product gate NOT accepted

The real Chat app exposed the exact eight generic/lifecycle actions. Read-only list/status/discovery calls reached the bridge/runtime. Lifecycle actions plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

Evidence conclusion:

- adaptive local lifecycle/runtime is real;
- the generic Chat-facing contract is not product-accepted;
- the exact reason for OpenAI pre-MCP admission/blocking was not isolated;
- do not report one specific annotation as the proven cause and do not relabel the dispatcher to bypass review.

## 2026-08-13 — typed Browser ordinary-Chat E2E accepted

After the local `browser-isolated` profile and tunnel were confirmed ready, the Chat app was refreshed/scanned and tested from a new ordinary Chat.

Typed action:

```text
browser_navigate("https://example.com")
```

Result:

```text
Example Domain
```

No generic `tool_invoke` was used. This accepts the concrete typed direct Browser path through ordinary Chat.

## 2026-08-13/14 — combined typed Filesystem + Playwright runtime accepted locally

A temporary synthetic combined configuration ran one 1MCP runtime with both Filesystem and Playwright ready through the existing tunnel.

First inventory:

- Filesystem: 14 typed actions;
- Playwright: 20 typed actions;
- local total: 34.

The Chat-facing app effectively surfaced 20 actions: all 14 Filesystem actions plus the first 6 Playwright actions. Later Playwright actions including `browser_navigate` and `browser_click` were not available in that snapshot.

A discriminator then reduced Filesystem to four typed actions:

- `read_text_file`;
- `write_file`;
- `search_files`;
- `list_allowed_directories`.

Playwright remained at 20 actions, for a local total of 24. Both backends and the tunnel were ready.

This establishes an observed action-snapshot pressure/truncation in the tested Chat app. It does **not** establish an official universal OpenAI limit of exactly 20 actions.

## 2026-08-14 — combined typed ordinary-Chat Filesystem + Browser E2E accepted

After Refresh/new Chat with the 24-tool local configuration, ordinary Chat through the same `Chat Local Bridge Test` app completed a multi-backend typed workflow:

- `list_allowed_directories` returned `C:\Users\eahra\AppData\Local\Temp\chat-final-system-e2e`;
- `read_text_file(input.txt)` returned `FINAL_TYPED_E2E_INPUT_20260813`;
- `write_file(output2.txt, FINAL_24_TOOL_TYPED_OK)` succeeded;
- `browser_navigate(https://example.com)` succeeded;
- `browser_find` located the current `Learn more` link (the originally expected `More information...` text was no longer present);
- `browser_click` navigated to IANA;
- final page title was `Example Domains`;
- `read_text_file(output2.txt)` returned `FINAL_24_TOOL_TYPED_OK`.

No `tool_invoke`, `tool_schema`, `mcp_enable`, `mcp_disable`, `mcp_reload` or other untyped invocation was used.

This accepts concrete typed multi-backend use through one ordinary-Chat app/conversation on synthetic scoped local data.

## 2026-08-14 — app permission behavior observed

With `Chat Local Bridge Test` set to **Allow read actions**, a clean two-step test showed:

- `read_text_file(input.txt)` completed without an approval card;
- isolated `write_file(permission-test-2.txt, WRITE_CONFIRMATION_TEST_OK)` produced a real UI permission card;
- the user selected **Allow once**;
- the write then completed.

The model's textual self-report about whether approval occurred is not authoritative; the visible UI card is the acceptance evidence.

With the app then set to **Allow all actions**, sequential typed calls `read_text_file`, `browser_navigate` and `write_file` each completed without approval.

## 2026-08-14 — composite OpenAI safety block observed

Under **Allow all actions**, one larger requested workflow combining local read -> browser interaction -> write-result was blocked by OpenAI safety after `list_allowed_directories`; later filesystem/browser calls were denied before execution.

A control experiment then requested the relevant typed actions separately in the same style of ordinary Chat:

- `read_text_file` -> PASS;
- `browser_navigate` -> PASS;
- `write_file` -> PASS.

Evidence conclusion:

- app permission mode is not the only OpenAI safety layer;
- the blocked composite workflow is not evidence that those local typed tools/backends are broken;
- exact safety heuristics are external and were not isolated.

## 2026-08-14 — installed/source split-brain defect diagnosed

A target-machine diagnostic found an installed adaptive runtime under `%LOCALAPPDATA%\ChatAgentPlatform\app` still listening on `127.0.0.1:3050` while source-checkout profile status reported all known source scopes stopped. The stale installed runtime returned HTTP 200 readiness with an empty catalog and interfered with source Browser startup diagnostics.

After stopping the installed copy, source `browser-isolated` startup became healthy and Playwright inspection returned all 20 local typed actions.

This proves the split-brain lifecycle defect existed.

## 2026-08-14 — single-owner fix remote acceptance only

Functional head `64fa0a27fd4d2656d938061a61c85abb72f7b6b0` adds shared manager ownership state, cross-copy delegation and fail-closed occupied-port behavior.

On that exact head the following remote workflows passed:

- Chat Profile Acceptance `31776737312`;
- CI `31776737308`;
- CodeQL Security `31776737298`;
- Module Candidate Acceptance `31776737301`;
- Secret History Scan `31776737292`.

This is remote/CI acceptance only. Do not claim target-machine installed/source handoff acceptance until that exact implementation runs there.

## Local vision / LM Studio status — NOT ACCEPTED YET

Official research confirms that Liquid AI released `LFM2.5-VL-3B` on 2026-08-12 and publishes GGUF/llama.cpp plus ONNX support, and current LM Studio documentation exposes model listing/loading, `--estimate-only`, GPU-offload selection, JIT loading, TTL and auto-eviction capabilities.

No target-machine LM Studio/LFM2.5-VL-3B benchmark has run yet. These remain Stage 25 candidates, not acceptance evidence.

# Current State

Last synchronized with functional head `64fa0a27fd4d2656d938061a61c85abb72f7b6b0` on 2026-08-14. Chat Profile Acceptance run `31776737312`, CI run `31776737308`, CodeQL run `31776737298`, Module Candidate Acceptance run `31776737301` and Secret History Scan run `31776737292` all passed on that exact head. Later documentation-only commits do not imply additional runtime acceptance. Always check the current PR HEAD and workflows.

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

Stage 24 real-machine evidence now includes:

- standalone bootstrap, official tunnel-client verification, DPAPI runtime-key storage and no-console tray behavior;
- direct `files-readonly` ordinary-Chat E2E returned `CHAT_LOCAL_FILES_E2E_OK`;
- fresh-snapshot direct typed Browser E2E: `browser_navigate(https://example.com)` returned `Example Domain`;
- combined typed Filesystem + Playwright ordinary-Chat E2E in one conversation: scoped `list_allowed_directories`, `read_text_file`, `write_file`, `browser_navigate`, `browser_find`, `browser_click` all executed and the browser reached IANA `Example Domains`;
- isolated write-permission test: app mode `Allow read actions` produced a real one-time approval card for `write_file`;
- full-access control: typed `read_text_file`, `browser_navigate` and `write_file` each passed sequentially in one conversation without approval.

## Chat action-snapshot findings

Changing the local direct profile does not automatically replace an already-scanned Chat action snapshot. Refresh/new Chat was required to see the new typed Browser surface.

A second scaling experiment exposed 14 Filesystem + 20 Playwright tools locally (34 total). The Chat-facing app effectively surfaced 20: all 14 Filesystem plus the first 6 Playwright actions, which excluded later `browser_navigate` and `browser_click`.

After reducing Filesystem to 4 typed actions, local inventory was 24 total. A refreshed/new Chat then successfully called the needed Filesystem and Browser actions, including `browser_navigate` and `browser_click`.

Conclusion: the tested app showed an **effective action-snapshot truncation around 20 actions**. This is measured product behavior, not an officially documented universal OpenAI limit. Stage 24 must not hard-code 20 as a guaranteed platform constant.

## Generic adaptive contract — runtime accepted, product surface not accepted

`runtime/chat-profiles/adaptive/mcp.json` still registers Filesystem + Playwright as a pre-approved disabled catalog. Direct profiles remain on `@1mcp/agent@0.34.4`; adaptive pins `@1mcp/agent@0.35.0-beta.3`, Lazy Loading ON and Async Loading OFF through the hash-guarded `runtime/1mcp-adaptive-shim` compatibility package.

The runtime/lifecycle implementation is real and green locally/remotely: enable -> lazy discovery -> real invocation -> disable -> capability removal -> process cleanup works for Filesystem and Playwright.

However, the real ordinary-Chat generic-surface test did **not** promote this contract. The exact eight generic/lifecycle actions were visible, and read-only list/status/discovery calls reached MCP, but lifecycle calls plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

Do not claim a proven single cause for that pre-MCP block. The generic dispatcher is additionally a design concern because one static Chat-facing tool descriptor cannot truthfully describe the schemas/side effects of every nested downstream operation. Keep adaptive as useful diagnostic/CI lifecycle infrastructure while the typed scaling boundary is designed.

## Composite workflow safety finding

With `Chat Local Bridge Test` set to `Allow all actions`, one long request combining local file read -> browser work -> local result write was blocked by OpenAI safety after the first harmless call. The relevant typed read, browser navigation and write actions then passed when requested separately in the same style of ordinary-Chat workflow.

Therefore:

- app permission mode is not the only OpenAI safety layer;
- a composite safety block is not sufficient evidence that a local typed tool/backend is broken;
- architecture should use truthful typed actions, scoped resources and reversible operations rather than depending on permission mode alone.

## Windows single-owner lifecycle fix

A real target-machine defect was found: an installed adaptive runtime under `%LOCALAPPDATA%\ChatAgentPlatform\app` could remain on `127.0.0.1:3050` while the source checkout reported its own known profiles stopped. A new source runtime could then read the stale runtime's health endpoint.

Functional head `64fa0a27...` adds a shared `%LOCALAPPDATA%\ChatAgentPlatform\state\manager-owner.json` ownership record and public-manager coordination so installed/source copies share lifecycle ownership. A source copy starting while a foreign owner exists delegates/stops the real owner first; an occupied MCP port without a trustworthy owner fails closed rather than accepting another process's readiness.

All remote Windows/CI/security checks are green on `64fa0a27...`. Exact target-machine installed/source handoff acceptance for this new owner-state fix is still required before declaring the issue closed.

## Current Stage 24 architecture question

The product requirement is now:

```text
ordinary ChatGPT
  -> concrete typed actions with truthful schemas and side effects
  -> scalable capability publication/selection
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP / focused adapters
  -> replaceable task-active backends
```

Do not return to one Chat app per backend. Do not promote an opaque generic `tool_invoke` solely to avoid action-count pressure.

The exact scalable typed mechanism remains **PROVISIONAL** and must be proven against the observed Chat snapshot behavior.

## Safety model

Use three separate concepts:

```text
AVAILABLE
ACTIVE
AUTHORIZED
```

A backend can be registered without running. Start only what the task needs. Multiple backends may be active simultaneously if the workflow actually requires them. Prefer scoped roots, reversible workspaces, backups/git and consequence-based authorization over asking the user to approve every low-risk tool call.

Direct `files-readonly` and `browser-isolated` separation remains valuable diagnostic evidence and fallback, not a permanent ban on Browser + Filesystem coexistence.

## Planned local specialist inference

After Stage 24, evaluate LM Studio/`llmster` as a replaceable local inference runtime manager, not a second planner. Required behavior includes model/capability discovery, memory estimation before load, hardware-aware variant choice, load/JIT/TTL/unload and a stable typed specialist boundary.

`LiquidAI/LFM2.5-VL-3B`, officially released 2026-08-12, is the first preferred `local-vision` candidate because it targets screen/UI understanding, OCR/document/chart understanding, grounding and multi-image input and ships with GGUF/llama.cpp plus ONNX support.

It is not yet accepted on the target Windows machine. Benchmark actual model variants/quantizations and runtime compatibility before promotion. ChatGPT remains the intelligence layer; the local model supplies bounded visual perception/extraction.

## Remaining Stage 24 gates

1. target-machine acceptance of the single-owner installed/source lifecycle fix;
2. implement and test the smallest scalable typed Chat-facing capability mechanism justified by the action-snapshot evidence;
3. real ordinary Chat proves useful multi-backend behavior through that mechanism without one app per backend and without relying on opaque generic invocation;
4. exact final functional head passes CI/security/acceptance and docs are synchronized;
5. only then accept Stage 24 and integrate/merge to `main`.

## Work after Stage 24

Stage 25 should establish the local specialist inference runtime and first `local-vision` backend, beginning with LM Studio/`llmster` evaluation and LFM2.5-VL-3B benchmarking.

Stage 26 should benchmark professional application backends (REAPER, Origin, FFmpeg, Blender, Windows UI fallback) through the stable bridge/capability boundary.

Stage 27 should harden distribution, updates, repair, rollback and release packaging.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`. Historical Yandex/Tailscale paths are not active product dependencies.

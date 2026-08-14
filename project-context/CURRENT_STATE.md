# Current State

Last synchronized with functional head `ffcc2e407c7b9a71caa9e19c07962e2182928c41` on 2026-08-14. Chat Profile Acceptance run `31801462054`, CI run `31801462040`, CodeQL run `31801462047`, Module Candidate Acceptance run `31801462032` and Secret History Scan run `31801462041` all passed on that exact head. Later documentation-only commits do not imply additional runtime acceptance. Always check the current PR HEAD and workflows.

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

Official OpenAI documentation also confirms that ChatGPT MCP app tool definitions use a frozen reviewed snapshot and later server-side tool changes are not automatically enabled. Therefore 1MCP tags/presets/runtime filtering are useful local mechanisms but do not by themselves solve ordinary-Chat tool-surface scaling without Refresh. OpenAI Tool Search is a promising large-tool mechanism in the API/Agents SDK, but it is not currently documented as a custom-MCP-app capability in the ordinary Chat product path used by this project.

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

## Windows single-owner lifecycle — target accepted for the measured split-brain defect

A real target-machine defect was found: an installed adaptive runtime under `%LOCALAPPDATA%\ChatAgentPlatform\app` could remain on `127.0.0.1:3050` while the source checkout reported its own known profiles stopped. A new source runtime could then read the stale runtime's health endpoint.

The public manager now uses shared `%LOCALAPPDATA%\ChatAgentPlatform\state\manager-owner.json` ownership state. Installed and source copies delegate status to the real owner, stop a foreign owner before takeover and fail closed when `3050` is occupied without trustworthy ownership.

Target Windows acceptance on 2026-08-14 proved:

- installed `reference` start -> installed owner, one `3050` listener, MCP+tunnel ready;
- source `Status` correctly observed the installed owner;
- installed -> source takeover stopped the installed runtime, started source and transferred owner state;
- installed `Status` correctly observed the source owner;
- source -> installed takeover transferred ownership back with exactly one `3050` listener;
- `Stop` invoked through the non-owning source copy stopped the installed owner, freed `3050` and removed owner state;
- an unrelated listener on `3050` caused public `Start` to fail closed instead of accepting foreign readiness;
- the initial occupied-port diagnostic formatting defect was fixed in commit `923d2f9...`;
- functional Windows CI on `ffcc2e407...` now binds a real foreign listener on `3050` and verifies the fail-closed diagnostic path automatically.

The measured installed/source split-brain blocker is therefore closed. The foreign-owner `Toggle` branch remains covered by code/contract regression but was not separately re-run as a dedicated target-machine user test; do not overstate that narrower path as independent target evidence.

## Current Stage 24 architecture question

The product requirement is now:

```text
ordinary ChatGPT
  -> small stable set of concrete semantic typed actions
  -> capability projection onto the larger approved local catalog
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP / focused adapters
  -> replaceable task-active backends
```

Do not return to one Chat app per backend. Do not promote an opaque generic `tool_invoke` solely to avoid action-count pressure.

The exact scalable typed mechanism remains **PROVISIONAL**. The current strongest candidate is a smallest compatibility facade/projection with fixed, truthful semantic actions grouped by real operation/consequence class, while 1MCP remains the replaceable backend runtime. It must not become a planner, workflow engine or second generic MCP platform.

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

1. design and implement the smallest scalable typed Chat-facing capability projection justified by the frozen-snapshot/action-pressure evidence;
2. real ordinary Chat proves useful multi-backend behavior through that mechanism without one app per backend, routine per-operation Refresh or opaque generic invocation;
3. preserve accepted direct/adaptive/lifecycle regressions and truthful safety semantics;
4. exact final functional head passes CI/security/acceptance and docs are synchronized;
5. only then accept Stage 24 and integrate/merge to `main`.

## Work after Stage 24

Stage 25 should establish the local specialist inference runtime and first `local-vision` backend, beginning with LM Studio/`llmster` evaluation and LFM2.5-VL-3B benchmarking.

Stage 26 should benchmark professional application backends (REAPER, Origin, FFmpeg, Blender, Windows UI fallback) through the stable bridge/capability boundary.

Stage 27 should harden distribution, updates, repair, rollback and release packaging.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`. Historical Yandex/Tailscale paths are not active product dependencies.

# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT Chat as the intelligence layer while local capabilities remain replaceable standard MCP modules.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Accepted 2026-08-10:

- official OpenAI Secure MCP Tunnel created and linked to the ChatGPT workspace;
- official `openai/tunnel-client` reached `ready` on Windows;
- local 1MCP reached `ready`;
- ChatGPT discovered and invoked `sequential_thinking`;
- result returned to the same ChatGPT conversation.

## Stage 22 — Remove superseded custom platform infrastructure — DONE

The active repository no longer ships the old universal Rust/Python core or transport stack.

Removed from the active tree:

- `agent-platform.exe` universal runtime source;
- custom `/gpt` ingress and polling transport;
- Rust `relay-server`;
- Yandex gateway/function/deployment assets;
- Stage 4 relay/GPT Action tests and workflows;
- Python behavioral oracle and Rust/Python parity layer;
- media/REAPER/mastering implementation as platform core;
- release/SBOM/license packaging built around the deprecated universal binary;
- Tailscale `8443` pilot lifecycle from the product path.

The pre-cleanup tree is preserved by Git history at `a446397d99276856c614bc49526cab422c7e74bd`.

## Stage 23 — Quality-first module catalog and ready-made selection — IN PROGRESS

Economic rule: the baseline bridge must add **zero mandatory SaaS subscriptions**. Quality is still a hard gate; do not choose a poor free tool over a professional local/vendor solution.

Completed in the first Stage 23 slice:

- module selection policy added;
- cost policy hardened against subscription chains and hidden paid dependencies;
- primary-source compatibility catalog created;
- pinned read-only Filesystem MCP candidate profile added;
- pinned isolated/headless Microsoft Playwright MCP candidate profile added;
- Windows CI candidate acceptance path added for health, tool discovery and harmless calls;
- REAPER, Windows desktop automation and Origin paths classified for real local testing rather than prematurely added to the default tool surface.

For every desired local capability:

1. define the exact user operation and risk;
2. find official/vendor MCP;
3. find mature OSS MCP;
4. find a mature generic CLI/API adapter;
5. only if all fail, extract or implement one small project-owned MCP adapter.

Do not restore old media code merely because it already exists in history.

Stage 23 is complete only when the catalog contains tested install/start/health/call evidence for the modules promoted to the baseline set. Candidate configs are deliberately separate from `runtime/mcp.json` until Stage 24 security acceptance.

## Stage 24 — Privileged module security

Before enabling filesystem, shell, browser, application control, credentials or devices in the default ChatGPT-facing runtime:

- define least-privilege tool exposure;
- verify ChatGPT-side permission behavior;
- add module-specific allowlists/scopes;
- use 1MCP `disabledTools`/tags/filters or equivalent upstream controls to reduce tool surface;
- run negative/unauthorized tests;
- document secret handling and recovery.

## Stage 25 — Optional Windows manager

Only after module management stabilizes, consider a thin UI/manager for:

- installing/detecting 1MCP and official tunnel-client;
- adding/removing MCP modules;
- start/stop/status;
- diagnostics;
- safe local secret references.

It must not become an agent, workflow engine or second policy platform.

## Definition of Done

The product succeeds when ordinary ChatGPT can use useful local modules with no project-owned generic transport/runtime, no mandatory SaaS subscription chain, and a user can add or replace a module without changing the bridge core.

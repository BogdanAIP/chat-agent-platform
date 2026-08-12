# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT Chat as the intelligence layer while local capabilities remain replaceable standard MCP modules.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Accepted 2026-08-10:

- official OpenAI Secure MCP Tunnel linked to ChatGPT;
- official `tunnel-client` reached ready on Windows;
- local 1MCP reached ready;
- ChatGPT discovered and invoked `sequential_thinking`;
- result returned to the same ChatGPT conversation.

## Stage 22 — Remove superseded custom platform infrastructure — DONE

The active repository no longer ships the old universal Rust/Python core, custom `/gpt`, polling relay, Rust relay server, Yandex deployment, media platform core or release machinery for the obsolete binary. The pre-cleanup tree remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`.

## Stage 23 — Quality-first module selection — DONE

Accepted results:

- baseline adds zero mandatory SaaS subscriptions;
- module selection has quality/cost/license/maintenance/security/supply-channel gates;
- Filesystem MCP `2026.7.10` passed Windows health/discovery/read acceptance;
- Microsoft Playwright MCP `0.0.78` passed Windows health/discovery/navigation/close acceptance;
- REAPER, Origin, FFmpeg, Blender and Windows UI have ready-made-first candidate paths;
- 1MCP remains replaceable infrastructure rather than product identity.

## Stage 24 — Least-privilege ordinary Chat + Windows lifecycle — IN PROGRESS

Stage 24 promotes capabilities only through explicit task profiles on the existing Secure MCP Tunnel path.

Profiles:

- `reference` — harmless connectivity profile;
- `files-readonly` — one explicit workspace root, no browser, no create/write/edit/move;
- `browser-isolated` — isolated/headless Playwright, no filesystem, unsafe code/evaluate/file-upload/direct-request tools disabled.

Security rule: do **not** combine open-web browser access and arbitrary local-file reading in an always-on baseline profile.

The measured Windows usability requirement is now part of Stage 24 through a deliberately thin bootstrap/manager:

- verify PowerShell/Node/npm/1MCP prerequisites;
- install one reviewed official `openai/tunnel-client` artifact with checksum verification;
- create/reuse the official tunnel profile through `tunnel-client init`;
- keep tunnel profile, runtime key and state outside Git;
- install the manager/runtime bundle under `%LOCALAPPDATA%\ChatAgentPlatform\app`;
- store the runtime key with DPAPI `CurrentUser`;
- provide start/stop/status/profile selection and a tray indicator;
- keep tray as UI over controller state, not a second lifecycle implementation;
- prove startup rollback and conflicting Runtime Scope recovery.

Stage 24 acceptance gates:

1. all lifecycle/bootstrap scripts parse on Windows CI;
2. forbidden tools are absent from actual MCP discovery;
3. only one normal Chat-facing profile owns the fixed `3050` endpoint;
4. conflicting Runtime Scopes remain observable and recoverable;
5. controller green state requires both MCP readiness and tunnel `/readyz` readiness;
6. manager/profile changes trigger full Windows profile acceptance;
7. bootstrap verifies the reviewed tunnel-client artifact before installation;
8. real local bootstrap succeeds without relying on repository-local tunnel secrets/configuration;
9. `files-readonly` performs a harmless ordinary-Chat end-to-end read;
10. `browser-isolated` performs a harmless ordinary-Chat end-to-end navigation;
11. profile switching does not silently preserve the previous capability surface.

Authenticated browser-session reuse, filesystem writes, Windows desktop automation, shell access and combined profiles remain separate future security decisions.

## Stage 25 — Application capability benchmarks

After Stage 24 acceptance, benchmark professional integrations on real workflows:

- REAPER: choose one immutable TwelveTake artifact and test a real project;
- Origin: choose one immutable Origin-Pro-MCP artifact and test installed Origin; use official OriginLab `originpro` only if a measured gap remains;
- FFmpeg: audit and benchmark `ffmpeg-mcp-lite==0.2.2` before writing an adapter;
- Blender: compare a reduced DCC-MCP profile with the smaller `djeada` server;
- Windows UI Automation: use only where specialized APIs cannot cover the operation.

Each promoted application capability gets its own narrow profile/tool surface rather than growing one universal desktop profile.

## Stage 26 — Distribution and maintenance hardening

Once module/profile behavior is stable:

- define the first stable release artifact;
- make bootstrap/update/repair/doctor flows versioned and repeatable;
- reduce runtime dependence on repeated `npx -y` resolution through a reproducible local dependency install/lock strategy;
- add explicit runtime-key rotation and uninstall/repair paths;
- define upgrade/rollback rules for manager bundle, 1MCP and tunnel-client;
- keep the installed UI/controller thin and non-agentic.

## Definition of Done

The product succeeds when ordinary ChatGPT can use useful local modules with no project-owned generic transport/runtime, no mandatory SaaS subscription chain, no second AI planner, and the user can safely install, select, replace and diagnose local capabilities without manually rebuilding infrastructure.

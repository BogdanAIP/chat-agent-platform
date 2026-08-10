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

## Stage 23 — Quality-first module catalog and ready-made selection — DONE

Economic rule: the baseline bridge must add **zero mandatory SaaS subscriptions**. Quality remains a hard gate; do not choose a poor free tool over a professional local/vendor solution.

Accepted Stage 23 results:

- module selection policy and cost firewall are documented;
- install artifacts must be pinned from the real npm/PyPI/GitHub Release/vendor supply channel;
- read-only Filesystem MCP `2026.7.10` passed real Windows 1MCP health/discovery/read acceptance;
- isolated/headless Microsoft Playwright MCP `0.0.78` passed real Windows 1MCP health/discovery/navigation/close acceptance;
- REAPER, Origin, FFmpeg, Windows UI and Blender have ready-made-first candidate paths and explicit fallback rules;
- no legacy media/application adapter is restored without a measured gap;
- normal Windows CI, Module Candidate Acceptance, CodeQL and secret-history checks pass.

Stage 23 does not make every researched module a default tool. It establishes the evidence-based selection process and the first technically accepted baseline capabilities.

## Stage 24 — Least-privilege ordinary Chat profiles — IN PROGRESS

Stage 24 promotes capabilities only through explicit task profiles on the existing Secure MCP Tunnel path.

Initial profiles:

- `files-readonly` — one explicit workspace root, no browser, no create/write/edit/move;
- `browser-isolated` — isolated/headless Playwright, no filesystem, with unsafe code/evaluate/file-upload/direct-request tools disabled.

Security rule: do **not** combine open-web browser access and arbitrary local-file reading in an always-on baseline profile. Read-only local data plus network transmission is still an exfiltration path under prompt injection. Capability separation is the primary boundary; upstream origin filters may be defense in depth but are not treated as the security boundary.

Before a profile is accepted for ordinary Chat:

1. prove the profile starts through the pinned 1MCP runtime;
2. prove forbidden tools are absent from actual discovery;
3. prove only one Chat-facing profile owns the fixed local tunnel port;
4. prove the official Secure MCP Tunnel remains ready;
5. invoke one harmless tool from ordinary Chat and receive the result back in the same conversation;
6. prove switching profiles does not silently expose the previous profile's tools.

Authenticated browser-session reuse, write-capable filesystem access, Windows desktop control, shell access and combined profiles remain outside the baseline until separately justified and reviewed.

## Stage 25 — Application capability benchmarks

After Stage 24 baseline profile acceptance, benchmark the selected local professional integrations against real workflows:

- REAPER: pin one exact TwelveTake artifact and test a real project;
- Origin: pin one exact Origin-Pro-MCP artifact and test the installed Origin; use official OriginLab `originpro` only if a measured gap remains;
- FFmpeg: audit and benchmark `ffmpeg-mcp-lite==0.2.2`; build a small adapter only if it fails measured needs;
- Blender: compare a reduced DCC-MCP profile with the smaller `djeada` server;
- Windows UI Automation: use only for gaps that specialized APIs cannot cover.

## Stage 26 — Optional Windows manager

Only after module/profile management stabilizes, consider a thin UI/manager for:

- installing/detecting 1MCP and official tunnel-client;
- choosing task profiles and allowed folders;
- adding/removing MCP modules;
- start/stop/status;
- diagnostics;
- safe local secret references.

It must not become an agent, workflow engine or second policy platform.

## Definition of Done

The product succeeds when ordinary ChatGPT can use useful local modules with no project-owned generic transport/runtime, no mandatory SaaS subscription chain, and a user can add or replace a module without changing the bridge core.

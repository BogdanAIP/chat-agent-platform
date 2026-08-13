# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT Chat as the intelligence layer while local capabilities remain replaceable MCP modules. Scale capability count without scaling ChatGPT plugin count or keeping every local process permanently running.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Accepted 2026-08-10: Secure MCP Tunnel + official tunnel-client + local 1MCP + Sequential Thinking round trip from ordinary ChatGPT.

## Stage 22 — Remove superseded custom platform infrastructure — DONE

Removed the obsolete universal Rust/Python core, custom ingress/polling/Yandex/media platform runtime. Historical implementation remains in Git at `a446397d99276856c614bc49526cab422c7e74bd`.

## Stage 23 — Quality-first module selection — DONE

Accepted Windows candidates:

- Filesystem MCP `2026.7.10`;
- Microsoft Playwright MCP `0.0.78`;
- 1MCP direct baseline `0.34.4`.

Ready-made-first candidates were recorded for REAPER, Origin, FFmpeg, Blender and Windows UI fallback.

## Stage 24 — Windows lifecycle + scalable ordinary-Chat capability surface — IN PROGRESS

### Completed evidence inside Stage 24

- least-privilege direct `files-readonly` and `browser-isolated` profiles;
- robust profile status/conflict recovery;
- official tunnel readiness gating and startup rollback;
- verified standalone Windows bootstrap/manager under LocalAppData;
- DPAPI runtime key handling;
- tray/controller separation and no persistent console window;
- real ordinary-Chat `files-readonly` E2E;
- local `browser-isolated` readiness;
- real discovery that Chat action snapshots do not silently change after local profile switching.
- local adaptive same-session Filesystem + Playwright enable/invoke/disable acceptance with exact surface and process-cleanup checks;
- accepted direct files/browser regression after adding the adaptive compatibility launcher;
- adaptive Windows manager/bootstrap/status/start/stop/toggle/tray integration and interrupted-session recovery;
- exact integrated head `19ba303...` passed Chat Profile Acceptance, CI, module candidates, CodeQL and Secret History Scan.

### Adaptive convergence

The scalable target now uses one stable Chat-facing 1MCP Lazy Loading contract rather than one Chat app/plugin per capability.

Required stable surface:

- `tool_list`, `tool_schema`, `tool_invoke`;
- lifecycle `mcp_list`, `mcp_status`, `mcp_enable`, `mcp_disable`, `mcp_reload`;
- no Chat-facing install/uninstall/update/edit/search of arbitrary MCP catalog entries.

Backends are pre-approved locally, disabled by default and activated according to the task. Multiple backends may be active together when the workflow genuinely requires it.

Current experimental catalog: Filesystem + Playwright. Adaptive currently tests 1MCP `0.35.0-beta.3`; it is not accepted yet.

### Current gate

The beta.3 lifecycle/lazy-refresh blocker passes locally and in remote CI through a narrow hash-guarded compatibility package. Standalone manager/bootstrap/tunnel/no-console integration passes locally, and integrated-head CI is green. The active gate is now the final real ordinary-Chat one-snapshot E2E; do not promote the adaptive profile to accepted product behavior before it passes.

### Stage 24 Definition of Done

1. adaptive Filesystem enable/discover/invoke/disable/cleanup passes in one MCP session;
2. adaptive Playwright enable/discover/navigate/disable/cleanup passes under the same stable tool contract;
3. only approved lazy/lifecycle tools are exposed to Chat;
4. accepted adaptive behavior is integrated into manager/bootstrap/status/start/stop/toggle/tray;
5. direct profiles remain working diagnostics/fallback during transition;
6. exact final functional HEAD passes `ci`, `Chat Profile Acceptance`, CodeQL and Secret History Scan;
7. real ordinary Chat proves backend selection/switching through one action snapshot without per-backend plugin creation or routine Refresh;
8. only then Stage 24 is integrated into `main`.

## Stage 25 — Professional application capability benchmarks

After Stage 24, benchmark real workflows and promote backends into the pre-approved local catalog:

- REAPER: choose an immutable TwelveTake artifact and test real audio/project operations;
- Origin: choose an immutable Origin-Pro-MCP artifact and test the installed Origin; fall back to official OriginLab APIs only for measured gaps;
- FFmpeg: audit and benchmark `ffmpeg-mcp-lite==0.2.2` before writing an adapter;
- Blender: compare a reduced DCC-MCP surface with the smaller `djeada` server;
- Windows UI Automation: high-privilege fallback only where specialized APIs cannot cover the task.

Promotion of a new backend should normally require catalog/config/security/acceptance work, **not a new ChatGPT plugin/app**.

Lifecycle should follow the task: enable required backends, keep shared backends active across dependent stages, disable idle backends, and allow concurrency when necessary.

## Stage 26 — Distribution and maintenance hardening

Once adaptive behavior and application backends are stable:

- first stable release artifact;
- reproducible local dependency installation/lock strategy instead of repeated registry resolution;
- versioned bootstrap/update/repair/doctor/uninstall;
- runtime-key rotation;
- manager/1MCP/tunnel-client upgrade and rollback rules;
- idle/process lifecycle policy and diagnostics;
- keep controller/UI thin and non-agentic.

## Definition of Done

The product succeeds when ordinary ChatGPT can discover and use useful local capabilities through a stable standard-MCP bridge, starting only what tasks require, without a second AI planner, mandatory SaaS chain, project-owned generic gateway, or one ChatGPT plugin per local tool.

# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/DECISIONS.md`
5. `project-context/ROADMAP.md`
6. `project-context/DEVELOPMENT_PRINCIPLES.md`

For Stage 24.1 transport history/evidence also read `project-context/DIRECT_SEMANTIC_TUNNEL.md`.

For module work also read `project-context/MODULE_SELECTION_POLICY.md` and `project-context/MODULE_CATALOG.md`.

## Source-of-truth order

When documents disagree, use this order:

1. current code, tests and current CI/log evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. accepted ADRs in `DECISIONS.md` and `ARCHITECTURE.md`;
4. `ROADMAP.md`;
5. `README.md` and historical PR text.

Do not revive an older design merely because it remains in Git history.

## Product boundary

- ordinary ChatGPT Chat is the primary intelligence/planning/orchestration layer;
- local components expose capabilities through standard MCP or the smallest focused local adapter around a strong local API/CLI;
- do not add a second planner, autonomous workflow brain or general-purpose agent runtime behind ChatGPT;
- specialized local inference is allowed only as a replaceable bounded capability backend;
- prefer official/vendor MCP, then mature OSS MCP, then a generic local API/CLI adapter, then the smallest project-owned adapter for a measured gap;
- do not build a project-owned tunnel, generic MCP gateway, registry, vault, job system or policy platform while an accepted ecosystem component covers the boundary.

## Stage 24 baseline — accepted historical evidence

Stage 24 was squash-merged to `main` on 2026-08-16 as `175d36236f80a1f99f091d4f031a1c6255f3652b` from PR #66.

It proved the exact five semantic tools (`workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`) through:

```text
ChatGPT -> Secure MCP Tunnel -> tunnel-client -> 1MCP -> semantic-projection
```

Do not describe that path as broken. It worked and remains useful baseline evidence.

## Stage 24.1 direction — direct semantic selected

Active branch: `chat/direct-semantic-tunnel`, PR #70.

A/B result:

```text
A — Stage 24 baseline
Tunnel -> HTTP 1MCP -> stdio semantic-projection

B — selected
Tunnel -> stdio semantic-projection
```

Candidate B passed Windows CI, target-machine backend/negative tests, hosted Secure MCP Tunnel, real ordinary-Chat five-tool E2E, first-class manager lifecycle, single-owner/fail-closed behavior, forced-crash recovery and duplicate-free repeated Start.

Both paths then passed 3/3 lifecycle cycles on the target machine. Average timings were:

- 1MCP: Start 123685 ms, repeated Start 84119 ms, Stop 23252 ms;
- direct stdio: Start 5007 ms, repeated Start 4876 ms, Stop 1043 ms.

Direct was approximately 24.70x / 17.25x / 22.29x faster respectively in this sample and used no local port-3050 listener.

Therefore normal public `semantic` is being promoted to direct stdio. `semantic-direct` remains temporarily as a compatibility/diagnostic alias. 1MCP remains replaceable internal infrastructure for adaptive lifecycle experiments, diagnostics, aggregation/inspection and future catalog work.

## Current release gate

Do not merge PR #70 until:

- final CI/security/profile/semantic workflows are green on the exact promotion head;
- the target Windows machine smokes **normal public `semantic`** and reports `active_profile=semantic`, `tunnel_binding=direct-stdio`, healthy readiness, one active scope, no conflict and zero port-3050 listeners;
- after merge, the stable LocalAppData manager bundle is updated from `main` and final status is verified.

## Findings that remain active

- concrete typed actions are the accepted Chat-facing contract;
- generic adaptive `tool_list` / `tool_schema` / `tool_invoke` is diagnostic infrastructure, not product surface;
- frozen Chat action snapshots require Refresh/review when tool definitions change;
- effective snapshot pressure/truncation around 20 actions was observed in the tested app, but is not an official universal limit;
- OpenAI app permission mode is not the only safety layer;
- the semantic projection must remain a small deterministic compatibility boundary and must not grow into a generic gateway/planner;
- installed/source single-owner and fail-closed regressions must remain green for both direct and 1MCP-backed managed transports.

## Safety without capability paralysis

Use the model `AVAILABLE -> ACTIVE -> AUTHORIZED`:

- a backend may be registered without running;
- start only what the task needs;
- multiple backends may run together when the workflow genuinely requires it;
- scope local roots, credentials and destructive operations at the strongest practical boundary;
- prefer rollback, backups, git and contained workspaces over confirmation for every low-risk action;
- reserve explicit confirmation for genuinely consequential or hard-to-reverse effects.

## Local specialist inference direction

After Stage 24.1, Stage 25 evaluates LM Studio/`llmster` as a replaceable local model-runtime manager and `LiquidAI/LFM2.5-VL-3B` as the first preferred local-vision candidate. Chat remains the planner; specialist models remain tools.

Do not hard-code the platform to one model/runtime before target-machine evidence.

## Development workflow

- inspect actual repository/PR/CI state before editing;
- use stage branches and isolated worktrees for parallel agents;
- parallelize only independent work;
- `main` is the integration line for accepted stages, not a scratch branch;
- do not force-push or rewrite `main` history;
- perform locally accessible acceptance directly when the environment permits;
- use the user only for the real ordinary-Chat UI/custom-app gate or another irreducible target-machine action;
- never substitute a mock/local MCP client for a claimed ordinary-Chat E2E;
- preserve accepted historical evidence while simplifying the active architecture;
- when local working-tree changes differ from remote, preserve/reconcile them intentionally rather than discarding them.

# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/DECISIONS.md`
5. `project-context/ROADMAP.md`
6. `project-context/DEVELOPMENT_PRINCIPLES.md`

For the active transport experiment also read `project-context/DIRECT_SEMANTIC_TUNNEL.md`.

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

## Accepted Stage 24 baseline

Stage 24 was squash-merged to `main` on 2026-08-16 as `175d36236f80a1f99f091d4f031a1c6255f3652b` from PR #66.

The accepted ordinary-Chat path is:

```text
ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> 1MCP
  -> five-tool semantic projection
  -> scoped Filesystem / isolated Playwright backends
```

Real ordinary-Chat acceptance proved the exact five semantic tools (`workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`) in one multi-backend workflow. The final pre-merge head passed the complete CI/security/acceptance suite.

Do not reopen Stage 24 or describe its 1MCP path as broken merely because a simpler candidate is now being tested.

## Active direction — Stage 24.1

Active branch: `chat/direct-semantic-tunnel`.

A/B test:

```text
A — accepted
Tunnel -> 1MCP -> semantic-projection

B — provisional
Tunnel -> stdio semantic-projection
```

Candidate B removes 1MCP only from the semantic critical path if measured evidence proves equivalence or improvement. 1MCP remains replaceable internal infrastructure for diagnostics, adaptive lifecycle experiments, aggregation/inspection and future catalog work where it adds value.

The first gate uses official `tunnel-client dev proxy --mcp-command` plus a real modern-protocol MCP client to exercise the five semantic actions without touching the production tunnel profile. Read `project-context/DIRECT_SEMANTIC_TUNNEL.md` for gates.

Do not switch the accepted installed `semantic` profile to Candidate B until Windows CI, target-machine acceptance, reversible manager integration and real ordinary-Chat A/B all pass.

## Stage 24 findings that remain active

- concrete typed actions are the accepted Chat-facing contract;
- generic adaptive `tool_list` / `tool_schema` / `tool_invoke` is diagnostic infrastructure, not product surface;
- frozen Chat action snapshots require Refresh/review when tool definitions change;
- effective snapshot truncation around 20 actions was observed in the tested app, but this is not an official universal limit;
- OpenAI app permission mode is not the only safety layer;
- the semantic projection must remain a small deterministic compatibility boundary and must not grow into a generic gateway/planner;
- direct `files-readonly` and `browser-isolated` paths remain deterministic diagnostics;
- installed/source single-owner and fail-closed regressions must remain green for profiles that use fixed port `3050`.

## Safety without capability paralysis

Use the model `AVAILABLE -> ACTIVE -> AUTHORIZED`:

- a backend may be registered without running;
- start only what the task needs;
- multiple backends may run together when the workflow genuinely requires it;
- scope local roots, credentials and destructive operations at the strongest practical boundary;
- prefer rollback, backups, git and contained workspaces over a confirmation dialog for every low-risk action;
- reserve explicit confirmation for genuinely consequential or hard-to-reverse effects.

## Local specialist inference direction

After the transport experiment, Stage 25 evaluates LM Studio/`llmster` as a replaceable local model-runtime manager and `LiquidAI/LFM2.5-VL-3B` as the first preferred local-vision candidate. Chat remains the planner; specialist models remain tools.

Do not hard-code the platform to one model/runtime before target-machine evidence.

## Development workflow

- inspect actual repository/PR/CI state before editing;
- use stage branches and isolated worktrees for parallel agents;
- parallelize only independent work;
- `main` is the integration line for accepted stages, not a scratch branch;
- do not force-push or rewrite `main` history;
- perform locally accessible Windows/CLI/process/MCP acceptance directly when the environment permits;
- use the user only for the real ordinary-Chat UI/custom-app gate or another irreducible target-machine action;
- never substitute a mock/local MCP client for a claimed ordinary-Chat E2E;
- preserve accepted baseline behavior during A/B work;
- when local working-tree changes differ from remote, preserve/reconcile them intentionally rather than discarding them.

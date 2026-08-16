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

For Stage 25 local specialist work also read `project-context/LOCAL_SPECIALIST_INFERENCE.md`.

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

## Stage 24.1 — DONE

Stage 24.1 was squash-merged to `main` on 2026-08-16 as `df1d5e232b739b62e72ad81e5d82fd01be53e884` from PR #70.

A/B result:

```text
A — Stage 24 baseline
Tunnel -> HTTP 1MCP -> stdio semantic-projection

B — selected normal semantic transport
Tunnel -> stdio semantic-projection
```

Candidate B passed Windows CI, target-machine backend/negative tests, hosted Secure MCP Tunnel, real ordinary-Chat five-tool E2E, first-class manager lifecycle, single-owner/fail-closed behavior, forced-crash recovery and duplicate-free repeated Start.

Both paths passed 3/3 lifecycle cycles on the target machine. Average timings were:

- 1MCP: Start 123685 ms, repeated Start 84119 ms, Stop 23252 ms;
- direct stdio: Start 5007 ms, repeated Start 4876 ms, Stop 1043 ms.

Direct was approximately 24.70x / 17.25x / 22.29x faster respectively in this sample and used no local port-3050 listener.

Post-merge installation acceptance also passed on the target machine from `main`:

```text
STAGE24_1_PERSISTENT_INSTALL=PASS
active_profile=semantic
tunnel_binding=direct-stdio
active_count=1
conflict=false
PORT_3050_LISTENER_COUNT=0
```

The normal public `semantic` profile is therefore direct stdio. `semantic-direct` remains temporarily as a compatibility/diagnostic alias. 1MCP remains replaceable internal infrastructure for adaptive lifecycle experiments, diagnostics, aggregation/inspection and future catalog work.

## Current stage — Stage 25 local specialist inference

Stage 25 is active.

Goal: add bounded local model-powered perception without adding a second planner/agent brain.

Current verified runtime/model direction:

- LM Studio/`llmster` is the first replaceable runtime-manager candidate;
- LM Studio supports headless `llmster`, `lms` lifecycle/model commands, local HTTP serving, OpenAI-compatible image chat, memory estimation before load, GPU offload controls and TTL/JIT unloading;
- `LiquidAI/LFM2.5-VL-3B` is an official Liquid AI model released on 2026-08-12; official Liquid AI blog/docs, Hugging Face model weights and a WebGPU demo were provided as direct release evidence;
- `LiquidAI/LFM2.5-VL-1.6B` and `LiquidAI/LFM2.5-VL-450M` remain useful smaller comparison candidates;
- the target laptop has only 7.68 GB RAM and Intel Iris Xe, so target-first benchmarking still starts with the 450M Q4 variant, then 1.6B Q4, and only then the 3B candidate if memory estimation and observed headroom permit it.

Preferred quality candidate: `LiquidAI/LFM2.5-VL-3B`. Target-first runtime candidate on the current laptop: `LiquidAI/LFM2.5-VL-450M-GGUF` Q4. Do not hard-code the platform to LM Studio or Liquid AI before acceptance.

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

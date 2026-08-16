# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## What the project is

`chat-agent-platform` is a thin bridge from ordinary ChatGPT Chat to local Windows capabilities through standard MCP. ChatGPT remains the planner/intelligence. The repository owns integration, lifecycle, deterministic compatibility adapters, configuration and acceptance logic, not a second AI agent platform.

## Stage 24 baseline — DONE

Stage 24 was squash-merged to `main` on 2026-08-16 as:

`175d36236f80a1f99f091d4f031a1c6255f3652b` — `Stage 24: standalone Windows bootstrap and lifecycle manager (#66)`.

Stage 24 proved the exact five-tool semantic ordinary-Chat contract through the then-normal 1MCP transport:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

The accepted session read `SEMANTIC_FINAL_INPUT_20260816`, navigated from `example.com` through the real `Learn more` link to `Example Domains`, wrote a result file and independently read it back. The Stage 24 1MCP path worked and remains valid acceptance evidence.

## Stage 24.1 — direct semantic transport selected

Active branch: `chat/direct-semantic-tunnel`, PR #70.

Stage 24.1 compared:

```text
A — Stage 24 baseline
Tunnel -> HTTP 1MCP -> stdio semantic-projection

B — selected
Tunnel -> stdio semantic-projection
```

Candidate B passed all transport, backend, ordinary-Chat, lifecycle, ownership, crash-recovery and A/B gates. The normal public `semantic` profile is therefore being promoted to direct stdio.

The intended normal product path after Stage 24.1 is:

```text
ordinary ChatGPT Chat
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> five-tool semantic projection over stdio
      -> Filesystem MCP
      -> Playwright MCP
```

`semantic-direct` remains temporarily as a compatibility/diagnostic alias during migration.

1MCP is **not removed**. It remains replaceable internal infrastructure for adaptive lifecycle experiments, diagnostics, aggregation/inspection and future catalog work where its features add measured value.

## Why the direct path won

The target Windows A/B comparison completed 3/3 healthy cycles on both transports.

| Metric | 1MCP baseline | Direct stdio |
|---|---:|---:|
| Average initial Start | 123685 ms | 5007 ms |
| Average repeated/idempotent Start | 84119 ms | 4876 ms |
| Average Stop | 23252 ms | 1043 ms |
| Port 3050 listeners | 1 | 0 |

Direct was about 24.70x faster to start, 17.25x faster on repeated Start and 22.29x faster to stop in this sample. It also passed the same five-tool ordinary-Chat workflow, first-class manager lifecycle, fail-closed ownership and forced-crash recovery.

## Current implementation boundary

On the active branch:

- public `semantic` routes to the direct stdio semantic controller;
- public `semantic-direct` is a temporary compatibility alias to the same transport;
- normal `semantic` keeps its profile identity (`active_profile=semantic`) while reporting `tunnel_binding=direct-stdio`;
- old Stage 24 `semantic` settings that still say `local-1mcp` are migration-normalized to direct stdio;
- the legacy internal 1MCP semantic path remains available for diagnostics/A-B evidence but is no longer the normal public route.

## Remaining Stage 24.1 release gate

Do not merge PR #70 until:

1. all final workflows are green on the exact promotion head;
2. the target Windows machine runs the normal public `semantic` profile and confirms `active_profile=semantic`, `tunnel_binding=direct-stdio`, healthy readiness, one active scope and zero listeners on port 3050;
3. after merge, the stable LocalAppData manager bundle is updated from `main` and its final status is verified.

The target smoke is a final profile-routing/release check. The already-passed ordinary-Chat five-tool E2E does not need to be repeated unless exported tool definitions or the Chat app action snapshot changes again.

## Important findings to preserve

- Chat action snapshots are frozen until reviewed/refreshed; server-side tool changes do not silently replace an already-scanned snapshot.
- Concrete typed Filesystem + Playwright actions work together in one ordinary-Chat conversation.
- A larger tested action inventory showed effective snapshot pressure/truncation around 20 actions; this is measured behavior, not an official universal limit.
- The generic adaptive `tool_list` / `tool_schema` / `tool_invoke` surface is not the ordinary-Chat product contract.
- OpenAI safety is context-sensitive beyond app permission mode.
- The semantic projection must remain a small deterministic typed compatibility boundary, not a planner or generic gateway.
- Installed/source manager ownership and fail-closed handling apply to both 1MCP-backed and direct semantic managed runtimes.

## Product boundary

- ordinary ChatGPT remains the intelligence/planning layer;
- local specialist models may be bounded capability backends but never the second planner;
- prefer official/vendor or mature OSS components before project-owned infrastructure;
- do not recreate a project-owned generic MCP gateway, registry, vault, job system or workflow brain;
- keep 1MCP only where its measured capabilities are useful rather than forcing it into every request path.

## After Stage 24.1

Stage 25 evaluates local specialist inference without creating a second planner. LM Studio/`llmster` remains the first replaceable runtime-manager candidate and `LiquidAI/LFM2.5-VL-3B` the first preferred `local-vision` model candidate, subject to target-machine benchmarking.

## How to continue safely

Before changing code:

- inspect the active branch, PR, exact head and workflow logs;
- read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md` and `DEVELOPMENT_PRINCIPLES.md`;
- preserve the five-tool semantic contract and single-owner/fail-closed regressions;
- run locally accessible acceptance directly;
- use the user only for real ordinary-Chat UI/custom-app or other irreducible target-machine gates;
- never claim an ordinary-Chat or target-machine test unless that exact path actually ran;
- preserve/reconcile local uncommitted work rather than discarding it.

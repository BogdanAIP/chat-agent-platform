# Current State

## Stage 24 — complete

Stage 24 was squash-merged to `main` on 2026-08-16 as commit `175d36236f80a1f99f091d4f031a1c6255f3652b` from PR #66.

The accepted Stage 24 baseline proved the exact five-tool semantic ordinary-Chat contract through 1MCP:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

Real ordinary-Chat E2E read `SEMANTIC_FINAL_INPUT_20260816`, navigated through the actual `Learn more` link from `example.com` to IANA `Example Domains`, wrote a result file and independently read it back. This remains valid historical acceptance evidence; Stage 24's 1MCP route was not broken.

## Stage 24.1 — direct semantic transport selected

Active branch: `chat/direct-semantic-tunnel`.

PR #70 evaluates and now **selects** the simpler transport:

```text
Stage 24 baseline
Tunnel -> HTTP 1MCP -> stdio semantic-projection

Stage 24.1 selected path
Tunnel -> stdio semantic-projection
```

The normal public `semantic` profile is being promoted to the direct stdio path. `semantic-direct` remains temporarily as a compatibility/diagnostic alias. 1MCP remains in the project as replaceable internal infrastructure for adaptive lifecycle experiments, aggregation/inspection, diagnostics and future catalog work where it adds measured value.

## Stage 24.1 evidence — all A/B gates passed

### Automated and target direct acceptance

Direct tunnel acceptance passed with:

```text
DIRECT_SEMANTIC_PROTOCOL_ERA=modern
DIRECT_SEMANTIC_TOOL_COUNT=5
DIRECT_SEMANTIC_FILESYSTEM=PASS
DIRECT_SEMANTIC_BROWSER=PASS
DIRECT_SEMANTIC_NEGATIVE_CASES=PASS
DIRECT_SEMANTIC_1MCP_USED=False
DIRECT_SEMANTIC_TUNNEL=PASS
```

Target-machine timing for the direct harness included:

```text
DIRECT_SEMANTIC_CONNECT_MS=305
DIRECT_SEMANTIC_STARTUP_MS=372
DIRECT_SEMANTIC_ACCEPTANCE_MS=7341
```

### Hosted ordinary-Chat direct E2E

The existing `Chat Local Bridge Test` app required one Refresh because its frozen action snapshot retained old 1MCP-qualified action IDs. After Refresh, the same five semantic actions passed through the existing Secure MCP Tunnel without 1MCP:

```text
workspace_read(input.txt)
=> SEMANTIC_FINAL_INPUT_20260816

web_open / web_observe / web_interact / web_observe
=> Example Domains

workspace_write(result-direct.txt)
workspace_read(result-direct.txt)
=> SEMANTIC_FINAL_INPUT_20260816
   Example Domains
```

### Public manager lifecycle and recovery

The first-class managed direct profile passed:

```text
Start -> Status -> Stop -> Status -> Start
```

with healthy status, one authoritative owner, `tunnel_binding=direct-stdio`, no conflict and no listener on port 3050.

Forced termination of the owned direct tunnel-client then proved recovery: status became stopped, a normal `Start` created exactly one replacement process with a new PID, and a second `Start` reused it instead of creating a duplicate.

### Target A/B lifecycle comparison

Both paths completed 3/3 healthy cycles on the target Windows machine.

| Metric | 1MCP baseline | Direct stdio |
|---|---:|---:|
| Average initial Start | 123685 ms | 5007 ms |
| Average repeated/idempotent Start | 84119 ms | 4876 ms |
| Average Stop | 23252 ms | 1043 ms |
| Port 3050 listeners while running | 1 | 0 |

Direct stdio was approximately 24.70x faster to start, 17.25x faster on repeated Start and 22.29x faster to stop in this sample with no observed reliability loss.

## Current implementation state

The branch now routes both public `semantic` and the temporary `semantic-direct` alias to the managed direct stdio controller. Normal `semantic` preserves its public profile identity while reporting:

```text
active_profile=semantic
tunnel_binding=direct-stdio
settings.profile=semantic
settings.tunnel_profile=direct-stdio
```

Existing Stage 24 settings with `profile=semantic` and stale `tunnel_profile=local-1mcp` are migration-normalized to the promoted direct transport.

The legacy 1MCP-backed controller still contains its internal semantic implementation for diagnostics/A-B evidence; normal public `semantic` no longer routes through it.

## Remaining Stage 24.1 release work

1. final CI/security/profile/semantic workflows must pass on the exact promotion head;
2. the target Windows machine must run one smoke test using the **normal public `semantic` profile** and confirm healthy direct status plus zero port-3050 listeners;
3. after merge, update the stable `%LOCALAPPDATA%\ChatAgentPlatform\app` bundle from `main` and verify final status;
4. then close Stage 24.1 and continue Stage 25.

## Stage 24 findings that remain active

- Chat action snapshots are frozen until reviewed/refreshed;
- concrete typed actions are the ordinary-Chat product contract;
- generic adaptive `tool_list` / `tool_schema` / `tool_invoke` remains diagnostic infrastructure, not product surface;
- the measured large-action snapshot pressure is evidence, not a universal official constant;
- OpenAI safety can block composite workflows independently of app permission mode;
- `semantic-projection` must remain deterministic/non-agentic and must not grow into a generic gateway;
- installed/source single-owner and fail-closed behavior remain required for every managed transport.

## Work after Stage 24.1

Stage 25 evaluates local specialist inference/runtime management without creating a second planner. LM Studio/`llmster` remains the first runtime-manager candidate and `LiquidAI/LFM2.5-VL-3B` the first preferred `local-vision` candidate, subject to real target-hardware acceptance.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`. Historical Yandex/Tailscale paths are not active product dependencies.

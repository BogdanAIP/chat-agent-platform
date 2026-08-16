# Direct Semantic Tunnel Binding — Stage 24.1

Status: **DONE / RELEASE-COMPLETE**.

Stage 24.1 was squash-merged to `main` on 2026-08-16 as:

```text
df1d5e232b739b62e72ad81e5d82fd01be53e884
Stage 24.1: direct semantic tunnel A/B acceptance (#70)
```

## Decision

Stage 24.1 selected the direct stdio semantic transport as the normal public `semantic` path:

```text
ordinary ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> stdio semantic-projection
      -> Filesystem MCP
      -> Playwright MCP
      -> future focused adapters
```

The accepted Stage 24 baseline remains valid historical evidence:

```text
Tunnel -> HTTP 1MCP -> stdio semantic-projection
```

1MCP was not found broken. The direct path won because it preserved the same five-tool behavior and reliability gates while removing an unnecessary hop from this specific critical path.

1MCP remains replaceable internal infrastructure for adaptive lifecycle experiments, aggregation/inspection, diagnostics and future catalog work where its features add measured value.

## Stable Chat-facing contract

Transport promotion did not change the ordinary-Chat semantic surface:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

`semantic-projection` remains a small deterministic compatibility boundary. It is not a planner, registry, generic gateway or renamed `tool_invoke`.

## Automated Windows direct gate — PASSED

PR #70 added a Windows acceptance path using official `tunnel-client v0.0.11` `dev proxy` with `--mcp-command` bound directly to `semantic-projection.mjs`.

The reviewed tunnel-client Windows archive SHA256 is:

```text
eb912c86c6ccde90cda805cb17009507176a656725cf86c36fabe1901a12e29b
```

Observed successful markers included:

```text
DIRECT_SEMANTIC_PROTOCOL_ERA=modern
DIRECT_SEMANTIC_TOOL_COUNT=5
DIRECT_SEMANTIC_FILESYSTEM=PASS
DIRECT_SEMANTIC_BROWSER=PASS
DIRECT_SEMANTIC_NEGATIVE_CASES=PASS
DIRECT_SEMANTIC_CONNECT_MS=156
DIRECT_SEMANTIC_TUNNEL_ACCEPTANCE=PASS
DIRECT_SEMANTIC_STARTUP_MS=336
DIRECT_SEMANTIC_ACCEPTANCE_MS=7640
DIRECT_SEMANTIC_1MCP_USED=False
DIRECT_SEMANTIC_TUNNEL=PASS
```

The initial CI attempt exposed Windows command-string quoting in the test harness. The harness was corrected to match the official wrapper's shell-quoting convention and the subsequent run passed. This was a harness defect, not a semantic-runtime failure.

## Target Windows direct gate — PASSED

The real target Windows machine used the already-installed official tunnel-client and passed:

```text
DIRECT_SEMANTIC_PROTOCOL_ERA=modern
DIRECT_SEMANTIC_TOOL_COUNT=5
DIRECT_SEMANTIC_FILESYSTEM=PASS
DIRECT_SEMANTIC_BROWSER=PASS
DIRECT_SEMANTIC_NEGATIVE_CASES=PASS
DIRECT_SEMANTIC_CONNECT_MS=305
DIRECT_SEMANTIC_TUNNEL_ACCEPTANCE=PASS
DIRECT_SEMANTIC_STARTUP_MS=372
DIRECT_SEMANTIC_ACCEPTANCE_MS=7341
DIRECT_SEMANTIC_1MCP_USED=False
DIRECT_SEMANTIC_TUNNEL=PASS
```

The hosted candidate then used the existing Secure MCP Tunnel with:

```text
SEMANTIC_DIRECT_STATUS=ready
SEMANTIC_DIRECT_1MCP_USED=False
active_profile=semantic-direct
tunnel_binding=direct-stdio
conflict=false
PORT_3050_LISTENER_COUNT=0
```

## Ordinary-Chat E2E — PASSED

The existing `Chat Local Bridge Test` app needed one Refresh because its frozen action snapshot still contained old 1MCP-qualified internal action IDs. After Refresh, ordinary Chat successfully executed all five semantic actions through the direct path:

```text
workspace_read(input.txt)
=> SEMANTIC_FINAL_INPUT_20260816

web_open(example.com)
web_observe
web_interact(Learn more)
web_observe
=> Example Domains

workspace_write(result-direct.txt)
workspace_read(result-direct.txt)
=> SEMANTIC_FINAL_INPUT_20260816
   Example Domains
```

No raw Filesystem/Playwright actions or generic invocation tool was used.

## First-class manager lifecycle — PASSED

The public manager gained a reversible managed direct semantic profile and passed on the target machine:

```text
Start -> Status -> Stop -> Status -> Start
```

with one authoritative owner at:

```text
%LOCALAPPDATA%\ChatAgentPlatform\app\scripts\semantic-direct-controller.ps1
```

Healthy state remained:

```text
tunnel_running=true
tunnel_ready=true
mcp_ready=true
active_count=1
conflict=false
tunnel_binding=direct-stdio
PORT_3050_LISTENER_COUNT=0
```

## Crash recovery and idempotence — PASSED

The owned direct `tunnel-client` was forcibly terminated on the target machine. Status correctly became stopped. A normal public-manager `Start` created exactly one replacement process with a new PID. A second `Start` reused that process rather than creating a duplicate.

Observed markers:

```text
DIRECT_PROCESS_COUNT_BEFORE=1
OLD_TUNNEL_ALIVE_AFTER_KILL=False
DIRECT_PROCESS_COUNT_AFTER=1
PID_CHANGED=True
PORT_3050_LISTENER_COUNT=0
DIRECT_PROCESS_COUNT_AFTER_SECOND_START=1
SECOND_START_REUSED_PROCESS=True
```

## Target A/B lifecycle comparison — PASSED

Both paths completed 3/3 healthy lifecycle cycles on the same target Windows machine.

| Metric | Stage 24 `semantic` via 1MCP | Direct stdio | Direct improvement |
|---|---:|---:|---:|
| Average initial Start | 123685 ms | 5007 ms | ~24.70x faster |
| Average repeated/idempotent Start | 84119 ms | 4876 ms | ~17.25x faster |
| Average Stop | 23252 ms | 1043 ms | ~22.29x faster |
| Local port 3050 listeners while running | 1 | 0 | fixed semantic HTTP hop removed |
| Successful cycles | 3/3 | 3/3 | no loss in this sample |

The direct path had already passed modern protocol negotiation, exact five-tool inventory, real Filesystem + Playwright operations, negative cases, hosted ordinary-Chat E2E, first-class lifecycle, fail-closed ownership and crash recovery. The A/B run therefore closed the final reliability/diagnostic promotion gate.

## Promotion implementation — PASSED

The public manager routes normal `semantic` through the direct stdio controller. `semantic-direct` remains temporarily as a compatibility/diagnostic alias. Existing Stage 24 settings with `profile=semantic` and a stale `tunnel_profile=local-1mcp` are interpreted as promoted direct semantic settings rather than forcing the old route.

Final exact promotion-head CI was fully green. The target Windows machine then passed the normal public `semantic` smoke:

```text
DEFAULT_PROFILE=semantic
TUNNEL_BINDING=direct-stdio
SEMANTIC_PROFILE=semantic
active_profile=semantic
active_count=1
conflict=false
DIRECT_PROCESS_COUNT=1
PORT_3050_LISTENER_COUNT=0
NORMAL_SEMANTIC_DIRECT_PROMOTION=PASS
```

## Post-merge stable installation — PASSED

After PR #70 merged, post-merge `main` workflows were fully green. The target machine updated the stable LocalAppData manager bundle from merged `main`.

SHA256 equality was verified for:

- installed `chat-platform.ps1`;
- installed `semantic-direct-controller.ps1`;
- installed `runtime/semantic-projection/bin/semantic-projection.mjs`.

Final persistent status:

```text
STAGE24_1_PERSISTENT_INSTALL=PASS
active_profile=semantic
tunnel_binding=direct-stdio
tunnel_running=true
tunnel_ready=true
mcp_ready=true
active_count=1
conflict=false
PORT_3050_LISTENER_COUNT=0
```

The authoritative owner is the stable installed controller, not a temporary worktree copy.

## After Stage 24.1

Stage 25 is active. Continue with `project-context/LOCAL_SPECIALIST_INFERENCE.md` for the local VLM/runtime plan.

# Current State

## Stage 24 — complete

Stage 24 was squash-merged to `main` on 2026-08-16 as commit `175d36236f80a1f99f091d4f031a1c6255f3652b` from PR #66.

Final pre-merge head `87a8701b938a128901646d096e13142700cc109a` passed all six final workflows:

- Chat Profile Acceptance `31946162031`;
- Semantic Projection Acceptance `31946162063`;
- CI `31946162008`;
- CodeQL Security `31946162010`;
- Module Candidate Acceptance `31946162087`;
- Secret History Scan `31946162104`.

The accepted ordinary-Chat path is:

```text
ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> 1MCP
  -> semantic-projection
      -> Filesystem MCP
      -> Playwright MCP
```

The accepted semantic surface is exactly:

| Tool | Closed mapping |
|---|---|
| `workspace_read` | roots / read_text / search |
| `workspace_write` | write_file |
| `web_open` | browser_navigate |
| `web_observe` | browser_find / browser_snapshot |
| `web_interact` | browser_click / browser_type |

Real target-machine ordinary-Chat E2E on 2026-08-16 read `SEMANTIC_FINAL_INPUT_20260816`, used the browser semantic tools to reach IANA `Example Domains`, wrote `result.txt`, and independently read back exactly:

```text
SEMANTIC_FINAL_INPUT_20260816
Example Domains
```

Therefore the five-tool semantic projection is locally/CI accepted and ordinary-Chat product accepted through the Stage 24 baseline.

## Active branch — direct semantic tunnel A/B

Current development branch: `chat/direct-semantic-tunnel`.

The current work evaluates whether the semantic path should be simplified from:

```text
A: tunnel-client -> HTTP 1MCP -> stdio semantic-projection
```

to:

```text
B: tunnel-client -> stdio semantic-projection
```

This is **PROVISIONAL**. Baseline A remains the accepted product path until Candidate B passes all promotion gates.

Candidate B does not mean removing 1MCP from the project. 1MCP remains replaceable internal infrastructure for diagnostics, adaptive lifecycle experiments, aggregation/inspection and future catalog work where those features are useful.

## Direct-tunnel experiment implementation

The branch currently adds:

- `runtime/semantic-projection/tests/direct-tunnel-acceptance.mjs` — connects through the tunnel-client local ingress with modern MCP version negotiation, checks exact five-tool inventory, real scoped Filesystem calls, real Playwright calls and negative cases;
- `scripts/test-direct-semantic-tunnel.ps1` — starts official `tunnel-client dev proxy` with `--mcp-command` bound directly to the semantic projection, waits for readiness, records timings, runs the acceptance and cleans up;
- `.github/workflows/direct-semantic-tunnel.yml` — Windows CI using verified official `tunnel-client v0.0.11` and the same reviewed archive SHA256 as Stage 24 bootstrap;
- `project-context/DIRECT_SEMANTIC_TUNNEL.md` — experiment rationale, risks and promotion gates.

Expected pass markers include:

```text
DIRECT_SEMANTIC_PROTOCOL_ERA=modern
DIRECT_SEMANTIC_TOOL_COUNT=5
DIRECT_SEMANTIC_FILESYSTEM=PASS
DIRECT_SEMANTIC_BROWSER=PASS
DIRECT_SEMANTIC_NEGATIVE_CASES=PASS
DIRECT_SEMANTIC_1MCP_USED=False
DIRECT_SEMANTIC_TUNNEL=PASS
```

## Promotion gates for Candidate B

1. Windows CI direct-tunnel acceptance passes.
2. Target-machine direct-tunnel test passes and startup/operation timings are captured.
3. Public manager can start/status/stop a direct semantic transport without weakening accepted single-owner/fail-closed behavior.
4. The existing Chat app refreshes to the same exact five actions through Candidate B.
5. Real ordinary Chat repeats the accepted read -> browser -> write -> independent read workflow through Candidate B.
6. Regression comparison shows no material loss in reliability, cleanup or diagnostics.
7. Only then may Candidate B replace the current `semantic` transport path.

## Stage 24 findings that remain active

- frozen Chat action snapshots require review/Refresh after tool-definition changes;
- the generic adaptive meta-tool surface is not the ordinary-Chat product contract;
- typed semantic actions are the accepted scaling boundary;
- the tested large surface showed effective snapshot truncation around 20 actions, but this is not an official universal limit;
- OpenAI safety can still block composite workflows independently of app permission mode;
- the semantic projection must remain deterministic/non-agentic and must not become a project-owned generic MCP gateway;
- installed/source manager ownership and occupied-port fail-closed behavior remain required regressions for the Stage 24 baseline.

## Work after this experiment

Stage 25 remains local specialist inference/runtime-manager evaluation, beginning with LM Studio/`llmster` and `LiquidAI/LFM2.5-VL-3B` as replaceable candidates subject to target-machine evidence.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`. Historical Yandex/Tailscale paths are not active product dependencies.

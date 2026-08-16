# Direct Semantic Tunnel Binding — A/B Experiment

Status: **WINDOWS CI ACCEPTED; target-machine and ordinary-Chat promotion pending**.

## Goal

Evaluate whether the accepted five-tool semantic projection should sit directly behind the official OpenAI `tunnel-client` stdio MCP binding instead of requiring 1MCP in the ordinary-Chat semantic request path.

This is an architecture simplification experiment, not a claim that 1MCP is broken. Stage 24 ordinary-Chat acceptance passed through 1MCP and remains the product baseline until the direct path proves at least equivalent behavior.

## Baseline A — accepted Stage 24 path

```text
ordinary ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP
  -> semantic-projection
      -> Filesystem MCP
      -> Playwright MCP
```

This path is product accepted and must remain available during the experiment.

## Candidate B — direct semantic stdio path

```text
ordinary ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> stdio main MCP binding
  -> semantic-projection
      -> Filesystem MCP
      -> Playwright MCP
```

The candidate removes one runtime/process/protocol hop only from the semantic Chat-facing path. It does **not** remove 1MCP from the repository.

## Why this is worth measuring

Potential advantages:

- fewer runtime hops in the critical semantic path;
- no semantic dependency on the fixed local 1MCP HTTP listener when the direct path is eventually promoted;
- simpler failure attribution between Chat/tunnel/projection/backends;
- fewer long-lived processes for the normal semantic profile;
- direct protocol negotiation between `tunnel-client` and the project-owned semantic compatibility boundary.

Potential costs:

- public manager lifecycle/status/ownership logic must understand a tunnel-owned stdio MCP child before promotion;
- 1MCP aggregation, presets, lazy lifecycle and inspection remain useful for diagnostics/adaptive experiments and future larger catalogs;
- stdio transport has no MCP session ID, so stateful designs must not accidentally rely on HTTP session semantics;
- the accepted Stage 24 path already works, so simplification must beat or match it on measured stability rather than architectural taste alone.

## Automated Windows gate — PASSED

PR #70 added a real Windows acceptance path using official `tunnel-client v0.0.11` `dev proxy` with `--mcp-command` bound directly to `semantic-projection.mjs`.

Direct Semantic Tunnel Acceptance run `31947227216` passed on Windows Server 2025 with the reviewed tunnel-client archive SHA256 `eb912c86c6ccde90cda805cb17009507176a656725cf86c36fabe1901a12e29b`.

Observed pass markers:

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

This proves, through the official tunnel-client path and without a 1MCP runtime:

1. modern MCP era negotiation succeeds through `server/discover`;
2. exactly five Chat-facing semantic tools are visible;
3. raw Filesystem/Playwright and generic meta-tools do not leak;
4. `workspace_read` and `workspace_write` execute against a scoped workspace;
5. path traversal remains rejected;
6. `web_open`, `web_observe` and `web_interact` execute through real Playwright;
7. tunnel-client can own the semantic projection directly over stdio on Windows.

The first CI attempt exposed Windows command-string quoting in the test harness. The harness was changed to match the official wrapper's shell-quoting convention and to surface tunnel stdout/stderr on startup failure. The subsequent run passed. This was a harness defect, not a semantic-runtime failure.

## Target-machine command

On a machine with the accepted official tunnel-client installed:

```powershell
.\scripts\test-direct-semantic-tunnel.ps1
```

This test uses a temporary workspace and the tunnel-client local test control plane. It does not modify the production tunnel configuration, stop the accepted installed semantic profile or require a hosted control-plane API key.

## Remaining promotion gates

Candidate B is not the default product path until all of the following pass:

1. **DONE:** Windows CI direct-tunnel acceptance;
2. target-machine direct-tunnel acceptance with startup/operation timing recorded;
3. public manager integration can start/status/stop the direct semantic path without weakening single-owner/fail-closed behavior;
4. ordinary Chat refresh sees the same exact five semantic actions through the existing tunnel/app;
5. the same real multi-backend ordinary-Chat workflow passes through Candidate B;
6. regression comparison shows no material loss in reliability or diagnostics;
7. only then rename/promote direct binding as the normal `semantic` path.

## 1MCP after possible promotion

If Candidate B wins, keep 1MCP as replaceable internal infrastructure for:

- direct diagnostic/reference profiles where useful;
- adaptive lifecycle experiments;
- local catalog aggregation and inspection;
- future backend lifecycle/catalog work that benefits from 1MCP features.

Do not turn `semantic-projection` into a project-owned generic MCP gateway to replace 1MCP. The projection remains a small fixed typed compatibility boundary.

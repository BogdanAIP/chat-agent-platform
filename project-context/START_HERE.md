# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## What the project is

`chat-agent-platform` is a thin bridge from ordinary ChatGPT Chat to local Windows capabilities through standard MCP. ChatGPT remains the planner/intelligence. The repository owns integration, lifecycle, deterministic compatibility adapters, configuration and acceptance logic, not a second AI agent platform.

## Accepted Stage 24 baseline

Stage 24 is **DONE** and was squash-merged to `main` on 2026-08-16 as:

`175d36236f80a1f99f091d4f031a1c6255f3652b` — `Stage 24: standalone Windows bootstrap and lifecycle manager (#66)`.

The final PR head before merge was `87a8701b938a128901646d096e13142700cc109a`. All six final workflows passed on that exact head:

- Chat Profile Acceptance `31946162031`;
- Semantic Projection Acceptance `31946162063`;
- CI `31946162008`;
- CodeQL Security `31946162010`;
- Module Candidate Acceptance `31946162087`;
- Secret History Scan `31946162104`.

The accepted product path is:

```text
ordinary ChatGPT Chat
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> local 1MCP
  -> five-tool semantic projection
      -> Filesystem MCP
      -> Playwright MCP
```

Real ordinary-Chat acceptance on 2026-08-16 proved the exact semantic surface:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

The accepted session read `SEMANTIC_FINAL_INPUT_20260816`, navigated through the actual `Learn more` link from `example.com` to IANA `Example Domains`, wrote `result.txt`, and independently read back exactly:

```text
SEMANTIC_FINAL_INPUT_20260816
Example Domains
```

No raw Filesystem/Playwright tools, generic `tool_invoke`, one-app-per-backend split or per-operation Refresh was used.

## Active work — direct semantic tunnel A/B

Active branch: `chat/direct-semantic-tunnel`.

Current work is a **post-Stage-24 transport simplification experiment**, not a replacement already accepted in production.

Baseline A remains the accepted path:

```text
tunnel-client -> HTTP 1MCP -> stdio semantic-projection
```

Candidate B is:

```text
tunnel-client -> stdio semantic-projection
```

Candidate B removes 1MCP only from the ordinary-Chat semantic request path. It does not remove 1MCP from the repository. 1MCP remains replaceable infrastructure for direct diagnostics, adaptive lifecycle experiments, aggregation/inspection and future catalog work where its features are useful.

The branch now contains:

- `runtime/semantic-projection/tests/direct-tunnel-acceptance.mjs`;
- `scripts/test-direct-semantic-tunnel.ps1`;
- `.github/workflows/direct-semantic-tunnel.yml`;
- `project-context/DIRECT_SEMANTIC_TUNNEL.md`.

The automated candidate uses the official `tunnel-client dev proxy` local test control plane and binds its main MCP channel directly to `semantic-projection.mjs` through stdio. It must prove modern protocol negotiation, the same exact five tools, real Filesystem + Playwright behavior, negative cases and `DIRECT_SEMANTIC_1MCP_USED=False`.

Do not change the installed production `semantic` profile to Candidate B until the direct CI/local acceptance and real ordinary-Chat A/B gates pass.

## Important Stage 24 findings to preserve

- Chat action snapshots are frozen until reviewed/refreshed; local filtering does not silently replace an already-scanned app snapshot.
- Concrete typed Filesystem + Playwright actions work in one ordinary-Chat conversation.
- A large tested action inventory showed effective snapshot truncation around 20 actions; this is measured behavior, not an official universal limit.
- The generic adaptive `tool_list` / `tool_schema` / `tool_invoke` surface is not the accepted ordinary-Chat product contract.
- OpenAI safety is context-sensitive beyond app permission mode; a long composite prompt can be blocked while the same typed calls pass sequentially.
- Installed/source manager ownership and fail-closed handling for the fixed `3050` listener are accepted for the Stage 24 baseline.

## Product boundary

- ordinary ChatGPT remains the intelligence/planning layer;
- the semantic projection remains a small deterministic typed compatibility boundary, not a planner or generic gateway;
- do not recreate `tool_invoke` under another name;
- prefer official/vendor or mature OSS components before project-owned infrastructure;
- preserve the accepted Stage 24 baseline while Candidate B is experimental;
- do not remove 1MCP merely because Candidate B exists; promote the simpler path only after measured equivalence or improvement.

## After the transport experiment

Stage 25 will evaluate local specialist inference without creating a second planner. LM Studio/`llmster` remains the first replaceable runtime-manager candidate and `LiquidAI/LFM2.5-VL-3B` the first preferred `local-vision` model candidate, subject to real target-hardware benchmarking.

## How to continue safely

Before changing code:

- inspect the active branch, recent commits, open PR and current workflow logs;
- read `AGENTS.md`, this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md` and `DEVELOPMENT_PRINCIPLES.md`;
- distinguish accepted Stage 24 evidence from the provisional direct-tunnel candidate;
- preserve accepted direct/adaptive/single-owner regressions;
- run locally accessible acceptance yourself;
- use the user only for the real ordinary-Chat UI/custom-app gate or another irreducible target-machine action;
- never report Candidate B as accepted before the actual gates pass.

# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/STAGE25_1_VISION_INTEGRATION.md`
5. `project-context/DECISIONS.md`
6. `project-context/ROADMAP.md`
7. `project-context/DEVELOPMENT_PRINCIPLES.md`

Historical Stage 24.1 transport evidence is in `DIRECT_SEMANTIC_TUNNEL.md`. Historical/pre-acceptance Stage 25 runtime/model research remains in `LOCAL_SPECIALIST_INFERENCE.md`, `ACTIVE_VISUAL_GROUNDING.md`, `STAGE25_TARGET_BENCHMARKS.md` and dated handoffs. Those files do not override current #73/#74 evidence.

## Source-of-truth order

When documents disagree:

1. current code, tests and exact current CI/target evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. `ARCHITECTURE.md` and accepted ADRs;
4. `STAGE25_1_VISION_INTEGRATION.md` for active browser/vision integration;
5. `ROADMAP.md`;
6. historical research/handoff documents and README.

Do not revive an older design merely because it remains in Git history.

## Product boundary

- ordinary ChatGPT Chat is the primary and only planning/intelligence layer;
- local components expose deterministic capabilities or bounded specialist perception;
- never add a second planner, autonomous workflow brain, generic local agent runtime, or hidden `tool_invoke` equivalent;
- prefer official/vendor MCP, then mature OSS MCP, then a generic local API/CLI adapter, then the smallest focused project-owned adapter for a measured gap;
- do not build a project-owned tunnel, generic MCP gateway, registry, vault, job system or policy platform while accepted ecosystem components cover those boundaries.

## Accepted semantic foundation

The public semantic surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Normal path:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> focused backends/adapters
```

1MCP remains internal replaceable diagnostic/adaptive/aggregation infrastructure.

## Stage 25 accepted grounding evidence

PR #73 merged to `main` as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target-laptop grounding baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Target evidence with Chrome running:

```text
Search = HIT
Send = HIT
state Send = HIT
Gamma = safe ABSTAIN
tiny indicator = safe ABSTAIN
Export CSV absent = correct ABSTAIN
present_target_hits = 3/5
false_clicks = 0
provider/context_errors = 0
```

Do not describe LM Studio/llmster or 450M Q4 as the current accepted grounding baseline.

## Current Stage 25.1 evidence

Active branch: `chat/stage25-1-vision-integration-foundation`.

Draft PR: #74.

Fully-green implementation evidence head before the latest docs update: `c7eecc4ec1c4796e943816c9e51256d6b181b452`.

Proved on Windows CI:

- same Playwright-session CSS screenshot -> one-shot visual token -> exact freshness recheck -> coordinate action/ABSTAIN;
- positive intended click and replay guard;
- layout shift, scroll, overlay, navigation/page replacement -> stale ABSTAIN/no action;
- missing/ambiguous grounder -> ABSTAIN/no action;
- exact five public semantic tools remain unchanged;
- focused local-vision runtime lifecycle passes synthetic Doctor/Start/Touch/TTL/Stop/tamper/foreign-listener/ownership tests;
- Windows junction read/write escape is blocked on the pinned Filesystem stack;
- class-aware production grounding policy forces repeated-row and tiny targets to ABSTAIN until separately promoted;
- CodeQL Actions/JavaScript/Python and Secret Scan are green.

Do not overstate these results: the browser bridge still uses an injected deterministic grounder in CI, and the lifecycle proof uses a fake loopback runtime. Real F16 target-laptop end-to-end integration is still pending.

## Current next order

1. explicit `CONTROL_PLANE_API_KEY` child-environment regression/scrub if required;
2. explicit localhost/private-network navigation scope policy/regression that preserves intentional local HTTP workflows;
3. real npm lockfile + `npm ci` migration;
4. model-neutral real local-VLM grounder behind the runtime owner + production policy;
5. controlled semantic->vision escalation behind the already-proved same-session bridge;
6. real target-Windows F16 lifecycle + same-session acceptance with Chrome open;
7. only then consider more target-class promotion/public capability changes.

## Development workflow

- inspect actual repository/PR/CI state before editing;
- create stage branches from exact current `main`;
- keep `main` as integration line, not scratch;
- do not force-push/rewrite `main`;
- update authoritative docs whenever accepted evidence changes;
- distinguish deterministic CI from real target-machine and ordinary-Chat acceptance;
- use the user only for irreducible target-machine or Chat UI gates;
- never claim an ordinary-Chat or target-machine test unless that exact path ran;
- do not weaken fail-closed behavior merely to increase benchmark hit rate.

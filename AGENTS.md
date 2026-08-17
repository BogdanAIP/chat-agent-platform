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

Historical Stage 24.1 transport evidence is in `project-context/DIRECT_SEMANTIC_TUNNEL.md`. Historical/pre-acceptance Stage 25 runtime/model research remains in `LOCAL_SPECIALIST_INFERENCE.md`, `ACTIVE_VISUAL_GROUNDING.md`, `STAGE25_TARGET_BENCHMARKS.md` and the dated Stage 25 handoff. Those files do not override current accepted #73 evidence.

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
- never add a second planner, autonomous workflow brain, generic local agent runtime, or hidden `tool_invoke` equivalent behind ChatGPT;
- prefer official/vendor MCP, then mature OSS MCP, then a generic local API/CLI adapter, then the smallest focused project-owned adapter for a measured gap;
- do not build a project-owned tunnel, generic MCP gateway, registry, vault, job system or policy platform while accepted ecosystem components cover those boundaries.

## Accepted semantic foundation

Stage 24 accepted the exact public semantic surface:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Stage 24.1 selected the normal direct stdio path:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> focused backends/adapters
```

1MCP remains internal replaceable diagnostic/adaptive/aggregation infrastructure.

## Stage 25 accepted grounding evidence

PR #73 was squash-merged to `main` on 2026-08-17 as:

`acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target-laptop grounding baseline:

```text
llama.cpp b10448 / commit ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Final target result with Chrome running:

```text
Search = HIT
Send = HIT
state-disambiguated Send = HIT
Gamma repeated-row = safe ABSTAIN
tiny indicator = safe ABSTAIN
Export CSV absent = correct ABSTAIN
false_clicks = 0
provider/context_errors = 0
present_target_hits = 3/5
```

The model never clicks. The adapter provides bounded perception plus deterministic validation/ABSTAIN.

Do not describe LM Studio/llmster or 450M Q4 as the current accepted grounding runtime/model. They remain useful historical research candidates only.

## Current Stage 25.1 rule

Active branch: `chat/stage25-1-vision-integration-foundation`.

Do not implement `VLM coordinate -> blind click`.

Required integration invariant:

```text
same Playwright page/session
  -> semantic grounding first
  -> if unavailable/ambiguous: capture
  -> local vision grounding
  -> deterministic validation + freshness proof
  -> action in same page/session OR ABSTAIN
```

If capture/action identity, coordinate space, viewport/scroll state, or page freshness is uncertain, fail closed and do not mutate the page.

The first integration test must prove both:

1. semantic miss/ambiguity -> visual HIT -> action -> observable result;
2. uncertain/stale visual result -> ABSTAIN -> zero page mutation.

Keep vision runtime lifecycle outside `semantic-projection` as a focused non-agentic owner with resource admission, health, cleanup and idle unload.

## Development workflow

- inspect actual repository/PR/CI state before editing;
- create stage branches from the exact current `main` commit;
- keep `main` as the integration line, not a scratch branch;
- do not force-push/rewrite `main`;
- update authoritative documentation whenever accepted architecture/runtime evidence changes;
- distinguish deterministic CI from real target-machine and ordinary-Chat acceptance;
- use the user only for irreducible target-machine or Chat UI gates;
- never claim an ordinary-Chat or target-machine test unless that exact path ran;
- preserve/reconcile local uncommitted work rather than discarding it;
- do not weaken fail-closed behavior merely to increase benchmark hit rate.

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

Historical Stage 24.1 transport evidence is in `project-context/DIRECT_SEMANTIC_TUNNEL.md`. Historical/pre-acceptance Stage 25 runtime/model research remains in `LOCAL_SPECIALIST_INFERENCE.md`, `ACTIVE_VISUAL_GROUNDING.md`, `STAGE25_TARGET_BENCHMARKS.md` and dated handoffs. Those files do not override current accepted #73/#74 evidence.

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

Public semantic tools remain exactly:

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
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused backends/adapters
```

1MCP remains internal replaceable diagnostic/adaptive/aggregation infrastructure.

## Stage 25 accepted grounding evidence

PR #73 merged to `main` as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target-laptop baseline:

```text
llama.cpp b10448 / commit ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Target result with Chrome running: Search/Send/state HIT; Gamma/tiny safe ABSTAIN; absent Export CSV correct ABSTAIN; 0 false clicks; 0 provider/context errors; 3/5 present-target HIT.

Do not describe LM Studio/llmster or 450M Q4 as the accepted baseline.

## Current Stage 25.1 state

Active branch: `chat/stage25-1-vision-integration-foundation`, draft PR #74.

Already proved/implemented:

- same Playwright session CSS capture -> one-shot visual token -> exact fresh re-capture -> coordinate action/ABSTAIN;
- stale layout/scroll/overlay/navigation and replay fail closed;
- focused llama.cpp lifecycle/resource owner with strict process/artifact identity;
- class-aware production authorization; repeated-row/tiny remain forced ABSTAIN;
- Windows junction containment;
- explicit scrub-before-core-load for inherited tunnel credentials;
- committed semantic npm lockfile + product/acceptance `npm ci`;
- direct private/link-local/metadata literal IP blocking while loopback remains allowed;
- CodeQL Actions + JS/TS + Python and broader Dependabot;
- model-neutral Python production-grounder boundary, unit-proved and non-authorizing on parse/invalid/repeated/absent cases.

Still **not** accepted:

- real F16 same-session end-to-end action path;
- automatic semantic miss/ambiguity -> vision escalation in ordinary Chat;
- repeated-row or tiny-target production clicks;
- claim of a full DNS/redirect browser network sandbox;
- stable product release.

Required integration invariant:

```text
same Playwright page/session
  -> semantic grounding first
  -> if unavailable/ambiguous: CSS capture
  -> reviewed local runtime + production visual grounder
  -> deterministic authorization
  -> freshness proof
  -> action in same page/session OR ABSTAIN
```

If capture/action identity, coordinate space, browser state or freshness is uncertain, fail closed and do not mutate the page.

## Development workflow

- inspect actual repository/PR/CI state before editing;
- create stage branches from exact current `main`;
- keep `main` as integration line, not scratch;
- do not force-push/rewrite `main`;
- update authoritative documentation whenever accepted architecture/runtime/security evidence changes;
- distinguish deterministic CI from real target-machine and ordinary-Chat acceptance;
- use the user only for irreducible target-machine or Chat UI gates;
- never claim a target/ordinary-Chat result unless that exact path ran;
- preserve/reconcile local uncommitted work rather than discarding it;
- do not weaken fail-closed behavior merely to increase benchmark hit rate;
- never reintroduce unlocked semantic npm install when dependencies are absent;
- do not expose tunnel-only credentials to semantic core/downstream children;
- do not describe Playwright origin filters as a complete network security boundary.

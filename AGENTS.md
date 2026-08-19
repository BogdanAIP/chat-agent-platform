# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ROADMAP.md`
4. `project-context/ARCHITECTURE.md`
5. `project-context/MODULE_CATALOG.md`
6. `project-context/KNOWN_ISSUES.md`
7. `project-context/STAGE26_2A_PRODUCTION_WINDOWS_RUNTIME.md`
8. `project-context/STAGE26_2B_DESKTOP_OBSERVATION.md`
9. `project-context/STAGE26_PROCEDURAL_MEMORY.md`
10. older qualification docs only as needed for historical evidence.

## Source-of-truth order

When documents disagree:

1. current code/tests + exact current PR/CI/physical target evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. `ROADMAP.md`, `ARCHITECTURE.md`, `MODULE_CATALOG.md`, `KNOWN_ISSUES.md`;
4. accepted stage-specific qualification documents;
5. `DECISIONS.md` and `DEVELOPMENT_PRINCIPLES.md`;
6. historical research/handoffs/older README revisions.

Never hard-code a docs SHA as permanently current. Resolve live `main` and relevant PR heads before branching/editing.

## Current repository state

Current integration line after landing #83–#87:

```text
main = d044926846d9c2e198c906ff5174308da0974b03
```

Current open accepted work:

```text
#88 Stage 26.2B Desktop Observation / DesktopState
physical runtime head = dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a
ready for review; not merged
```

Do not merge PRs unless the user explicitly authorizes merge.

## Public semantic contract

Current Chat-facing tools remain exactly:

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
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused backends/adapters
```

1MCP remains internal replaceable diagnostic/adaptive/aggregation infrastructure.

## Non-negotiable product boundary

- ordinary ChatGPT is the only general planner/intelligence;
- local components may provide deterministic observation/execution, bounded specialist perception, verification and non-agentic procedural memory;
- no second local planner/autonomous workflow brain;
- no generic hidden `tool_invoke`, shell/Python executor or unbounded workflow dispatcher;
- current observed state outranks remembered procedure;
- observation is not authorization;
- procedure/model proposal is not authorization;
- action delivery is not completion evidence;
- stale/ambiguous/UNKNOWN evidence causes zero mutation;
- prefer mature upstream, then the smallest focused project adapter for a measured gap;
- do not duplicate qualified OpenAdapt mechanisms without a demonstrated blocker.

## Accepted browser foundation

Stage 25.2 remains semantic/native first. Local LFM2.5-VL-450M F16 starts only on the reviewed zero-exact-candidate browser path, is proposal-only and remains behind deterministic target/freshness authorization.

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
CPU 8 threads
ctx 2048
```

## Accepted Stage 26 state

### 26.1A / 26.1B

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
Capture qualification head = 7a9daa9329d81994833c22b4ca2e321927527dcc
```

### 26.1C–26.1E — merged

```text
#83 executor accepted
#84 baseline measured ~183.6 s / 185.6 s p50/p95
#85 window-scoped UIA accepted
```

Stage 26.1E controlled fixture evidence: 97 scoped resolutions, 0 Desktop fallback, 0 binding failure/ambiguity, 0 false/unrelated-window actions, ~3.324 s p50 / ~3.720 s p95. Do not generalize this to universal Windows accuracy.

### 26.2A — production Windows runtime — merged #87

Maintained runtime owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA. Physical production benchmark preserved zero false/unrelated-window actions and ~3.410 s p50 / ~3.631 s p95.

### 26.2B — DesktopState — physically accepted / PR #88 open

Exact tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Physical read-only result:

```text
SAME_IDENTITY_PASS=True
CONTROL_CONTRACT_PASS=True
SCREENSHOT_DIGEST_PASS=True
FRESHNESS_CONTRACT_PASS=True
BOUNDED_CONTROL_COUNT_PASS=True
OBSERVATION_ONLY_PASS=True
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
ACTION_COUNT=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
PASS=True
```

The state carries identity, bounded controls, coordinate space, observation-only fingerprints, visible text, screenshot/frame digests, provenance and freshness. Screenshot bytes are not retained in DesktopState.

## Current critical path

```text
merge #88 only on explicit authorization
 -> Stage 26.2C native desktop F16 Grounder
 -> Stage 26.2D UIA -> vision routing + adversarial accuracy suite
 -> Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime
 -> Stage 26.4 Human Demo -> transferable skill
 -> Stage 27/28 release work
```

Desktop vision must use native exact-window pixel coordinates, never the browser CSS/Playwright adapter. VLM proposals never authorize actions or task completion.

## Optional/parallel work

- Procedure-state dataset + TRM/STARM/FPRM/small-model experiments are optional after real verified data and measured need; not Stage 27/28 prerequisites.
- Multi-Chat/Codex orchestration is a separate upper layer; keep it outside Windows/procedure safety core.

## Development workflow

- inspect live repository/PR/CI state before editing;
- branch from the exact intended base;
- preserve physically tested runtime heads and evidence;
- distinguish docs-only descendants from physically tested code heads;
- keep `main` as integration line, not scratch;
- never rewrite/force-push `main`;
- use the user only for irreducible target-machine or ordinary-Chat UI gates;
- never claim a target path passed unless that exact path ran;
- do not weaken fail-closed behavior to improve hit rate;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- track browser network isolation, Windows root/junction containment, credential isolation and release-grade artifact reproducibility as cross-cutting requirements.

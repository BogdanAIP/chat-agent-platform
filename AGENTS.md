# Agent Entry Point

This repository is designed to be continued safely from a fresh ordinary ChatGPT session.

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
10. older qualification docs only as historical evidence when needed.

## Source-of-truth order

When documents disagree:

1. current code/tests + exact current PR/CI/physical target evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. `ROADMAP.md`, `ARCHITECTURE.md`, `MODULE_CATALOG.md`, `KNOWN_ISSUES.md`;
4. accepted stage-specific qualification documents;
5. `DECISIONS.md` and `DEVELOPMENT_PRINCIPLES.md`;
6. historical research/handoffs/older revisions.

Always resolve live `main` and relevant PR heads before branching/editing. Never treat a documentation SHA as permanently current.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources for development, review, orchestration or execution unless the user explicitly re-enables them later.

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

## Accepted Windows foundation

### Stage 26.1A / 26.1B

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
Capture qualification head = 7a9daa9329d81994833c22b4ca2e321927527dcc
```

### Stage 26.1C–26.1E — accepted and merged

#83 executor accepted; #84 baseline measured; #85 window-scoped UIA accepted.

Controlled Stage 26.1E evidence: 97 scoped resolutions, 0 Desktop fallback, 0 binding failure/ambiguity, 0 false/unrelated-window actions, about 3.324 s p50 / 3.720 s p95. Do not generalize this to universal Windows accuracy.

### Stage 26.2A — production Windows runtime — accepted and merged #87

Maintained runtime owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA. Physical production benchmark preserved zero false/unrelated-window actions and about 3.410 s p50 / 3.631 s p95.

### Stage 26.2B — DesktopState — accepted

Introduced by PR #88. Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

```text
SAME_IDENTITY_PASS=True
CONTROL_CONTRACT_PASS=True
SCREENSHOT_DIGEST_PASS=True
FRESHNESS_CONTRACT_PASS=True
BOUNDED_CONTROL_COUNT_PASS=True
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
CHROME_SURVIVAL_PASS=True
FIXTURE_CLEANUP_PASS=True
PASS=True
```

DesktopState is evidence only. Observation fingerprints are not executor authorization. Screenshot bytes are not retained in DesktopState.

Self-review corrected the first qualification reporting: `ACTION_COUNT=0` and related values were constants, not instrumented counters, so they are excluded from physical evidence. Read-only behavior is established by direct code review plus CI source-boundary tests proving the observer/driver expose no executor or actuation channel.

## Current critical path

```text
Stage 26.2C native desktop F16 Grounder
 -> Stage 26.2D UIA -> vision routing + adversarial accuracy suite
 -> Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27/28 release work
```

Desktop vision must use native exact-window pixel coordinates, never the browser CSS/Playwright adapter. VLM proposals never authorize actions or task completion.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass, and applicable review/acceptance checks are satisfied, merge it without waiting for a separate merge command.

Do not auto-merge when there is an unresolved finding, conflict, ambiguous scope, failed/skipped required test, or unavailable required review evidence. Surface the blocker instead.

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

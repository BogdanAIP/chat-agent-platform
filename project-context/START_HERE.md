# Start Here — authoritative continuation guide

Use this file first in a fresh ChatGPT or Codex session.

## Resolve live repository state first

Never treat a documentation SHA as permanently current. Resolve live `main`, then inspect any active PR heads relevant to the task.

## Read current authoritative context

1. `project-context/CURRENT_STATE.md`
2. `project-context/ROADMAP.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/MODULE_CATALOG.md`
5. `project-context/KNOWN_ISSUES.md`
6. stage-specific accepted documents as needed

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## Product boundary

Ordinary ChatGPT remains the only general planner/intelligence layer.

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused local capabilities
```

Current public semantic tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

Local components may observe, execute bounded actions, verify effects, reuse procedures and run bounded specialist perception. They must not become a second universal planner or expose generic hidden execution.

## Accepted browser foundation

Stage 25.2 remains semantic/native first. Local LFM2.5-VL-450M F16 starts only on the reviewed zero-exact-candidate browser path, is proposal-only and remains behind deterministic target/freshness authorization.

Accepted target specialist:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
CPU 8 threads
ctx 2048
```

## Accepted Windows state

### Stage 26.1A / 26.1B

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
Capture qualification head = 7a9daa9329d81994833c22b4ca2e321927527dcc
```

### Stage 26.1C–26.1E — merged

#83 executor accepted; #84 latency baseline measured; #85 window-scoped UIA accepted.

Controlled Stage 26.1E evidence: 97 scoped resolutions, 0 Desktop fallback, 0 binding failures/ambiguities, 0 false/unrelated-window actions, about 3.324 s p50 / 3.720 s p95. Do not generalize this to universal Windows accuracy.

### Stage 26.2A — Production Windows Runtime Foundation — merged #87

Maintained `runtime/windows/` owns bounded actuation, PID/HWND window-scoped UIA and verifier foundation.

Physical production benchmark preserved zero false/unrelated-window actions and about 3.410 s p50 / 3.631 s p95.

### Stage 26.2B — Desktop Observation / DesktopState — accepted

PR #88 carries the production read-only observer. Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Accepted physical result:

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

`DesktopState` is evidence, not authorization. Observation-only control fingerprints are distinct from executor authorization fingerprints. Screenshot bytes are not retained in the state.

## Current critical path

```text
Stage 26.2C native desktop F16 Grounder
 -> Stage 26.2D UIA -> vision routing + adversarial accuracy suite
 -> Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27/28 distribution and clean-user release
```

Desktop vision must use native exact-window pixel coordinates, never the browser CSS/Playwright adapter. VLM proposals never authorize actions or task completion.

## Merge policy

Once a branch is logically complete, intended diff is verified, required physical/CI tests pass, and the applicable review/acceptance gate passes, it may be merged without waiting for a separate merge command.

If a required review is unavailable, skipped, ambiguous, or reports findings, do not auto-merge; surface the blocker instead.

## Optional/parallel directions

- Procedure-state dataset + TRM/STARM/FPRM/small-model experiments are optional research only after real verified data and measured need; not Stage 27/28 prerequisites.
- Multi-Chat/Codex orchestration is a separate upper layer; keep it outside Windows/procedure safety core.

## Non-negotiable rules

- ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- observation/model/procedure proposal is not authorization;
- current observed state outranks remembered history;
- verification controls completion;
- stale/ambiguous/UNKNOWN fails closed;
- never persist private chain-of-thought;
- raw desktop capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve credential isolation, Windows junction/root containment and browser network residual-risk tracking;
- release-grade Python/model/OpenAdapt reproducibility is required before stable distribution.

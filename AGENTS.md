# Agent Entry Point

This repository is designed to be continued safely from a fresh ChatGPT or Codex session.

## Read first

1. `project-context/START_HERE.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ROADMAP.md`
4. `project-context/ARCHITECTURE.md`
5. `project-context/MODULE_CATALOG.md`
6. `project-context/KNOWN_ISSUES.md`
7. `project-context/STAGE26_PROCEDURAL_MEMORY.md`
8. accepted Stage 26.1 qualification documents/results as needed
9. `project-context/DECISIONS.md`
10. `project-context/DEVELOPMENT_PRINCIPLES.md`

Historical Stage 25/25.1/early Stage 26 plans remain useful evidence but do not override current code, exact target evidence or synchronized authoritative context.

## Source-of-truth order

When documents disagree:

1. current code/tests + exact current PR/CI/physical target evidence;
2. `START_HERE.md` and `CURRENT_STATE.md`;
3. `ROADMAP.md`, `ARCHITECTURE.md`, `MODULE_CATALOG.md`, `KNOWN_ISSUES.md`;
4. accepted stage-specific qualification documents;
5. `DECISIONS.md` and `DEVELOPMENT_PRINCIPLES.md`;
6. historical research/handoffs/older README revisions.

## Resolve repository state first

Never hard-code a docs SHA as permanently current. Resolve live `main` and inspect relevant PR heads before branching/editing.

At creation of the current docs-sync branch:

```text
main = def67e45d7a72547c53bcf339d00124f4edca0be
```

Accepted but still stacked/unmerged Windows qualification PRs:

```text
#83 Stage 26.1C head = 4bf08dd9b8d1ff010f14723f9bb0384b97334a2b
#84 Stage 26.1D head = 114e865090d39d218418958c40cf359b5f6808da
#85 Stage 26.1E head = 66390aca1dadf57c4f11568ec311ad6fcdbd7596
```

This documentation branch is stacked on exact accepted #85 head. Do not claim C/D/E are in `main` until explicitly landed.

## Public semantic contract

Current public Chat-facing tool names remain exactly:

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
- procedure/model proposal is never authorization;
- action delivery is never completion evidence by itself;
- prefer mature upstream, then the smallest focused project adapter for a measured gap;
- do not duplicate qualified OpenAdapt mechanisms or write a new Windows actuator without a demonstrated blocker.

## Accepted browser behavior

Stage 25.2 remains semantic/native first. Vision is only allowed on the explicitly reviewed zero-exact-candidate path, is local/on-demand/proposal-only, and remains behind deterministic target/freshness authorization. Disabled/unpromoted/unresolved semantic ambiguity ABSTAINS without VLM.

Accepted target specialist:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
CPU 8 threads
ctx 2048
```

## Accepted Stage 26 direction

### Stage 26.1A — OpenAdapt core — accepted

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

Use Flow `Workflow`/`ProgramGraph`; adapt `SkillLibrary` under project candidate-first trust; reuse Capture/Windows mechanisms where qualified.

### Stage 26.1B — bounded Windows Capture — accepted

Accepted qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Do not continue describing Capture as the next unresolved gate.

### Stage 26.1C — hardened typed Windows executor — accepted on target / PR #83

Accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Accepted boundary includes loopback/auth, legacy generic exec disabled/unreachable in qualification config, typed bounded input, stale frame/context refusal, focus/fingerprint gates, bounded pointer/keyboard/scroll and zero false/unrelated-window actions.

### Stage 26.1D — latency baseline — accepted benchmark / PR #84

Warm action sequence measured approximately 183.6 s p50 / 185.6 s p95. Exact source inspection identified desktop-wide UIA traversal as dominant blocker.

### Stage 26.1E — window-scoped UIA — accepted on target / PR #85

Accepted head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

Physical result:

```text
WINDOW_SCOPED_FIND_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
p50=3323.570 ms
p95=3720.061 ms
speedup ~55x/~50x
```

Do not convert controlled fixture 97/97 into a global Windows accuracy claim. The accepted run exercised role+name; broader `AutomationId`, custom controls and real apps need separate evidence.

## Current critical path

1. land stacked #83 -> #84 -> #85 safely;
2. after #83 merge, retarget #84 to `main`, inspect resulting diff/CI, then merge only if explicitly authorized;
3. after #84 merge, retarget #85 to `main`, inspect resulting diff/CI, then merge only if explicitly authorized;
4. retarget this docs sync to `main`, verify intended docs-only diff/CI;
5. Stage 26.2A Production Windows Runtime Foundation;
6. Stage 26.2B DesktopState/observation;
7. Stage 26.2C native desktop F16 Grounder;
8. Stage 26.2D semantic/UIA -> vision routing + adversarial accuracy suite;
9. Stage 26.2E one real medium-complexity application E2E;
10. Stage 26.3 Verified Procedure Runtime;
11. Stage 26.4 Human Demo -> transferable candidate skill;
12. Stage 27/28 distribution and clean-user release.

### Verifier rule

A minimal verifier is part of Stage 26.2A, not something deferred until procedure work:

```text
observe before
 -> authorize
 -> act
 -> observe after
 -> PASS | FAIL | UNKNOWN
```

`UNKNOWN` must not silently advance.

## Optional/parallel work

- Procedure-state dataset + TRM/STARM/FPRM/small-model experiments are optional research only after real verified data and measured need; not Stage 27/28 prerequisites.
- Multi-Chat/Codex orchestration is a separate upper layer; never merge it into Windows/procedure safety core and do not make it a release prerequisite.

## Development workflow

- inspect live repository/PR/CI state before editing;
- branch from the exact intended base;
- preserve physically tested heads; do not rewrite accepted evidence casually;
- keep `main` as integration line, not scratch;
- do not force-push/rewrite `main`;
- update authoritative docs with accepted architecture/runtime/security changes;
- distinguish deterministic CI from physical target and ordinary-Chat acceptance;
- use the user only for irreducible target-machine/Chat UI gates;
- never claim a path passed unless that exact path ran;
- preserve local uncommitted work rather than discarding it;
- do not weaken fail-closed behavior to improve hit rate;
- never persist private chain-of-thought;
- raw capture is sensitive local data until retention/redaction/encryption policy is accepted;
- browser DNS/redirect residual risk, Windows junction containment, credential isolation and release-grade artifact reproducibility remain explicit cross-cutting requirements.

# Start Here — authoritative continuation guide

Use this file first in a fresh ordinary ChatGPT session.

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

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources for development, review, orchestration or execution unless the user explicitly re-enables them later.

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

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Local components may observe, execute bounded actions, verify effects, reuse procedures and run bounded specialist perception, but they must not become a second universal planner or expose generic hidden execution.

## Accepted browser foundation

Stage 25.2 remains semantic/native first. Local LFM2.5-VL-450M F16 starts only on the reviewed zero-exact-candidate browser path, is proposal-only and remains behind deterministic target/freshness authorization.

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

#83 executor accepted; #84 latency baseline measured; #85 window-scoped UIA accepted. Controlled Stage 26.1E evidence: 97 scoped resolutions, zero Desktop fallback/binding failures/ambiguities/false/unrelated-window actions, about 3.324 s p50 / 3.720 s p95.

### Stage 26.2A — Production Windows Runtime Foundation — merged #87

Maintained `runtime/windows/` owns bounded actuation, PID/HWND window-scoped UIA and verifier foundation. Physical production benchmark preserved zero false/unrelated-window actions and about 3.410 s p50 / 3.631 s p95.

### Stage 26.2B — Desktop Observation / DesktopState — merged #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

DesktopState is bounded read-only evidence carrying session/application/process/window identity, native coordinate space, controls, frame/screenshot digests, provenance and freshness inputs. It is not authorization.

### Stage 26.2C — Native Desktop LFM2.5-VL Grounder — accepted

Introduced by PR #89. Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054`

Key acceptance:

```text
POSITIVE_GROUNDER_STATUS=proposal
POSITIVE_GROUNDER_REASON=grounder-accepted-ordinal-alias-proposal-only
POSITIVE_INVENTORY_MATCH_COUNT=1
POSITIVE_PASS2_DETECTION_COUNT=1
SAME_FRAME_BINDING_PASS=True
COORDINATE_CONTRACT_PASS=True
TARGET_POINT_INSIDE_UIA_PASS=True
TARGET_EVIDENCE_BINDING_PASS=True
ABSENT_TARGET_ABSTAIN_PASS=True
STALE_FRAME_REJECTION_PASS=True
PROPOSAL_ONLY_CONTRACT_PASS=True
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
VISION_RESTORED_PASS=True
FIXTURE_CLEANUP_PASS=True
PASS=True
```

The model read `1. Benchmark start` as `Benchmark start`. Desktop matching therefore uses exact match first and only a narrowly bounded leading ordinal alias (`N.` / `N)`) when exactly one already-observed inventory label matches. General fuzzy matching is forbidden. Grounder output is proposal-only and never authorizes an action.

## Current critical path

```text
Stage 26.2D UIA -> vision routing + freshness authorization + adversarial accuracy suite
 -> Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27/28 distribution and clean-user release
```

Stage 26.2D must preserve structure-before-pixels, escalate only on a promoted unresolved miss, re-observe before action and keep stale/ambiguous evidence fail-closed. Fixture success is not general Windows accuracy.

## Merge policy

Once a branch is logically complete, intended diff is verified, required physical/CI tests pass and the applicable review/acceptance gate passes, merge it without waiting for a separate merge command. Stop instead on unresolved findings, conflicts, ambiguous scope or failed/skipped required evidence.

## Optional/parallel directions

- Procedure-state dataset + TRM/STARM/FPRM/small-model experiments are optional research only after real verified data and measured need.
- Multi-chat orchestration is a separate upper layer and must not use Codex or Work resources under the current constraint.

## Non-negotiable rules

- ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- model/procedure/observation proposal is not authorization;
- current observed state outranks remembered history;
- verification controls completion;
- stale/ambiguous/UNKNOWN fails closed;
- never persist private chain-of-thought;
- raw desktop capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- release-grade Python/model/OpenAdapt reproducibility is required before stable distribution.

# Start Here — authoritative continuation guide

Use this file first in a fresh ChatGPT or Codex session.

## 1. Resolve live repository state first

Never treat a documentation SHA as permanently current. Resolve live `main`, then inspect relevant PR heads and exact CI/physical evidence.

Current integration line after landing #83–#87:

```text
main = d044926846d9c2e198c906ff5174308da0974b03
```

Current open PR:

```text
#88 Stage 26.2B Desktop Observation / DesktopState
physical runtime head = dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a
state = open, ready for review, not merged
```

The physical acceptance comment for #88 is `5346606994`.

## 2. Read current authoritative context

Read in this order:

1. `project-context/CURRENT_STATE.md`
2. `project-context/ROADMAP.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/MODULE_CATALOG.md`
5. `project-context/KNOWN_ISSUES.md`
6. `project-context/STAGE26_2A_PRODUCTION_WINDOWS_RUNTIME.md`
7. `project-context/STAGE26_2B_DESKTOP_OBSERVATION.md`
8. `project-context/STAGE26_PROCEDURAL_MEMORY.md`
9. older qualification documents only as historical evidence.

When documents disagree, current code/tests + exact PR/CI/physical target evidence outrank prose.

## 3. Product boundary

Ordinary ChatGPT remains the only general planner/intelligence.

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

Do not add desktop/public tool names until the post-desktop ADR. Do not hide native desktop control behind misleading browser semantics.

1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

## 4. Accepted browser foundation

Stage 25/25.1/25.2 established semantic/accessibility-first browser control with local LFM2.5-VL-450M F16 only on the reviewed zero-exact-candidate fallback path.

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Accepted Stage 25.2 target evidence: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors.

## 5. Accepted Stage 26 substrate

Pinned OpenAdapt foundations:

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

Use Flow `Workflow`/`ProgramGraph`; adapt lifecycle under project candidate-first trust; reuse Capture/Windows mechanics where qualified. Do not build duplicate generic recorder/compiler/skill-store/actuator components without a measured blocker.

## 6. Stage 26.1B Capture — accepted

Exact qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

## 7. Stage 26.1C executor — accepted and merged #83

Physical accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Legacy generic exec remains excluded. Bounded typed actions, stale frame/context refusal, focus/fingerprint checks and zero false/unrelated-window actions were physically proven.

## 8. Stage 26.1D / 26.1E — latency blocker found and removed; merged #84/#85

Baseline:

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

Window-scoped result:

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
```

Do not call this universal Windows accuracy; it is controlled WinForms role+name evidence.

## 9. Stage 26.2A production Windows runtime — accepted and merged #87

Production runtime now owns:

```text
runtime/windows/actuation.py
runtime/windows/verifier.py
runtime/windows/window_scoped_uia.py
```

Physical production benchmark preserved 97/97 scoped resolution, zero Desktop fallback/binding failures/false actions and ~3.4 s p50 / ~3.63 s p95 full-cycle latency.

Verifier foundation is `PASS | FAIL | UNKNOWN`. Action delivery alone never means task success.

## 10. Stage 26.2B Desktop Observation / DesktopState — physically accepted, PR #88 open

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-observation-qualification\observation-20260819-184904\result.json`

Accepted read-only result:

```text
SAME_IDENTITY_PASS=True
CONTROL_CONTRACT_PASS=True
SCREENSHOT_DIGEST_PASS=True
FRESHNESS_CONTRACT_PASS=True
BOUNDED_CONTROL_COUNT_PASS=True
OBSERVATION_ONLY_PASS=True
WINDOW_ENUM_CALLS=2
WINDOW_NAME_MATCH_COUNT=2
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
ACTION_COUNT=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
CHROME_SURVIVAL_PASS=True
FIXTURE_CLEANUP_PASS=True
PASS=True
```

`DesktopState` carries identity, coordinate space, bounded UIA controls, observation-only fingerprints, visible text, screenshot digest, frame digest, provenance and freshness evidence. Observation is not authorization and screenshot bytes are not retained in the state.

Scope is controlled WinForms read-only observation, not cross-application UIA coverage and not desktop VLM accuracy.

## 11. Immediate critical path

```text
land #88 only on explicit merge authorization
 -> 26.2C native desktop F16 Grounder
 -> 26.2D UIA -> vision routing + adversarial accuracy suite
 -> 26.2E one real application E2E
 -> 26.3 Verified Procedure Runtime
 -> 26.4 Human Demo -> transferable candidate skill
 -> 27/28 distribution + clean-user stable release
```

### 26.2C invariant

Do not reuse browser CSS/Playwright coordinates for native Windows. Desktop vision receives an exact-window image and returns only a bounded proposal tied to window/frame/coordinate-space evidence.

### 26.2D invariant

Exercise duplicate labels, disabled/hidden targets, wrong window/process, overlays, focus changes, stale/recreated windows, AutomationId, role+name, weak/custom UIA, UIA-missing visual fallback and ambiguous vision -> ABSTAIN before broad accuracy claims.

## 12. Optional / parallel work

Procedure-state dataset and TRM/STARM/FPRM/small-model experiments remain optional research after real verified data and measured need. They are not Stage 27/28 prerequisites.

Multi-Chat/Codex orchestration remains a separate upper layer, outside Windows/procedure safety core.

## 13. Non-negotiable rules

- ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- observation is not authorization;
- model/procedure proposal is not authorization;
- current observed state outranks remembered history;
- verification controls completion;
- stale/ambiguous/UNKNOWN fails closed;
- generic Windows code execution stays disabled/unreachable;
- never persist private chain-of-thought;
- raw desktop capture is sensitive local data;
- preserve credential isolation, Windows root/junction containment and browser network residual-risk tracking;
- use the user only for irreducible target-machine or ordinary-Chat UI gates.

# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Do not treat a documentation SHA as permanently current.

## Operating constraint

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

Current public semantic tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Local Windows components may observe, execute bounded actions, verify effects and later reuse procedures, but they must not become a second autonomous planner or expose generic code execution.

---

# Accepted foundation

## Stage 24 / 24.1 — semantic surface and direct tunnel — ACCEPTED

Five public semantic tools, Windows lifecycle and direct stdio semantic tunnel are accepted foundations.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — ACCEPTED

Accepted local visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Stage 25.2 target evidence remains 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks and 0 errors. Vision is proposal-only and starts only on the reviewed zero-exact-candidate browser path.

---

# Stage 26 accepted evidence

## Stage 26.1A — OpenAdapt core qualification — ACCEPTED

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

Flow `Workflow`/`ProgramGraph` is adopted behind project boundaries; `SkillLibrary` lifecycle is adapted under candidate-first trust; Capture/Windows mechanics are reused where qualified.

## Stage 26.1B — bounded Windows Capture — ACCEPTED

Exact target-tested qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

## Stage 26.1C — hardened typed Windows executor — ACCEPTED / MERGED #83

Physical accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Accepted: authenticated loopback agent, legacy generic exec absent/disabled, bounded typed actions, stale frame/context refusal, focus/fingerprint gates, guarded keyboard/pointer/scroll, layout-independent Unicode typing, zero false and unrelated-window actions.

## Stage 26.1D — warm latency baseline — ACCEPTED / MERGED #84

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

Desktop-wide UIA traversal was the dominant blocker.

## Stage 26.1E — window-scoped UIA — ACCEPTED / MERGED #85

Physical accepted head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

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

This is controlled WinForms role+name evidence, not a claim of universal Windows accuracy.

## Stage 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Physical accepted runtime head before landing:

`6ae5c3a9e624c8c341857c025625b203b796b41c`

Maintained runtime includes bounded actuation, verifier foundation and PID/HWND window-scoped UIA.

Physical production benchmark:

```text
WINDOW_SCOPED_FIND_CALLS=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
FALSE_ACTION_COUNT=0
UNRELATED_WINDOW_ACTION_COUNT=0
p50=3410.031 ms
p95=3630.583 ms
```

Verifier foundation is `PASS | FAIL | UNKNOWN`; action delivery is not task completion.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED

Introduced by PR #88. Exact physically tested runtime head:

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

`DesktopState` is evidence only. Observation/control fingerprints are not executor authorization. Screenshot bytes are not retained in the state; the state carries digest/freshness/provenance evidence.

Scope remains controlled WinForms read-only observation. Real-app coverage, broader AutomationId/custom-control coverage and desktop VLM remain separate future evidence.

---

# Current critical path

1. Stage 26.2C — native desktop LFM2.5-VL Grounder;
2. Stage 26.2D — deterministic UIA -> vision routing plus adversarial accuracy suite;
3. Stage 26.2E — one real medium-complexity application E2E with deterministic postcondition/rollback;
4. Stage 26.3 — Verified Procedure Runtime;
5. Stage 26.4 — Human Demo -> transferable candidate skill;
6. Stage 27/28 — distribution, clean-user E2E and stable release.

## Stage 26.2C next boundary

Do not reuse browser CSS/Playwright coordinates as native Windows coordinates. The desktop Grounder must consume an exact-window image and return only a proposal bound to window/frame/coordinate-space evidence. It never authorizes a click or task completion.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass, and applicable review/acceptance checks are satisfied, merge it without waiting for a separate merge command.

If there is an unresolved finding, conflict, ambiguous scope, failed/skipped required test or unavailable required review evidence, stop and surface the blocker.

---

# Optional / parallel work

Procedure-state datasets and TRM/STARM/FPRM/small-model experiments remain optional research after real verified data and measured need. They are not Stage 27/28 prerequisites.

Multi-chat orchestration remains a separate upper layer. Under the current operating constraint it must not use Codex or Work resources.

---

# Residual risks

- fixture results are not cross-application accuracy evidence;
- desktop Grounder/routing is not yet implemented;
- real application Windows E2E is not accepted;
- procedural runtime/product trust adapter is not integrated;
- screenshot -> coordinate action will remain a narrow freshness/TOCTOU boundary that must fail closed;
- browser DNS/rebinding/private-network isolation remains incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- model/procedure proposal is not authorization;
- observation is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/uncertain/UNKNOWN evidence causes zero mutation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

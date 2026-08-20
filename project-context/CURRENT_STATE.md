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

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Generic Windows code execution remains disabled/unreachable.

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

Stage 25.2 remains structure-first; local vision is proposal-only and starts only on the reviewed zero-exact-candidate browser path.

---

# Stage 26 accepted evidence

## Stage 26.1A — OpenAdapt core qualification — ACCEPTED

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

## Stage 26.1B — bounded Windows Capture — ACCEPTED

Physical qualification head: `7a9daa9329d81994833c22b4ca2e321927527dcc`.

## Stage 26.1C — hardened typed Windows executor — ACCEPTED / MERGED #83

Physical accepted head: `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.

## Stage 26.1D — warm latency baseline — ACCEPTED / MERGED #84

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

Desktop-wide UIA traversal was the dominant blocker.

## Stage 26.1E — window-scoped UIA — ACCEPTED / MERGED #85

Physical accepted head: `66390aca1dadf57c4f11568ec311ad6fcdbd7596`.

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

Controlled WinForms evidence only; not universal Windows accuracy.

## Stage 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Physical accepted runtime head: `6ae5c3a9e624c8c341857c025625b203b796b41c`.

Maintained runtime owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA. Production benchmark preserved zero false/unrelated-window actions with about 3.410 s p50 / 3.631 s p95.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED / MERGED #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-observation-qualification\observation-20260819-184904\result.json`

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

`DesktopState` is evidence only; observation fingerprints are not action authorization. Screenshot bytes are not retained in the state.

## Stage 26.2C — Native Desktop LFM2.5-VL Grounder — ACCEPTED

Introduced by PR #89. Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Physical result:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\result.json`

Exact-window screenshot:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\exact-window.png`

Screenshot SHA-256:

`b32ea145964c64de783077ed43ebc70839fab882bfd83c24931ee0f7fee8d95a`

Accepted evidence:

```text
VISION_READY_PASS=True
VISION_RESTORED_PASS=True
POSITIVE_GROUNDER_STATUS=proposal
POSITIVE_GROUNDER_REASON=grounder-accepted-ordinal-alias-proposal-only
POSITIVE_DECISION=accepted
POSITIVE_INVENTORY_DETECTION_COUNT=2
POSITIVE_INVENTORY_MATCH_COUNT=1
POSITIVE_INVENTORY_LABELS_JSON=["Benchmark start","Guarded list click + scroll"]
POSITIVE_PASS2_DETECTION_COUNT=1
POSITIVE_PASS2_LABELS_JSON=["Benchmark start"]
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
FIXTURE_CLEANUP_PASS=True
PASS=True
```

The local VLM detected the intended button as `Benchmark start` while the rendered fixture label was `1. Benchmark start`. Desktop matching therefore uses exact match first and a narrowly bounded ordinal-prefix alias only after `inventory-absent`; the alias must identify exactly one already-observed inventory label. General fuzzy matching is not used.

Grounder output is proposal-only. It carries exact frame/window/process/coordinate evidence and explicit bounded abstain diagnostics. It does not authorize clicks, continuation or task completion.

Scope remains one controlled WinForms fixture. Cross-application accuracy and action routing are not yet accepted.

---

# Current critical path

1. **Stage 26.2D — deterministic UIA -> vision routing + freshness authorization + adversarial accuracy suite**;
2. Stage 26.2E — one real medium-complexity application E2E with deterministic postcondition/rollback;
3. Stage 26.3 — Verified Procedure Runtime;
4. Stage 26.4 — Human Demo -> transferable candidate skill;
5. Stage 27/28 — distribution, clean-user E2E and stable release.

## Stage 26.2D boundary

Required routing remains:

```text
native/UIA structure first
 -> exact safe element => deterministic path
 -> promoted unresolved miss only
      -> same-session exact-window screenshot
      -> Stage 26.2C Grounder proposal
      -> deterministic same-window / same-frame / target authorization
      -> one bounded action OR ABSTAIN
```

Semantic ambiguity must not automatically escalate to vision. Current observation must be fresh before action. Model proposal is never authorization.

Adversarial coverage must include duplicate labels, disabled/hidden controls, wrong process/window, stale/recreated windows, overlays/focus change, AutomationId, role+name, custom/weak UIA, UIA-missing visual fallback and visual ambiguity -> ABSTAIN. Measure false-action and unrelated-window rates explicitly.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable review/acceptance checks are satisfied, merge it without waiting for a separate merge command.

Stop instead on unresolved findings, conflict, ambiguous scope or failed/skipped required evidence.

---

# Optional / parallel work

Procedure-state datasets and TRM/STARM/FPRM/small-model experiments remain optional research after real verified data and measured need. Multi-chat orchestration remains a separate upper layer and must not use Codex/Work under the current constraint.

---

# Residual risks

- fixture results are not cross-application accuracy evidence;
- UIA -> vision authorization/routing is not yet accepted;
- real application Windows E2E is not accepted;
- procedural runtime/product trust adapter is not integrated;
- screenshot -> coordinate action remains a narrow freshness/TOCTOU boundary that must fail closed;
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

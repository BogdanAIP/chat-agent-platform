# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Exact code/tests/current CI/physical evidence outrank prose.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them.

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

The local platform may observe, execute bounded actions, verify effects, reuse verified procedures and run bounded specialist perception. It must not become a second universal planner, autonomous workflow brain or generic hidden execution channel.

---

# Accepted foundation

## Stage 24 / 24.1 — semantic surface and direct tunnel — ACCEPTED

Five public semantic tools, Windows lifecycle and direct stdio semantic tunnel are accepted foundations. 1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — ACCEPTED

Accepted local visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Vision remains structure-first, proposal-only and behind deterministic authorization.

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

## Stage 26.1E — window-scoped UIA — ACCEPTED / MERGED #85

Physical accepted head: `66390aca1dadf57c4f11568ec311ad6fcdbd7596`.

```text
WINDOW_SCOPED_FIND_CALLS=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
p50=3323.570 ms
p95=3720.061 ms
```

Controlled WinForms evidence only; not universal Windows accuracy.

## Stage 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Physical accepted runtime head: `6ae5c3a9e624c8c341857c025625b203b796b41c`.

Maintained `runtime/windows/` owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA. Production benchmark preserved zero false/unrelated-window actions with about 3.410 s p50 / 3.631 s p95.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED / MERGED #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

DesktopState is bounded read-only evidence carrying session/application/process/window identity, native coordinate space, UIA controls, frame/screenshot digests, provenance and freshness inputs. Observation is not authorization.

## Stage 26.2C — Native Desktop LFM2.5-VL Grounder — ACCEPTED / MERGED #89

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Physical result:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\result.json`

Key evidence:

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
PASS=True
```

The physical result proves only the observed fixture behavior. The rendered `1. Benchmark start` was read by the model as `Benchmark start`; a narrowly bounded ordinal-prefix alias recovered one unique already-observed inventory label. General fuzzy matching is forbidden.

## Stage 26.2D — deterministic UIA -> vision routing — ACCEPTED / MERGED #90

Integration merge:

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted PR head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-routing-qualification\routing-20260820-085625`

Key evidence:

```text
NATIVE_POINT_GUARD_PREFLIGHT_PASS=True
NATIVE_POINT_GUARD_WRONG_WINDOW_REFUSAL_PASS=True
NATIVE_POINT_GUARD_DELIVERY_PASS=True
VISION_DISABLED_ABSTAIN_PASS=True
ROLE_CONFLICT_ABSTAIN_PASS=True
NEGATIVE_ZERO_ACTION_PASS=True
POSITIVE_ROUTE_STATUS=delivered
POSITIVE_ROUTE_REASON=vision-zero-exact-delivered
POSITIVE_CONSISTENCY_IOU=0.34455881673798816
FRESH_REOBSERVATION_PASS=True
GUARDED_CLICK_RECEIPT_PASS=True
FIXTURE_START_POSTCONDITION_PASS=True
FIXTURE_NO_EXTRA_MUTATION_PASS=True
SINGLE_ACTION_PASS=True
STRUCTURAL_EXECUTOR_CALLS=0
COORDINATE_EXECUTOR_CALLS=1
GROUNDER_CALLS=1
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
PASS=True
```

Two exact-window screenshots around inference had identical SHA-256:

`f318c355d0f180968c030cbd25b23947791cb146d5ba8b5a11a1ad7b5e87012f`

This physically proves one structure-first visual-fallback path through VLM proposal, deterministic evidence authorization, fresh same-window frame checks, native foreground/hit-test guard and one guarded click. It is still controlled WinForms evidence, not general application accuracy.

---

# Active release-critical work

## Stage 26.2E — first real application E2E — ACTIVE

Active branch at this snapshot:

`chat/stage26-2e-vscode-real-app-e2e`

The qualification candidate is an isolated VS Code window with a new disposable `.txt` file under a specifically prefixed `%TEMP%` root, an isolated `--user-data-dir`, isolated extensions directory and extensions disabled.

The physical gate may perform exactly one guarded Unicode text delivery after exact PID/HWND/DesktopState/focused-editor/native-point guards pass. Completion is independently verified from the saved file size/SHA-256; the workspace must contain only the expected artifact; a deliberately wrong verifier expectation must map to ABSTAIN before any action; exact window and disposable TEMP root must then be rolled back.

Read:

`project-context/STAGE26_2E_REAL_APPLICATION_E2E.md`

A physical VS Code qualification has not yet been accepted at the time of this document update.

---

# Current critical path

```text
Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27 distribution/maintenance
 -> Stage 28 clean-user E2E / stable release
```

Do not insert a local generic Agent Control Plane/Planner between 26.2E and 26.3. That conflicts with the product boundary: ordinary ChatGPT remains the only general planner/intelligence.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable acceptance gates are satisfied, merge it without waiting for a separate merge command.

Stop on unresolved findings, conflict, ambiguous scope or failed/skipped required evidence.

---

# Residual risks

- one controlled WinForms routing PASS is not broad real-application evidence;
- Stage 26.2E real application E2E is not yet accepted;
- `AutomationId` still lacks dedicated accepted physical coverage across real applications;
- verified procedural runtime/product trust adapter is not integrated;
- browser DNS/rebinding/redirect/private-network isolation remains incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- model/procedure/observation proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/uncertain/UNKNOWN evidence causes zero mutation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.
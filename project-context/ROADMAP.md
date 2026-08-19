# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the only general intelligence/planning layer while the local platform supplies bounded observation, execution, verification, procedural memory and optional specialist inference.

```text
ordinary ChatGPT
  = task understanding / strategy / adaptation / escalation

Chat Agent Platform
  = scoped files/browser/windows capabilities
  + deterministic/native observation
  + bounded local vision fallback
  + authorization and guarded execution
  + verification
  + non-agentic procedural memory
  + optional specialized local reasoning later
```

The product must not become a second autonomous agent brain, a generic hidden workflow dispatcher or an unbounded local code-execution gateway.

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Any desktop/public-contract change waits for an explicit post-desktop ADR.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources for development, review, orchestration or execution unless the user explicitly re-enables them later.

---

# Completed foundation

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Secure MCP Tunnel + official tunnel-client + local MCP round trip accepted.

## Stage 22 — Remove superseded universal platform core — DONE

Obsolete universal Rust/Python/custom-ingress core removed from active architecture.

## Stage 23 — Quality-first module selection — DONE

Focused Filesystem/Playwright/1MCP candidates and selection rules accepted.

## Stage 24 / 24.1 — Windows lifecycle + stable semantic surface + direct tunnel — DONE

Normal path:

```text
ChatGPT
 -> Secure MCP Tunnel
 -> official tunnel-client
 -> secure semantic launcher
 -> direct stdio semantic-projection
 -> focused local backends/adapters
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — DONE

Accepted visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Stage 25.2 accepted target result: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors. Vision remains proposal-only and only starts on the reviewed zero-exact-candidate browser path.

---

# Stage 26 — Windows capability + verified procedural memory — ACTIVE

The active order is production Windows capability first, then real-app evidence, then procedural integration.

## Stage 26.0 — UI-Mate analysis + procedural architecture — DONE

UI-Mate remains a demonstration-guided workflow/state reference, not a second GUI planner.

## Stage 26.1A — OpenAdapt core qualification — ACCEPTED

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
```

Flow `Workflow`/`ProgramGraph`: ADOPT behind project boundaries. `SkillLibrary` lifecycle: ADAPT under candidate-first trust. Capture/Windows mechanics: reuse where qualified.

## Stage 26.1B — bounded Windows Capture — ACCEPTED

Physical qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Accepted bounded interactive-session capture, raw UIA evidence, compile path, scoped structural suppression, zero foreign structural-window evidence, explicit refusal of unaccepted replay and clean local artifact handling.

## Stage 26.1C — hardened typed Windows executor — ACCEPTED / MERGED #83

Physical accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Accepted boundary: loopback/auth, legacy generic exec disabled/unreachable, bounded typed input, stale frame/context refusal, UIA uniqueness, fingerprint/focus gates, guarded pointer/keyboard/scroll, zero false/unrelated-window actions.

## Stage 26.1D — warm Windows latency baseline — ACCEPTED / MERGED #84

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

Root cause: repeated desktop-wide UIA traversal.

## Stage 26.1E — window-scoped UIA resolver — ACCEPTED / MERGED #85

Physical accepted head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

```text
WINDOW_SCOPED_FIND_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
p50=3323.570 ms
p95=3720.061 ms
```

This is controlled WinForms role+name evidence, not universal Windows accuracy.

## Stage 26.1F — land qualification stack — DONE

#83 -> #84 -> #85 were safely landed by retargeting/rechecking downstream diffs and CI after squash history changes.

## Stage 26.1G — authoritative context synchronization — DONE / MERGED #86

Authoritative roadmap/architecture/current-state context was synchronized before production Windows work.

## Stage 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Maintained runtime owns:

```text
runtime/windows/actuation.py
runtime/windows/verifier.py
runtime/windows/window_scoped_uia.py
```

Physical production head:

`6ae5c3a9e624c8c341857c025625b203b796b41c`

Physical production benchmark:

```text
WINDOW_SCOPED_FIND_CALLS=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0
p50=3410.031 ms
p95=3630.583 ms
```

Verifier foundation:

```text
observe before
 -> authorize
 -> act
 -> observe after
 -> PASS | FAIL | UNKNOWN
```

Executor delivery is never equivalent to task success.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED

Introduced by PR #88. Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Evidence:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-observation-qualification\observation-20260819-184904\result.json`

Physically measured result:

```text
SAME_IDENTITY_PASS=True
CONTROL_CONTRACT_PASS=True
SCREENSHOT_DIGEST_PASS=True
FRESHNESS_CONTRACT_PASS=True
BOUNDED_CONTROL_COUNT_PASS=True
WINDOW_ENUM_CALLS=2
WINDOW_NAME_MATCH_COUNT=2
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
CHROME_PROCESS_COUNT_BEFORE=11
CHROME_PROCESS_COUNT_AFTER=11
CHROME_SURVIVAL_PASS=True
FIXTURE_CLEANUP_PASS=True
PASS=True
```

Canonical DesktopState carries session/application/process/window identity, native physical coordinate space, bounded controls, focused control, visible text, observation-only fingerprints, screenshot/frame digests, observed-at timestamp, provenance/freshness evidence and observed capabilities.

Observation and observation fingerprints are evidence, never action authorization. Screenshot bytes are not retained by DesktopState.

Self-review corrected the first qualification reporting: `OBSERVATION_ONLY_PASS=True` and `ACTION_COUNT=0` / related fields were constants in the harness, not instrumented measurements, so they are excluded from physical acceptance. The read-only claim is supported separately by code review and CI source-boundary tests that show the observer and driver expose no executor/actuation channel. Future qualification output binds observer/driver SHA-256 and reports only derived measurements.

Scope: controlled WinForms read-only evidence only. Cross-application UIA coverage and desktop VLM accuracy remain future gates.

---

# NEXT — Stage 26.2C: native desktop LFM2.5-VL Grounder

Do not reuse the browser CSS/Playwright coordinate adapter as if native Windows used the same coordinate system.

Target seam:

```text
locate(
  window_png,
  target_text,
  window_bounds,
  optional_uia_evidence
) -> GrounderProposal | None
```

Proposal evidence must bind to at least:

```text
point / bounded region
screen/window coordinate space
frame_digest
window identity
target evidence
confidence
```

The Grounder never returns authority such as `click`, `continue workflow` or `task complete`.

Acceptance must prove exact-window pixels only; correct native coordinate transform; stale/wrong-window refusal; local/on-demand model lifecycle; zero actuation inside the Grounder; ambiguity -> None/ABSTAIN; and explicit separation from browser coordinate contracts.

Use current `mss.MSS` API rather than the deprecated `mss.mss` path seen in the original Stage 26.2B qualification run.

---

# Stage 26.2D — UIA -> vision routing + adversarial accuracy suite

Routing pattern:

```text
native/UIA exact evidence
 -> deterministic action path
 -> promoted unresolved miss only
      -> current exact-window image
      -> bounded Grounder proposal
      -> same-window / same-frame / target authorization
      -> action OR ABSTAIN
```

Adversarial coverage before broad claims includes duplicate labels, disabled/hidden controls, wrong process/window, same/similar titles, overlays, focus changes, stale/recreated windows, AutomationId, role+name, custom/weak UIA, UIA-missing visual fallback and visual ambiguity -> ABSTAIN.

Metrics include target resolution success, false-action rate, unrelated-window action rate, safe-abstain behavior and p50/p95 latency. Do not convert fixture success into global desktop accuracy.

---

# Stage 26.2E — first real application E2E

Use one real medium-complexity user application with a disposable artifact, deterministic postcondition and clean rollback. Candidate names such as VS Code, OriginPro or Reaper are examples, not architecture.

Acceptance:

```text
false actions = 0
unrelated-window actions = 0
current-state verification = PASS
completion verification = PASS
recoverable mismatch = ABSTAIN rather than blind continuation
```

---

# Stage 26.3 — Verified Procedure Runtime

Only after real Windows application E2E:

```text
ChatGPT
 -> choose applicable procedure
 -> load ProgramGraph
 -> observe current state
 -> resolve next abstract transition
 -> authorization
 -> execution
 -> verify effect
 -> advance / recover / ABSTAIN
```

Priority:

```text
current observed state
 > current goal/verifier criteria
 > trusted procedural evidence
 > raw historical action sequence
```

## Stage 26.3A — candidate-first procedural trust

```text
DEMO
 -> CAPTURE
 -> COMPILE
 -> CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantined/disabled as evidence degrades
```

One demonstration never becomes permanent trust automatically.

## Stage 26.3B — advanced verifier/postcondition library

Expand Stage 26.2A verifier foundation for UI state, files, windows, applications, browser state, artifacts and structured outputs.

---

# Stage 26.4 — Human Demo -> Transferable Skill

```text
human demonstration
 -> OpenAdapt Capture
 -> structured trajectory
 -> ProgramGraph
 -> project CANDIDATE
 -> verified replay
 -> related changed-state/task replay
```

Acceptance is not blind macro replay. Vary filename/window order/modest layout while preserving task semantics; current state remains authoritative.

---

# Optional Research Track R — not release-critical

Procedure-state datasets and SpecializedReasoningBackend experiments begin only if real verified data and measurements justify them. Compare deterministic baseline with useful small-model families such as TRM/STARM/FPRM/future recursive approaches. A tiny model proposes; authorization/executor/verifier remain authoritative.

---

# Parallel Track M — multi-chat orchestration

Separate upper layer, not part of Windows/procedure safety core and not a release prerequisite. Under the current operating constraint it may coordinate ordinary ChatGPT sessions only; Codex and Work resources are disabled unless the user explicitly re-enables them.

---

# Merge policy

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable review/acceptance checks should be merged without waiting for a separate merge command.

Do not auto-merge when there is an unresolved finding, conflict, ambiguous scope, failed/skipped required test, or unavailable required review evidence. Surface the blocker instead.

---

# Public MCP contract — post-desktop ADR

Only after the Windows desktop surface exists decide whether the five current tools remain sufficient or a few truthful coarse desktop/procedure capabilities are needed.

Never preserve the tool count by hiding native desktop control behind `web_interact`, and never add generic `tool_invoke`/`run_anything`/opaque workflow execution.

---

# Stage 27 — Distribution & Maintenance

Installer/update/repair/doctor/uninstall/rollback/restart recovery/key rotation/artifact validation/lifecycle UI. Release-grade Python/model/OpenAdapt reproducibility is required here.

# Stage 28 — Clean User E2E / first stable release

Fresh-user flow must work without git checkout or developer-only Python/PowerShell setup.

---

# Cross-cutting invariants

- ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- observation is not authorization;
- model/procedure proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/ambiguous/UNKNOWN causes zero mutation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve credential isolation and Windows root/junction containment;
- track browser DNS/redirect/private-network residual risk;
- use the user only for irreducible target-machine or ordinary-Chat UI gates;
- keep `main` as integration line and preserve exact physical evidence heads.

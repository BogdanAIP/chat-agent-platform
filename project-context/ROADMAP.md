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

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them later.

---

# Completed foundation

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Secure MCP Tunnel + official tunnel-client + local MCP round trip accepted.

## Stage 22 — Remove superseded universal platform core — DONE

Obsolete universal Rust/Python/custom-ingress core removed from active architecture.

## Stage 23 — Quality-first module selection — DONE

Focused Filesystem/Playwright/1MCP candidates and selection rules accepted.

## Stage 24 / 24.1 — Windows lifecycle + stable semantic surface + direct tunnel — DONE

1MCP remains internal diagnostic/adaptive/aggregation infrastructure; the normal public path is direct semantic-projection.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — DONE

Accepted visual baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Stage 25.2 accepted target result: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors. Vision remains proposal-only and starts only on the reviewed zero-exact-candidate browser path.

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

## Stage 26.1B — bounded Windows Capture — ACCEPTED

Physical qualification head: `7a9daa9329d81994833c22b4ca2e321927527dcc`.

## Stage 26.1C — hardened typed Windows executor — ACCEPTED / MERGED #83

Physical accepted head: `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.

## Stage 26.1D — warm Windows latency baseline — ACCEPTED / MERGED #84

```text
p50 = 183606.855 ms
p95 = 185567.403 ms
```

## Stage 26.1E — window-scoped UIA resolver — ACCEPTED / MERGED #85

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

Controlled WinForms role+name evidence only; not universal Windows accuracy.

## Stage 26.1F — land qualification stack — DONE

#83 -> #84 -> #85 safely landed.

## Stage 26.1G — authoritative context synchronization — DONE / MERGED #86

Authoritative roadmap/architecture/current-state context synchronized before production Windows work.

## Stage 26.2A — Production Windows Runtime Foundation — ACCEPTED / MERGED #87

Maintained runtime owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA.

Physical production head: `6ae5c3a9e624c8c341857c025625b203b796b41c`.

Production benchmark preserved zero false/unrelated-window actions with about 3.410 s p50 / 3.631 s p95.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED / MERGED #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

Canonical DesktopState carries session/application/process/window identity, native physical coordinate space, bounded controls, focused control, visible text, observation-only fingerprints, screenshot/frame digests, observed-at timestamp, provenance/freshness evidence and observed capabilities.

Observation and observation fingerprints are evidence, never action authorization.

## Stage 26.2C — Native Desktop LFM2.5-VL Grounder — ACCEPTED

Introduced by PR #89. Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Physical result directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054`

Key result:

```text
POSITIVE_GROUNDER_STATUS=proposal
POSITIVE_GROUNDER_REASON=grounder-accepted-ordinal-alias-proposal-only
POSITIVE_DECISION=accepted
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

Accepted desktop label policy:

```text
exact inventory label first
 -> if inventory-absent only:
      remove one leading UI ordinal N. / N)
      -> exactly one already-observed inventory label => continue
      -> zero or multiple => ABSTAIN
```

There is no general fuzzy/Levenshtein/similarity matching. The Grounder returns only a bounded proposal/ABSTAIN with full frame/window/process/coordinate evidence and never authorizes an action.

This remains controlled WinForms evidence, not general desktop accuracy.

---

# NEXT — Stage 26.2D: deterministic UIA -> vision routing + adversarial accuracy suite

Required routing:

```text
native/UIA structure first
 -> exact safe element => deterministic path
 -> promoted unresolved miss only
      -> current same-session exact-window image
      -> Stage 26.2C Grounder proposal
      -> re-observe current state
      -> deterministic same-window / same-frame / target authorization
      -> one bounded action OR ABSTAIN
```

Semantic ambiguity must not automatically escalate to vision. The Grounder proposes; Stage 26.2D authorization decides whether a proposal is still fresh, uniquely bound and safe to execute.

Required freshness/identity binding includes at least:

```text
session_id
application_identity
process_id
process_generation
window_handle
window_instance
frame_digest / screenshot_digest
coordinate space
current target evidence
```

Adversarial coverage before broad claims includes:

- duplicate labels and ordinal aliases;
- disabled/hidden controls;
- wrong process/window and same/similar titles;
- window movement/recreation and stale frame/context;
- overlays and focus changes;
- AutomationId and role+name;
- custom/weak UIA;
- UIA-missing visual fallback;
- visual ambiguity -> ABSTAIN;
- target disappears between proposal and action;
- unrelated-window mutation must remain zero.

Metrics include resolution success, false-action rate, unrelated-window action rate, correct safe-abstain behavior and p50/p95 latency. Do not convert fixture success into global desktop accuracy.

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

Human demonstration -> Capture -> structured trajectory -> ProgramGraph -> project CANDIDATE -> verified changed-state replay. Acceptance is not blind macro replay.

---

# Optional Research Track R — not release-critical

Procedure-state datasets and SpecializedReasoningBackend experiments begin only if real verified data and measurements justify them. A tiny model proposes; authorization/executor/verifier remain authoritative.

# Parallel Track M — multi-chat orchestration

Separate upper layer, not part of Windows/procedure safety core and not a release prerequisite. Under the current constraint it may coordinate ordinary ChatGPT sessions only; Codex and Work are disabled unless explicitly re-enabled.

---

# Merge policy

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable review/acceptance checks should be merged without waiting for a separate merge command.

Do not auto-merge on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

---

# Public MCP contract — post-desktop ADR

Only after the Windows desktop surface exists decide whether the five current tools remain sufficient or a few truthful coarse desktop/procedure capabilities are needed. Never hide native desktop actions behind `web_interact` and never add generic `tool_invoke`/`run_anything`/opaque workflow execution.

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
- keep `main` as integration line and preserve exact physical evidence heads.

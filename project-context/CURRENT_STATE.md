# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Exact code/tests/current CI/physical evidence outrank prose.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them.

## Product boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. The local platform has a deterministic execution **Control Plane**, not a second current general-planning brain.

```text
ordinary ChatGPT
  task interpretation / strategy / adaptation
        |
        v
OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
        |
        v
local deterministic execution Control Plane + focused capabilities
```

The Control Plane may keep TaskState/checkpoints, advance a selected verified procedure through already-defined transitions, authorize each consequence, verify effects, apply bounded retry/recovery/resource budgets and escalate. It must ABSTAIN/escalate when current evidence does not uniquely match an allowed transition or new strategy is required.

A true local planner is future optional Track P, not current production architecture and not a Stage 27/28 prerequisite. See `CONTROL_PLANE.md`.

Current public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

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

The qualification candidate is an isolated VS Code window with a new disposable `.txt` file under a specifically prefixed `%TEMP%` root, isolated `--user-data-dir`, isolated extensions directory and extensions disabled.

The physical gate may perform exactly one guarded Unicode text delivery after exact PID/HWND/DesktopState/focused-editor/native-point guards pass. A deliberately wrong verifier expectation must map to ABSTAIN before any action. Immediately before typing, a fresh DesktopState must preserve the same exact window identity and focused-editor observation fingerprint. Completion is independently verified from the saved file size/SHA-256; the workspace must contain only the expected artifact. The exact qualification window is closed with `WM_CLOSE`; success additionally requires the `--wait` CLI to exit naturally with return code `0`, with `FORCED_CLI_CLEANUP=False`, before the disposable TEMP root is considered rolled back.

If the run fails before a bound HWND is established, cleanup is limited to windows carrying that run's randomized qualification filename. Forced CLI terminate/kill is cleanup only and can never satisfy `CLI_PROCESS_EXIT_PASS`.

Read:

`project-context/STAGE26_2E_REAL_APPLICATION_E2E.md`

A physical VS Code qualification has not yet been accepted.

### CI integrity finding fixed in this PR

Self-review found that the Windows `ci` PowerShell step could report success even when `python -m unittest` returned nonzero, because a later successful native command overwrote `$LASTEXITCODE`. The workflow now checks native-command exit codes explicitly and throws on failure. The previously hidden test failures were corrected without weakening production safety contracts. Exact-head CI must pass with this repaired propagation before the physical gate is considered ready.

---

# Current critical path

```text
Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime / deterministic execution Control Plane
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
    -> checkpoint / bounded recovery / resource-budget integration
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27 distribution/maintenance
 -> Stage 28 clean-user E2E / stable release
```

The deterministic Control Plane is not a second current general planner. It progresses only selected known procedure transitions under current-state authorization and verification. Novel strategy remains with ChatGPT.

Future optional Track P may later evaluate a local planner in shadow/bounded/general modes after verified procedure-state data and measured need. It remains behind the same authorization/verifier boundary.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable acceptance gates are satisfied, merge it without waiting for a separate merge command.

Stop on unresolved findings, conflict, ambiguous scope or failed/skipped required evidence.

---

# Residual risks

- one controlled WinForms routing PASS is not broad real-application evidence;
- Stage 26.2E physical real-app E2E is not yet accepted;
- `AutomationId` still lacks dedicated accepted physical coverage across real applications;
- Verified Procedure Runtime/Control Plane product trust adapter is not integrated;
- browser DNS/rebinding/redirect/private-network isolation remains incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- future local planner has not been researched against verified procedure-state data;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane may advance only already-defined authorized+verified procedure transitions;
- new strategy/ambiguity/stale/UNKNOWN -> ABSTAIN/escalate;
- semantic/native structure before pixels where reliable;
- model/procedure/observation proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

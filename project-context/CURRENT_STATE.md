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

Maintained `runtime/windows/` owns bounded actuation, verifier foundation and PID/HWND window-scoped UIA.

## Stage 26.2B — Desktop Observation / DesktopState — ACCEPTED / MERGED #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

DesktopState is bounded read-only evidence carrying session/application/process/window identity, native coordinate space, UIA controls, frame/screenshot digests, provenance and freshness inputs. Observation is not authorization.

## Stage 26.2C — Native Desktop LFM2.5-VL Grounder — ACCEPTED / MERGED #89

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

Grounder remains proposal-only and exact-window/evidence-bound.

## Stage 26.2D — deterministic UIA -> vision routing — ACCEPTED / MERGED #90

Integration merge before 26.2E:

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted PR head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

This physically proves one controlled structure-first visual-fallback path with deterministic evidence authorization, fresh same-window checks, native foreground/hit-test guard and one guarded click. It is not general application accuracy.

## Stage 26.2E — first real application E2E — ACCEPTED / PR #91

Exact physically accepted qualification head:

`457db0b634f2e47f53d41e359a238840fa3ca2ee`

Physical result directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448`

Accepted task: isolated VS Code + one disposable `.txt` under a specifically prefixed `%TEMP%` root.

Key physical evidence:

```text
PROJECT_HEAD=457db0b634f2e47f53d41e359a238840fa3ca2ee
WINDOW_BINDING_PASS=True
DESKTOP_OBSERVATION_PASS=True
FOCUSED_EDITOR_PRECONDITION_PASS=True
FOCUSED_EDITOR_ROLE=textbox
FRESH_PRE_ACTION_STATE_PASS=True
NATIVE_POINT_GUARD_PASS=True
KEYBOARD_FOCUS_GUARD_MODE=window_scoped_focused_observation_fingerprint
KEYBOARD_FOCUS_GUARD_ARMED_PASS=True
KEYBOARD_FOCUS_GUARD_PASS=True
MISMATCH_PROBE_VERIFICATION_STATUS=fail
MISMATCH_PROBE_DECISION=abstain
MISMATCH_PROBE_ZERO_ACTION_PASS=True
GUARDED_KEYBOARD_DELIVERY_PASS=True
KEYBOARD_ACTION_COUNT=1
COMPLETION_VERIFICATION_STATUS=pass
COMPLETION_VERIFICATION_PASS=True
CURRENT_STATE_VERIFICATION_PASS=True
WORKSPACE_EXPECTED_ONLY_PASS=True
KEYBOARD_FOCUS_GUARD_ARMS=1
KEYBOARD_FOCUS_GUARD_CALLS=1
KEYBOARD_FOCUS_GUARD_PASSES=1
KEYBOARD_FOCUS_GUARD_FAILURES=0
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
CLEANUP_REVALIDATION_PASS=True
APPLICATION_CLEANUP_PASS=True
CLI_PROCESS_RETURNCODE=0
CLI_PROCESS_EXIT_PASS=True
FORCED_CLI_CLEANUP=False
APP_ROOT_CLEANUP_PASS=True
ROLLBACK_PASS=True
STAGE26_2E_REAL_APPLICATION_E2E_RESULT=PASSED
QUALIFICATION_EXIT_CODE=0
```

Important real-app finding: Monaco's true keyboard target is an intentionally hidden `textbox` with zero geometry. Production authorization now binds the exact hidden focused observation fingerprint inside the exact PID/HWND/process-generation window. The top-level point guard remains a separate foreground/root-window guard and is not treated as Monaco control geometry.

This proves one real VS Code text-edit task with independent postcondition and rollback. It does not prove universal desktop accuracy.

---

# Active release-critical work

## Stage 26.3 — Verified Procedure Runtime / deterministic execution Control Plane — ACTIVE

The next problem is no longer “can the Windows runtime perform one safe real-app action?” That is now physically accepted.

The next problem is **autonomous verified progression of a known procedure without using the user as a PowerShell operator**.

Target flow:

```text
user gives one goal to ordinary ChatGPT
 -> ChatGPT selects an allowed known procedure + parameters
 -> local deterministic Control Plane
      load ProgramGraph
      bind TaskState/checkpoint
      observe current state
      select exactly one permitted known transition
      authorize action from current evidence
      execute bounded capability
      re-observe
      verify postcondition
      checkpoint + advance
      repeat while state remains known/permitted
 -> verified completion
    OR ABSTAIN/escalation to ChatGPT
```

The first end-to-end Stage 26.3 acceptance should specifically remove intermediate manual command entry. One user goal should be enough to initiate a bounded known procedure; the platform should continue deterministic transitions and return completion/evidence or a truthful escalation.

### Stage 26.3A — candidate-first procedural trust

A successful trajectory may become a project CANDIDATE, but never permanent trust from one demonstration alone:

```text
DEMO / successful trajectory
 -> CAPTURE
 -> COMPILE
 -> CANDIDATE
 -> replay / regression / variant evidence
 -> trusted reusable
 -> stale / quarantined / disabled / rollback as evidence degrades
```

### Stage 26.3B — advanced verifier/postcondition library

Expand deterministic completion evidence for UI, files/artifacts, process/window/application state, browser state and structured outputs.

### Stage 26.3C — checkpoints / bounded recovery / budgets

Longer procedures require explicit checkpoints, retry ceilings, safe known recovery branches, action/time/resource budgets and deterministic escalation reasons.

## Stage 26.4 — Human Demo -> transferable verified candidate skill

Human demonstration transfer follows only after the verified procedure runtime is accepted. Live re-resolution and verifier-controlled progression are required; macro replay is insufficient.

---

# Current critical path

```text
Stage 26.2E real application E2E — ACCEPTED
 -> Stage 26.3 Verified Procedure Runtime / deterministic execution Control Plane — ACTIVE
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

- one real VS Code task is not broad real-application coverage;
- `AutomationId` still lacks dedicated accepted physical coverage across real applications;
- Verified Procedure Runtime/Control Plane is not yet integrated or physically accepted;
- ordinary Chat -> local autonomous procedure execution without intermediate user commands is not yet physically accepted;
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

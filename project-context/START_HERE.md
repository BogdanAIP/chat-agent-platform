# Start Here — authoritative continuation guide

Use this file first in a fresh ordinary ChatGPT session.

## Resolve live repository state first

Never treat a documentation SHA as permanently current. Resolve live `main`, then inspect open PR heads relevant to the task.

## Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ROADMAP.md`
4. `project-context/ARCHITECTURE.md`
5. `project-context/MODULE_CATALOG.md`
6. `project-context/KNOWN_ISSUES.md`
7. active stage document as needed

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them later.

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

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Local components may observe, execute bounded actions, verify effects, reuse verified procedures and run bounded specialist perception, but they must not become a second universal planner or expose generic hidden execution.

## Accepted browser foundation

Stage 25.2 remains semantic/native first. Local LFM2.5-VL-450M F16 starts only on reviewed bounded visual paths, is proposal-only and remains behind deterministic target/freshness authorization.

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16
CPU 8 threads
ctx 2048
```

## Accepted Windows foundation

### Stage 26.1A / 26.1B

```text
openadapt-flow 1.31.0 @ d7f58d9f35c8369f16a9b378f23952d425334ad7
openadapt-capture 1.2.2 @ bcf12942d61d66b64d94e645e9124273a5cc5963
Capture qualification head = 7a9daa9329d81994833c22b4ca2e321927527dcc
```

### Stage 26.1C–26.1E — merged #83/#84/#85

Typed executor accepted; warm latency blocker measured; window-scoped UIA accepted. Controlled Stage 26.1E evidence: 97 scoped resolutions, zero Desktop fallback/binding failures/ambiguities/false/unrelated-window actions, about 3.324 s p50 / 3.720 s p95.

### Stage 26.2A — production Windows runtime — merged #87

Maintained `runtime/windows/` owns bounded actuation, PID/HWND window-scoped UIA and verifier foundation.

### Stage 26.2B — DesktopState — merged #88

Exact physically tested runtime head:

`dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a`

DesktopState is bounded read-only evidence carrying session/application/process/window identity, controls, coordinate space, frame/screenshot digests, provenance and freshness inputs. It is not authorization.

### Stage 26.2C — native desktop Grounder — merged #89

Exact physically accepted runtime head:

`eadf8ff5a873936441891a66b616c83c62736152`

The Grounder is exact-window proposal/ABSTAIN only. The physical fixture established the observed `1. Benchmark start` -> `Benchmark start` ordinal-prefix case; only one narrowly bounded ordinal alias is permitted after inventory-absent. No general fuzzy matching.

### Stage 26.2D — deterministic Windows vision routing — merged #90

Current integration line at this snapshot:

`main = 42d4130d59e23e2c2b1771ac428467efe27a4b98`

Exact physically accepted #90 head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-routing-qualification\routing-20260820-085625`

The physical run proved one real structure-first visual-fallback click with request/UIA/process/window/frame binding, `POSITIVE_CONSISTENCY_IOU=0.34455881673798816`, identical exact-window screenshots around inference, fresh re-observation, native foreground/WindowFromPoint guard, backend frame guard, exactly one coordinate executor delivery and clean fixture/runtime restore. Wrong-window, no-promotion and role-conflict probes refused before mutation.

This is controlled WinForms evidence, not broad application accuracy.

## Active work — Stage 26.2E real application E2E

At this snapshot the active branch is:

`chat/stage26-2e-vscode-real-app-e2e`

The qualification candidate is isolated VS Code. It uses only a specifically prefixed `%TEMP%` root, an isolated VS Code user-data directory, isolated extensions directory and one new disposable `.txt` file.

The gate may perform exactly one guarded Unicode text delivery after exact Code.exe PID/HWND/DesktopState/focused-editor/native-point checks. A deliberately wrong verifier expectation must produce FAIL -> ABSTAIN with zero action. Completion is independently verified from the autosaved file's exact size/SHA-256; the workspace must contain only the expected file; then the exact qualification window and isolated TEMP root must be rolled back.

Read:

`project-context/STAGE26_2E_REAL_APPLICATION_E2E.md`

A physical VS Code qualification is not accepted until its exact branch head passes CI and the target-machine run.

## Current critical path

```text
Stage 26.2E real application E2E
 -> Stage 26.3 Verified Procedure Runtime
    -> 26.3A candidate-first procedural trust
    -> 26.3B advanced verifier/postcondition library
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27/28 distribution and clean-user release
```

Do not replace Stage 26.3 with a local general Agent Control Plane/Planner. Ordinary ChatGPT remains the planner; local procedure machinery is bounded, non-agentic support.

## Merge policy

Once a branch is logically complete, intended diff is verified, required physical/CI tests pass and applicable acceptance gates pass, merge it without waiting for a separate merge command. Stop instead on unresolved findings, conflict, ambiguous scope or failed/skipped required evidence.

## Non-negotiable rules

- ordinary ChatGPT is the only general planner/intelligence;
- semantic/native structure before pixels where reliable;
- model/procedure/observation proposal is not authorization;
- current observed state outranks remembered history;
- verification controls completion;
- stale/ambiguous/UNKNOWN fails closed;
- never persist private chain-of-thought;
- raw desktop capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- release-grade Python/model/OpenAdapt reproducibility is required before stable distribution.
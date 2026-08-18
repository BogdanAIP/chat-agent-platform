# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT as the intelligence layer while local capabilities remain replaceable MCP modules or focused adapters. Do not expose hundreds of raw tools or run heavyweight local components permanently.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE
Secure MCP Tunnel + official tunnel-client + local MCP round trip accepted.

## Stage 22 — Remove superseded universal platform core — DONE
Obsolete universal Rust/Python/custom-ingress core removed; historical implementation remains in Git.

## Stage 23 — Quality-first module selection — DONE
Accepted Windows Filesystem/Playwright/1MCP candidates and selection rules.

## Stage 24 — Windows lifecycle + stable semantic Chat surface — DONE
Merged as `175d36236f80a1f99f091d4f031a1c6255f3652b` (#66). Public tools remain exactly `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`.

## Stage 24.1 — Direct semantic tunnel A/B — DONE
Merged as `df1d5e232b739b62e72ad81e5d82fd01be53e884` (#70). Normal path is ChatGPT -> Secure MCP Tunnel -> tunnel-client -> secure semantic launcher -> direct stdio semantic-projection. 1MCP stays internal diagnostic/adaptive/aggregation infrastructure.

## Stage 25 — Safe local vision grounding benchmark — DONE FOR BASELINE

PR #73 merged as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target configuration: llama.cpp `b10448/ad1de39e0`, LFM2.5-VL-450M F16 + F16 mmproj, CPU 8 threads, ctx 2048. Target result with Chrome running: Search/Send/state HIT; Gamma/tiny safe ABSTAIN; absent Export CSV correct ABSTAIN; 0 false clicks; 0 provider/context errors; 3/5 present-target HIT.

## Stage 25.1 — Same-session visual fallback foundation — DONE

PR #74 squash-merged to `main` as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Final reviewed target production-code HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

Accepted foundations include same-session screenshot/freshness/coordinate-action, TTL/capped prepared targets, focused llama.cpp lifecycle ownership, PID-bound loopback listener verification, class-aware fail-closed visual policy, secure installed semantic runtime, lock-hash-enforced `npm ci`, junction containment, bounded literal-IP browser policy and CodeQL across Actions/JavaScript/Python.

Accepted RAM policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

Final reviewed Stage 25.1 run: 3/3 expected HIT, 3/3 required ABSTAIN, 0 false clicks, 0 errors, minimum observed free physical RAM 0.60 GB, no safety stop, runtime stopped, Chrome alive.

## Stage 25.2 — Ordinary Chat semantic → vision escalation — ACCEPTED FOR MERGE

PR #77 integrates the Stage 25.1 vision foundation into the existing public `web_interact` without adding a sixth public tool, second planner, generic inference gateway or catch-all click-error fallback.

Final reviewed production-code HEAD: `41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

Accepted routing boundary:

```text
fresh accessibility snapshot
  -> 1 exact enabled button: semantic click; VLM does not start
  -> same-name buttons with exactly 1 enabled + disabled alternatives: semantic click
  -> disabled/non-button/ambiguous semantic target: ABSTAIN; VLM does not start
  -> 0 exact candidates: reviewed text-labeled same-session visual fallback
       -> target-blind button inventory
       -> local deterministic authorization
       -> freshness proof
       -> one coordinate click OR ABSTAIN
```

Important authorization rules:

- `targetText` is the semantic and visual anchor;
- planner-supplied `kind` is never accepted;
- planner `target` and free-form `instruction` cannot redirect visual grounding;
- router generates the canonical visual instruction from `targetText`;
- generic semantic click errors never escalate to vision;
- icon-only, repeated-row, tiny targets and semantic ambiguity are not automatically visually promoted by Stage 25.2;
- public semantic surface remains exactly five tools.

Final target-laptop evidence with normal Chrome workload open:

```text
semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true
Doctor physical free RAM = 2.62 GB
Doctor virtual free RAM = 8.129 GB
minimum observed free physical RAM = 1.04 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
STAGE25_2_FINAL_REVIEW_RESULT = PASSED
```

Result path: `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json`.

All 9 workflow families triggered for final Stage 25.2 code HEAD were green before documentation sync.

## Stage 26 — Professional application capability benchmarks — NEXT

Move from browser fixtures to real product workflows. Benchmark Windows UI and representative professional applications behind the same semantic-first/fail-closed capability philosophy. Initial candidates: Origin, REAPER, FFmpeg, Blender and broader Windows UI.

The purpose is not to expose application internals as hundreds of raw tools. Define focused capabilities and prove useful end-to-end workflows with ordinary ChatGPT as the only planner.

## Stage 27 — Distribution and maintenance hardening

Stable release artifact, complete locked dependencies, Python artifact/hash policy, model/runtime installation, update/repair/doctor/uninstall, key rotation, upgrade/rollback, restart recovery and thin lifecycle UI.

## Product-ready gate

Before declaring “install and use” rather than “development platform”:

1. Stage 25.2 must be merged and the five-tool Chat surface remain stable.
2. At least representative real Windows/application workflows must be accepted, not only HTML fixtures.
3. Installation must no longer depend on a git checkout or manual development repair steps.
4. Restart/recovery, doctor/repair/update/rollback/uninstall must be predictable.
5. A clean-user E2E must prove install -> connect Chat -> files -> browser semantic action -> browser visual fallback -> real desktop capability -> restart -> safe cleanup.
6. A stable release must be cut only after the above passes.

## Definition of Done

Ordinary ChatGPT can safely use scoped local capabilities through a small stable MCP surface without a second planner, generic hidden gateway, stale-coordinate action, uncontrolled network expansion or unreviewed dependency/runtime drift, and the Windows companion can be installed and maintained as a normal product rather than a development checkout.

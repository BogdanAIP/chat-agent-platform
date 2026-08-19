# Stage 26.1D — Windows hot-runtime benchmark

## Purpose

Stage 26.1C proved correctness and safety of the bounded Windows executor on the physical Windows host. It did **not** prove that the executor is fast enough for interactive use because the qualification harness intentionally included cold setup work such as an isolated virtual environment and exact dependency installation.

Stage 26.1D measures the executor's **warm action latency** separately from setup.

Parent acceptance head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

The accepted Stage 26.1C branch is not modified. Stage 26.1D imports the accepted executor qualification driver and reuses its exact bounded `input_fn`, UIA/fingerprint helpers, guarded keyboard path, guarded coordinate path and guarded scroll path.

## Benchmark model

The physical benchmark uses:

- one persistent benchmark virtual environment;
- one `win_agent` process for the complete benchmark run;
- one WinForms fixture process for the complete benchmark run;
- two warm-up cycles by default;
- ten measured cycles by default;
- no executor or fixture restart between cycles;
- no VLM in this baseline.

The fixture resets its own harmless state after each cycle. Every cycle must still deliver the exact accepted sequence:

1. `uia_invoke` start;
2. `uia_focus` textbox;
3. guarded `physical_type_text`;
4. guarded `physical_press` Enter;
5. guarded `physical_click` on the known list row;
6. guarded `physical_scroll`;
7. `uia_invoke` finish.

Each cycle uses a distinct expected string (`HOT_01`, `HOT_02`, ...), so a stale prior cycle cannot satisfy the next one.

## Timings

The benchmark records per-cycle wall-clock timings with `time.perf_counter_ns()` for:

- `start_uia_ms`;
- `focus_uia_ms`;
- `guarded_type_ms`;
- `guarded_press_ms`;
- `row_uia_find_ms`;
- `guarded_click_ms`;
- `guarded_scroll_ms`;
- `finish_uia_ms`;
- `action_sequence_total_ms`.

For each metric it reports min, mean, p50, p95 and max in JSON; p50 and p95 are also printed to the console.

The PowerShell harness separately records:

- `environment_setup_ms` — initial/reuse environment preparation;
- `benchmark_driver_ms` — total benchmark-driver lifetime.

`environment_setup_ms` is **not** part of `action_sequence_total_ms`.

## Persistent environment

The benchmark environment lives under:

`%LOCALAPPDATA%\ChatAgentPlatform\stage26\hot-runtime-env`

It is reused only if exact pin verification still matches:

- `openadapt-flow` 1.31.0 at the locked VCS commit;
- `mss==10.2.0`;
- `PyAutoGUI==0.9.54`;
- `uiautomation==2.0.29`.

`-RebuildEnvironment` forces a clean rebuild. This persistence exists only to separate one-time installation cost from warm execution latency.

## First physical run policy

The first Stage 26.1D run is measurement-only for latency. It deliberately reports:

`LATENCY_BUDGET_ENFORCED=False`

No arbitrary p50/p95 threshold is invented before physical evidence exists. Correctness and safety remain hard gates. After the first physical benchmark, measured values will be used to define an explicit interactive latency budget and identify the dominant layer before VLM grounding is added.

## Safety invariants

- no production Chat surface changes;
- no new public semantic tools;
- no generic shell/Python/command executor;
- no legacy OpenAdapt exec route;
- one loopback authenticated `win_agent`;
- accepted layout-independent text path is reused, not duplicated;
- no screenshots are persisted by the benchmark driver;
- only the exact benchmark fixture process may be killed during cleanup;
- Chrome is observed only for survival and is never targeted;
- `UNRELATED_WINDOW_ACTION_COUNT=0` and `FALSE_ACTION_COUNT=0` remain mandatory.

## What this benchmark does not measure

This baseline intentionally excludes:

- ChatGPT planning latency;
- tunnel/MCP round trips;
- semantic-projection latency;
- local F16 VLM inference;
- application-specific business logic.

Those layers can be added separately after the executor baseline is known, so regressions can be attributed instead of hidden inside one end-to-end number.

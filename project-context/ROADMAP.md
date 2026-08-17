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

Accepted foundations:

- one pinned Playwright MCP same-session screenshot -> one-shot prepared target -> exact fresh screenshot -> coordinate action or ABSTAIN;
- replay/layout/scroll/overlay/navigation/missing/ambiguous cases fail closed;
- prepared targets are TTL-purged and capped at 256; expiry/capacity fails closed;
- focused llama.cpp lifecycle owner with exact artifact/process identity, Touch, TTL unload and Stop/Sweep;
- production inference verifies `127.0.0.1:3068` belongs to the controller-returned PID before sending a screenshot;
- class-aware production verifier; repeated-row/tiny remain forced ABSTAIN;
- Windows junction containment and tunnel credential scrub-before-core-load;
- bootstrap installed semantic runtime matches source (`package.json`, `package-lock.json`, secure launcher, core);
- applied lockfile SHA256 is recorded and changed/missing marker forces `npm ci`;
- direct literal private/link-local/metadata/non-public IP destinations are blocked while loopback remains available;
- CodeQL covers Actions, JavaScript/TypeScript and Python.

Accepted RAM policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

The original 1.50 GB start floor was proven too brittle after Playwright load at 1.446–1.486 GB free physical RAM. The final reviewed run passed with a 0.60 GB minimum, no safety stop, runtime stopped afterward and Chrome still running.

Final target evidence:

```text
expected_hits = 3
hits = 3
expected_abstains = 3
correct_abstains = 3
safe_misses = 0
false_clicks = 0
errors = 0
safety_pass = true
acceptance_pass = true
Doctor physical_free_gb = 1.919
Doctor virtual_free_gb = 8.335
minimum observed free physical RAM = 0.60 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

Do not describe this as 6/6 visual accuracy; the Stage 25 present-target baseline remains 3/5 because repeated-row/tiny are intentionally unpromoted.

Residuals remain explicit: screenshot->click is not atomic, PID-bound loopback is not cryptographic endpoint authentication, DNS/rebinding/redirect isolation is incomplete, Python packaging is not release-grade, and `glob@10.5.0` needs a separate dependency follow-up.

All 11 workflow families were green on the final PR head before merge.

## Next active follow-up — Ordinary Chat semantic → vision escalation

Implement automatic internal escalation in a separate PR while keeping the public surface at five tools:

```text
semantic DOM/accessibility first
  -> resolved: act semantically
  -> unavailable/ambiguous:
       same-session screenshot
       -> reviewed local F16 grounder
       -> deterministic authorization
       -> freshness proof
       -> coordinate action OR ABSTAIN
```

Define exactly which semantic misses/ambiguities are eligible and preserve fail-closed behavior.

## Stage 26 — Professional application capability benchmarks
Benchmark REAPER, Origin, FFmpeg, Blender and Windows UI workflows behind the same semantic capability philosophy.

## Stage 27 — Distribution and maintenance hardening
Stable release artifact, complete locked dependencies, Python artifact/hash policy, update/repair/doctor/uninstall, key rotation, upgrade/rollback and thin lifecycle UI.

## Definition of Done
Ordinary ChatGPT can safely use scoped local capabilities through a small stable MCP surface without a second planner, generic hidden gateway, stale-coordinate action, uncontrolled network expansion or unreviewed dependency/runtime drift.

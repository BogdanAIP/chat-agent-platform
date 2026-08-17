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

Merged as `175d36236f80a1f99f091d4f031a1c6255f3652b` (#66).

Public tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 24.1 — Direct semantic tunnel A/B — DONE

Merged as `df1d5e232b739b62e72ad81e5d82fd01be53e884` (#70).

Selected normal path:

```text
ChatGPT -> Secure MCP Tunnel -> tunnel-client -> secure semantic launcher -> direct stdio semantic-projection
```

1MCP stays internal diagnostic/adaptive/aggregation infrastructure.

## Stage 25 — Safe local vision grounding benchmark — DONE FOR BASELINE

PR #73 merged as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target configuration:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Target result with Chrome running: Search/Send/state HIT; Gamma/tiny safe ABSTAIN; absent Export CSV correct ABSTAIN; 0 false clicks; 0 provider/context errors; 3/5 present-target HIT.

## Stage 25.1 — Same-session visual fallback foundation — REVIEWED TARGET ACCEPTANCE PASSED

PR #74 on `chat/stage25-1-vision-integration-foundation`.

Final reviewed target HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

### P0.1 Source-of-truth synchronization — DONE

Authoritative docs describe #73 and the reviewed Stage 25.1 implementation/evidence instead of historical LM Studio/Q4 state.

### P0.2 Same-session capture/freshness/action boundary — DONE

One pinned Playwright MCP session supports:

```text
CSS screenshot
-> one-shot prepared visual target
-> fresh CSS screenshot
-> exact freshness validation
-> coordinate action OR ABSTAIN
```

Replay, layout, scroll, overlay, navigation, missing and ambiguous cases fail closed. Prepared targets are TTL-purged and capped at 256 outstanding entries; capacity/expiry fails closed. No second browser or unrestricted `browser_evaluate` is required.

Residual: final freshness screenshot and coordinate click remain separate MCP calls, so a narrow TOCTOU window remains.

### P1.4 Focused local-vision lifecycle/resource admission — DONE

Approved artifact/runtime identity, loopback start/health, process ownership, Touch, TTL unload, Stop/Sweep, tamper/foreign-listener/ownership-mismatch rejection are covered by Windows CI and final real F16 target acceptance.

Pre-merge review added PID-bound listener verification: production inference verifies that `127.0.0.1:3068` is owned by the controller-returned runtime PID before sending a screenshot. Wrong PID fails closed.

RAM admission was calibrated from the target workload:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

The original 1.50 GB start floor was proven too brittle after Playwright load at 1.446–1.486 GB free physical RAM. The reviewed 1.35 GB policy then passed the full target gate with minimum observed free physical RAM 0.60 GB, `SAFETY_STOP=false`, runtime stopped afterward and user Chrome still running.

### P1.5 Production grounding verifier — DONE FOR CURRENT PROMOTED CLASSES

Class-aware deterministic authorization is implemented. Inventory-backed text and reviewed icon/state classes resolve under measured guards. Repeated-row and tiny classes remain forced ABSTAIN until separately promoted.

### P1.6 Adversarial/stale browser tests — DONE FOR CURRENT BRIDGE CONTRACT

Covered: replay, token expiry/capacity, layout shift, scroll, overlay, navigation/page replacement, missing and ambiguous target.

### P1.7 Security regressions — SUBSTANTIALLY DONE

Proved:

- Windows junction read/write containment;
- tunnel credential inheritance was real in `tunnel-client v0.0.11`, and secure launcher scrub-before-core-load passes a sentinel regression;
- direct `web_open` to private/link-local/metadata/non-public literal IP destinations is blocked while reviewed loopback remains allowed;
- loopback vision listener must match the controller-owned PID before inference.

Residual: current URL policy is not a complete DNS/redirect network sandbox, and PID-bound loopback is not cryptographic endpoint authentication.

### P1.8 Static analysis/dependency maintenance — DONE FOR CURRENT NODE/PYTHON SURFACE

CodeQL covers Actions, JavaScript/TypeScript and Python. Dependabot covers Actions, semantic npm and Python requirements. Secret history scan remains active.

The final reviewed head passed all 11 workflow families. The JavaScript/TypeScript CodeQL job required one retry after GitHub returned `No server is currently available to service your request` during init; the retry completed successfully.

### P1/P2.9 Reproducible dependencies — NODE SIDE DONE; PYTHON RELEASE HARDENING PENDING

Semantic projection has a committed npm lockfile and product/acceptance paths use `npm ci`.

Pre-merge review closed an installed/source drift: bootstrap now installs `package.json`, `package-lock.json`, secure semantic launcher and core, and standalone installed-layout acceptance verifies the same contract.

Semantic dependency installation records the applied lockfile SHA256 and re-runs `npm ci` when that lock changes or the marker is absent.

Vision Python currently has the exact pin `Pillow==12.3.0`; release-grade Python artifact/hash policy is still pending.

Deprecated transitive `glob@10.5.0` remains a separate post-Stage-25.1 dependency PR.

### P0.3/P1.10 Real production grounder integration — DONE FOR FOUNDATION

A model-neutral production grounder boundary, fixed-profile runtime-backed runner and same-session bridge integration are implemented and proved.

Final target Windows evidence on reviewed HEAD `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c` with Chrome open:

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
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
STAGE25_1_REVIEW_RESULT = PASSED
```

Do not describe this as 6/6 visual accuracy; it is a six-case safety/behavior gate. The accepted Stage 25 present-target baseline remains 3/5 because repeated-row/tiny are intentionally not promoted.

Real integration defects and review findings closed before merge include:

- Windows descendant-stdio cold-Start settlement;
- long-run target wrapper stdout/stderr buffering;
- PID-unbound vision listener acceptance;
- prepared-token unbounded retention;
- stale bootstrap installed semantic bundle;
- lockfile-change reuse of old `node_modules`;
- overly brittle 1.50 GB cold-start RAM gate.

## Next follow-up — Ordinary Chat semantic → vision escalation

After merging the Stage 25.1 foundation, implement the automatic internal escalation policy in a separate PR while keeping the public surface at five tools:

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

This follow-up must define exactly which semantic misses/ambiguities are eligible, preserve fail-closed behavior, and avoid turning vision into a generic public tool or second planner.

## P2 cleanup

After the escalation policy stabilizes, extract any remaining common inference transport, keep production naming model-neutral, and retain Stage 25 benchmark evidence separately.

## Stage 26 — Professional application capability benchmarks

Benchmark REAPER, Origin, FFmpeg, Blender and Windows UI workflows behind the same semantic capability philosophy.

## Stage 27 — Distribution and maintenance hardening

Stable release artifact, complete locked dependencies, Python artifact/hash policy, update/repair/doctor/uninstall, key rotation, upgrade/rollback and thin lifecycle UI.

## Definition of Done

Ordinary ChatGPT can safely use scoped local capabilities through a small stable MCP surface, starting heavyweight components only when needed, without a second planner, generic hidden gateway, stale-coordinate browser action, uncontrolled network expansion or unreviewed dependency/runtime drift.

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
ChatGPT -> Secure MCP Tunnel -> tunnel-client -> direct stdio semantic-projection
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

## Stage 25.1 — Same-session visual fallback integration — ACTIVE

Draft PR #74 on `chat/stage25-1-vision-integration-foundation`.

### P0.1 Source-of-truth synchronization — DONE

Authoritative docs describe #73 and current Stage 25.1 implementation instead of historical LM Studio/Q4/PR #72 state.

### P0.2 Same-session capture/freshness/action boundary — PROVED

One pinned Playwright MCP session now supports:

```text
CSS screenshot
-> one-shot prepared visual target
-> fresh CSS screenshot
-> exact freshness validation
-> coordinate action OR ABSTAIN
```

Replay, layout, scroll, overlay, navigation, missing and ambiguous cases fail closed. No second browser or unrestricted `browser_evaluate` is required.

### P1.4 Focused local-vision lifecycle/resource admission — PROVED SYNTHETICALLY

Approved artifact/runtime identity, memory admission, loopback start/health, process ownership, Touch, TTL unload, Stop/Sweep, tamper/foreign-listener/ownership-mismatch rejection are covered by Windows CI.

Real F16 lifecycle on the target laptop remains part of the final integration acceptance.

### P1.5 Production grounding verifier — DONE FOR CURRENT PROMOTED CLASSES

Class-aware deterministic authorization is implemented. Inventory-backed text and reviewed icon/state classes can resolve under measured guards. Repeated-row and tiny classes remain forced ABSTAIN until separately promoted.

### P1.6 Adversarial/stale browser tests — DONE FOR CURRENT BRIDGE CONTRACT

Covered: replay, layout shift, scroll, overlay, navigation/page replacement, missing and ambiguous target. More application-specific canvas/WebGL/hostile visual content belongs with later capability benchmarks.

### P1.7 Security regressions — SUBSTANTIALLY DONE

Proved:

- Windows junction read/write containment;
- tunnel credential inheritance was real in `tunnel-client v0.0.11`, and secure launcher scrub-before-core-load now passes a sentinel regression;
- direct `web_open` to private/link-local/metadata/non-public literal IP destinations is blocked while reviewed loopback remains allowed.

Residual: current URL policy is not a complete DNS/redirect network sandbox. Upstream Playwright origin filters are defense-in-depth only and explicitly do not define a redirect security boundary.

### P1.8 Static analysis/dependency maintenance — DONE FOR CURRENT NODE/PYTHON SURFACE

CodeQL covers Actions, JavaScript/TypeScript and Python. Dependabot covers Actions, semantic npm and Python requirements. Secret history scan remains active.

### P1/P2.9 Reproducible dependencies — NODE SIDE DONE; PYTHON RELEASE HARDENING PENDING

Semantic projection now has a committed npm lockfile and product/acceptance paths use `npm ci`. Unlocked install is refused when dependencies are absent.

Vision Python currently has the exact small pin `Pillow==12.3.0`; release-grade Python artifact/hash policy is still pending.

### P0.3/P1.10 Real production grounder integration — ACTIVE

A model-neutral production grounder boundary is implemented and unit-proved. It wraps the accepted native-bbox provider with the class-aware production policy and exposes only resolved/abstain evidence; it does not own runtime or browser action.

Next:

1. add runtime-backed internal runner: focused lifecycle owner -> loopback production grounder;
2. connect that runner to the proved same-session bridge without changing the five public tools;
3. prove deterministic CI plumbing and fail-closed behavior;
4. run real F16 same-session acceptance on target Windows with Chrome open;
5. only then decide whether/how semantic miss/ambiguity automatically escalates to vision in the ordinary Chat flow.

### P2 cleanup

After real integration stabilizes, extract any remaining common inference transport, keep production naming model-neutral, and retain Stage 25 benchmark evidence separately.

## Stage 26 — Professional application capability benchmarks

After Stage 25.1 stabilizes, benchmark REAPER, Origin, FFmpeg, Blender and Windows UI workflows behind the same semantic capability philosophy.

## Stage 27 — Distribution and maintenance hardening

Stable release artifact, complete locked dependencies, update/repair/doctor/uninstall, key rotation, upgrade/rollback and thin lifecycle UI.

## Definition of Done

Ordinary ChatGPT can safely use scoped local capabilities through a small stable MCP surface, starting heavyweight components only when needed, without a second planner, generic hidden gateway, stale-coordinate browser action, uncontrolled network expansion or unreviewed dependency/runtime drift.

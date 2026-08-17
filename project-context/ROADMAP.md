# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT as the intelligence layer while local capabilities remain replaceable MCP modules or focused adapters. Do not scale local capability count by exposing hundreds of raw Chat tools or by running every local process continuously.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Secure MCP Tunnel + official tunnel-client + local MCP round trip accepted.

## Stage 22 — Remove superseded universal platform core — DONE

Obsolete universal Rust/Python/custom-ingress core removed; historical implementation remains recoverable in Git.

## Stage 23 — Quality-first module selection — DONE

Accepted Windows Filesystem/Playwright/1MCP candidates and selection rules.

## Stage 24 — Windows lifecycle + stable semantic Chat surface — DONE

Merged as `175d36236f80a1f99f091d4f031a1c6255f3652b` (#66).

Accepted public tools:

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

Selected target-laptop grounding baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Final target result with Chrome running: Search/Send/state HIT; Gamma/tiny safe ABSTAIN; absent Export CSV correct ABSTAIN; 0 false clicks; 0 provider/context errors; 3/5 present-target HIT.

## Stage 25.1 — Same-session visual fallback integration — ACTIVE

Draft PR #74 on `chat/stage25-1-vision-integration-foundation`.

### P0.1 Source-of-truth synchronization — DONE ON PR BRANCH

Authoritative docs updated for #73 and Stage 25.1.

### P0.2 Same-session capture/freshness/action boundary — PROVED IN WINDOWS CI

Internal bridge now proves, using one pinned Playwright MCP 0.0.78 client/session:

```text
CSS screenshot
-> prepared one-shot visual target
-> fresh CSS screenshot
-> exact freshness validation
-> coordinate action OR ABSTAIN
```

Positive coordinate action, replay prevention, stale-layout ABSTAIN and grounder ABSTAIN passed. Existing exact five-tool semantic acceptance also remains green.

This proves no second browser and no unrestricted `browser_evaluate` are needed for the internal visual-action boundary.

### P0.3 Real semantic -> VLM -> same-session action integration — PENDING

The bridge acceptance currently uses an injected deterministic grounder. Before production fallback, add the accepted real local-VLM grounder behind a focused runtime owner, then prove the same positive/negative chain with the real F16 model on target Windows.

### P1.4 Focused local-vision lifecycle/resource admission — ACTIVE

Implement:

- exact approved llama.cpp/model/mmproj identity;
- conservative physical/virtual memory admission;
- loopback-only owned process start/health;
- touch/use tracking;
- idle TTL/unload;
- explicit stop;
- crash/stale-state cleanup;
- no unrelated process or Chrome termination.

### P1.5 Production grounding verifier — PENDING

Use target-class-aware deterministic verification rather than one global IoU threshold.

### P1.6 Adversarial/stale browser tests — PARTIAL

Layout-shift stale capture already proved. Still add scroll, navigation/page replacement, overlays, repeated visual targets, tiny/state/absent cases, canvas/WebGL where practical and hostile prompt-like on-screen text.

### P1.7 Security regressions — PENDING

- Windows link/junction workspace containment;
- localhost/private-network browser navigation policy;
- tunnel credential inheritance into child processes.

### P1.8 Static analysis/dependency maintenance — PENDING

Broaden security/static analysis to active Node/Python implementation and add npm/Python dependency maintenance coverage.

### P1/P2.9 Reproducible dependencies — PENDING

Move stable runtime away from unlocked npm installation and define reproducible Python dependencies.

### P2.10 Internal cleanup — PENDING

After P0/P1 contracts stabilize, extract common loopback inference transport and use model-neutral production naming while retaining benchmark evidence.

## Stage 26 — Professional application capability benchmarks

After Stage 25.1 stabilizes, benchmark REAPER, Origin, FFmpeg, Blender and Windows UI workflows behind the same semantic capability philosophy.

## Stage 27 — Distribution and maintenance hardening

Stable release artifact, locked dependencies, update/repair/doctor/uninstall, key rotation, upgrade/rollback and thin lifecycle UI.

## Definition of Done

Ordinary ChatGPT can safely use scoped local capabilities through a small stable MCP surface, starting heavyweight components only when needed, without a second planner, generic hidden gateway, unsafe stale-coordinate browser action or hard-coded unreplaceable model/runtime identity.

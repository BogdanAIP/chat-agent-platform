# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT as the intelligence layer while local capabilities remain replaceable MCP modules or focused adapters. Do not scale capability count by exposing hundreds of raw Chat tools or by running every local process continuously.

## Stages 21–24.1 — DONE

- Stage 21: Secure MCP Tunnel + official tunnel-client + local MCP round trip.
- Stage 22: obsolete universal Rust/Python/custom-ingress core removed.
- Stage 23: quality-first Windows module selection.
- Stage 24 (#66): exact five-tool semantic Chat surface accepted.
- Stage 24.1 (#70): direct stdio semantic path selected; 1MCP retained internally for diagnostic/adaptive/aggregation use.

Accepted public tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

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

Fully-green implementation evidence before the current docs update: `c7eecc4ec1c4796e943816c9e51256d6b181b452`.

### P0.1 Source-of-truth synchronization — DONE

Authoritative docs describe the accepted #73/F16 state and Stage 25.1 boundaries.

### P0.2 Same-session capture/freshness/action boundary — PROVED

One pinned Playwright MCP 0.0.78 client/session proves:

```text
CSS screenshot
-> prepared one-shot visual target
-> fresh CSS screenshot
-> exact freshness validation
-> coordinate action OR ABSTAIN
```

Passed cases: positive intended click, replay guard, layout shift, scroll, overlay, navigation/page replacement, missing target and ambiguous target. Every stale/uncertain case produced no coordinate action. Exact five-tool semantic acceptance remains green.

### P0.3 Real semantic -> VLM -> same-session action integration — PENDING

The browser bridge still uses an injected deterministic grounder in CI. Connect the accepted real local-VLM path only through the focused runtime owner, then run real target-Windows acceptance with Chrome open.

### P1.4 Focused local-vision lifecycle/resource admission — PROVED SYNTHETICALLY

Implemented reviewed F16 profile with exact runtime/model hashes, physical+virtual memory admission, loopback-only owned start/health, Touch, idle TTL unload, explicit Stop, tamper rejection, foreign-listener fail-closed and ownership-mismatch fail-closed behavior.

Synthetic Windows lifecycle acceptance is green. Real target-laptop F16 lifecycle remains pending.

### P1.5 Production grounding verifier — IMPLEMENTED / UNIT-TESTED

Evidence-based promotion policy:

- text/state: unique target-blind inventory + unique refinement; no global high-IoU rule;
- icon: unique two-pass result + positive overlap;
- repeated-row and tiny targets: forced ABSTAIN until separate target evidence promotes them;
- absent/unreviewed/error paths: no action.

### P1.6 Adversarial/stale browser tests — SUBSTANTIALLY PROVED

Green Windows coverage now includes layout shift, scroll, overlay, navigation/page replacement, replay, missing and ambiguous target. Remaining useful future cases include canvas/WebGL where practical and hostile on-screen prompt-like content.

### P1.7 Security regressions — PARTIAL

**PROVED:** Windows workspace junction read/write escape is blocked on the current pinned stack, while normal in-root write still works.

**PENDING:**

- explicit localhost/private-network browser scope policy/regression;
- explicit tunnel credential inheritance test and downstream environment scrub if required.

### P1.8 Static analysis/dependency maintenance — IMPROVED / PROVED

CodeQL matrix now covers `actions`, `javascript-typescript`, and `python`; all three jobs are green on the fully tested head.

Dependabot now monitors Actions, semantic npm, and root pip requirements.

### P1/P2.9 Reproducible dependencies — PENDING

Move semantic runtime away from unlocked `npm install --package-lock=false`; commit and validate a real lockfile before switching production/bootstrap/CI to `npm ci`. Keep Python dependency locking/update policy explicit.

### P2.10 Internal cleanup — PENDING

After remaining security/reproducibility/real-model gates stabilize, extract common loopback inference transport and use model-neutral production naming while retaining benchmark evidence.

## Stage 26 — Professional application capability benchmarks

After Stage 25.1 stabilizes, benchmark REAPER, Origin, FFmpeg, Blender and Windows UI workflows behind the same semantic capability philosophy.

## Stage 27 — Distribution and maintenance hardening

Stable release artifact, locked dependencies, update/repair/doctor/uninstall, key rotation, upgrade/rollback and thin lifecycle UI.

## Definition of Done

Ordinary ChatGPT can safely use scoped local capabilities through a small stable MCP surface, starting heavyweight components only when needed, without a second planner, generic hidden gateway, unsafe stale-coordinate browser action or hard-coded unreplaceable model/runtime identity.

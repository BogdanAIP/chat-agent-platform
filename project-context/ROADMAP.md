# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT as the only intelligence/planning layer while local capabilities remain replaceable MCP modules, focused adapters, bounded perception backends and non-agentic procedural memory. Do not expose hundreds of raw tools or run heavyweight local components permanently.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Secure MCP Tunnel + official tunnel-client + local MCP round trip accepted.

## Stage 22 — Remove superseded universal platform core — DONE

Obsolete universal Rust/Python/custom-ingress core removed from the active tree; history remains in Git.

## Stage 23 — Quality-first module selection — DONE

Accepted Windows Filesystem/Playwright/1MCP candidates and selection rules.

## Stage 24 — Windows lifecycle + stable semantic Chat surface — DONE

Merged as `175d36236f80a1f99f091d4f031a1c6255f3652b` (#66). Public tools are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 24.1 — Direct semantic tunnel A/B — DONE

Merged as `df1d5e232b739b62e72ad81e5d82fd01be53e884` (#70). Normal path is ChatGPT -> Secure MCP Tunnel -> tunnel-client -> secure semantic launcher -> direct stdio semantic-projection. 1MCP stays internal diagnostic/adaptive/aggregation infrastructure.

## Stage 25 — Safe local vision grounding benchmark — DONE FOR BASELINE

PR #73 merged as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target configuration: llama.cpp `b10448/ad1de39e0`, LFM2.5-VL-450M F16 + F16 mmproj, CPU 8 threads, ctx 2048. Target result: 3/5 present-target HIT, repeated-row/tiny safe ABSTAIN, absent target correct ABSTAIN, zero false clicks/provider-context errors.

## Stage 25.1 — Same-session visual fallback foundation — DONE

PR #74 squash-merged as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Accepted same-session screenshot/freshness/coordinate action, fail-closed stale/replay/layout/scroll/overlay/navigation handling, focused vision-runtime lifecycle, PID-bound listener verification, installed-layout parity, dependency integrity, junction containment, credential scrub and security regressions.

## Stage 25.2 — Ordinary Chat semantic → vision escalation — DONE

PR #77 squash-merged as runtime/code milestone:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

Accepted routing:

```text
fresh accessibility snapshot
  -> exact enabled button: semantic click; VLM stays stopped
  -> same-name buttons with exactly one enabled + disabled alternatives: semantic click
  -> disabled/non-button/ambiguous exact evidence: ABSTAIN; VLM stays stopped
  -> zero exact candidates:
       same-session screenshot
       -> reviewed local F16 text-labeled grounder
       -> deterministic authorization
       -> freshness proof
       -> one coordinate click OR ABSTAIN
```

Final target result: `semantic_hits=2`, `visual_hits=1`, `correct_abstains=2`, `false_clicks=0`, `errors=0`, `semantic_cases_started_vlm=0`, `acceptance_pass=true`; runtime stopped afterward and Chrome remained running.

## Stage 26 — Procedural Memory / Demo2Workflow — ACTIVE

Purpose: reuse successful procedures as bounded procedural memory without adding a second planner or blind macro replay.

Upstream technical reference: official `Tencent/UI-Mate`, analyzed at pinned commit `d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`. We adopt the separation between rich trajectory evidence and compact current-subtask workflow guidance, while strengthening trust and completion verification for our architecture. We do not adopt UI-Mate as the product planner/agent.

Authoritative design: `project-context/STAGE26_PROCEDURAL_MEMORY.md`.

### Stage 26.0 — Upstream analysis + authoritative contract/context sync — DONE

Completed through PR #78, merged as documentation milestone:

`04dccfd30eb06a82899e2771f6d53ab4c8387128`.

Completed work:

- pinned upstream reference/license;
- reviewed `demo_workflow.py`, agent integration, prepared demonstration trajectory and bundled example runner;
- defined what is adopted/rejected;
- synchronized stale cross-chat continuation docs after Stage 25.2;
- preserved the ChatGPT-only planner boundary;
- made Windows desktop surface and the later public-contract decision explicit.

### Stage 26.1 — Procedural data foundation — NEXT

Build:

- raw trajectory schema;
- secret/sensitive-data redaction and retention/deletion policy;
- coordinate-free compiled skill schema;
- versioned local skill store;
- schema validation and deterministic stale/disable handling;
- explicit candidate/verified/promoted lifecycle.

No public Chat tool-name change in this step.

### Stage 26.2 — Demo Compiler + verifier + self-demo dogfood

Compile successful existing Chat/tool-driven trajectories into candidate workflows, then prove:

- no coordinate replay in compiled skills;
- current state outranks remembered milestones;
- completion advances only with verifier evidence;
- a changed/variant task adapts rather than blindly replaying;
- an incompatible workflow does not force execution;
- one lucky success does not auto-promote trust.

Start here because current semantic/browser execution gives exact structured actions and results. This is not yet arbitrary human desktop recording.

### Stage 26.3 — Windows desktop surface — REQUIRED / DO NOT DROP

**This stage is deliberately written into the roadmap so it is not lost.**

Build a scoped Windows desktop capability surface:

```text
native/deterministic UI observation first
  -> screen capture where needed
  -> bounded local visual grounding where needed
  -> reviewed keyboard/mouse action
  -> verification / ABSTAIN
```

Requirements:

- use native/semantic structure before pixels where available;
- screen/vision is a bounded fallback/evidence source, not a second planner;
- keyboard/mouse actions are scoped and fail closed;
- preserve observable before/after evidence for later procedural-memory compilation;
- select concrete local programs/capabilities from real user tasks and evidence at the time of benchmarking; do not preselect a fixed application list in the roadmap.

### Stage 26.4 — Human demonstration capture + transferable skill acceptance

Once Windows desktop observation/actuation exists:

- record a real user demonstration;
- compile it into a coordinate-free candidate skill;
- verify goals/completion criteria;
- re-apply it to a related changed task/state;
- prove current UI state takes precedence over remembered action history.

### Stage 26.5 — Public contract decision — EXPLICIT DECISION POINT

Only after Windows desktop surface exists, decide by ADR and ordinary-Chat acceptance whether:

1. the current five public tools can remain the product contract behind a small truthful semantic surface; or
2. a small number of new truthful public tool names is required.

Until this decision:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

remain the accepted public tool names.

Do not create a generic opaque workflow dispatcher or hide desktop/workflow operations behind misleading existing semantics merely to preserve a tool count.

## Stage 27 — Distribution and maintenance hardening

After the Stage 26 capability boundary is accepted:

- stable install artifact;
- complete locked dependencies;
- Python/model artifact and hash policy;
- installer/update/repair/doctor/uninstall;
- key rotation;
- upgrade/rollback;
- restart recovery;
- thin lifecycle UI.

## Stage 28 — Clean-user product E2E + first stable release

Before saying “install and use” rather than “development platform”, prove:

```text
install
 -> connect ordinary ChatGPT
 -> scoped files
 -> browser semantic action
 -> browser visual fallback
 -> procedural-memory reuse
 -> Windows desktop capability
 -> restart/recovery
 -> safe cleanup / repair path
```

Then cut the first stable release.

## Cross-cutting follow-ups

- repeated-row/tiny/icon-only visual promotion only with separate evidence;
- decide whether stronger DNS/redirect/private-network isolation is required;
- release-grade Python/model reproducibility;
- dependency cleanup including deprecated transitive dependencies;
- repository metadata cleanup where needed.

## Context-continuation rule

Do not embed a docs commit as permanently “current main”. Fresh sessions must resolve live `main` from GitHub first, then use the stable milestone/acceptance SHAs above as historical evidence.

## Definition of Done

Ordinary ChatGPT can safely use scoped local capabilities through a small truthful MCP surface, reuse verified user/task procedures without a second planner or blind replay, and operate through a maintainable Windows companion whose desktop capability and public-contract boundary have been explicitly accepted. The installed product must recover predictably and not depend on a development git checkout for normal use.

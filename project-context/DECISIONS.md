# Decisions

Historical ADR detail remains in Git history. This file lists the decisions that govern current development.

A decision marked **PROVISIONAL** is the active direction but is not product-accepted until its stated gate passes.

## ADR-010 — Off-the-shelf MCP bridge — ACCEPTED

Use standard MCP and mature reachability/runtime components. Ordinary ChatGPT is the intelligence/orchestration layer. Selection order is official/vendor, mature OSS, mature generic adapter, then the smallest project-owned focused adapter for a measured gap.

## ADR-011 — OpenAI Secure MCP Tunnel is primary ChatGPT reachability — ACCEPTED

Accepted by real ordinary-Chat E2E. Historical custom/public ingress experiments are not the normal path.

## ADR-012 — Superseded universal core removed — ACCEPTED

The old universal agent/gateway platform is historical only. Recover specific pieces only for a later measured gap.

## ADR-013 — 1MCP is replaceable internal infrastructure — ACCEPTED

1MCP remains useful for diagnostics, adaptive lifecycle experiments and aggregation/inspection. Stage 24.1 removed it from the normal semantic critical path because direct stdio was materially simpler/faster with equivalent tested behavior, not because 1MCP was broken.

## ADR-014 — Privileged capabilities require scoped acceptance — ACCEPTED

Filesystem writes, shell, browser, application control, credentials and devices require scoped configuration and negative tests before promotion. Legitimate workflows may combine capabilities when needed; security controls scope/consequence rather than imposing arbitrary permanent mutual exclusion.

## ADR-015 — Thin Windows bootstrap/manager is integration code — ACCEPTED

Bootstrap/controller/tray may install, configure, start/stop, report health and coordinate accepted components. They must not become a planner, workflow engine, generic gateway/registry/vault or authorization platform.

## ADR-016 — Generic adaptive meta-tool contract is not the ordinary-Chat product surface — ACCEPTED NEGATIVE DECISION

Do not promote generic `tool_schema` / `tool_invoke` / arbitrary backend dispatch as the ordinary-Chat contract. Keep concrete truthful typed semantics. Revisit only if a future standard/product mechanism exposes downstream semantics truthfully and passes ordinary-Chat acceptance.

## ADR-017 — AVAILABLE -> ACTIVE -> AUTHORIZED lifecycle — ACCEPTED FOR CURRENT CAPABILITIES

Use separate capability states:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Do not keep every backend/model running. Activate what the task needs, permit legitimate concurrent capabilities, and keep authorization scoped to the actual operation/consequence.

Future desktop/device/consequential capabilities still require their own scoped acceptance.

## ADR-018 — Small concrete semantic Chat-facing surface — ACCEPTED

Current public tool names are:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

The project scales by projecting a small truthful semantic surface onto reviewed local capabilities rather than publishing huge raw inventories or hiding heterogeneous operations behind opaque dispatch.

The observed Chat action-snapshot size behavior is empirical compatibility evidence, not a universal hard-coded product limit.

## ADR-019 — One authoritative Windows manager owner — ACCEPTED

Installed/source copies coordinate one authoritative runtime owner. Ambiguous/unowned shared runtime state fails closed. The direct semantic path owns/identifies its exact tunnel-client process; legacy 1MCP-backed profiles retain their accepted port/process checks.

## ADR-020 — Local specialist inference is a capability backend, not a second brain — ACCEPTED

Stage 25-25.2 accepted bounded local vision on the target Windows machine using llama.cpp + LFM2.5-VL-450M F16 behind focused internal boundaries.

Decision:

- local models may provide bounded perception/extraction/grounding/classification;
- ChatGPT remains the planner;
- model output is non-authorizing evidence;
- runtime/model identity remains replaceable behind a focused provider-neutral boundary;
- heavy local inference follows resource admission and deterministic lifecycle/unload;
- no generic model-management/raw-prompt surface is exposed to ordinary Chat.

Earlier LM Studio/3B/1.6B/Q4 candidate discussion is historical research, not the current accepted runtime/model path.

## ADR-021 — Direct semantic stdio tunnel binding — ACCEPTED AND RELEASE-COMPLETE

Normal public semantic transport is:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
```

1MCP remains internal/replaceable. Direct transport does not expand `semantic-projection` into a gateway/planner/lifecycle platform.

## ADR-022 — Semantic-first same-session local vision integration — ACCEPTED

Stage 25.1 and Stage 25.2 satisfied the original acceptance direction and supersede the earlier provisional text.

Current browser interaction rule:

```text
fresh accessibility snapshot
  -> exact enabled semantic target: act semantically; VLM stays stopped
  -> disabled/non-button/unresolved semantic ambiguity: ABSTAIN; VLM stays stopped
  -> reviewed zero-exact-candidate miss only:
       same-session capture
       -> bounded local visual grounder
       -> deterministic authorization
       -> freshness proof
       -> one action OR ABSTAIN
```

`targetText` is the authorization anchor. Planner `target`, free-form instruction and planner-supplied kind cannot redirect visual authorization. Generic semantic click errors never invoke vision.

PR #77 was squash-merged as `2a410476ef849fd6d9c172703a004b1befcbcfb1` after real-F16 target acceptance and green CI/security/lifecycle gates.

## ADR-023 — Procedural memory is guidance/state, not a second planner — PROVISIONAL

Stage 26 adopts a procedural-memory pattern informed by official `Tencent/UI-Mate` (`d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`) without adopting UI-Mate as the product agent/model.

Direction:

```text
successful structured trajectory
  -> Demo Compiler
  -> coordinate-free versioned candidate skill
  -> compact current-subtask guidance
  -> current observed state remains authoritative
  -> completion verifier
  -> evidence-based trust lifecycle
```

Rules:

- ChatGPT remains the only planner/interpreter;
- a stored workflow is advice/evidence, not action authorization;
- compiled skills must not replay coordinates;
- current state outranks remembered milestones;
- one successful run creates at most a candidate skill;
- skill retrieval/ranking is non-authorizing;
- subtask advancement requires applicable verifier evidence, not only a model completion claim;
- private chain-of-thought must not be stored in procedural memory;
- raw screenshot/sensitive-data retention requires explicit redaction/retention policy.

Acceptance gate is defined in `STAGE26_PROCEDURAL_MEMORY.md` and includes variant-task adaptation, incompatible/stale fail-closed behavior and deterministic skill version/trust handling.

## ADR-024 — Windows desktop surface precedes any public-contract expansion decision — PROVISIONAL

A scoped Windows desktop surface is an explicit required Stage 26.x item.

Preferred layering:

```text
native/deterministic UI observation first
  -> screen capture where needed
  -> bounded vision where needed
  -> reviewed keyboard/mouse actuation
  -> verification / ABSTAIN
```

Concrete local programs/capabilities are chosen later from real tasks/evidence; no fixed future application list is architectural policy.

Until the desktop surface exists, the accepted public tool names remain the current five and procedural-memory foundations may stay internal/tested.

Only after desktop acceptance, make a separate ADR + ordinary-Chat acceptance decision whether:

- a few new truthful public capability names are required; or
- the same small-semantic-surface philosophy can continue without expanding tool names.

Do not preserve the number five by misleadingly overloading existing tools, and do not introduce a generic opaque workflow/desktop dispatcher.

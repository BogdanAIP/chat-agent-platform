# Current State

## Resolve live repository state before editing

Do not treat an embedded documentation merge SHA as permanently current. Resolve live `main` from GitHub before branching or editing.

Stable accepted milestones:

- Stage 25.2 runtime/code merge: `2a410476ef849fd6d9c172703a004b1befcbcfb1` (#77);
- Stage 26 architecture/context activation: `04dccfd30eb06a82899e2771f6d53ab4c8387128` (#78).

Live `main` may be newer than either milestone because of later code/docs integration.

The accepted ordinary-Chat path is:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

Current public Chat-facing tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Ordinary ChatGPT remains the only planner/intelligence.

## Accepted foundation through Stage 25.2

### Stage 24 / 24.1

Five-tool semantic surface, Windows lifecycle and direct stdio semantic tunnel are accepted product foundations.

### Stage 25 — local grounding baseline

Accepted target configuration:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
present-target hits = 3/5
false clicks = 0
```

Repeated-row and tiny target classes remain deliberately unpromoted.

### Stage 25.1 — same-session visual foundation

Accepted foundations include:

- same Playwright page/session screenshot -> prepared target -> freshness -> coordinate action or ABSTAIN;
- stale/replay/layout/scroll/overlay/navigation uncertainty fails closed;
- focused llama.cpp lifecycle owner and deterministic unload;
- PID-bound loopback listener verification before inference;
- class-aware visual authorization;
- secure installed semantic runtime and lock-hash-enforced dependency installation;
- Windows junction containment, credential scrub, bounded literal-IP browser policy and security regressions.

Reviewed RAM policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

### Stage 25.2 — MERGED AND ACCEPTED

PR #77 was squash-merged as runtime/code milestone:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

Accepted `web_interact(click)` routing:

```text
fresh accessibility snapshot
  -> exact enabled button
       -> semantic click; VLM stays stopped
  -> duplicate same-name buttons with exactly one enabled + disabled alternatives
       -> semantic click; VLM stays stopped
  -> disabled exact target
       -> ABSTAIN; VLM stays stopped
  -> exact target of an unpromoted semantic role
       -> ABSTAIN; VLM stays stopped
  -> unresolved semantic ambiguity
       -> ABSTAIN; VLM stays stopped
  -> zero exact candidates
       -> SAME Playwright page/session screenshot
       -> reviewed F16 text-labeled visual grounder
       -> deterministic authorization
       -> exact freshness proof
       -> one coordinate click OR ABSTAIN
```

Authorization rules:

- `targetText` is the semantic and visual authorization anchor;
- planner-supplied target `kind` is not accepted;
- planner `target` and free-form `instruction` cannot redirect visual grounding;
- generic semantic click failures never trigger vision;
- icon-only, repeated-row and tiny targets are not automatically promoted.

Final real target evidence with normal Chrome workload open:

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
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

## Stage 26 — Procedural Memory / Demo2Workflow — ACTIVE DESIGN

Stage 26 architecture/context activation was merged in PR #78 as milestone:

`04dccfd30eb06a82899e2771f6d53ab4c8387128`.

Stage 26.0 — upstream analysis + contract/context synchronization — is **DONE**.

Next implementation step: **Stage 26.1 — procedural data foundation**.

Technical reference: official `Tencent/UI-Mate`, pinned during analysis to upstream commit:

`d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`.

We do not adopt UI-Mate as a second GUI agent or large local planner. We adopt the procedural-memory pattern:

```text
successful trajectory
  -> raw structured evidence
  -> Demo Compiler
  -> coordinate-free versioned candidate skill
  -> compact current-subtask guidance
  -> current observed state remains authoritative
  -> completion verifier
  -> evidence-based promotion / stale / disable
```

Stage 26 rules:

- stored workflows are guidance/evidence, not authorization and not planners;
- do not persist private chain-of-thought;
- one successful run creates at most a candidate skill;
- completion pointer advances only on applicable verifier evidence;
- retrieval may rank candidate skills but cannot authorize an action;
- current observed state outranks remembered milestones/action history;
- specific local programs/capabilities are selected later from actual tasks and evidence, not preselected in the roadmap.

## Stage 26.1 — NEXT

Implement the procedural data foundation:

- raw trajectory schema;
- redaction/retention/deletion policy;
- compiled coordinate-free skill schema;
- versioned local skill store;
- deterministic parser/validator;
- candidate/verified/promoted/stale/disabled lifecycle.

No public Chat tool-name change in this step.

## Stage 26.2 — after 26.1

Demo Compiler + verifier + self-demo dogfood using successful controlled Chat/tool-driven trajectories. Acceptance must include a related changed/variant case, not only identical replay.

## Stage 26.3 — Windows desktop surface — REQUIRED / DO NOT DROP

This is an explicit planned capability boundary:

```text
native/deterministic UI observation first
  -> screen capture where needed
  -> bounded visual grounding where needed
  -> reviewed keyboard/mouse action
  -> verification / ABSTAIN
```

True arbitrary human “show me once” recording belongs at or after this layer because the current browser semantic bridge observes controlled tool actions rather than arbitrary Windows user interaction.

Concrete local programs/capabilities are chosen later from real tasks and evidence.

## Stage 26.4 — human demonstration capture

After desktop observation/actuation exists, record a real user demonstration, compile it into a coordinate-free candidate, verify it and re-apply it to a related changed task/state.

## Stage 26.5 — public contract decision

Only after Windows desktop surface exists, make a separate ADR + ordinary-Chat acceptance decision whether:

- the existing small-semantic-surface philosophy can continue; or
- a small number of new truthful public tool names is required.

Until then the accepted public tool names remain the current five.

Do not overload existing tools or add a generic opaque workflow dispatcher merely to preserve a tool count.

## Remaining product work

- Stage 26.1 procedural data foundation;
- Stage 26.2 compiler/verifier/self-demo acceptance;
- Stage 26.3 Windows desktop surface;
- Stage 26.4 human demonstration capture and transfer;
- Stage 26.5 public contract decision;
- stronger DNS/redirect/private-network boundary decision;
- release-grade Python/model artifact reproducibility;
- deprecated transitive dependency cleanup;
- Stage 27 installer/update/repair/doctor/uninstall/key rotation/rollback/restart recovery;
- Stage 28 clean-user product E2E and first stable release.

## Active rules

- resolve live `main` before work;
- ChatGPT is the only planner/intelligence;
- semantic/native structure comes before vision whenever reliable structure exists;
- local vision starts only on explicitly authorized paths and may ABSTAIN;
- stale or uncertain visual evidence causes zero mutation;
- remembered procedure never overrides current observed state;
- procedural memory stores structured evidence, not private reasoning;
- public semantic surface remains exactly five tool names until the explicit post-desktop contract decision;
- accepted implementation evidence and authoritative documentation move together.

# Current State

## Current accepted `main`

`2a410476ef849fd6d9c172703a004b1befcbcfb1` — `Stage 25.2: semantic-first internal vision escalation (#77)`.

The accepted ordinary-Chat path is:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

Current public Chat-facing tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Ordinary ChatGPT remains the only planner/intelligence.

## Stage 24 / 24.1 — ACCEPTED

Stage 24 accepted the five-tool semantic surface and Windows lifecycle. Stage 24.1 selected direct stdio semantic tunnel binding as the normal public path while retaining 1MCP internally where its lifecycle/diagnostic features add value.

## Stage 25 — grounding baseline ACCEPTED

PR #73 was squash-merged as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Accepted target baseline:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
present-target hits = 3/5
false clicks = 0
```

Repeated-row and tiny target classes remain deliberately unpromoted. Do not describe the safety gate as universal visual accuracy.

## Stage 25.1 — same-session visual foundation ACCEPTED

PR #74 was squash-merged as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Accepted foundations include:

- same Playwright page/session screenshot -> prepared target -> freshness -> coordinate action or ABSTAIN;
- stale/replay/layout/scroll/overlay/navigation uncertainty fails closed;
- prepared visual targets are TTL-purged/capped;
- focused llama.cpp lifecycle owner and deterministic unload;
- PID-bound loopback listener verification before inference;
- class-aware visual authorization;
- secure installed semantic runtime and lock-hash-enforced `npm ci`;
- Windows junction containment, credential scrub, bounded literal-IP browser policy and CodeQL coverage.

Reviewed RAM policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

## Stage 25.2 — MERGED AND ACCEPTED

PR #77 was squash-merged to current `main` as:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

### Accepted routing contract

For `web_interact(operation=click)` with bounded `visualFallback` intent:

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

Generic semantic click failures never trigger vision.

Authorization rules:

- `targetText` is the semantic and visual authorization anchor;
- planner-supplied target `kind` is not accepted;
- planner `target` and free-form `instruction` cannot redirect visual grounding;
- the router builds canonical visual instruction locally from `targetText`;
- safe ABSTAIN is a successful no-action result, not a disguised backend error;
- icon-only, repeated-row and tiny targets are not automatically promoted.

Final real target evidence with normal Chrome workload left open:

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

Result path:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json`

## Active priority — Stage 26 Procedural Memory / Demo2Workflow

Stage 26 is **design-active, not product-accepted**. Read `project-context/STAGE26_PROCEDURAL_MEMORY.md` before implementation.

The technical reference is official `Tencent/UI-Mate`, pinned during analysis to upstream commit:

`d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`.

We are not adopting UI-Mate as a second GUI agent or adding a large local planner. We adopt the procedural-memory pattern:

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

Important Stage 26 rules:

- stored workflows are guidance/evidence, not authorization and not planners;
- do not persist private chain-of-thought;
- one successful run creates at most a candidate skill;
- completion pointer advances only on applicable verifier evidence, not merely because a model says `subtask_complete`;
- retrieval may rank candidate skills but cannot authorize an action;
- current observed state outranks remembered milestones/action history;
- specific local programs/capabilities are selected later from actual tasks and evidence, not preselected in the roadmap.

## Explicit planned Stage 26.x — Windows desktop surface

**Do not omit or forget this layer.**

After the procedural data/compiler foundation, build a scoped Windows desktop capability surface with deterministic/native observation first, screen capture and bounded vision where needed, reviewed keyboard/mouse execution and fail-closed authorization.

True arbitrary human “show me once” recording belongs at or after this layer, because the current browser semantic bridge observes its own controlled actions but does not yet provide a general Windows demonstration recorder.

Only after the Windows desktop surface exists should the project make an explicit ADR deciding whether ordinary Chat needs new public tool names or whether the current small-semantic-surface philosophy can continue with a few coarse truthful actions.

Until then the accepted public tool names remain the same five.

## Remaining product work

- Stage 26.1 procedural data foundation: raw trajectory/redaction/retention, compiled skill schema, versioning/store/validation;
- Stage 26.2 Demo Compiler + completion verifier + self-demo/variant-task acceptance;
- Stage 26.3 Windows desktop surface;
- Stage 26.4 human demonstration capture + transferable skill acceptance;
- Stage 26.5 explicit public contract decision;
- stronger DNS/redirect/private-network boundary decision;
- release-grade Python/model artifact reproducibility;
- dependency cleanup for deprecated transitive `glob@10.5.0`;
- Stage 27 installer/update/repair/doctor/uninstall/key rotation/rollback/restart recovery;
- Stage 28 clean-user end-to-end product acceptance and first stable release.

## Active rules

- ChatGPT is the only planner/intelligence;
- semantic/native structure comes before vision whenever reliable structure exists;
- local vision starts only on explicitly authorized paths and may ABSTAIN;
- stale or uncertain visual evidence causes zero mutation;
- remembered procedure never overrides current observed state;
- procedural memory stores structured evidence, not private reasoning;
- public semantic surface remains exactly five tools until the explicit post-desktop contract decision;
- heavy local vision starts only when admitted/needed and unloads deterministically;
- accepted implementation evidence and authoritative documentation move together.

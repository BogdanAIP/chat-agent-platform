# Current State

## Accepted platform foundation

Stage 24 was squash-merged on 2026-08-16 as `175d36236f80a1f99f091d4f031a1c6255f3652b` (#66). Stage 24 accepted the exact five-tool semantic ordinary-Chat contract:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Stage 24.1 was squash-merged on 2026-08-16 as `df1d5e232b739b62e72ad81e5d82fd01be53e884` (#70). The selected normal path is direct stdio:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> Filesystem / Playwright / focused adapters
```

The 1MCP path remains valid historical acceptance and internal diagnostic/adaptive infrastructure; it is not the normal semantic critical path.

## Stage 25 grounding benchmark — MERGED / SAFETY GATE PASSED

PR #73 was squash-merged to `main` on 2026-08-17 as:

`acc6334ef0114d3ca6b6a243d904605cd00a321a` — `Stage 25: safe local vision grounding benchmark (#73)`.

Current target-laptop grounding configuration:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = LFM2.5-VL-450M F16
CPU path = 8 threads
ctx = 2048
batch = 128
ubatch = 64
cache K/V = q8_0
image tokens = 64..256
parallel = 1
```

The selected target-laptop model is F16, not Q4. The current accepted runtime for the grounding benchmark is llama.cpp, not LM Studio/llmster.

Final target evidence with Chrome running:

| Case | Result |
|---|---|
| labeled primary Send | HIT |
| icon-only Search | HIT |
| repeated-row Gamma menu | safe ABSTAIN |
| tiny alert indicator | safe ABSTAIN |
| enabled-vs-disabled Send | HIT |
| absent Export CSV | correct ABSTAIN |

Aggregate safety result:

```text
present-target HIT = 3/5
false clicks = 0
provider/context errors = 0
```

The native bbox adapter now includes target-blind labeled-button inventory, bounded downscale-only refinement crops, deterministic remapping, and fail-closed non-text pass disagreement. The model never performs an action itself.

This benchmark proves a safe perception candidate. It does not prove production browser integration.

## Stage 25.1 — ACTIVE: same-session visual fallback integration

Active branch:

`chat/stage25-1-vision-integration-foundation`

No visual coordinate is authorized for automatic interaction until the project proves this invariant:

```text
same Playwright page/session
  -> semantic attempt
  -> screenshot of current page/viewport
  -> local vision grounding
  -> freshness/coordinate validation
  -> action in the same page/session OR ABSTAIN
```

Current integration gap: `semantic-projection` acts through semantic/accessibility targets, while the Stage 25 benchmark adapter consumes an image and can return a source-image point. There is not yet a production-safe bridge that proves the screenshot and eventual action belong to the same unchanged browser state.

Therefore Stage 25.1 must first establish an internal browser-grounding contract and acceptance tests. A simple `VLM point -> click` implementation is forbidden.

## Current P0/P1 work

P0:

1. synchronize authoritative documentation with #73;
2. define same-session capture/ground/action invariants;
3. add integration acceptance proving HIT and ABSTAIN/no-action behavior.

P1:

4. add focused local-vision lifecycle/resource admission instead of loading the model permanently;
5. strengthen grounding verification per target class rather than one global IoU threshold;
6. test stale layout, scroll, overlays, repeated targets, tiny targets and other adversarial browser states;
7. test workspace link/junction containment, private-network navigation policy and tunnel-key inheritance;
8. broaden static analysis/dependency maintenance;
9. move stable installation toward locked/reproducible npm/Python dependencies.

## Active architectural findings

- ordinary ChatGPT is the planner/intelligence;
- semantic DOM/accessibility grounding remains first choice;
- local vision is a bounded fallback and may ABSTAIN;
- current public tool count remains five;
- `semantic-projection` must remain a thin deterministic compatibility boundary, not a model manager or second planner;
- local inference lifecycle should be a focused owned subsystem with explicit resource admission and cleanup;
- installed/source single-owner and fail-closed guarantees remain required;
- no stable product release exists yet.

## Historical Stage 25 research

Documents that describe LM Studio/llmster, 450M Q4 or PR #72 as the active next step are retained as research/history. They do not override the accepted #73 target evidence above.

The complete pre-Stage-22 implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd` for historical extraction only.

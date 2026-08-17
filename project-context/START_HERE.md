# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## Current accepted integration line

Current accepted `main` after Stage 25 grounding benchmark:

`acc6334ef0114d3ca6b6a243d904605cd00a321a` — `Stage 25: safe local vision grounding benchmark (#73)`.

Stage 24 and 24.1 remain accepted historical foundations. The normal ordinary-Chat path is:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

The public semantic surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure; it is not the normal semantic critical path.

## Stage 25 grounding baseline — ACCEPTED SAFETY EVIDENCE

PR #73 selected the current target-laptop grounding candidate:

```text
runtime = llama.cpp b10448 / commit ad1de39e0
model = LiquidAI/LFM2.5-VL-450M-GGUF F16
projector = mmproj LFM2.5-VL-450M F16
execution = CPU, 8 threads, ctx 2048
```

Target Windows evidence with Chrome running:

- Search: HIT;
- Send: HIT;
- enabled Send/state disambiguation: HIT;
- Export CSV absent target: correct ABSTAIN;
- repeated-row Gamma action: safe ABSTAIN;
- tiny alert indicator: safe ABSTAIN;
- false clicks: 0;
- provider/context errors: 0.

Accuracy on present targets is therefore 3/5. This is a safe grounding candidate, not a finished browser controller.

Older Stage 25 documents that discuss LM Studio/`llmster`, 450M Q4 as an untested candidate, or active PR #72 are pre-acceptance research/history and do not override this file, current code/tests, or `CURRENT_STATE.md`.

## Current development — Stage 25.1 vision integration foundation

Active branch:

`chat/stage25-1-vision-integration-foundation`

Do not connect a VLM coordinate directly to a browser click.

The required product path is:

```text
web operation
  -> semantic DOM/accessibility grounding first
  -> only if semantic grounding is unavailable/ambiguous:
       capture from the SAME Playwright page/session
       -> bounded local vision grounding
       -> deterministic validation / freshness verification
       -> resolved action OR ABSTAIN
  -> perform any action only in that SAME Playwright page/session
```

A visual result is invalid for automatic interaction if the page/viewport/scroll/coordinate space cannot be proven to still match the captured frame. Uncertainty must produce ABSTAIN and no page mutation.

Read `project-context/STAGE25_1_VISION_INTEGRATION.md` before implementation work.

## Immediate priority order

1. Keep source-of-truth documentation synchronized with accepted #73 evidence.
2. Define and prove same-session screenshot -> grounding -> action semantics before auto-click.
3. Add semantic->vision integration acceptance with both HIT and ABSTAIN/no-action cases.
4. Add a focused local-vision lifecycle owner with resource admission, health, cleanup and idle unload; do not inflate `semantic-projection` or the public manager into a generic process/AI gateway.
5. Strengthen production grounding verification without a single global IoU threshold.
6. Add stale-layout/adversarial browser tests.
7. Add security regression coverage for workspace links/junctions, private-network browser navigation policy, and tunnel-key inheritance.
8. Improve static analysis and npm/Python dependency maintenance.
9. Move stable distribution toward locked/reproducible dependencies.
10. Refactor duplicated inference transport/model-specific naming only after the P0/P1 boundaries are proven.

## Non-negotiable product boundary

- ordinary ChatGPT remains the planner/intelligence;
- local models are bounded perception/extraction backends, never a second planner;
- prefer semantic DOM/accessibility grounding over vision when deterministic structure exists;
- visual grounding must fail closed;
- keep the public tool surface small and truthful;
- do not expose raw prompts, arbitrary inference endpoints, arbitrary model administration, generic `tool_invoke`, or unrestricted local paths/remote images;
- preserve single-owner/fail-closed lifecycle guarantees;
- use the user only for irreducible target-machine or ordinary-Chat UI gates.

## Source-of-truth order

When documents disagree:

1. current code, tests and exact current CI/target evidence;
2. this file and `CURRENT_STATE.md`;
3. `ARCHITECTURE.md` and accepted ADRs;
4. `STAGE25_1_VISION_INTEGRATION.md` for current vision-integration work;
5. `ROADMAP.md`;
6. historical Stage 25 research/handoff documents and README.

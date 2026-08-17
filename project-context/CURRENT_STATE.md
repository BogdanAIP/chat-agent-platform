# Current State

## Accepted foundation

Stage 24 (#66) accepted the exact five public semantic tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Stage 24.1 (#70) selected the normal direct stdio path:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> focused backends/adapters
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

## Stage 25 grounding benchmark — ACCEPTED

PR #73 was squash-merged to `main` on 2026-08-17 as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Current target-laptop grounding baseline:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
```

Final target evidence with Chrome running:

```text
Search = HIT
Send = HIT
state-disambiguated Send = HIT
Gamma = safe ABSTAIN
tiny indicator = safe ABSTAIN
Export CSV absent = correct ABSTAIN
present-target hits = 3/5
false clicks = 0
provider/context errors = 0
```

This is a safe visual-grounding fallback baseline, not a finished browser controller.

## Stage 25.1 — ACTIVE

Branch: `chat/stage25-1-vision-integration-foundation`

Draft PR: #74 — `Stage 25.1: same-session vision fallback foundation`.

### P0 documentation synchronization — DONE ON BRANCH

Authoritative docs now reflect #73, llama.cpp/F16 and the real 3/5 + safe-abstain result. Older LM Studio/llmster/Q4/PR #72 material remains historical research only.

### P0 same-session browser bridge — PROVED IN WINDOWS CI

Head `3183c537ca018d46d4d32c392ad101c20fe137b2` adds an internal same-session bridge using the already pinned Playwright MCP 0.0.78 opt-in vision primitives.

Proved path:

```text
one Playwright MCP client/session
  -> browser_take_screenshot(scale=css)
  -> bounded deterministic grounder
  -> one-shot prepared visual token
  -> fresh same-session screenshot
  -> exact dimensions + SHA256 freshness validation
  -> browser_mouse_click_xy OR ABSTAIN
```

Dedicated Windows workflow completed successfully and also reran the existing semantic acceptance, preserving the exact five public tools.

Positive case: intended visual-only target clicked exactly once.

Negative cases: replayed token, layout-shifted stale capture and grounder ABSTAIN all produced no coordinate action. This proves a second browser or unrestricted `browser_evaluate` is unnecessary for the same-session boundary.

The bridge is still internal only. Production `semantic-projection` has not yet been changed to invoke the real VLM or automatically escalate `web_interact`.

## Next active priority — local vision runtime lifecycle

Implement a focused non-agentic llama.cpp runtime owner with:

- exact approved runtime/model/projector identity;
- conservative physical/virtual memory admission;
- loopback-only owned process startup and readiness;
- status/use-touch;
- idle unload/TTL;
- explicit stop and stale/crash cleanup;
- no Chrome/unrelated-process termination.

It must remain separate from Chat planning, browser action choice and arbitrary model administration.

## Following P1 priorities

- production model-neutral grounder + semantic->vision escalation;
- class-aware grounding verifier;
- stale/adversarial browser coverage;
- Windows link/junction root containment regression;
- localhost/private-network navigation policy test;
- tunnel credential child-inheritance test;
- Node/Python static analysis and npm/Python dependency maintenance;
- reproducible dependency locking before stable distribution.

## Active rules

- ChatGPT is the only planner/intelligence;
- semantic DOM/accessibility grounding comes first;
- vision may ABSTAIN and never clicks by itself;
- stale visual evidence must not mutate the page;
- public semantic surface stays small and truthful;
- authoritative documentation is updated together with accepted implementation evidence;
- no stable product release exists yet.

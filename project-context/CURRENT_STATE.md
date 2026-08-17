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

## Stage 25.1 — ACTIVE / draft PR #74

Branch: `chat/stage25-1-vision-integration-foundation`.

Exact fully-green implementation head before this documentation update:

`c7eecc4ec1c4796e943816c9e51256d6b181b452`.

At that head, general `ci`, the same-session bridge workflow, synthetic vision-runtime workflow, Windows junction security regression, three-language CodeQL matrix and Secret History Scan all completed successfully.

### P0 source-of-truth synchronization — DONE

Authoritative docs reflect #73, llama.cpp/F16 and the real 3/5 + safe-abstain result. Older LM Studio/llmster/Q4/PR #72 material is historical research only.

### P0 same-session visual-action boundary — PROVED

One pinned Playwright MCP 0.0.78 client/session now proves:

```text
browser_take_screenshot(scale=css)
  -> bounded grounder
  -> one-shot prepared visual token
  -> fresh same-session screenshot
  -> exact viewport dimensions + screenshot SHA256
  -> browser_mouse_click_xy OR ABSTAIN
```

Windows acceptance proves:

- unchanged target -> exactly one intended coordinate action;
- prepared tokens are one-shot/replay-safe;
- layout shift -> stale ABSTAIN/no coordinate action;
- scroll -> stale ABSTAIN/no coordinate action;
- overlay -> stale ABSTAIN/no coordinate action;
- navigation/page replacement -> stale ABSTAIN/no coordinate action;
- missing/ambiguous grounder result -> ABSTAIN/no action;
- existing exact five-tool semantic acceptance remains green.

A second browser and unrestricted `browser_evaluate` are therefore unnecessary for this boundary.

### P1 focused local-vision lifecycle — PROVED SYNTHETICALLY

A separate non-agentic runtime owner now exists for the reviewed F16 profile. It enforces:

- exact llama.cpp build markers;
- exact model/mmproj size + SHA256;
- loopback-only binding;
- conservative physical + virtual memory admission;
- owned process identity using PID + executable + full command-line SHA256 + UTC creation ticks;
- idempotent healthy Start;
- Touch/use tracking;
- idle TTL unload;
- explicit Stop;
- foreign-listener fail-closed behavior;
- ownership-mismatch fail-closed behavior;
- model tamper rejection;
- no Chrome/unrelated-process termination.

Synthetic Windows acceptance passed all lifecycle cases. **Real target-laptop F16 lifecycle acceptance is still pending** and must not be inferred from the fake runtime test.

### P1 class-aware production grounding authorization — IMPLEMENTED / UNIT-TESTED

Production promotion is deliberately stricter than benchmark output:

- `labeled_button` and `visual_state`: unique target-blind text inventory + unique refinement; no global/high IoU threshold;
- `icon_only`: unique pass1 + unique pass2 + positive pass overlap;
- `repeated_similar_control`: forced ABSTAIN until separate target evidence promotes it;
- `tiny_target`: forced ABSTAIN until separate target evidence promotes it;
- absent/unreviewed/ambiguous/error paths: no action.

This prevents a future accidental benchmark `accepted` from promoting Gamma/tiny directly into a production click.

### P1 Windows junction containment — PROVED

A real Windows regression creates a junction from inside the allowed workspace to an outside directory and calls the normal semantic `workspace_*` tools.

Proved:

```text
junction read outside root = blocked
junction write outside root = blocked
normal write inside root = works
```

The suspected junction escape did not reproduce on the current pinned Filesystem MCP stack. Keep the regression as protection against future dependency behavior changes.

### P1 static analysis/dependency monitoring — IMPROVED / PROVED

CodeQL now analyzes:

```text
actions
javascript-typescript
python
```

All three jobs passed on `c7eecc4e`.

Dependabot now monitors:

- GitHub Actions;
- npm in `runtime/semantic-projection`;
- pip at repository root.

This improves monitoring but does not replace the still-pending reproducible lockfile work.

## Remaining priority work

1. Real model-neutral local-VLM grounder behind the runtime owner and same-session bridge.
2. Real target-Windows F16 lifecycle + same-session acceptance with Chrome open.
3. Explicit `CONTROL_PLANE_API_KEY` child-environment regression and scrub policy if needed.
4. Explicit localhost/private-network browser scope policy/regression without breaking intentional local-web workflows.
5. Reproducible npm/Python dependency installation/locking.
6. Additional target-class promotion only from measured evidence; repeated/tiny remain fail-closed.
7. P2 cleanup: common inference transport/model-neutral internal naming after safety boundaries stabilize.

## Active rules

- ChatGPT is the only planner/intelligence;
- semantic DOM/accessibility grounding comes first;
- vision may ABSTAIN and never clicks by itself;
- stale visual evidence cannot mutate the page;
- public semantic surface stays exactly five tools during this work;
- heavyweight model lifecycle remains separate from semantic planning/action logic;
- authoritative docs are updated with proven evidence;
- no stable product release exists yet.

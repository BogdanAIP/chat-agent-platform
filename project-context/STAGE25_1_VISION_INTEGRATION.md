# Stage 25.1 — Same-session visual fallback integration

Status: **ACTIVE DESIGN / IMPLEMENTATION FOUNDATION**

Branch: `chat/stage25-1-vision-integration-foundation`

Base: `acc6334ef0114d3ca6b6a243d904605cd00a321a` (`main` after PR #73).

## Why this stage exists

Stage 25 #73 proved a safe local grounding candidate on the target Windows laptop, but the benchmark adapter and the semantic browser path are still separate systems:

```text
semantic-projection / Playwright
  -> semantic refs/actions

local vision benchmark
  -> image
  -> bbox/point OR ABSTAIN
```

The missing production boundary is not “call the model.” The missing boundary is proving that capture, grounding and action refer to the **same unchanged Playwright page/session and coordinate space**.

A direct `VLM returned (x,y) -> click` implementation is forbidden until this contract is proven.

## Accepted Stage 25 evidence

Merged PR #73 baseline:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LiquidAI/LFM2.5-VL-450M-GGUF F16
mmproj = F16
threads = 8
ctx = 2048
```

Final target result with Chrome running:

```text
Search = HIT
Send = HIT
state-disambiguated Send = HIT
Gamma repeated-row = safe ABSTAIN
tiny indicator = safe ABSTAIN
Export CSV absent = correct ABSTAIN
false_clicks = 0
provider/context_errors = 0
present_target_hits = 3/5
```

This is the Stage 25.1 starting point. Do not repeat LM Studio/Q4 candidate selection unless a new measured comparison is intentionally requested.

## Required product flow

```text
ordinary ChatGPT
  -> existing semantic browser operation
  -> semantic DOM/accessibility grounding first
       -> resolved: use semantic target
       -> absent/ambiguous/insufficient:
            capture from SAME Playwright page/session
            -> local visual grounding
            -> deterministic validator
            -> freshness/coordinate proof
            -> resolved action OR ABSTAIN
  -> action, if any, executes in SAME Playwright page/session
```

Vision remains an internal browser-grounding strategy. It does not become a planner and does not automatically require a sixth public Chat tool.

## Same-session invariants

An automatic visual action is authorized only if the implementation can establish all applicable invariants below.

### Session/page identity

- capture and action belong to the same Playwright-controlled browser context and page;
- navigation/page replacement after capture invalidates the result;
- the implementation must not silently open a second browser/page to perform perception or action.

### Coordinate identity

- the coordinate space is explicit (`css_viewport` is preferred for browser action semantics);
- screenshot pixel dimensions and browser viewport dimensions are related deterministically;
- device-pixel ratio/scale/zoom handling is known rather than guessed;
- scroll offsets are captured and verified if relevant;
- image crop/downscale transforms are deterministic and invertible back to the authorized browser coordinate space.

### Freshness

- relevant page state must be revalidated before action;
- layout/scroll/navigation changes invalidate stale visual results;
- an implementation may use a bounded capture token/fingerprint/epoch only if it is deterministic and tied to the same page state;
- uncertainty is never converted into “best effort” coordinate action.

### Mutation safety

- `ABSTAIN` and `error` must produce zero browser mutation;
- diagnostics retained after ABSTAIN are non-authorizing;
- a grounding result cannot be reused after a page state change unless recaptured/revalidated.

## Semantic-first policy

Vision is not invoked merely because it exists.

Use semantic/accessibility grounding when a target can be deterministically resolved. Escalate to vision only for cases such as:

- icon-only controls without a reliable semantic ref;
- canvas/WebGL or otherwise non-semantic visual targets;
- repeated/state-dependent targets where semantic structure is insufficient;
- visual-only affordances that cannot be identified safely through the accepted semantic backend.

Do not replace a stable semantic ref with a visual coordinate.

## Internal model-neutral contract

The production boundary should use a provider/model-neutral result. Candidate shape:

```text
GroundingResult {
  status: "resolved" | "abstain" | "error",
  source: "semantic" | "vision",
  target_kind: "text" | "icon" | "repeated" | "tiny" | "state" | "unknown",
  coordinate_space: "semantic_ref" | "css_viewport",
  semantic_ref?: string,
  bbox?: {x1,y1,x2,y2},
  point?: {x,y},
  capture_context?: {
    viewport_width,
    viewport_height,
    scroll_x,
    scroll_y,
    scale,
    page_state_token
  },
  reason: string,
  diagnostics?: object
}
```

The exact schema may change after inspecting the pinned Playwright MCP capabilities. The invariant is more important than the field names: only `status=resolved` with fresh same-session evidence may authorize action.

## Pinned Playwright capability decision

Before writing browser action glue, inspect the actual pinned `@playwright/mcp@0.0.78` tool surface and implementation path.

Preferred order:

1. reuse a reviewed Playwright MCP primitive if it can capture and act in the same managed page with the required coordinate semantics;
2. compose existing reviewed primitives inside the deterministic semantic projection if this preserves the invariant;
3. only if the pinned MCP lacks a required narrow primitive, add the smallest focused browser-grounding adapter around Playwright/session state.

Do **not** enable unrestricted `browser_evaluate`, `browser_run_code_unsafe`, arbitrary network requests or a generic browser scripting endpoint as a shortcut.

## Integration acceptance — P0

The first real Stage 25.1 acceptance must use one Playwright page and prove both paths.

### Positive case

```text
open fixture/page
-> semantic lookup intentionally unavailable/ambiguous for target
-> capture from same page
-> visual grounding resolves target
-> freshness passes
-> action executes in same page
-> page exposes deterministic success marker
```

Required assertions:

- same page/session identity retained;
- no second browser instance used;
- expected visual decision is `resolved`;
- action point/ref is inside authorized target;
- page success marker changes exactly once;
- no unrelated interaction occurred.

### Negative case

```text
open fixture/page
-> capture
-> make page stale OR return uncertain visual grounding
-> validator returns ABSTAIN
-> no action
-> page state remains unchanged
```

Required assertions:

- zero click/type/navigation after ABSTAIN;
- diagnostic bbox/point, if retained, is non-actionable;
- stale result cannot be replayed.

## Vision runtime lifecycle — P1

The Stage 25 benchmark assumed an already-running llama.cpp server. Production integration needs a focused non-agentic lifecycle owner.

Responsibilities:

```text
approved runtime/model artifact identity
-> resource admission
-> start if needed
-> health/readiness
-> inference availability
-> idle TTL/unload
-> crash/stale-process cleanup
```

Non-responsibilities:

- user-goal planning;
- arbitrary model selection/download;
- Chat-facing model administration;
- browser action decisions;
- generic job orchestration.

The lifecycle owner should be separate from `semantic-projection` and should not turn `chat-platform.ps1` into a heavyweight model supervisor.

## Resource admission

The current F16 model is viable but leaves limited headroom on the target laptop. Production admission must check real available memory before load/start and fail closed when headroom is insufficient. Never auto-kill Chrome or arbitrary user processes to make room.

A later quantized/model comparison is allowed only as a measured optimization. It must not silently replace the accepted F16 baseline merely because it uses less RAM.

## Grounding verifier — P1

Do not use one global IoU threshold.

Current evidence shows different reliable strategies by target class:

- text-labeled targets benefit from target-blind inventory plus refinement;
- icon/non-text targets need pass-consistency/freshness checks;
- repeated rows require stronger context disambiguation;
- tiny targets should prefer safe ABSTAIN over a guessed click;
- state-dependent targets need state evidence, not label text alone.

The verifier should produce explicit deterministic reason codes and preserve fail-closed behavior.

## Adversarial/stale-state tests — P1

Add at least:

- layout shift after capture;
- scroll after capture;
- navigation/page replacement after capture;
- overlay/modal introduced after capture;
- repeated visually similar rows/icons;
- tiny target;
- enabled/disabled visual state;
- absent target;
- canvas/WebGL or other non-semantic target where practical;
- hostile/on-screen text that attempts to instruct the VLM rather than describe the requested UI target.

## Security regressions — P1

Add explicit tests for:

1. Windows symlink/junction escape from an authorized filesystem root;
2. localhost/private-network browser navigation policy;
3. absence of `CONTROL_PLANE_API_KEY` in semantic-projection and downstream backend environments unless explicitly required.

Do not describe these as confirmed vulnerabilities until a test proves one.

## Supply-chain/dependency hardening — P1/P2

- expand static analysis to the real Node/Python implementation in addition to Actions;
- keep PowerShell syntax/contract tests explicit;
- add npm/Python dependency update coverage;
- move stable distribution away from unlocked runtime installation (`npm install --package-lock=false`);
- preserve checksum/hash verification for downloaded binaries/artifacts.

## Refactoring after contracts stabilize — P2

After same-session and lifecycle gates are green:

- extract duplicated loopback JSON inference transport from benchmark provider modules;
- expose model-neutral internal names (`VisionRuntime`, `VisualGrounder`, `GroundingResult`);
- keep model-specific native bbox prompts/adapters behind provider implementations;
- separate benchmark evidence/assets from production runtime code without deleting historical evidence.

## Public Chat surface

Do not add a public `vision_*` action solely for browser fallback. If later document/image/chart tasks require independent vision capability, design that separately with a truthful bounded schema and run a fresh Chat app Refresh/review + ordinary-Chat E2E gate.

Until then, exported Chat tools remain exactly five.

## Stage 25.1 completion gate

Stage 25.1 is complete only when:

- same-session capture/ground/action is proven;
- stale/uncertain visual results cannot mutate the page;
- local vision lifecycle/resource admission is deterministic and leaves no stale process;
- security regressions are explicit;
- integration CI reacts to changes in the visual grounding/runtime path;
- target Windows acceptance passes with realistic Chrome usage;
- the public semantic contract remains truthful and small;
- authoritative documentation matches the merged implementation.

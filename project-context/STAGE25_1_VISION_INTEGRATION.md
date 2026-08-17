# Stage 25.1 — Same-session visual fallback integration

Status: **ACTIVE IMPLEMENTATION**

Branch: `chat/stage25-1-vision-integration-foundation`

Draft PR: #74.

Base: `acc6334ef0114d3ca6b6a243d904605cd00a321a` (`main` after PR #73).

## Accepted Stage 25 starting point

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

This is a safe perception baseline, not a finished browser controller.

## Fully-green Stage 25.1 evidence point

Implementation head `c7eecc4ec1c4796e943816c9e51256d6b181b452` completed successfully in:

- general `ci`;
- Stage 25.1 Vision Bridge Acceptance;
- Stage 25.1 Vision Runtime Acceptance;
- Stage 25.1 Security Regressions (Windows junction);
- CodeQL Security for Actions, JavaScript/TypeScript and Python;
- Secret History Scan.

The documentation after that head records only behavior actually demonstrated at or before this evidence point.

## P0 same-session bridge — PROVED IN WINDOWS CI

The internal `SameSessionVisualGroundingBridge` uses the already pinned Playwright MCP 0.0.78 vision capability in one MCP client/session:

```text
browser_take_screenshot(type=png, fullPage=false, scale=css)
  -> bounded grounder
  -> one-shot opaque visual-target token
  -> re-capture same CSS viewport
  -> exact dimensions + SHA256 freshness check
  -> browser_mouse_click_xy only when unchanged
```

Acceptance proves:

- intended visual-only target is clicked exactly once when the frame is unchanged;
- token replay cannot cause a second action;
- layout shift invalidates the prepared target;
- scroll invalidates the prepared target;
- a newly introduced overlay invalidates the prepared target;
- navigation/page replacement invalidates the prepared target;
- missing or ambiguous grounder output yields ABSTAIN;
- every stale/uncertain path produces zero coordinate action;
- the existing exact five-tool public semantic acceptance still passes.

This closes the architectural question of whether a second browser or unsafe `browser_evaluate` is required: **it is not**.

The current freshness policy intentionally requires an exact full CSS screenshot match. It may over-abstain on dynamic pages. Any later relaxation must be deterministic and separately accepted.

## Required product flow

```text
ordinary ChatGPT
  -> existing semantic browser operation
  -> semantic DOM/accessibility grounding first
       -> resolved: act semantically
       -> unavailable/ambiguous:
            SAME Playwright page/session
            -> CSS-pixel capture
            -> local visual grounding
            -> production authorization policy
            -> freshness proof
            -> resolved action OR ABSTAIN
```

Vision remains an internal grounding strategy, not a planner and not a reason to add a sixth public Chat tool.

## Focused vision runtime lifecycle — PROVED SYNTHETICALLY

The benchmark originally assumed an already-running llama.cpp server. Stage 25.1 now has a separate non-agentic runtime owner for the reviewed profile.

Production profile fixes:

- llama.cpp command and required `build 10448` / `ad1de39e0` markers;
- exact F16 model/mmproj filenames, sizes and SHA256;
- `127.0.0.1` only;
- accepted Stage 25 CPU/context arguments;
- conservative physical + virtual memory admission;
- idle TTL and watchdog interval.

Owned-process identity requires:

```text
PID
+ exact executable
+ SHA256(full actual Windows CommandLine)
+ exact process creation UTC ticks
```

Windows fake-loopback acceptance proves:

```text
Doctor = PASS
idempotent Start = PASS
Touch + idle TTL unload = PASS
explicit Stop = PASS
tampered model rejection = PASS
foreign listener fail-closed = PASS
ownership mismatch fail-closed = PASS
```

The controller never kills Chrome or arbitrary user processes. Arbitrary production config/model/runtime overrides remain disabled outside explicit test mode.

**Boundary:** this is deterministic/synthetic lifecycle proof. The real F16 model still needs target-laptop lifecycle acceptance with realistic Chrome usage.

## Production grounding authorization — IMPLEMENTED / UNIT-TESTED

`runtime/local_vision_adapter/production_policy.py` intentionally authorizes less than the benchmark adapter.

Current promotion policy:

- `labeled_button`: unique target-blind text inventory + unique refinement; no global/high IoU threshold;
- `visual_state`: same unique text inventory guard;
- `icon_only`: unique pass1 + unique pass2 + positive coarse/refined overlap;
- `repeated_similar_control`: forced ABSTAIN even if a benchmark row says `accepted`;
- `tiny_target`: forced ABSTAIN even if a benchmark row says `accepted`;
- absent, unknown, ambiguous or error paths: no action.

This preserves the measured valid very-low-overlap text case while preventing benchmark-only success from silently promoting unproven target classes.

## Security regressions

### Windows workspace junction — PROVED SAFE ON CURRENT PINNED STACK

A real Windows test created:

```text
allowed workspace/outside-link -> junction -> outside directory
```

Then called the normal semantic tools. Result:

```text
workspace_read through junction = blocked
workspace_write through junction = blocked
normal write inside workspace = works
```

The suspected junction escape did not reproduce. Keep the regression because future Filesystem MCP behavior can change.

### Tunnel credential inheritance — PENDING

The direct controller temporarily provides `CONTROL_PLANE_API_KEY` to tunnel-client startup. Do not assume it is absent from semantic/downstream children. Add an explicit regression and, if necessary, atomically scrub it from downstream backend environments without breaking packaged/installed semantic layout.

### Browser localhost/private-network scope — PENDING

The isolated Playwright profile is not a network sandbox, and local HTTP is intentionally used by accepted workflows/tests. Therefore do not impose an arbitrary blanket block. Define and test a truthful policy that preserves explicit local-web capability while preventing vision from autonomously expanding navigation scope.

## Supply-chain/static-analysis status

CodeQL now runs three jobs:

```text
actions
javascript-typescript
python
```

All three passed on the fully-green evidence head.

Dependabot now monitors GitHub Actions, semantic npm dependencies and root pip requirements.

Secret history scanning remains enabled and green.

## Reproducible dependency installation — PENDING

Semantic projection still uses exact top-level npm pins but runtime/bootstrap/CI currently installs without a committed lockfile:

```text
npm install --ignore-scripts --no-audit --no-fund --package-lock=false
```

Next hardening step is to generate/commit a real package lock from the pinned manifest, validate it, then switch reviewed install paths to `npm ci`. Do not hand-author a lockfile.

## Real production integration still pending

The browser bridge CI uses an injected deterministic grounder. It does **not** yet connect the real llama.cpp/VLM to `semantic-projection` or alter public `web_observe`/`web_interact` behavior.

Dependency-valid next work:

1. explicit credential inheritance regression / environment scrub policy;
2. explicit local/private browser scope policy/regression;
3. reproducible npm dependency lock/install;
4. model-neutral production grounder client combining the runtime owner + accepted native-bbox adapter + production policy;
5. controlled semantic->vision escalation behind the same-session bridge;
6. target-Windows real F16 lifecycle + real same-session acceptance with Chrome open;
7. only after those gates, consider additional target-class promotion or public capability changes.

## Public Chat surface

Exported Chat tools remain exactly five. Do not add a public `vision_*` tool solely for browser fallback. Independent document/image/chart analysis may justify a separate future capability with its own reviewed schema and ordinary-Chat acceptance.

## Completion gate

Stage 25.1 is complete only when:

- same-session capture/ground/action remains fail-closed;
- real local VLM is connected through the same boundary;
- stale/uncertain visual results cannot mutate the page;
- real target-laptop runtime admission/lifecycle leaves no stale process;
- credential/network scope regressions are explicit;
- dependencies are reproducible enough for the promoted path;
- integration CI reacts to visual/runtime changes;
- target Windows acceptance passes with realistic Chrome usage;
- public semantic contract remains truthful and small;
- authoritative documentation matches the merged implementation.

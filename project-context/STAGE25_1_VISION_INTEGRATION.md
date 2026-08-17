# Stage 25.1 — Same-session visual fallback integration

Status: **ACTIVE IMPLEMENTATION**

Branch: `chat/stage25-1-vision-integration-foundation`

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

## P0 same-session bridge — PROVED IN WINDOWS CI

PR #74 head `3183c537ca018d46d4d32c392ad101c20fe137b2` added an internal `SameSessionVisualGroundingBridge` and a real Windows Playwright acceptance. The dedicated `Stage 25.1 Vision Bridge Acceptance` workflow completed successfully.

The proof uses the already pinned `@playwright/mcp@0.0.78` with its opt-in vision capability in one MCP client/session:

```text
browser_take_screenshot(type=png, fullPage=false, scale=css)
  -> injected bounded grounder
  -> one-shot opaque visual-target token
  -> re-capture same CSS viewport
  -> exact dimensions + SHA256 freshness check
  -> browser_mouse_click_xy only when unchanged
```

Acceptance proved:

- coordinate action reaches the intended visual-only target in the same Playwright session;
- visual tokens are one-shot and cannot be replayed;
- a layout change after preparation changes the capture and causes `stale-visual-capture` ABSTAIN;
- stale/uncertain results cause zero coordinate click;
- grounder ABSTAIN causes zero action;
- the existing exact five-tool public semantic acceptance still passes.

This closes the architectural question of whether a second browser or unsafe `browser_evaluate` is required: **it is not**. The pinned Playwright MCP can provide the narrow same-session capture/action primitives internally.

The current freshness policy is deliberately strict: the full CSS screenshot must match exactly before commit. This may over-abstain on dynamic pages, but it is the correct safe first policy. Any later relaxation must be measured and deterministic.

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
            -> deterministic validation
            -> freshness proof
            -> resolved action OR ABSTAIN
```

Vision remains an internal browser-grounding strategy. It does not become a planner and does not automatically require a sixth public Chat tool.

## Same-session invariants

Automatic visual action requires all applicable conditions:

1. capture and action belong to the same Playwright client/session/page;
2. coordinate space is explicit and deterministic;
3. screenshot and viewport dimensions agree in CSS pixels;
4. any navigation/layout/scroll/visual state change that invalidates the prepared target causes ABSTAIN;
5. prepared targets are short-lived and one-shot;
6. ABSTAIN/error produces zero page mutation;
7. diagnostics retained after ABSTAIN are non-authorizing.

Do not replace a stable semantic ref with a visual coordinate.

## Production integration still pending

The CI bridge currently uses an injected deterministic grounder. It intentionally does **not** yet wire the real llama.cpp/VLM into `semantic-projection` or change public `web_observe`/`web_interact` behavior.

Next dependency-valid work:

1. focused local-vision runtime lifecycle/resource admission;
2. model-neutral production grounder adapter using the accepted native-bbox path;
3. controlled semantic->vision escalation behind the same-session bridge;
4. target-Windows acceptance with the real F16 model and Chrome open.

## Vision runtime lifecycle — P1 ACTIVE

The Stage 25 benchmark assumed an already-running llama.cpp server. Production integration needs a focused non-agentic runtime owner.

Responsibilities:

```text
approved runtime/model artifact identity
-> physical + virtual memory admission
-> owned process start
-> loopback-only health/readiness
-> touch/use tracking
-> idle TTL unload
-> explicit stop
-> crash/stale-state cleanup
```

Non-responsibilities:

- user-goal planning;
- arbitrary model selection/download;
- Chat-facing model administration;
- browser action decisions;
- generic job orchestration;
- killing Chrome or unrelated user processes.

The lifecycle owner remains separate from `semantic-projection` and from the public platform manager's core responsibilities.

## Resource policy

The accepted F16 model is viable but leaves limited memory headroom on the target laptop. Admission must fail closed before model start when conservative physical/virtual memory floors are not met. Exact production thresholds remain subject to target-machine acceptance; do not lower them merely to make a test pass.

## Grounding verifier — P1

Do not use one global IoU threshold. Current evidence needs class-aware verification:

- text-labeled targets: target-blind inventory + refinement;
- icon/non-text: pass consistency + freshness;
- repeated rows: stronger contextual disambiguation;
- tiny targets: safe ABSTAIN over guessed click;
- state-dependent targets: state evidence, not label text alone.

## Adversarial/stale-state tests — P1

The first CI already proves one layout-shift stale-capture case. Remaining coverage includes scroll, navigation/page replacement, overlays, repeated visual targets, tiny/state/absent cases, canvas/WebGL where practical, and hostile on-screen prompt-like text.

## Security regressions — P1

Add explicit tests for:

1. Windows symlink/junction escape from an authorized filesystem root;
2. localhost/private-network browser navigation policy;
3. absence of `CONTROL_PLANE_API_KEY` in semantic-projection/downstream backend environments unless explicitly required.

Do not describe these as confirmed vulnerabilities until tests prove one.

## Supply-chain/dependency hardening — P1/P2

- expand static analysis to active Node/Python code in addition to Actions;
- keep PowerShell syntax/contract checks explicit;
- add npm/Python dependency update coverage;
- move stable distribution away from unlocked runtime install (`npm install --package-lock=false`);
- preserve checksum/hash verification for downloaded binaries/model artifacts.

## Public Chat surface

Do not add a public `vision_*` action solely for browser fallback. Independent document/image/chart analysis may justify a separate future reviewed capability, but that is a different contract and requires Refresh/review + ordinary-Chat acceptance.

Until then exported Chat tools remain exactly five.

## Stage 25.1 completion gate

Stage 25.1 is complete only when:

- same-session capture/ground/action remains green (PROVED for deterministic injected grounder);
- real local VLM is connected through the same boundary and remains fail-closed;
- stale/uncertain visual results cannot mutate the page;
- runtime resource admission/lifecycle leaves no stale process;
- security regressions are explicit;
- integration CI reacts to visual/runtime changes;
- target Windows acceptance passes with realistic Chrome usage;
- public semantic contract remains truthful and small;
- authoritative documentation matches merged implementation.

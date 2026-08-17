# Stage 25.1 — Same-session visual fallback integration

Status: **TARGET ACCEPTANCE PASSED — FOUNDATION READY FOR MERGE**

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

Stage 25 target result with Chrome running:

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

This remains a safe perception baseline, not universal visual accuracy.

## Same-session bridge — PROVED

The internal `SameSessionVisualGroundingBridge` uses pinned `@playwright/mcp@0.0.78` in one MCP client/session:

```text
browser_take_screenshot(type=png, fullPage=false, scale=css)
  -> bounded grounder
  -> one-shot opaque visual-target token
  -> re-capture same CSS viewport
  -> exact dimensions + SHA256 freshness check
  -> browser_mouse_click_xy only when unchanged
```

Windows acceptance proves intended coordinate action, replay protection, layout/scroll/overlay/navigation stale ABSTAIN, missing/ambiguous grounder ABSTAIN and zero action on uncertain evidence. Exact five public semantic tools remain unchanged.

The full-screenshot freshness policy is intentionally strict. Over-abstention is preferable to stale-coordinate mutation until narrower deterministic freshness is separately measured.

## Focused vision runtime owner — PROVED SYNTHETICALLY AND ON TARGET

`scripts/local-vision-runtime.ps1` owns only lifecycle/resource admission:

```text
reviewed llama.cpp + model + mmproj identity
-> memory admission
-> loopback Start/health
-> exact owned process identity
-> Touch
-> idle TTL / resource-pressure Sweep
-> Stop
```

Production defaults are fixed by `config/local-vision-runtime.json`: profile `lfm25-vl-450m-f16`, host `127.0.0.1`, port `3068`, reviewed llama.cpp build markers and exact model/mmproj hashes. Arbitrary runtime/model overrides are test-only.

Windows CI proves idempotent Start, Touch/TTL, explicit Stop, tampered artifact rejection, foreign listener rejection and ownership mismatch refusal.

The real target-laptop run additionally proves the reviewed runtime can cold-start under the user's normal Chrome workload, serve repeated F16 vision inference, remain above the emergency safety floor, and stop cleanly afterward without terminating Chrome.

## Production grounding policy — PROVED FOR CURRENT PROMOTED CLASSES

The benchmark row is not itself authorization. `production_policy.py` applies class-aware rules:

- labeled button / visual state: unique target-blind text inventory + unique refinement;
- icon-only: unique pass1 + unique pass2 + positive pass consistency;
- repeated similar controls: forced ABSTAIN;
- tiny targets: forced ABSTAIN;
- absent/unreviewed/ambiguous/error: no action.

Do not replace this with one global IoU threshold; accepted target evidence includes valid text refinement with low overlap.

## Model-neutral production grounder boundary — PROVED

`runtime/local_vision_adapter/production_grounder.py` accepts one PNG capture plus bounded `instruction`, `kind` and optional `target_text`, runs the accepted native-bbox implementation, then applies production authorization.

It intentionally does **not**:

- start/stop llama.cpp;
- select/download a model;
- accept arbitrary inference endpoints;
- inspect browser/page state;
- perform a browser action;
- return raw model responses through production diagnostics.

Only an authorized result contains a point/bbox. Repeated-row, absent, parse-failure and invalid-image cases remain non-authorizing.

## Runtime-backed runner — PROVED

The Node runtime-backed grounder is fixed to the reviewed profile and port and delegates lifecycle to the focused PowerShell owner.

A real target run exposed two Windows integration defects, both now closed:

1. **cold Start descendant-stdio settlement** — the controller process could exit while a long-lived descendant retained inherited stdio handles, delaying Node's child `close` until the 150 s timeout. Controller actions now settle on the controller process `exit` after a bounded drain. Windows regression marker: `RUNTIME_BACKED_VISUAL_GROUNDER_DESCENDANT_STDIO=PASS`.
2. **target wrapper output buffering** — the wrapper redirected Node stdout/stderr and only drained them after process exit. It now inherits the console directly, eliminating that long-run buffered-output deadlock class.

The final target run completed autonomously with `TEST_EXIT_CODE=0`.

## Final real target-laptop acceptance — PASSED

The production-like six-case same-session test passed on target Windows using HEAD `956ca9e7d4b23c4af3b0f51c50f2450f4066abba`, with user Chrome intentionally left open.

Exact case evidence:

```text
labeled-primary-button:
  expected = HIT
  prepare = promoted-text-inventory
  commit = visual-click-committed
  marker = CLICKED:send-primary
  classification = hit

icon-only-control:
  expected = HIT
  prepare = promoted-icon-consistent
  commit = visual-click-committed
  marker = CLICKED:search-icon
  classification = hit

repeated-row-action:
  expected = ABSTAIN
  reason = target-class-not-promoted:repeated-similar-control
  classification = correct_abstain

tiny-indicator:
  expected = ABSTAIN
  reason = target-class-not-promoted:tiny-target
  classification = correct_abstain

state-disambiguation:
  expected = HIT
  prepare = promoted-text-inventory
  commit = visual-click-committed
  marker = CLICKED:send-primary
  classification = hit

absent-target:
  expected = ABSTAIN
  reason = target-declared-absent
  classification = correct_abstain
```

Summary:

```text
expected_hits = 3
hits = 3
expected_abstains = 3
correct_abstains = 3
safe_misses = 0
false_clicks = 0
errors = 0
safety_pass = true
acceptance_pass = true
```

Resource/lifecycle evidence:

```text
Doctor physical_free_gb = 2.704
Doctor virtual_free_gb = 9.207
minimum observed free physical RAM = 1.2 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
CHROME_RUNNING_AFTER wrapper cleanup = true
TEST_EXIT_CODE = 0
STAGE25_1_RESULT = PASSED
```

The reviewed 1.50 GB cold-start threshold did not need weakening.

Do **not** describe this as "6/6 visual accuracy". It is a six-case safety/behavior acceptance gate. The accepted Stage 25 present-target baseline remains 3/5 because repeated-row and tiny target classes are intentionally not promoted.

## Credential boundary — PROVED

Review of exact `openai/tunnel-client v0.0.11` showed its semantic stdio child inherits the tunnel-client environment.

The accepted fix is:

```text
tunnel-client
  -> semantic-projection-launcher.mjs
       -> delete CONTROL_PLANE_API_KEY / OPENAI_API_KEY
       -> import semantic-projection.mjs
```

A Windows sentinel regression proves scrub occurs before semantic core load.

## Dependency reproducibility — NODE PATH PROVED

Semantic projection has a committed npm lockfile and product/runtime/acceptance paths use `npm ci`.

Vision Python remains intentionally small (`Pillow==12.3.0`) but release-grade Python artifact/hash reproducibility is pending.

The locked semantic graph currently emits a deprecation warning for transitive `glob@10.5.0`. Track it as a dedicated post-Stage-25.1 dependency follow-up rather than changing the graph inside this accepted foundation.

## Browser network boundary

`web_open` preserves reviewed local loopback workflows while reducing unintended private-network reachability:

- allow `localhost`, `*.localhost`, IPv4 127/8 and IPv6 `::1`;
- reject direct RFC1918, link-local/metadata, CGNAT and other explicit non-public/special IP destinations before `browser_navigate`;
- reject direct `metadata.google.internal`;
- use Playwright `blocked-origins` for metadata endpoints only as defense-in-depth.

Do **not** describe this as a complete network sandbox. DNS hostname resolution/rebinding and redirect policy remain residual work if stronger isolation is required.

## Required eventual product flow

```text
ordinary ChatGPT
  -> existing semantic browser operation
  -> semantic DOM/accessibility grounding first
       -> resolved: act semantically
       -> unavailable/ambiguous:
            SAME Playwright page/session
            -> CSS-pixel capture
            -> focused runtime owner Start/Status
            -> local production visual grounder
            -> deterministic authorization
            -> freshness proof
            -> resolved action OR ABSTAIN
```

Vision remains an internal grounding strategy, not a planner and not a sixth public Chat tool.

## Deliberately not part of this PR

- no automatic local-vision fallback wired into public `web_observe` / `web_interact`;
- no public generic VLM/inference tool;
- no generic planner/runtime gateway;
- no promotion of repeated-row/tiny classes;
- no claim of complete DNS/redirect sandboxing;
- no release-grade Python packaging or stable release.

## Completion gate

The Stage 25.1 **foundation** completion gate is satisfied:

- real local F16 VLM uses the proved same-session boundary and remains fail-closed;
- stale/uncertain results cannot mutate the page;
- runtime admission/lifecycle leaves no stale owned process;
- repeated/tiny classes remain blocked;
- security/dependency regressions remain explicit and green;
- target Windows acceptance passes with realistic Chrome usage;
- public semantic contract remains exactly five tools;
- authoritative documentation records the accepted evidence.

The next development work should be a separate follow-up for the ordinary-Chat semantic miss/ambiguity escalation policy rather than expanding this already-proved foundation PR.

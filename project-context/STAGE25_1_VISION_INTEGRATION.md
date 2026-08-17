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

Target result with Chrome running:

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

## Same-session bridge — PROVED

The internal `SameSessionVisualGroundingBridge` uses the pinned `@playwright/mcp@0.0.78` vision capability in one MCP client/session:

```text
browser_take_screenshot(type=png, fullPage=false, scale=css)
  -> bounded grounder
  -> one-shot opaque visual-target token
  -> re-capture same CSS viewport
  -> exact dimensions + SHA256 freshness check
  -> browser_mouse_click_xy only when unchanged
```

Windows acceptance proves intended coordinate action, replay protection, layout/scroll/overlay/navigation stale ABSTAIN, missing/ambiguous grounder ABSTAIN and zero action on uncertain evidence. Exact five public semantic tools remain unchanged.

The full-screenshot freshness policy is intentionally strict. Over-abstention is preferable to stale-coordinate mutation until a narrower deterministic freshness proof is measured.

## Focused vision runtime owner — PROVED SYNTHETICALLY

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

Production defaults are fixed by `config/local-vision-runtime.json`: reviewed profile `lfm25-vl-450m-f16`, host `127.0.0.1`, port `3068`, reviewed llama.cpp build markers and exact model/mmproj hashes. Arbitrary runtime/model overrides are test-only.

Windows CI proves idempotent Start, Touch/TTL, explicit Stop, tampered artifact rejection, foreign listener rejection and ownership mismatch refusal. Real target-laptop F16 lifecycle remains part of the final end-to-end gate.

## Production grounding policy — PROVED FOR CURRENT PROMOTED CLASSES

The benchmark row is not itself authorization. `production_policy.py` applies class-aware rules:

- labeled button / visual state: unique target-blind text inventory + unique refinement;
- icon-only: unique pass1 + unique pass2 + positive pass consistency;
- repeated similar controls: forced ABSTAIN;
- tiny targets: forced ABSTAIN;
- absent/unreviewed/ambiguous/error: no action.

Do not replace this with one global IoU threshold; accepted target evidence includes valid text refinement with very low overlap.

## Model-neutral production grounder boundary — IMPLEMENTED, UNIT-PROVED

`runtime/local_vision_adapter/production_grounder.py` accepts one PNG capture plus bounded `instruction`, `kind` and optional `target_text`, runs the accepted native-bbox implementation, then applies production authorization.

It intentionally does **not**:

- start/stop llama.cpp;
- select/download a model;
- accept arbitrary inference endpoints;
- inspect browser/page state;
- perform a browser action;
- return raw model responses through production diagnostics.

Only an authorized result contains a point/bbox. Repeated-row, absent, parse-failure and invalid-image unit cases remain non-authorizing.

## Credential boundary — PROVED

Review of exact `openai/tunnel-client v0.0.11` showed its semantic stdio child inherits the tunnel-client environment. Therefore the prior assumption that `CONTROL_PLANE_API_KEY` might be stripped upstream was false.

The accepted fix is a reviewed launcher:

```text
tunnel-client
  -> semantic-projection-launcher.mjs
       -> delete CONTROL_PLANE_API_KEY / OPENAI_API_KEY
       -> import semantic-projection.mjs
```

A Windows sentinel regression proves scrub occurs before semantic core load. Downstream MCP SDK stdio children keep their own restricted environment behavior.

## Dependency reproducibility — NODE PATH PROVED

Semantic projection has a committed npm lockfile generated from the exact manifest and verified immediately with `npm ci`.

Current rules:

- product helper validates manifest/lock pins;
- dependencies absent + lockfile absent -> fail closed;
- installation uses `npm ci --ignore-scripts --no-audit --no-fund`;
- semantic/direct/security/vision-bridge acceptance uses `npm ci`;
- standalone installed-layout includes package.json, package-lock.json, secure launcher and core and also uses `npm ci`.

Vision Python remains intentionally small (`Pillow==12.3.0`) but release-grade Python artifact/hash reproducibility is still pending.

## Browser network boundary

`web_open` preserves reviewed local loopback workflows while reducing unintended private-network reachability:

- allow `localhost`, `*.localhost`, IPv4 127/8 and IPv6 `::1`;
- reject direct RFC1918, link-local/metadata, CGNAT and other explicit non-public/special IP destinations before `browser_navigate`;
- reject direct `metadata.google.internal`;
- use Playwright `blocked-origins` for metadata endpoints only as defense-in-depth.

Do **not** describe this as a complete network sandbox. The pinned Playwright MCP documentation explicitly says origin filters are not a security boundary and do not cover redirects. DNS hostname resolution/rebinding and redirect policy therefore remain residual work if stronger network isolation is required.

## Required production flow

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

Vision remains an internal grounding strategy, not a planner and not automatically a sixth public Chat tool.

## Next implementation sequence

1. add an internal runtime-backed grounder runner that invokes the focused owner and the production grounder without accepting arbitrary endpoint/model choices;
2. connect that runner to `SameSessionVisualGroundingBridge` behind tests, still without automatic public fallback;
3. prove fake/deterministic runtime plumbing and no-action failure modes in CI;
4. run real F16 capture -> grounding -> authorization -> freshness -> action/ABSTAIN on target Windows with Chrome open;
5. only after that decide the exact semantic miss/ambiguity escalation policy for ordinary Chat.

## Completion gate

Stage 25.1 is complete only when:

- real local F16 VLM uses the proved same-session boundary and remains fail-closed;
- stale/uncertain results cannot mutate the page;
- runtime admission/lifecycle leaves no stale process;
- repeated/tiny classes remain blocked unless separately promoted by evidence;
- security/dependency regressions remain explicit and green;
- target Windows acceptance passes with realistic Chrome usage;
- public semantic contract remains truthful and small;
- authoritative documentation matches merged implementation.

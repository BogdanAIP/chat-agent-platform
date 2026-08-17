# Stage 25.1 — Same-session visual fallback integration

Status: **TARGET ACCEPTANCE PASSED AFTER PRE-MERGE REVIEW — FOUNDATION READY FOR MERGE**

Branch: `chat/stage25-1-vision-integration-foundation`

Base: `acc6334ef0114d3ca6b6a243d904605cd00a321a` (`main` after PR #73).

Final reviewed target HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

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

Prepared targets are now also bounded operationally: expired entries are purged, outstanding targets are capped at 256, capacity overflow fails closed, and expired tokens cannot mutate the page.

The full-screenshot freshness policy is intentionally strict. The final screenshot and coordinate click are still separate MCP calls, so a narrow post-check TOCTOU window remains a documented residual risk.

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

Pre-merge review added a fail-closed listener-ownership guard: before screenshot inference the runner verifies through Windows TCP state that `127.0.0.1:3068` belongs to the exact PID returned by the controller. A wrong listener PID prevents Python inference. Loopback TCP is not cryptographic process authentication, so a theoretical same-user port-reuse race after the check remains residual.

Windows CI proves idempotent Start, Touch/TTL, explicit Stop, tampered artifact rejection, foreign listener rejection, ownership mismatch refusal and the PID-bound listener regression.

## RAM admission calibration — REVIEWED ON TARGET

The original production cold-start floor was `1.50 GB`. A post-review target run on HEAD `49f1a9a7d3a4f90202b535693917829bef773f72` failed closed before llama.cpp inference because Playwright-active free physical RAM fluctuated between `1.446` and `1.486 GB` while virtual RAM remained about `7.7 GB`:

```text
errors = 6
false_clicks = 0
safety_pass = true
acceptance_pass = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
```

This established that the 1.50 GB pre-start gate was too brittle for the reviewed browser-active workload. The production start floor was therefore calibrated to `1.35 GB` while keeping downstream safety floors unchanged:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target-wrapper emergency cutoff = 0.30 GB
```

The final reviewed target run then passed with a minimum observed free physical RAM of `0.60 GB`, above the `0.50 GB` runtime pressure floor and above the `0.30 GB` emergency cutoff. `SAFETY_STOP` remained false.

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

It intentionally does **not** start/stop llama.cpp, select/download a model, accept arbitrary inference endpoints, inspect browser/page state, perform a browser action, or expose raw model responses through production diagnostics.

Only an authorized result contains a point/bbox. Repeated-row, absent, parse-failure and invalid-image cases remain non-authorizing.

## Runtime-backed runner — PROVED

The Node runtime-backed grounder is fixed to the reviewed profile and port and delegates lifecycle to the focused PowerShell owner.

Real target testing exposed two Windows integration defects, both closed before final acceptance:

1. **cold Start descendant-stdio settlement** — controller actions now settle on the controller process `exit` after a bounded drain instead of waiting for descendant-held stdio until a 150 s timeout. Regression marker: `RUNTIME_BACKED_VISUAL_GROUNDER_DESCENDANT_STDIO=PASS`.
2. **target wrapper output buffering** — the wrapper now inherits Node stdout/stderr directly instead of redirecting and draining only after exit.

The final reviewed target run completed autonomously with `TEST_EXIT_CODE=0`.

## Installed semantic runtime / reproducibility — REVIEWED

Pre-merge review found that the bootstrap installed-layout contract lagged the secure source-tree contract. It now installs and validates:

```text
package.json
package-lock.json
semantic-projection-launcher.mjs
semantic-projection.mjs
```

Installed-layout validation checks exact dependency pins and scrub-before-import ordering. Semantic dependency installation records the SHA256 of the applied `package-lock.json` and re-runs `npm ci` when that lock changes or the marker is absent.

The secure launcher deletes `CONTROL_PLANE_API_KEY` and `OPENAI_API_KEY` before semantic core import. Windows acceptance proves the standalone installed layout uses the same contract.

Vision Python remains intentionally small (`Pillow==12.3.0`) but release-grade Python artifact/hash reproducibility is pending. The locked semantic graph still contains deprecated transitive `glob@10.5.0`; keep that as a dedicated post-Stage-25.1 dependency follow-up.

## Final real target-laptop acceptance — PASSED

The production-like six-case same-session test passed on target Windows using reviewed HEAD `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`, with user Chrome intentionally left open.

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
Doctor physical_free_gb = 1.919
Doctor virtual_free_gb = 8.335
minimum observed free physical RAM = 0.60 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
CHROME_RUNNING_AFTER wrapper cleanup = true
TEST_EXIT_CODE = 0
STAGE25_1_REVIEW_RESULT = PASSED
```

Do **not** describe this as "6/6 visual accuracy". It is a six-case safety/behavior acceptance gate. The accepted Stage 25 present-target baseline remains 3/5 because repeated-row and tiny target classes are intentionally not promoted.

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

The Stage 25.1 **foundation** completion gate is satisfied on the reviewed code:

- real local F16 VLM uses the proved same-session boundary and remains fail-closed;
- stale/uncertain results cannot mutate the page;
- runtime admission/lifecycle leaves no stale owned process;
- listener ownership is PID-bound before inference;
- prepared visual targets are TTL/cap bounded;
- installed semantic runtime matches the secure locked source contract;
- repeated/tiny classes remain blocked;
- complete CI/security matrix is green on the reviewed code;
- target Windows acceptance passes with realistic Chrome usage and calibrated RAM admission;
- public semantic contract remains exactly five tools.

The next development work should be a separate follow-up for the ordinary-Chat semantic miss/ambiguity escalation policy rather than expanding this already-proved foundation PR.

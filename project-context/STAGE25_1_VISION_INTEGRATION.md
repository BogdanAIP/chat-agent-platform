# Stage 25.1 — Same-session visual fallback integration

Status: **MERGED AND ACCEPTED**

PR #74 `Stage 25.1: same-session vision fallback foundation` was squash-merged to `main` as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Final reviewed target production-code HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

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

Pinned `@playwright/mcp@0.0.78` is used in one MCP client/session:

```text
browser_take_screenshot(type=png, fullPage=false, scale=css)
  -> bounded grounder
  -> one-shot opaque visual-target token
  -> re-capture same CSS viewport
  -> exact dimensions + SHA256 freshness check
  -> browser_mouse_click_xy only when unchanged
```

Replay, layout/scroll/overlay/navigation stale state, missing/ambiguous grounding and expired tokens produce zero coordinate action. Prepared targets are TTL-purged and capped at 256; capacity overflow fails closed.

Residual: freshness screenshot and coordinate click remain separate MCP calls, so a narrow post-check TOCTOU window remains.

## Focused vision runtime owner — PROVED

`scripts/local-vision-runtime.ps1` owns only lifecycle/resource admission. Production defaults are fixed by `config/local-vision-runtime.json`: profile `lfm25-vl-450m-f16`, host `127.0.0.1`, port `3068`, reviewed llama.cpp markers and exact model/mmproj hashes.

Production inference additionally verifies through Windows TCP state that `127.0.0.1:3068` belongs to the exact controller-returned runtime PID before sending a screenshot. Wrong PID fails closed before Python inference.

Residual: PID-bound loopback is not cryptographic endpoint authentication; a theoretical same-user post-check port-reuse race remains.

## RAM admission calibration — ACCEPTED

The original production start floor `1.50 GB` was proven too brittle on the real browser-active target workload. A post-review run failed closed before llama.cpp inference with Playwright-active free physical RAM `1.446–1.486 GB`, while virtual RAM remained about `7.7 GB`; false clicks remained zero and Chrome/runtime cleanup remained correct.

Accepted policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target-wrapper emergency cutoff = 0.30 GB
```

The final target run passed with minimum observed free physical RAM `0.60 GB`, above both the runtime pressure floor and emergency cutoff, with `SAFETY_STOP=false`.

## Production grounding policy — PROVED FOR CURRENT PROMOTED CLASSES

- labeled button / visual state: unique target-blind text inventory + unique refinement;
- icon-only: unique pass1 + unique pass2 + positive pass consistency;
- repeated similar controls: forced ABSTAIN;
- tiny targets: forced ABSTAIN;
- absent/unreviewed/ambiguous/error: no action.

The benchmark row is not authorization. Do not replace the class-aware policy with one global IoU threshold.

## Runtime-backed runner — PROVED

The Node runner is fixed to the reviewed profile/port and delegates lifecycle to the focused PowerShell owner.

Target testing exposed and closed:

- cold Start descendant-stdio settlement;
- target wrapper stdout/stderr buffering;
- PID-unbound listener health;
- overly brittle 1.50 GB pre-start RAM gate.

The final target run completed autonomously with `TEST_EXIT_CODE=0`.

## Installed semantic runtime / reproducibility — PROVED FOR NODE PATH

Bootstrap installs and validates the same semantic contract as source:

```text
package.json
package-lock.json
semantic-projection-launcher.mjs
semantic-projection.mjs
```

The launcher deletes `CONTROL_PLANE_API_KEY` and `OPENAI_API_KEY` before semantic core import. Applied lockfile SHA256 is recorded and a changed/missing marker forces `npm ci`.

Vision Python remains exactly pinned to `Pillow==12.3.0`, but release-grade Python artifact/hash policy remains pending. Deprecated transitive `glob@10.5.0` remains a separate dependency follow-up.

## Final real target-laptop acceptance — PASSED

Target Windows, reviewed production-code HEAD `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`, user Chrome intentionally open:

```text
labeled-primary-button = HIT / CLICKED:send-primary
icon-only-control = HIT / CLICKED:search-icon
repeated-row-action = correct ABSTAIN
tiny-indicator = correct ABSTAIN
state-disambiguation = HIT / CLICKED:send-primary
absent-target = correct ABSTAIN

expected_hits = 3
hits = 3
expected_abstains = 3
correct_abstains = 3
safe_misses = 0
false_clicks = 0
errors = 0
safety_pass = true
acceptance_pass = true

Doctor physical_free_gb = 1.919
Doctor virtual_free_gb = 8.335
minimum observed free physical RAM = 0.60 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
STAGE25_1_REVIEW_RESULT = PASSED
```

Do **not** describe this as "6/6 visual accuracy". It is a six-case safety/behavior acceptance gate. The accepted Stage 25 present-target baseline remains 3/5 because repeated-row and tiny target classes are intentionally not promoted.

## Browser network boundary

Direct RFC1918, link-local/metadata, CGNAT and other explicit non-public/special IP destinations are rejected before navigation while intended loopback remains allowed. This is not a complete DNS/rebinding/redirect sandbox.

## Deliberately not part of Stage 25.1

- no automatic local-vision fallback wired into public `web_observe` / `web_interact`;
- no public generic VLM/inference tool;
- no second planner or generic inference gateway;
- no promotion of repeated-row/tiny classes;
- no claim of complete DNS/redirect sandboxing;
- no release-grade Python packaging or stable release.

## Completion gate — SATISFIED

The reviewed production code passed the real target F16 gate, the final documentation descendant passed all 11 CI/security workflow families, and PR #74 was merged to `main` as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

## Next active work

Implement the ordinary-Chat semantic miss/ambiguity -> internal vision escalation policy in a separate PR while keeping the public contract at exactly five tools:

```text
semantic DOM/accessibility first
  -> resolved: act semantically
  -> unavailable/ambiguous:
       same-session screenshot
       -> reviewed local F16 grounder
       -> deterministic authorization
       -> freshness proof
       -> coordinate action OR ABSTAIN
```

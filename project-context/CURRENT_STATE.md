# Current State

## Accepted foundation

Stage 24 accepted exactly five public semantic tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Stage 24.1 selected the normal path:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused backends/adapters
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. ChatGPT remains the only planner/intelligence.

## Stage 25 grounding benchmark — ACCEPTED

PR #73 was squash-merged to `main` as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Target-laptop baseline:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
```

Final Stage 25 evidence with Chrome running:

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

This remains the accepted perception baseline. Do not call it 6/6 accuracy; the six-case gate is a safety/behavior result while the present-target baseline is 3/5.

## Stage 25.1 — MERGED AND ACCEPTED

PR #74 `Stage 25.1: same-session vision fallback foundation` was squash-merged to `main` as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Final reviewed target production-code HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

The full same-session F16 acceptance passed on the target Windows laptop with the user's normal Chrome workload intentionally left open:

```text
labeled Send = HIT
Search icon = HIT
state-disambiguated Send = HIT
Gamma repeated-row = correct ABSTAIN
tiny indicator = correct ABSTAIN
absent target = correct ABSTAIN

expected_hits = 3
hits = 3
expected_abstains = 3
correct_abstains = 3
safe_misses = 0
false_clicks = 0
errors = 0
safety_pass = true
acceptance_pass = true

Doctor physical free RAM = 1.919 GB
Doctor virtual free RAM = 8.335 GB
minimum observed free physical RAM = 0.60 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
STAGE25_1_REVIEW_RESULT = PASSED
```

Do not describe this as 6/6 visual accuracy. The accepted Stage 25 present-target baseline remains 3/5 because repeated-row/tiny are deliberately unpromoted.

### Reviewed RAM policy

A post-review run proved the original `1.50 GB` cold-start floor too brittle after Playwright load at `1.446–1.486 GB` free physical RAM. Production policy is now:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

The final accepted run reached a minimum of `0.60 GB`, above the runtime pressure floor and emergency cutoff, with no safety stop.

### Pre-merge review findings — CLOSED

- production inference verifies the `127.0.0.1:3068` listener belongs to the controller-returned PID before sending a screenshot;
- prepared visual tokens are TTL-purged, capped at 256 and fail closed on expiry/capacity;
- bootstrap installed semantic layout now matches source: `package.json`, `package-lock.json`, secure launcher and core;
- applied lockfile SHA256 is recorded and a changed/missing marker forces `npm ci`;
- Chrome non-termination regression assertion was corrected;
- Windows descendant-stdio and target wrapper output-buffering defects are closed;
- authoritative docs and PR review record residual risks rather than claiming stronger isolation than proved.

### Proven Stage 25.1 foundations

- same-session Playwright screenshot/freshness/coordinate-action boundary;
- fail-closed stale/replay/layout/scroll/overlay/navigation behavior;
- focused llama.cpp lifecycle owner with exact artifact/process identity;
- PID-bound loopback listener verification before inference;
- class-aware production policy with repeated-row/tiny forced ABSTAIN;
- runtime-backed fixed-profile F16 grounder;
- Windows junction containment;
- tunnel credential scrub before semantic core import;
- reproducible locked Node dependency path with `npm ci` and lock-hash marker;
- bounded direct browser literal-IP network policy;
- CodeQL Actions + JavaScript/TypeScript + Python;
- real target cleanup with runtime stopped and Chrome alive.

All 11 workflow families were green on the final PR head before merge.

## What Stage 25.1 deliberately does not do

- no automatic local-vision fallback is wired into public `web_observe` / `web_interact` yet;
- no sixth public vision/VLM tool exists;
- no generic inference gateway or second planner exists;
- repeated-row and tiny target classes remain non-promoted;
- current browser URL filtering is not claimed as a complete DNS/redirect sandbox;
- PID-bound loopback is not cryptographic endpoint authentication;
- Python vision packaging is not yet release-grade;
- no stable release is declared.

## Next active priority

Implement the ordinary-Chat semantic miss/ambiguity -> internal vision escalation policy as a separate follow-up while keeping the public five-tool contract unchanged:

```text
ordinary ChatGPT
  -> semantic DOM/accessibility grounding first
       -> resolved: act semantically
       -> unavailable/ambiguous:
            SAME Playwright page/session
            -> CSS-pixel capture
            -> focused runtime owner
            -> local production visual grounder
            -> deterministic authorization
            -> freshness proof
            -> coordinate action OR ABSTAIN
```

## Remaining important work

- define exactly which semantic misses/ambiguities are eligible for internal vision escalation;
- keep repeated-row/tiny fail-closed until separately improved and measured;
- decide whether stronger backend-level DNS/redirect/private-network isolation is required;
- make Python vision dependencies release-grade reproducible beyond `Pillow==12.3.0`;
- investigate deprecated transitive `glob@10.5.0` in a separate dependency PR;
- update stale repository metadata when a repository-description write path is available;
- no stable product release yet.

## Active rules

- ChatGPT is the only planner/intelligence;
- semantic DOM/accessibility grounding comes first;
- vision may ABSTAIN and never acts by itself;
- stale or uncertain visual evidence causes zero page mutation;
- public semantic surface stays small and truthful;
- heavy local vision starts only when admitted/needed and unloads deterministically;
- documentation changes together with accepted implementation evidence.

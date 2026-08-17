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
  -> direct stdio semantic-projection
  -> focused backends/adapters
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

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

## Stage 25.1 — TARGET GATE PASSED; PR FOUNDATION READY FOR FINAL REVIEW

Branch: `chat/stage25-1-vision-integration-foundation`

PR: #74 — `Stage 25.1: same-session vision fallback foundation`.

The real target-laptop same-session F16 acceptance passed on HEAD `956ca9e7d4b23c4af3b0f51c50f2450f4066abba` with the user's normal Chrome workload intentionally left open.

Exact final target evidence:

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

Doctor physical free RAM = 2.704 GB
Doctor virtual free RAM = 9.207 GB
minimum observed free physical RAM = 1.2 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
STAGE25_1_RESULT = PASSED
```

The final run completed autonomously. It did not require manual termination and it did not weaken the reviewed 1.50 GB cold-start admission threshold.

### PROVED foundations on PR #74

1. **Same-session visual action boundary**
   - one pinned Playwright MCP 0.0.78 client/session;
   - CSS screenshot -> one-shot visual token -> fresh re-capture -> exact dimensions/SHA256 -> coordinate action or ABSTAIN;
   - replay, layout shift, scroll, overlay, navigation replacement, missing and ambiguous targets produce no coordinate action;
   - exact five public tools remain unchanged.

2. **Focused local-vision lifecycle owner**
   - approved llama.cpp/model/mmproj identity;
   - physical/virtual memory admission;
   - loopback-only start/health;
   - PID + executable + full command SHA256 + UTC process-creation ticks ownership;
   - Touch, TTL unload, Stop and Sweep;
   - tampered artifacts, foreign listeners and ownership mismatch fail closed;
   - no Chrome/unrelated-process termination;
   - real F16 target cleanup is proved.

3. **Class-aware production authorization policy**
   - inventory-backed text and reviewed icon/state classes resolve only under their measured guards;
   - repeated-row and tiny targets remain forced ABSTAIN until separately promoted;
   - no global high-IoU rule.

4. **Runtime-backed production grounder**
   - fixed reviewed profile `lfm25-vl-450m-f16` and loopback port 3068;
   - Node cannot select arbitrary model paths/endpoints;
   - reviewed Python production grounder executes the bounded request;
   - Touch occurs even on failure;
   - provider/contract failures cannot authorize a click;
   - Windows descendant-stdio regression closes the real cold-Start timeout defect.

5. **Windows workspace containment**
   - real junction read/write escape attempts are blocked;
   - normal in-root access remains functional.

6. **Tunnel credential containment**
   - exact `openai/tunnel-client v0.0.11` inherits its parent environment into the semantic stdio child;
   - a reviewed semantic launcher deletes `CONTROL_PLANE_API_KEY` and `OPENAI_API_KEY` before importing semantic core;
   - Windows sentinel regression proves scrub-before-core-load.

7. **Reproducible semantic Node dependencies**
   - committed npm lockfile;
   - product/runtime/acceptance paths use `npm ci`;
   - unlocked installation is refused when dependencies are absent.

8. **Bounded direct browser network scope**
   - loopback remains allowed;
   - direct RFC1918/link-local/metadata/CGNAT/reserved non-public IP destinations are rejected before navigation;
   - DNS resolution/rebinding and redirects remain a documented residual risk.

9. **GitHub security automation**
   - CodeQL: Actions + JavaScript/TypeScript + Python;
   - Dependabot: Actions + semantic npm + Python requirements;
   - reachable Git history remains Gitleaks-scanned.

## What Stage 25.1 deliberately does not do

- no automatic local-vision fallback is wired into public `web_observe` / `web_interact` yet;
- no sixth public vision/VLM tool exists;
- no generic inference gateway or second planner exists;
- repeated-row and tiny target classes remain non-promoted;
- current browser URL filtering is not claimed as a complete DNS/redirect sandbox;
- Python vision packaging is not yet release-grade;
- no stable release is declared.

## Next active priority

Merge the coherent Stage 25.1 foundation after final documentation/CI review, then implement the ordinary-Chat semantic miss/ambiguity escalation policy as a separate follow-up rather than expanding the already-proved foundation PR.

The intended next flow remains:

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

- design and prove the public semantic miss/ambiguity escalation policy without changing the five-tool contract;
- keep repeated-row/tiny fail-closed until separately improved and measured;
- decide whether stronger backend-level DNS/redirect/private-network isolation is required;
- make Python vision dependencies release-grade reproducible beyond the exact `Pillow==12.3.0` pin;
- investigate deprecated transitive `glob@10.5.0` in a separate dependency PR after Stage 25.1;
- update stale repository metadata when a repository-metadata write path is available;
- no stable product release yet.

## Active rules

- ChatGPT is the only planner/intelligence;
- semantic DOM/accessibility grounding comes first;
- vision may ABSTAIN and never acts by itself;
- stale or uncertain visual evidence causes zero page mutation;
- public semantic surface stays small and truthful;
- heavy local vision starts only when admitted/needed and unloads deterministically;
- documentation changes together with accepted implementation evidence.

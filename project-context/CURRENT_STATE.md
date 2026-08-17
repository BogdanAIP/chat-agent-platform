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

Final evidence with Chrome running:

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

This is a safe fallback baseline, not a finished browser controller.

## Stage 25.1 — ACTIVE

Branch: `chat/stage25-1-vision-integration-foundation`

Draft PR: #74 — `Stage 25.1: same-session vision fallback foundation`.

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
   - no Chrome/unrelated-process termination.

3. **Class-aware production authorization policy**
   - inventory-backed text and reviewed icon/state classes can resolve only under their measured guards;
   - repeated-row and tiny targets remain forced ABSTAIN until separately promoted;
   - no global high-IoU rule.

4. **Windows workspace containment**
   - real junction read/write escape attempts are blocked;
   - normal in-root access remains functional.

5. **Tunnel credential containment**
   - exact `openai/tunnel-client v0.0.11` inherits its parent environment into the semantic stdio child;
   - a reviewed semantic launcher now deletes `CONTROL_PLANE_API_KEY` and `OPENAI_API_KEY` before importing semantic core;
   - Windows regression injects a sentinel and proves scrub-before-core-load;
   - downstream MCP SDK stdio children retain their own safe environment filtering.

6. **Reproducible semantic Node dependencies**
   - committed npm lockfile generated from the exact manifest and immediately verified with `npm ci`;
   - product runtime refuses unlocked installation when dependencies are absent;
   - semantic/direct/security/vision-bridge acceptance installs with `npm ci`;
   - standalone installed-layout copies the lockfile and secure launcher and also uses `npm ci`.

7. **Bounded direct browser network scope**
   - loopback (`localhost`, 127/8, `::1`) remains allowed for reviewed local workflows;
   - direct RFC1918/link-local/metadata/CGNAT/reserved non-public IP destinations are rejected before `browser_navigate`;
   - Playwright `blocked-origins` is used only as defense-in-depth for metadata endpoints, not as a claimed security boundary;
   - DNS resolution and redirects remain a documented residual risk because upstream Playwright MCP explicitly does not make origin filters a redirect security boundary.

8. **Broader GitHub security automation**
   - CodeQL: Actions + JavaScript/TypeScript + Python;
   - Dependabot: Actions + semantic npm + Python requirements;
   - complete reachable Git history remains Gitleaks-scanned.

### Production visual grounder boundary — IMPLEMENTED, UNIT-PROVED

`runtime/local_vision_adapter/production_grounder.py` now converts one PNG capture plus bounded target metadata into a model-neutral bridge result using the accepted native-bbox adapter and deterministic production policy.

It does **not** start llama.cpp, choose models, inspect Playwright state or click. It returns only `resolved`/`abstain`; provider/contract failures are non-authorizing errors. Raw model responses are not included in production diagnostics.

CI proves text resolution, forced repeated-row ABSTAIN, absent inventory one-request abstention, provider parse failure fail-closed and non-PNG rejection.

## Next active priority

Connect the proved pieces without changing the five public Chat tools:

```text
same Playwright session PNG
  -> focused runtime owner Start/Status
  -> production visual grounder against reviewed loopback llama.cpp
  -> production authorization
  -> same-session freshness bridge
  -> coordinate action OR ABSTAIN
```

First prove this with deterministic/fake runtime plumbing in CI, then run the real F16 chain on the target Windows laptop with Chrome open.

## Remaining important work

- real runtime-backed grounder runner and controlled semantic escalation;
- real F16 same-session target-laptop acceptance;
- keep repeated-row/tiny fail-closed until separately improved and measured;
- decide whether stronger backend-level DNS/redirect/private-network isolation is required; do not claim current direct-input policy is a full network sandbox;
- make Python vision dependencies release-grade reproducible beyond the current exact `Pillow==12.3.0` pin;
- update repository metadata that still describes the removed Rust-first core when a repository-metadata write path is available;
- no stable product release yet.

## Active rules

- ChatGPT is the only planner/intelligence;
- semantic DOM/accessibility grounding comes first;
- vision may ABSTAIN and never acts by itself;
- stale or uncertain visual evidence causes zero page mutation;
- public semantic surface stays small and truthful;
- heavy local vision starts only when admitted/needed and unloads deterministically;
- documentation changes together with accepted implementation evidence.

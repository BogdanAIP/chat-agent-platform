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

Accepted target baseline:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
present-target hits = 3/5
false clicks = 0
```

Repeated-row and tiny target classes remain deliberately unpromoted. Do not describe the six-case Stage 25 safety gate as 6/6 visual accuracy.

## Stage 25.1 — MERGED AND ACCEPTED

PR #74 was squash-merged to `main` as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94`.

Final reviewed target production-code HEAD: `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`.

Accepted foundations:

- same-session Playwright screenshot -> prepared target -> exact freshness -> coordinate action or ABSTAIN;
- stale/replay/layout/scroll/overlay/navigation uncertainty fails closed;
- prepared visual targets are TTL-purged and capped at 256;
- focused llama.cpp lifecycle owner with exact artifact/process ownership and deterministic unload;
- production inference verifies the `127.0.0.1:3068` listener belongs to the controller-returned PID;
- class-aware visual verifier;
- secure installed semantic runtime and lock-hash-enforced `npm ci`;
- junction containment, credential scrub, bounded literal-IP browser policy and CodeQL coverage.

Reviewed RAM policy:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

## Stage 25.2 — FINAL REVIEWED CODE ACCEPTED FOR MERGE

PR #77 `Stage 25.2: semantic-first internal vision escalation` wires the already accepted Stage 25.1 visual foundation into public `web_interact` while keeping exactly five public tools.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

### Accepted routing contract

For `web_interact(operation=click)` with bounded `visualFallback` intent:

```text
fresh accessibility snapshot
  -> exact enabled button -> semantic click; VLM stays stopped
  -> duplicate same-name buttons with exactly one enabled and disabled alternatives
       -> semantic click; VLM stays stopped
  -> disabled exact target -> ABSTAIN; VLM stays stopped
  -> exact target of an unpromoted semantic role -> ABSTAIN; VLM stays stopped
  -> unresolved semantic ambiguity -> ABSTAIN; VLM stays stopped
  -> zero exact candidates
       -> same Playwright page/session screenshot
       -> reviewed F16 text-labeled visual grounder
       -> deterministic authorization
       -> exact freshness
       -> one coordinate click OR ABSTAIN
```

Generic semantic click failures never trigger vision.

### Authorization hardening completed in review

Two merge-blocking findings were found after the first successful target run and fixed before the final accepted run:

1. A single exact accessibility candidate was previously clickable regardless of role/disabled state. It is now actionable only when it is an enabled `button`; disabled or non-button exact matches ABSTAIN without VLM.
2. Planner-supplied `target`/free-form `instruction` could conceptually influence visual refinement separately from `targetText`. The router now treats `targetText` as the sole visual anchor, ignores planner redirection for authorization and generates the canonical visual instruction locally from `targetText`.

Additional boundaries:

- no planner-supplied target `kind`;
- `semanticName`, when supplied for compatibility, must normalize exactly to `targetText`;
- no automatic icon-only, repeated-row or tiny-target promotion in Stage 25.2;
- semantic ambiguity does not invoke vision;
- safe ABSTAIN is returned as no-action rather than masquerading as a backend error;
- installed `%LOCALAPPDATA%`-style semantic bundle contains the reviewed vision dependency closure and does not require the git checkout at runtime.

### Final real target evidence

Target Windows laptop, normal user Chrome workload intentionally left open:

```text
HEAD = 41ef3f4032ae9169d940b3a04e5bdfe75170ca85
public_tools = 5
semantic-unique Save = semantic_hit
semantic-enabled-state Send = semantic_hit
semantic-ambiguity Delete = correct_abstain
semantic-miss Launch = visual_hit through real F16
semantic-miss absent Export CSV = correct_abstain

semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true

Doctor physical free RAM = 2.62 GB
Doctor virtual free RAM = 8.129 GB
minimum observed free physical RAM = 1.04 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
VISION_RUNTIME_STATE_AFTER_TEST = stopped
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
STAGE25_2_FINAL_REVIEW_RESULT = PASSED
```

Result path:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json`

All 9 workflow families triggered on this production-code HEAD completed successfully before documentation sync: CI, Semantic Projection Acceptance, Chat Profile Acceptance, Direct Semantic Tunnel Acceptance, Semantic Dependency Reproducibility, Stage 25.1 Vision Bridge Acceptance, Stage 25.1 Security Regressions, CodeQL Security and Secret History Scan.

## What Stage 25.2 deliberately does not claim

- repeated-row and tiny visual targets remain unpromoted;
- icon-only automatic semantic-miss promotion is not part of this first public escalation boundary;
- screenshot -> click is still a narrow non-atomic TOCTOU boundary;
- PID-bound loopback is not cryptographic endpoint authentication;
- browser DNS/rebinding/redirect isolation is incomplete;
- Python vision distribution is not release-grade;
- no stable end-user release is declared yet.

## Next active priority — Stage 26

Move from browser fixtures to representative real Windows/product workflows. Benchmark focused capabilities for Windows UI and professional applications such as Origin, REAPER, FFmpeg and Blender, preserving:

- ChatGPT as the only planner/intelligence;
- semantic/native application structure before vision where available;
- vision as bounded perception only;
- fail-closed authorization and no stale-coordinate mutation;
- a small stable Chat-facing surface rather than raw application tool explosion.

## Remaining product work

- real professional/Windows application acceptance;
- stronger network isolation decision for DNS/redirect/private-network behavior;
- release-grade Python/model artifact reproducibility;
- dependency cleanup for deprecated transitive `glob@10.5.0`;
- installer/update/repair/doctor/uninstall/key rotation/rollback/restart recovery;
- final clean-user end-to-end product acceptance;
- first stable release.

## Active rules

- ChatGPT is the only planner/intelligence;
- semantic/accessibility grounding comes first;
- local vision starts only on explicitly authorized semantic miss paths;
- vision may ABSTAIN and never acts by itself;
- stale or uncertain visual evidence causes zero page mutation;
- public semantic surface remains exactly five tools;
- heavy local vision starts only when admitted/needed and unloads deterministically;
- accepted implementation evidence and documentation move together.

# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## Current accepted integration line

The ordinary-Chat product path is:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

The public semantic surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. ChatGPT remains the only planner/intelligence.

## Accepted foundation through Stage 25.1

- Stage 24: five-tool semantic surface and Windows lifecycle accepted.
- Stage 24.1: direct semantic tunnel selected as normal path.
- Stage 25: LFM2.5-VL-450M F16 local grounding baseline accepted on the target laptop; present-target accuracy remains 3/5 because repeated-row/tiny are deliberately unpromoted.
- Stage 25.1: same-session screenshot -> visual grounding -> freshness -> coordinate action/ABSTAIN foundation accepted and merged in PR #74.

Stage 25.1 reviewed RAM policy remains:

```text
min_start_physical_gb = 1.35
min_start_virtual_gb = 3.0
min_run_physical_gb = 0.5
min_run_virtual_gb = 1.5
target emergency cutoff = 0.30 GB
```

Read `project-context/STAGE25_1_VISION_INTEGRATION.md` for the low-level same-session/freshness/lifecycle foundation.

## Stage 25.2 — semantic-first internal vision escalation

PR #77 implements the first public ordinary-Chat semantic→vision escalation inside the existing five-tool surface.

Final reviewed and target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

Routing contract:

```text
web_interact(click + bounded visualFallback)
  -> fresh accessibility snapshot
  -> exact enabled button
       -> semantic click; VLM stays stopped
  -> same-name buttons with exactly one enabled + disabled alternatives
       -> semantic click; VLM stays stopped
  -> disabled/non-button/ambiguous exact semantic evidence
       -> ABSTAIN; VLM stays stopped
  -> zero exact candidates
       -> SAME Playwright page/session screenshot
       -> reviewed local F16 labeled-button grounder
       -> deterministic authorization
       -> exact freshness proof
       -> one coordinate click OR ABSTAIN
```

Non-negotiable Stage 25.2 authorization:

- `targetText` is the semantic and visual anchor;
- planner-supplied `kind` is not accepted;
- planner `target` and free-form `instruction` cannot redirect the visual target;
- router builds a canonical visual instruction locally from `targetText`;
- semantic ambiguity and generic semantic click failures do not invoke vision;
- disabled/non-button exact matches ABSTAIN rather than being clicked or visually escalated;
- Stage 25.2 does not automatically promote icon-only, repeated-row or tiny-target classes;
- visual uncertainty/staleness always means ABSTAIN and zero page mutation.

Final real target acceptance with normal Chrome workload open:

```text
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

Result:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json`

All 9 workflow families triggered for the final Stage 25.2 production-code HEAD were green before docs synchronization.

## Current development priority — Stage 26

Do not reopen semantic→vision architecture without a concrete regression. The next work is product capability, not another abstract browser layer.

Priority:

1. benchmark representative real Windows UI workflows;
2. benchmark focused Origin and REAPER workflows first, then FFmpeg/Blender where useful;
3. keep semantic/native structure first and vision bounded/fail-closed;
4. define focused capabilities rather than exposing huge raw application tool surfaces;
5. measure real task success, false actions, recovery and resource behavior on the target machine.

After representative real-application acceptance, proceed to Stage 27 distribution/maintenance hardening: release artifacts, Python/model hashes, installer/update/repair/doctor/uninstall, key rotation, upgrade/rollback, restart recovery, thin lifecycle UI and a clean-user end-to-end acceptance.

## Product-ready boundary

Do not declare the project “ready to install and just use” until:

- Stage 25.2 is merged;
- representative real desktop/application workflows are accepted;
- normal installation no longer depends on a git checkout;
- restart/recovery and update/repair/uninstall are predictable;
- clean-user E2E passes from installation through Chat files/browser/vision/desktop action and restart;
- first stable release is cut.

## Residual risks that remain explicit

- repeated-row/tiny/icon-only automatic visual promotion is incomplete;
- screenshot and coordinate click are separate MCP calls, leaving a narrow TOCTOU window;
- PID-bound loopback is not cryptographic endpoint authentication;
- DNS/rebinding/redirect browser isolation is incomplete;
- Python/model packaging is not release-grade;
- deprecated transitive `glob@10.5.0` remains a dependency follow-up;
- professional applications are not product-accepted yet;
- no stable release exists yet.

## Non-negotiable product boundary

- ordinary ChatGPT remains the planner/intelligence;
- local models are bounded perception/extraction backends, never a second planner;
- prefer semantic/native structure over vision whenever deterministic structure exists;
- visual grounding must fail closed;
- keep the public tool surface small and truthful;
- do not expose raw prompts, arbitrary inference endpoints, arbitrary model administration, generic `tool_invoke`, or unrestricted local paths/remote images;
- preserve single-owner/fail-closed lifecycle guarantees;
- use the user only for irreducible target-machine or ordinary-Chat UI gates.

## Source-of-truth order

When documents disagree:

1. current code, tests and exact current CI/target evidence;
2. this file and `CURRENT_STATE.md`;
3. `ROADMAP.md` and `KNOWN_ISSUES.md`;
4. `ARCHITECTURE.md` and accepted ADRs;
5. `STAGE25_1_VISION_INTEGRATION.md` for same-session visual-foundation details;
6. historical Stage 25 research/handoff documents and older README revisions.

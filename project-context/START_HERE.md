# Start Here — authoritative continuation guide

Use this file as the first context document in a new ChatGPT or Codex session.

## Resolve live `main` first

Do not treat an embedded docs merge SHA as permanently current. Before creating a branch or changing code/docs, resolve live `main` from GitHub and use that exact SHA as the base.

Stable accepted milestones:

- Stage 25.2 runtime/code merge: `2a410476ef849fd6d9c172703a004b1befcbcfb1` — PR #77;
- Stage 26 architecture/context activation: `04dccfd30eb06a82899e2771f6d53ab4c8387128` — PR #78;
- Stage 26.1A target-tested qualification-code HEAD: `f8e8f606db845821b8fa24c09f9032015fb0e79e` — PR #80 branch before docs-only descendants.

Live `main` may be newer. Always resolve it rather than copying a historical SHA blindly.

The ordinary-Chat path remains:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

The current public semantic surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. ChatGPT remains the only planner/intelligence.

## Accepted foundation through Stage 25.2

- Stage 24: five-tool semantic surface and Windows lifecycle accepted.
- Stage 24.1: direct semantic tunnel selected as normal path.
- Stage 25: LFM2.5-VL-450M F16 local grounding baseline accepted on the target laptop; present-target accuracy remains 3/5 because repeated-row/tiny are deliberately unpromoted.
- Stage 25.1: same-session screenshot -> grounding -> freshness -> coordinate action/ABSTAIN foundation accepted and merged.
- Stage 25.2: first public semantic-first internal vision escalation accepted and merged in PR #77.

Stage 25.2 final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`

Final target evidence with normal Chrome workload open:

```text
semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true
minimum observed free physical RAM = 1.04 GB
SAFETY_STOP = false
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

### Stage 25.2 routing invariant

```text
fresh accessibility snapshot
  -> exact enabled button: semantic click; VLM stays stopped
  -> same-name buttons with exactly one enabled + disabled alternatives: semantic click
  -> disabled/non-button/ambiguous exact semantic evidence: ABSTAIN; VLM stays stopped
  -> zero exact candidates:
       same Playwright page/session screenshot
       -> reviewed F16 text-labeled visual grounder
       -> deterministic authorization
       -> freshness proof
       -> one coordinate click OR ABSTAIN
```

`targetText` is the authorization anchor. Planner `target`, free-form `instruction` and planner-supplied `kind` cannot redirect visual authorization.

## Active development priority — Stage 26 Procedural Memory

Read, in order:

1. `project-context/STAGE26_PROCEDURAL_MEMORY.md`
2. `project-context/STAGE26_1A_OPENADAPT_QUALIFICATION.md`
3. `project-context/CURRENT_STATE.md`
4. `project-context/ROADMAP.md`

### Stage 26.0 — UI-Mate analysis — DONE

Official `Tencent/UI-Mate` remains the workflow-guidance reference: rich demonstration evidence is reduced to compact current-subtask guidance while live state remains authoritative. UI-Mate is **not** adopted as a second planner/agent.

### Stage 26.1A — OpenAdapt core qualification — TARGET PASS

Broader upstream research found that `OpenAdaptAI/openadapt-flow` + `openadapt-capture` already implement much of the previously planned project-owned recorder/compiler/skill-store/lifecycle substrate.

Pinned and target-tested:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Real Windows target result on qualification-code HEAD `f8e8f606db845821b8fa24c09f9032015fb0e79e`:

```text
Python 3.12.10
exact Flow/Capture commit verification = PASS
PHASE_B_PASS=True
PHASE_C_TUTORIAL_PASS=True
PROBE_ERROR=<null>
ERROR=<null>
STAGE26_1A_PREFLIGHT_RESULT=PASSED
TEST_EXIT_CODE=0
Chrome processes before/after = 15/15
```

Result artifact:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json`

Current decisions:

- Flow compiler + `Workflow`/`ProgramGraph`: **ADOPT** behind project boundaries;
- `SkillLibrary` + learn/teach lifecycle: **ADAPT**, keeping stricter project candidate-first trust;
- Capture: **continue real Windows qualification; do not write our own recorder first**;
- Windows backend/agent: **security A/B required**;
- local LFM2.5-VL F16: candidate adapter through OpenAdapt's narrow proposal-only `Grounder` seam;
- OpenAdapt Desktop: Stage 27 distribution/cockpit reference only for now.

No OpenAdapt dependency has been integrated into production `semantic-projection` or the installed product path yet.

## Next active step — Stage 26.1B real bounded Windows Capture qualification

Use a harmless bounded test window first.

Prove:

- capture starts/stops in the interactive user session;
- selected window scope is respected;
- click, typing, key and scroll evidence are captured;
- UIA evidence is retained when exposed;
- capture converts to Flow recording input;
- compile/replay succeeds or explicitly refuses;
- false actions = 0;
- unrelated-window actions = 0;
- raw artifacts remain only in the explicit local qualification directory;
- cleanup succeeds and unrelated user applications remain untouched.

Do not preselect a fixed application list. Concrete local programs/capabilities are chosen later from real tasks and evidence.

## Then — Stage 26.1C executor A/B + F16 seam

Compare:

```text
A. OpenAdapt typed WindowsBackend + hardened local interactive-session agent
B. OpenAdapt IR/runtime + narrower native/project-owned actuator
```

The pinned OpenAdapt server has bounded typed `/input`, `/input/guarded`, `/uia/find` and `/uia/act` routes; legacy `/execute_windows` is disabled by default. Product acceptance must still prove generic exec cannot be enabled/reached in our configuration and review process/session/auth/blast-radius boundaries.

Then prototype local F16 as a proposal-only OpenAdapt Grounder. Identity/risk/freshness/effect checks remain authoritative.

## Stage 26.2 — ChatGPT procedural integration

After upstream capability gates, integrate accepted components behind the existing ChatGPT-only planner boundary.

A procedure is memory/evidence, not a second planner and not authorization. Current state outranks remembered history. Bootstrap procedures must follow project candidate policy rather than silently becoming trusted.

## Stage 26.3 — Windows desktop surface — REQUIRED / DO NOT DROP

This remains a separate required product stage:

```text
native/deterministic UI observation first
  -> screen capture where needed
  -> bounded local visual grounding where needed
  -> reviewed keyboard/mouse action
  -> verification / ABSTAIN
```

Productize whichever Windows observation/actuation combination wins qualification. Specific local programs are chosen later from actual tasks.

## Stage 26.4 — human demonstration transferable-skill acceptance

After desktop surface acceptance, record a real user demonstration, compile it through the accepted procedural substrate, apply project trust policy, verify completion/effects and re-apply it to a related changed task/state.

## Stage 26.5 — public contract decision

Only after Windows desktop surface exists, decide explicitly whether the current five public tool names remain sufficient or a small number of new truthful public tools is required.

Until that decision:

- current accepted public tool names remain the same five;
- procedural components stay internal/non-agentic unless a truthful Chat-facing boundary is separately designed and accepted;
- do not hide workflow execution behind misleading existing tool semantics;
- do not add a generic opaque `workflow_execute`/`tool_invoke` equivalent.

## Stage 27 / 28

Stage 27 is distribution/maintenance hardening. Before recreating installer/cockpit/sidecar infrastructure, evaluate reusable OpenAdapt Desktop patterns against the exact Flow runtime selected by this project.

Stage 28 is clean-user product E2E + first stable release.

## Residual risks that remain explicit

- repeated-row/tiny/icon-only automatic visual promotion is incomplete;
- screenshot and coordinate click remain a narrow non-atomic TOCTOU boundary;
- PID-bound loopback is not cryptographic endpoint authentication;
- DNS/rebinding/redirect browser isolation is incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not product-accepted;
- OpenAdapt Capture is not yet target-qualified for real Windows recording;
- Windows executor authority boundary is not accepted yet;
- F16 OpenAdapt adapter is not implemented yet;
- Windows desktop surface and arbitrary human demo capture are not product-accepted yet;
- no stable release exists yet.

## Non-negotiable product boundary

- ordinary ChatGPT remains the planner/intelligence;
- local models are bounded perception/extraction backends, never a second planner;
- remembered procedures are bounded guidance/evidence, never a second planner;
- do not duplicate accepted upstream mechanisms without a demonstrated blocker;
- prefer semantic/native structure over vision whenever deterministic structure exists;
- visual grounding must fail closed;
- raw capture is sensitive by default and not safe-to-sync automatically;
- keep the public tool surface small and truthful;
- preserve single-owner/fail-closed lifecycle guarantees;
- use the user only for irreducible target-machine or ordinary-Chat UI gates.

## Source-of-truth order

When documents disagree:

1. current code, tests and exact current CI/target evidence;
2. this file and `CURRENT_STATE.md`;
3. `STAGE26_1A_OPENADAPT_QUALIFICATION.md` and `STAGE26_PROCEDURAL_MEMORY.md`;
4. `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`;
5. `DEVELOPMENT_PRINCIPLES.md` and current capability contracts;
6. Stage 25/25.1 research, dated handoffs and older README revisions.

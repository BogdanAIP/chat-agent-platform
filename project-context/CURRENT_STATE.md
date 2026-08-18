# Current State

## Resolve live repository state before editing

Do not treat an embedded documentation merge SHA as permanently current. Resolve live `main` from GitHub before branching or editing.

Stable accepted milestones:

- Stage 25.2 runtime/code merge: `2a410476ef849fd6d9c172703a004b1befcbcfb1` (#77);
- Stage 26 architecture/context activation: `04dccfd30eb06a82899e2771f6d53ab4c8387128` (#78);
- Stage 26.1A target-tested qualification code: `f8e8f606db845821b8fa24c09f9032015fb0e79e` (#80 branch before docs-only descendants).

Live `main` may be newer than these milestones. Resolve it rather than assuming a docs SHA is current.

The accepted ordinary-Chat path remains:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

Current public Chat-facing tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Ordinary ChatGPT remains the only planner/intelligence.

## Accepted foundation through Stage 25.2

### Stage 24 / 24.1

Five-tool semantic surface, Windows lifecycle and direct stdio semantic tunnel are accepted product foundations.

### Stage 25 — local grounding baseline

Accepted target configuration:

```text
llama.cpp = b10448 / commit ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
present-target hits = 3/5
false clicks = 0
```

Repeated-row and tiny target classes remain deliberately unpromoted.

### Stage 25.1 — same-session visual foundation

Accepted foundations include same-session screenshot -> prepared target -> freshness -> coordinate action or ABSTAIN, fail-closed stale/replay/layout/scroll/overlay/navigation handling, focused llama.cpp lifecycle, PID-bound listener verification, class-aware visual authorization and installed-layout/security hardening.

### Stage 25.2 — MERGED AND ACCEPTED

PR #77 was squash-merged as runtime/code milestone:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

Accepted `web_interact(click)` routing:

```text
fresh accessibility snapshot
  -> exact enabled button
       -> semantic click; VLM stays stopped
  -> duplicate same-name buttons with exactly one enabled + disabled alternatives
       -> semantic click; VLM stays stopped
  -> disabled / unpromoted role / unresolved semantic ambiguity
       -> ABSTAIN; VLM stays stopped
  -> zero exact candidates
       -> SAME Playwright page/session screenshot
       -> reviewed F16 text-labeled visual grounder
       -> deterministic authorization
       -> exact freshness proof
       -> one coordinate click OR ABSTAIN
```

`targetText` remains the semantic/visual authorization anchor. Planner `target`, free-form `instruction` and planner-supplied `kind` cannot redirect visual authorization.

Final target evidence: `semantic_hits=2`, `visual_hits=1`, `correct_abstains=2`, `false_clicks=0`, `errors=0`, `semantic_cases_started_vlm=0`, `acceptance_pass=true`; runtime stopped afterward and Chrome remained running.

## Stage 26 — Procedural Memory / Demo2Workflow — ACTIVE

Authoritative design:

- `project-context/STAGE26_PROCEDURAL_MEMORY.md`
- `project-context/STAGE26_1A_OPENADAPT_QUALIFICATION.md`

### Stage 26.0 — UI-Mate analysis + contract/context sync — DONE

PR #78 activated the procedural-memory architecture and preserved these rules:

- ChatGPT is the only planner/intelligence;
- remembered procedure is guidance/evidence, not authorization;
- current observed state outranks remembered action history;
- no private chain-of-thought is persisted;
- Windows desktop surface is an explicit required future stage;
- public contract is reconsidered only after desktop surface exists.

### Stage 26.1A — OpenAdapt core qualification — TARGET PASS

Broader research found that `OpenAdaptAI/openadapt-flow` and `openadapt-capture` already implement major parts of the originally planned project-owned recorder/compiler/skill-store/lifecycle substrate.

Pinned target-tested upstreams:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Target-tested qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`.

Real Windows result:

```text
Python 3.12.10
FLOW_INSTALLED_COMMIT matches expected
FLOW_INSTALLED_VERSION=1.31.0
CAPTURE_INSTALLED_COMMIT matches expected
CAPTURE_INSTALLED_VERSION=1.2.2
PHASE_B_PASS=True
PHASE_C_TUTORIAL_PASS=True
PROBE_ERROR=<null>
ERROR=<null>
STAGE26_1A_PREFLIGHT_RESULT=PASSED
TEST_EXIT_CODE=0
Chrome process count 15 -> 15
```

Result artifact:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json`

The tutorial path is model-free and upstream's lifecycle contract checks production `VERIFIED` outcome, effect evidence, digest-bound receipt and `model_calls=0`.

Current component decisions:

- Flow compiler + `Workflow` / `ProgramGraph`: **ADOPT** behind project boundaries;
- `SkillLibrary` + learning/teach lifecycle: **ADAPT** because project policy remains candidate-first and upstream bootstrap v1 becomes active immediately;
- Capture recorder: continue real Windows qualification before adoption; do not build our own recorder first;
- Windows backend/agent: continue security A/B; typed/guarded/UIA routes exist and legacy `/execute_windows` is disabled by default, but the interactive-session authority boundary still needs acceptance;
- F16 integration: adapt through OpenAdapt's narrow proposal-only `Grounder` seam after capture qualification;
- OpenAdapt Desktop: distribution/cockpit reference for Stage 27, not current runtime baseline.

No OpenAdapt code has been integrated into `semantic-projection` or the installed product path yet.

## Stage 26.1B — NEXT — real bounded Windows Capture qualification

Use a harmless bounded test window first.

Required evidence:

- capture start/stop in the interactive user session;
- selected window scope respected;
- click, typing, key and scroll evidence captured;
- UIA evidence retained when exposed;
- conversion to Flow recording input;
- compile/replay success or bounded explicit refusal;
- false actions = 0;
- unrelated-window actions = 0;
- raw artifacts remain only in the explicit local qualification directory;
- cleanup successful; unrelated user applications remain untouched.

Concrete local programs/capabilities are not preselected; choose them later from actual tasks and evidence.

## Stage 26.1C — after capture

Executor security A/B:

```text
A. OpenAdapt typed WindowsBackend + hardened local interactive-session agent
B. OpenAdapt IR/runtime + narrower native/project-owned actuator
```

Then prototype the accepted local LFM2.5-VL-450M F16 through OpenAdapt's `Grounder` protocol. Grounder output remains only a proposal; identity/risk/freshness/effect checks remain authoritative.

## Stage 26.2 — ChatGPT procedural integration + variant-task dogfood

Integrate accepted upstream pieces behind the ChatGPT-only planner boundary. Prove current-state-first reuse, candidate-first trust, verifier/effect-based completion and changed/variant task behavior without blind replay.

## Stage 26.3 — Windows desktop surface — REQUIRED / DO NOT DROP

This explicit product stage remains:

```text
native/deterministic UI observation first
  -> screen capture where needed
  -> bounded local visual grounding where needed
  -> reviewed keyboard/mouse action
  -> verification / ABSTAIN
```

Productize whichever Windows observation/actuation combination wins the qualification A/B. Concrete local programs/capabilities are selected later from real tasks and evidence.

## Stage 26.4 — human demonstration transferable-skill acceptance

After the desktop surface is accepted, record a real user demonstration, compile it through the accepted procedural substrate, apply project trust policy, verify it and re-apply it to a related changed task/state.

## Stage 26.5 — public contract decision

Only after Windows desktop surface exists, make a separate ADR + ordinary-Chat acceptance decision whether the current five public tools remain sufficient or a small number of new truthful public tool names is required.

Do not overload existing tools or add a generic opaque workflow dispatcher merely to preserve a tool count.

## Remaining product work

- Stage 26.1B real Windows Capture qualification;
- Stage 26.1C executor security A/B + F16 seam;
- Stage 26.2 ChatGPT procedural integration + variant-task acceptance;
- Stage 26.3 Windows desktop surface;
- Stage 26.4 human demonstration capture and transfer;
- Stage 26.5 public contract decision;
- raw demonstration retention/redaction/encryption policy;
- stronger DNS/redirect/private-network boundary decision;
- release-grade Python/model/OpenAdapt artifact reproducibility;
- dependency cleanup;
- Stage 27 installer/update/repair/doctor/uninstall/key rotation/rollback/restart recovery, with OpenAdapt Desktop patterns evaluated before reimplementation;
- Stage 28 clean-user product E2E and first stable release.

## Active rules

- resolve live `main` before work;
- ChatGPT is the only planner/intelligence;
- do not duplicate accepted upstream procedural mechanisms without an integration blocker;
- semantic/native structure comes before vision whenever reliable structure exists;
- local vision starts only on explicitly authorized paths and may ABSTAIN;
- stale or uncertain evidence causes zero mutation;
- remembered procedure never overrides current observed state;
- procedural memory stores structured evidence, not private reasoning;
- raw capture is not safe-to-sync by default;
- public semantic surface remains exactly five tool names until the explicit post-desktop contract decision;
- accepted implementation evidence and authoritative documentation move together.

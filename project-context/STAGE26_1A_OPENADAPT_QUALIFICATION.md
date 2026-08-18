# Stage 26.1A — OpenAdapt Qualification Spike

Status: **CORE QUALIFICATION ACCEPTED / PRODUCT INTEGRATION NOT STARTED**

Base project `main` resolved before branch creation:

`58b441b9b50291189ac32f72d194b5ba6d0a182c`

Target-tested qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`

This gate exists because the first Stage 26 design assumed the project would need to build its own recorder, demo compiler, skill store and lifecycle after reviewing Tencent/UI-Mate. Broader upstream research found that OpenAdapt already implements substantial portions of those boundaries. Stage 26 therefore qualifies upstream components before duplicating them.

Exact source pins live in `config/stage26-openadapt-lock.json`.

## Product invariant

Ordinary ChatGPT remains the only planner/intelligence.

OpenAdapt is evaluated only as a local non-agentic procedural engine and authoring/runtime substrate:

```text
ordinary ChatGPT
  -> understands the current task and decides whether a known procedure applies
  -> current live state remains authoritative
  -> bounded local capability/procedural substrate
       -> deterministic procedure execution where qualified
       -> verification
       -> HALT/ABSTAIN on uncertainty
  -> ChatGPT/user handles genuinely new task logic or a halted case
```

Do not adopt an OpenAdapt planner, generic autonomous agent loop, generated per-workflow MCP inventory, or hidden catch-all workflow dispatcher.

Current public Chat tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Stage 26.1A does not change that contract.

## Pinned upstream candidates

### openadapt-flow

Pinned commit:

`d7f58d9f35c8369f16a9b378f23952d425334ad7`

Observed package version: `1.31.0`.

License: MIT.

Qualified candidate responsibilities:

- demonstration compiler;
- `Workflow` / `ProgramGraph` IR;
- typed parameters, predicates, guards, loops, branches and subflows;
- deterministic replay and refusal;
- lint/certification policies;
- postconditions and system-of-record effect verification;
- `SkillLibrary` version/lifecycle substrate;
- multi-trace induction;
- halt -> teach -> regression gate -> promotion/refusal;
- backend protocol suitable for testing a narrower project-owned actuator if required;
- grounder protocol suitable for adapting the accepted local LFM2.5-VL F16 runtime.

### openadapt-capture

Pinned commit:

`bcf12942d61d66b64d94e645e9124273a5cc5963`

Observed package version: `1.2.2`.

License: MIT.

Candidate responsibilities:

- native mouse/keyboard/screen capture;
- Windows UIA structural observations when exposed by the application;
- local capture session and conversion into Flow compiler input.

Important boundary: raw capture may contain everything visible or typed. It is not accepted for long-lived product storage until this project defines and tests retention, deletion, encryption and redaction behavior around the raw boundary.

### openadapt-desktop

Pinned commit:

`86b1da232d88537e5e4b92ec23571008ed7ff81f`

Observed package version: `0.15.0`.

License: MIT.

Role in this gate: **distribution/cockpit reference, not execution baseline**.

At the pin above its build extra freezes `openadapt-flow[browser,console]==1.27.1`, while the Flow source under qualification reports `1.31.0`. Desktop is therefore evaluated separately for installer/sidecar/cockpit ideas rather than assumed to provide the exact runtime under qualification.

## Real Windows target evidence

Exact target rerun on qualification-code HEAD `f8e8f606db845821b8fa24c09f9032015fb0e79e`:

```text
PYTHON_VERSION=3.12.10
FLOW_EXPECTED_COMMIT=d7f58d9f35c8369f16a9b378f23952d425334ad7
FLOW_INSTALLED_COMMIT=d7f58d9f35c8369f16a9b378f23952d425334ad7
FLOW_INSTALLED_VERSION=1.31.0
CAPTURE_EXPECTED_COMMIT=bcf12942d61d66b64d94e645e9124273a5cc5963
CAPTURE_INSTALLED_COMMIT=bcf12942d61d66b64d94e645e9124273a5cc5963
CAPTURE_INSTALLED_VERSION=1.2.2
PHASE_B_PASS=True
TUTORIAL_REQUESTED=True
PHASE_C_TUTORIAL_PASS=True
CHROME_PROCESS_COUNT_BEFORE=15
CHROME_PROCESS_COUNT_AFTER=15
PROBE_ERROR=<null>
ERROR=<null>
STAGE26_1A_PREFLIGHT_RESULT=PASSED
TEST_EXIT_CODE=0
STAGE26_1A_TARGET_RESULT=PASSED
```

Result artifact:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json`

Normal user Chrome remained running. The harness used an isolated Python 3.12 venv and isolated Playwright browser directory; the venv/browser artifacts were removed after the run.

### Harness defect found and corrected during qualification

An earlier target run installed Flow only with `[browser]` while the probe imported `WindowsBackend`. The pinned Flow package declares `requests` in its official `[windows]` extra, so the probe failed with `ModuleNotFoundError: requests`.

This was a qualification-harness defect, not an upstream runtime failure. The harness was corrected to install:

```text
Phase B: openadapt-flow[windows]
Phase B + tutorial: openadapt-flow[browser,windows]
```

The exact rerun then passed.

## What Stage 26.1A answers

### Q1 — Can Flow replace our planned Demo Compiler / IR?

**Decision: ADOPT as the upstream procedural-program substrate, behind project boundaries.**

Evidence:

- exact pinned package imports without model/API credentials;
- tutorial compile/replay path completed `VERIFIED` on the target Windows machine;
- upstream quickstart lifecycle requires production `standard` profile, effect verification, digest-bound receipt and `model_calls=0` for the tutorial;
- `Workflow` / `ProgramGraph` preserve semantic/structural target evidence plus visual evidence rather than requiring blind coordinate replay;
- current state is re-observed at replay time;
- structural resolution refuses stale/ambiguous targets rather than selecting the first candidate.

Do not build a competing project-owned compiler/IR before an integration blocker is demonstrated.

### Q2 — Can Flow replace the planned skill store/lifecycle?

**Decision: ADAPT, not blind ADOPT.**

Reusable upstream capabilities include:

- versioned skill revisions;
- `candidate` / `active` / `superseded` / `rolled_back` states;
- provenance with parent version and source traces;
- held-out/regression/canary learning gates;
- governed HALT -> teach -> learn -> promote/refuse path.

Project adaptation is required because upstream `SkillLibrary.create_skill()` makes the first version immediately `active`. Chat Agent Platform must not silently treat one newly compiled demonstration as product-trusted. A thin project policy adapter must preserve the stricter candidate-first rule at the product boundary.

Do not recreate the underlying version store or learning loop unless the adapter proves insufficient.

### Q3 — Can Capture replace our planned human recorder?

**Decision: CONTINUE QUALIFICATION; do not build our own recorder first.**

The pinned Flow/Capture packages install together and expose the expected recorder/adapter symbols. Upstream recording design already provides window-scoped capture, UIA evidence where available, exact conversion to Flow recording input and local-only operation.

Still required on the real target in **Stage 26.1B / Phase D**:

- start/stop a bounded harmless window recording;
- capture click, typing, key and scroll evidence;
- confirm UIA evidence where the fixture exposes it;
- convert -> compile -> replay or bounded refusal;
- false actions = 0;
- unrelated-window actions = 0;
- raw artifacts remain only in the selected local qualification directory;
- cleanup succeeds.

### Q4 — Is the Windows execution boundary acceptable?

**Decision: CONTINUE AS ADAPT / SECURITY A/B.**

Important updated finding: in the pinned server, `/execute_windows` is a **legacy arbitrary-Python route disabled by default**. The default agent exposes bounded typed routes including:

```text
/screenshot
/context/identity
/input
/input/guarded
/uia/locator-at
/uia/text-at-point
/uia/find
/uia/act
```

The client/server also have stale/ambiguous refusal paths and action-delivery receipts.

That is materially safer than the early upstream impression, but the Windows agent remains a separate interactive-session authority boundary. Before product integration compare:

```text
A. OpenAdapt typed WindowsBackend + hardened loopback/session agent
B. OpenAdapt IR/runtime + narrower native/project-owned UIA actuator
```

Acceptance must explicitly cover callable authority, process/session ownership, authentication, stale/focus/frame binding, blast radius and whether the legacy exec route is impossible in the product configuration.

### Q5 — Can our accepted local F16 become an OpenAdapt Grounder?

**Decision: ADAPT CANDIDATE; prototype after Windows capture qualification.**

The pinned `Grounder` protocol is narrow:

```text
current PNG + intent + optional OCR label
  -> GrounderMatch proposal OR None
```

Upstream explicitly treats a grounder result as a proposal only; deterministic identity/risk checks remain authoritative. This is compatible with the accepted local LFM2.5-VL-450M F16 model and does not require a new public Chat vision tool.

Required prototype properties remain:

- F16 lifecycle stays focused/on-demand and unloads after use;
- no model proposal authorizes an action by itself;
- existing identity/risk/freshness/effect gates remain authoritative;
- no screenshot egress is introduced.

### Q6 — What should happen to Stage 27?

**Decision: ADAPT/REFERENCE.**

OpenAdapt Desktop already demonstrates a Beta Tauri cockpit, frozen Python sidecar and installer packaging lane. Because its current bundled Flow version differs from the qualified Flow pin, it is not accepted as the runtime baseline. Re-evaluate its installer/sidecar/update/cockpit patterns during Stage 27 before building equivalent distribution infrastructure from scratch.

## Decision matrix after Stage 26.1A core qualification

| Component | Decision | Next gate |
| --- | --- | --- |
| Flow compiler + IR | **ADOPT** | integration behind ChatGPT-only boundary |
| SkillLibrary + learning lifecycle | **ADAPT** | candidate-first project policy wrapper |
| Capture recorder | **CONTINUE QUALIFICATION** | real bounded Windows Phase D |
| Windows backend/agent | **ADAPT / A/B REQUIRED** | executor security Phase E |
| F16 Grounder integration | **ADAPT CANDIDATE** | bounded adapter Phase F |
| Desktop cockpit/distribution patterns | **REFERENCE / ADAPT** | Stage 27 evaluation |

## Next active work

### Stage 26.1B — real Windows Capture qualification — NEXT

Use a harmless bounded fixture. Do not start with a consequential user workload or preselected application list.

Acceptance measures:

- exact captured action count/classes;
- window scope respected;
- UIA evidence availability;
- conversion and compile result;
- replay outcome or explicit bounded refusal;
- false actions = 0;
- unrelated-window actions = 0;
- raw capture location/retention recorded;
- cleanup successful;
- normal user Chrome and unrelated applications untouched.

### Stage 26.1C — executor security A/B + F16 seam

Only after capture/compiler acceptance:

- compare typed OpenAdapt Windows agent with a narrower actuator boundary;
- prove legacy arbitrary exec disabled/unreachable in the proposed product configuration;
- prototype the accepted local F16 through the narrow Grounder protocol;
- rerun stale/ambiguous/freshness/false-action acceptance.

### Stage 26.2 — ChatGPT procedural integration / dogfood

After upstream capability gates, integrate the accepted compiler/skill substrate behind the ChatGPT-only planner boundary and prove variant-task reuse without blind replay.

### Stage 26.3 — Windows desktop surface — REQUIRED / DO NOT DROP

Productize the accepted Windows observation/actuation/verification combination. Concrete local programs/capabilities are selected later from actual tasks and evidence.

### Stage 26.4 — human demonstration transferable-skill acceptance

Record a real user demonstration through the accepted desktop surface, compile it, verify it and re-apply it to a related changed task/state.

### Stage 26.5 — public contract decision

Only after Windows desktop surface exists, decide whether the current five public tool names remain sufficient or a small number of new truthful public tools is required.

## Hard safety boundaries

- ordinary ChatGPT remains the only planner/intelligence;
- do not expose `/execute_windows` or any equivalent generic code execution to ChatGPT;
- do not enable the legacy arbitrary-exec route in the product configuration;
- do not auto-generate hundreds of public MCP tools from workflow bundles;
- do not let retrieval or skill selection authorize consequential actions;
- do not persist private chain-of-thought;
- do not treat raw capture as safe-to-sync data;
- do not let a model proposal bypass identity, risk, freshness, postcondition or effect verification;
- do not claim arbitrary Windows application support from a fixture acceptance;
- do not integrate an upstream dependency into the installed product before exact-version and target acceptance.

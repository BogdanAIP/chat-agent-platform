# Stage 26.1A — OpenAdapt Qualification Spike

Status: **ACTIVE QUALIFICATION / NOT ADOPTED YET**

Base project `main` resolved before branch creation:

`58b441b9b50291189ac32f72d194b5ba6d0a182c`

This gate exists because Stage 26.0 originally concluded that the project would need to build its own recorder, demo compiler, skill store and lifecycle after reviewing Tencent/UI-Mate. A broader upstream review found that OpenAdapt already implements substantial portions of those boundaries. The project must therefore qualify the upstream before duplicating it.

Exact source pins live in `config/stage26-openadapt-lock.json`.

## Product invariant

Ordinary ChatGPT remains the only planner/intelligence.

OpenAdapt is being evaluated only as a local non-agentic procedural engine and authoring/runtime substrate:

```text
ordinary ChatGPT
  -> understands current task and decides whether a known procedure applies
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

Candidate responsibilities:

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

At the pin above its build extra freezes `openadapt-flow[browser,console]==1.27.1`, while current Flow main reports `1.31.0`. Desktop is therefore evaluated separately for installer/sidecar/cockpit ideas rather than being assumed to provide the exact runtime under qualification.

## What Stage 26.1A must answer

### Q1 — Can Flow replace our planned Demo Compiler / IR?

PASS requires all of the following from the pinned build:

- import and instantiate the core IR without model/API credentials;
- compile/replay path is deterministic on a healthy synthetic/tutorial workflow;
- compiled representation contains semantic/structural target evidence rather than requiring blind absolute-coordinate replay;
- ambiguous/unsupported state can refuse rather than silently proceed;
- current application state is re-observed at replay time.

### Q2 — Can Flow replace the planned skill store/lifecycle?

PASS requires evidence that pinned code provides:

- versioned skill revisions;
- candidate/active/superseded/rollback or equivalent governed states;
- provenance sufficient to identify the source traces/revision lineage;
- regression/held-out or equivalent promotion gate;
- safe refusal when a proposed learned correction is underdetermined.

Do not recreate these project-side before this question is decided.

### Q3 — Can Capture replace our planned human recorder?

PASS requires on the real Windows target:

- recording starts/stops in the interactive user session;
- a bounded test window can be recorded without affecting unrelated windows;
- click, typing, key and scroll evidence is captured correctly for the chosen fixture;
- structural UIA evidence is retained when the fixture exposes it;
- conversion to Flow recording is exact enough for compile/replay;
- no cloud transfer is required;
- raw artifacts remain within the explicitly selected local qualification directory.

### Q4 — Is the Windows execution boundary acceptable?

This is a security A/B, not an automatic adoption.

OpenAdapt's current `win_agent` exposes an internal `/execute_windows` contract capable of executing Python in the interactive desktop session. It is not permitted to become a Chat-facing capability.

Compare:

```text
A. OpenAdapt WindowsBackend + hardened loopback/session agent
B. OpenAdapt IR/runtime + narrower native/project-owned UIA actuator
```

Acceptance decision must explicitly cover:

- callable authority;
- process/session ownership;
- loopback authentication;
- command surface width;
- stale/ambiguous target behavior;
- before/after evidence;
- blast radius if the local caller is compromised.

A result may be `ADOPT`, `ADAPT`, or `REJECT`. A failure here does not invalidate Flow compiler/IR/lifecycle reuse.

### Q5 — Can our accepted local F16 become an OpenAdapt Grounder?

Prototype only after Q1/Q2 basic import gates pass.

Required properties:

- adapter implements the narrow Grounder contract;
- OpenAdapt receives only a proposal from F16, not authorization;
- existing identity/risk/freshness/effect checks remain authoritative;
- F16 lifecycle remains focused/on-demand and unloads after use;
- no new public Chat vision tool is introduced.

### Q6 — What should happen to Stage 27?

OpenAdapt Desktop already implements a Beta cockpit/frozen-sidecar/install packaging lane. After Flow/Capture qualification, evaluate whether its Tauri/sidecar/update/installer patterns can replace portions of the planned project-owned distribution layer.

Do not copy or integrate Desktop yet; first record which parts are reusable and which conflict with the ChatGPT-only product boundary.

## Qualification phases

### Phase A — offline/static contract

- validate exact lock schema;
- validate pins, versions and licenses recorded from upstream source;
- ensure no public Chat tool change;
- ensure qualification code does not import OpenAdapt into production semantic-projection.

### Phase B — isolated Python 3.12 source install

Use `scripts/stage26-openadapt-qualification.ps1` in a dedicated local directory.

The script must:

- resolve exact source pins from the lock file;
- require Python 3.12;
- create an isolated venv;
- install exact pinned Flow/Capture commits;
- verify installed package versions and key symbols;
- write machine-readable results;
- leave the existing Chat Agent Platform runtime and user Chrome untouched.

No target result is accepted unless the exact tested commits match the lock file.

### Phase C — upstream synthetic/tutorial lifecycle

After Phase B passes:

- record/compile/replay a synthetic or bundled upstream workflow;
- run deterministic refusal/drift tests where available;
- inspect emitted bundle/IR;
- inspect skill lifecycle and teach path;
- record model call count and any network/runtime side effects.

### Phase D — real Windows capture

Use a harmless bounded fixture first. Do not start with Origin, REAPER or another consequential user workload.

Acceptance measures:

- exact captured action count/classes;
- UIA evidence availability;
- compile success/refusal reason;
- replay outcome;
- false actions = 0;
- unrelated-window actions = 0;
- cleanup successful.

### Phase E — executor security A/B

Only after capture/compiler acceptance.

No merge that makes OpenAdapt Windows execution part of the product path until this A/B has a written result.

### Phase F — F16 adapter

Wire the already accepted local F16 only through the narrow Grounder seam and rerun a bounded visual-fallback acceptance.

## Decision matrix

Each component gets one explicit result:

| Component | Possible result | Default before evidence |
| --- | --- | --- |
| Flow compiler + IR | ADOPT / ADAPT / REJECT | UNDECIDED |
| SkillLibrary + learning lifecycle | ADOPT / ADAPT / REJECT | UNDECIDED |
| Capture recorder | ADOPT / ADAPT / REJECT | UNDECIDED |
| Windows backend/agent | ADOPT / ADAPT / REJECT | UNDECIDED |
| F16 Grounder integration | ADOPT / ADAPT / REJECT | UNDECIDED |
| Desktop cockpit/distribution patterns | ADOPT / ADAPT / REJECT | UNDECIDED |

No component is accepted merely because upstream CI or documentation calls it Beta/scoped-accepted.

## Merge gate for Stage 26.1A

Stage 26.1A may merge as a qualification milestone when:

1. exact pins and static contract are reviewed;
2. Phase B isolated install/import evidence is green on the target Windows machine;
3. Phase C synthetic/tutorial compiler/replay evidence is green or produces a bounded documented refusal;
4. no production runtime import/routing has been changed;
5. the next active implementation work is rewritten from evidence, not from the pre-research assumption that all procedural components must be project-owned.

Windows capture/executor/F16 may continue as follow-up qualification commits/PRs if they need separate target gates, but their status must remain explicit.

## Hard safety boundaries

- do not expose `/execute_windows` or equivalent generic code execution to ChatGPT;
- do not auto-generate hundreds of public MCP tools from workflow bundles;
- do not let retrieval or skill selection authorize consequential actions;
- do not persist private chain-of-thought;
- do not treat raw capture as safe-to-sync data;
- do not let a model proposal bypass identity, risk, freshness, postcondition or effect verification;
- do not claim arbitrary Windows application support from a fixture acceptance;
- do not merge an upstream dependency into the installed product before exact-version and target acceptance.

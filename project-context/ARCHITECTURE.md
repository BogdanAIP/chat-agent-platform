# Architecture

## Repository-state rule

Resolve live `main` from GitHub before new work. Documentation milestones can move `main` without changing accepted runtime/code evidence, so do not treat an embedded docs SHA as permanently current.

Stable milestones:

- accepted Stage 25.2 runtime/code merge: `2a410476ef849fd6d9c172703a004b1befcbcfb1` (#77);
- Stage 26 architecture/context activation: `04dccfd30eb06a82899e2771f6d53ab4c8387128` (#78);
- Stage 26.1A target-tested qualification code: `f8e8f606db845821b8fa24c09f9032015fb0e79e` (#80 branch before docs-only descendants).

## Product boundary

`chat-agent-platform` is a thin Windows companion that lets ordinary ChatGPT use scoped local capabilities. Ordinary ChatGPT remains the only planner/orchestrator. Local components may provide deterministic execution, bounded specialist inference and non-agentic procedural memory; they must not become a second agent brain.

## Accepted ordinary-Chat path

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> focused task-active backends/adapters
```

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains replaceable internal infrastructure for diagnostics, adaptive lifecycle experiments and aggregation where useful. The normal public `semantic` path is direct stdio.

## Capability projection rule

`semantic-projection` is a deterministic compatibility boundary. It may map one truthful semantic operation to one reviewed backend action or a small bounded deterministic sequence. It must not:

- decide user goals;
- execute arbitrary hidden plans;
- become procedural memory or a workflow planner;
- expose generic `tool_invoke` behavior under another name;
- dynamically route to arbitrary unreviewed models/endpoints;
- become a general process supervisor/model manager;
- hide new desktop/workflow consequence classes behind misleading existing schemas merely to avoid adding a truthful capability later.

## Capability and procedural trust lifecycle

Capability state:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedural trust is separate from capability authorization. OpenAdapt's internal skill statuses may be reused, but the product boundary remains candidate-first:

```text
new/learned procedure
  -> project CANDIDATE
  -> verification / regression / variant evidence
  -> trusted reusable status
  -> stale / quarantine / disable / rollback as needed
```

A trusted procedure is still guidance/executable program evidence, not blanket authorization for every action it contains.

## Browser grounding architecture — Stage 25.2 accepted

Deterministic semantic DOM/accessibility grounding is preferred whenever reliable structure exists.

```text
web_interact(click)
  -> fresh accessibility snapshot
       -> exact enabled button
            -> act semantically; VLM stays stopped
       -> same-name buttons with exactly one enabled + disabled alternatives
            -> act semantically; VLM stays stopped
       -> disabled/non-button/unresolved ambiguity
            -> ABSTAIN; VLM stays stopped
       -> zero exact candidates
            -> SAME Playwright page/session capture
            -> reviewed local F16 text-labeled grounder
            -> deterministic authorization
            -> exact freshness proof
            -> one coordinate action OR ABSTAIN
```

This supersedes earlier Stage 25.1 wording that treated semantic ambiguity as a possible vision-escalation case. Current accepted policy does not visually escalate unresolved semantic ambiguity. Generic semantic click failures also do not invoke vision.

`targetText` is the semantic/visual authorization anchor. Planner `target`, free-form `instruction` and planner-supplied `kind` cannot redirect the visual target.

## Local vision boundary

Accepted target-laptop baseline:

```text
runtime = llama.cpp b10448 / ad1de39e0
model = LiquidAI LFM2.5-VL-450M F16
projector = F16
CPU = 8 threads
ctx = 2048
```

The model is bounded perception. It never plans the user's workflow and never clicks by itself. Product code keeps runtime/model identity replaceable behind focused interfaces.

## Procedural-memory architecture — Stage 26 active

Stage 26.0 established the conceptual pattern from `Tencent/UI-Mate`.

Stage 26.1A then qualified a much more complete implementation candidate:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Target-tested qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`.

Real Windows evidence: exact commits verified, `PHASE_B_PASS=True`, `PHASE_C_TUTORIAL_PASS=True`, no probe/error, model-free tutorial verification, Chrome remained 15/15 processes.

Detailed qualification contract: `STAGE26_1A_OPENADAPT_QUALIFICATION.md`.

### Revised procedural split

Do not assume the repository owns its own generic recorder/compiler/skill-store implementation.

```text
ordinary ChatGPT
  planner / task interpretation / applicability / adaptation
        |
        | bounded procedure context / accepted routine invocation
        v
qualified procedural substrate
  OpenAdapt Flow compiler + Workflow/ProgramGraph
  adapted SkillLibrary/learn/teach lifecycle
  accepted capture source
  project trust/policy adapter
  project integration/authorization boundaries
        |
        v
accepted capability layer
  browser/files semantics today
  qualified Windows desktop surface later
  local F16 only as proposal-only bounded perception
```

The repository owns the integration and policy boundary. It reuses upstream procedural mechanics where qualified and writes a replacement only for a measured gap.

### Compiled-program evidence rule

The original Stage 26 design said compiled skills should contain no coordinates. Qualification produced a more accurate invariant.

OpenAdapt retains structural/native evidence and may also retain template/OCR/geometry/pixel evidence for fallback. Therefore the product rule is:

> A compiled procedure must not use blind historical absolute-coordinate replay as authority or primary identity.

Preferred order:

```text
live structural/native/semantic evidence
  -> deterministic re-resolution
  -> bounded OCR/template/geometry/visual fallback where allowed
  -> identity/risk/freshness checks
  -> action
  -> postcondition/effect verification
  -> HALT/ABSTAIN on unresolved state
```

Historical pixel evidence may exist inside a bundle, but it is evidence, not authority.

### Current-state priority

```text
current observed state
  > verifier/effect criteria / current task goal
  > prior successful procedural evidence
  > raw historical action sequence
```

A remembered procedure may guide execution but cannot override contradictory current evidence.

### Completion/effect verification

A model/Chat report that a subtask is complete is a proposal, not sufficient evidence:

```text
completion proposal
  -> native/deterministic verifier or system-of-record effect where possible
       PASS -> advance / complete
       FAIL -> remain / recover
       UNKNOWN -> observe / HALT / ABSTAIN / user input
```

Retrieval and workflow progress are non-authorizing. Every actual capability action still passes through its normal scope/authorization boundary.

## Windows capture qualification — next active gate

Stage 26.1B qualifies OpenAdapt Capture on a harmless bounded Windows fixture before any project recorder is written.

Required evidence:

- interactive-session record start/stop;
- selected window scope respected;
- click/type/key/scroll event capture;
- UIA evidence where exposed;
- conversion to Flow recording input;
- compile/replay success or bounded refusal;
- zero false/unrelated-window actions;
- explicit local raw-artifact containment and cleanup.

## Windows execution boundary — separate security decision

The pinned OpenAdapt server exposes bounded typed routes including `/input`, `/input/guarded`, `/uia/find` and `/uia/act`. Legacy arbitrary `/execute_windows` is disabled by default.

That does not automatically accept the agent boundary. Stage 26.1C compares:

```text
A. OpenAdapt typed WindowsBackend + hardened local interactive-session agent
B. OpenAdapt IR/runtime + narrower native/project-owned actuator
```

The selected design must explicitly cover callable authority, process/session ownership, authentication, stale/focus/frame binding, action-delivery evidence and blast radius. Product configuration must make legacy generic exec disabled/unreachable.

## F16 integration seam

OpenAdapt `Grounder` is a narrow proposal interface:

```text
current PNG + intent + optional OCR label
  -> proposed point/region/confidence OR None
```

The already accepted local LFM2.5-VL-450M F16 should be adapted here rather than replacing its existing lifecycle. F16 remains local, on-demand, unloadable and non-authorizing. Identity/risk/freshness/effect checks stay authoritative.

## Windows desktop surface — explicit required product boundary

Stage 26.3 remains deliberately separate and must not be lost.

```text
Windows task
  -> native/deterministic UI observation where available
  -> screen capture only where needed
  -> bounded local visual grounding where needed
  -> reviewed keyboard/mouse actuation
  -> post-action verification / ABSTAIN
```

Productize whichever Windows observation/actuation combination wins Stage 26.1B/26.1C qualification.

Concrete local programs/capabilities are selected from real tasks and evidence when this stage is benchmarked; architecture does not preselect a fixed list.

## Human demonstration transfer

Stage 26.4, after desktop-surface acceptance:

```text
real bounded human demonstration
  -> accepted capture source
  -> qualified compiler/IR
  -> project candidate/trust policy
  -> verifier/effect evidence
  -> related changed-task reuse
```

One demonstration is evidence, not automatic trust.

## Public contract decision after desktop surface

Current five public tool names are an accepted current contract, not a dogmatic permanent limit.

Only after Windows desktop surface exists, make an explicit ADR and ordinary-Chat acceptance decision between:

- preserving the existing small semantic philosophy with a few coarse truthful capabilities; or
- adding a small number of new public tool names if required for truthful semantics/safety.

Do not add a generic opaque workflow dispatcher, and do not overload current tools with unrelated desktop/workflow behavior solely to keep the count at five.

## Security boundaries

- tunnel reachability is outbound from the user machine;
- normal semantic transport is direct stdio;
- secrets live outside repository content and tunnel keys use Windows DPAPI;
- Filesystem roots and browser capability exposure remain explicitly scoped;
- local inference remains bounded and non-authorizing;
- workspace containment accounts for Windows links/junctions;
- browser DNS/rebinding/redirect isolation remains an explicit residual boundary;
- child backends must not inherit tunnel credentials unless required;
- raw desktop capture is sensitive local data and not safe-to-sync by default;
- private chain-of-thought must never be persisted into procedural memory;
- stale/malformed/incompatible procedures fail closed;
- OpenAdapt qualification does not itself grant production authority;
- generic Windows code execution must remain disabled/unreachable in product configuration.

## Windows management

The public manager/tray owns lifecycle/configuration/diagnostics only. It does not become workflow memory, a planner or a desktop agent brain. Installed/source copies coordinate through one authoritative runtime owner; ambiguous/unowned shared runtime state fails closed.

## Testing direction

Stage 25.2 browser semantic→vision integration is accepted; do not describe it as the next gate.

Current Stage 26 gates:

1. Stage 26.1B real bounded Windows Capture qualification;
2. Stage 26.1C Windows executor security A/B;
3. F16 Grounder adapter qualification;
4. ChatGPT procedural integration with current-state-first variant-task dogfood;
5. Windows desktop surface product acceptance;
6. human demonstration transfer acceptance;
7. explicit post-desktop public contract decision.

Changing exported Chat actions still requires explicit Refresh/review and fresh ordinary-Chat acceptance.

## Ownership

The repository owns thin integration assets: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, project trust/policy wrappers, focused missing-boundary adapters, tests and project context. It does not own a generic AI gateway, registry, vault, autonomous workflow brain, generic workflow engine or general model-serving platform while qualified upstream components cover those boundaries.

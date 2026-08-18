# Module / Capability Catalog

Status synchronized after merged Stage 25.2, Stage 26 architecture activation and Stage 26.1A OpenAdapt core qualification on 2026-08-18.

This is a **current capability-status catalog**, not a fixed list of future applications. Historical candidate research remains in Git history and dated Stage 23/25 documents.

## Repository-state rule

Resolve live `main` before new work. Stable milestones used for acceptance evidence:

- Stage 25.2 runtime/code baseline: `2a410476ef849fd6d9c172703a004b1befcbcfb1` (#77);
- Stage 26 architecture/context activation: `04dccfd30eb06a82899e2771f6d53ab4c8387128` (#78);
- Stage 26.1A target-tested qualification code: `f8e8f606db845821b8fa24c09f9032015fb0e79e` (#80 branch before docs-only descendants).

Live `main` may be newer because of later integration/docs commits.

## Status meanings

- **PRODUCT-ACCEPTED** — real ordinary-Chat/product path accepted for its scoped contract.
- **ACCEPTED-INFRASTRUCTURE** — accepted internal runtime/lifecycle component; not necessarily public product identity.
- **ACCEPTED-SPECIALIST** — bounded local specialist backend accepted behind a focused internal boundary.
- **QUALIFIED-UPSTREAM** — exact pinned upstream component passed the stated qualification gate but is not yet integrated into the installed product path.
- **ADAPT-CANDIDATE** — upstream mechanism is reusable but project policy/security wrapping remains required.
- **DIAGNOSTIC** — useful internal testing/lifecycle infrastructure, not the promoted Chat-facing contract.
- **ACTIVE-DESIGN** — current architecture/design work, not product-accepted.
- **FUTURE-SCOPED-GATE** — explicit future capability boundary requiring its own measured acceptance.
- **TASK-SELECTED-CANDIDATE** — choose a concrete implementation later from the actual task and evidence.

## Current catalog

| Capability class | Current implementation/direction | Status | Decision |
|---|---|---|---|
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | PRODUCT-ACCEPTED | Normal ordinary-Chat reachability. |
| Public semantic transport | direct stdio secure semantic launcher -> semantic-projection | PRODUCT-ACCEPTED | Normal public path. |
| Internal MCP aggregation/lifecycle | 1MCP lines retained internally | ACCEPTED-INFRASTRUCTURE / DIAGNOSTIC | Useful for diagnostics/adaptive lifecycle; not normal public semantic hop. |
| Windows manager ownership | shared authoritative owner + installed/source coordination | ACCEPTED-INFRASTRUCTURE | One owner; ambiguous/foreign runtime state fails closed. |
| Scoped files | official MCP Filesystem behind semantic projection | PRODUCT-ACCEPTED | `workspace_read` / `workspace_write`; scope/root policy remains explicit. |
| Browser | pinned Playwright MCP behind semantic projection | PRODUCT-ACCEPTED | `web_open` / `web_observe` / `web_interact`. |
| Semantic capability projection | project-owned deterministic five-tool compatibility boundary | PRODUCT-ACCEPTED | Small truthful public surface; not planner/gateway/workflow engine. |
| Local visual grounding | llama.cpp + LFM2.5-VL-450M F16 behind focused vision runtime/grounder | ACCEPTED-SPECIALIST | Stage 25/25.1/25.2 accepted target path; model/runtime remains replaceable. |
| Browser semantic→vision escalation | Stage 25.2 internal fallback inside `web_interact` | PRODUCT-ACCEPTED | Zero-exact-candidate promoted text-labeled miss only; ambiguity/disabled/non-button ABSTAIN without VLM. |
| Procedural compiler + IR | OpenAdapt Flow 1.31.0 `Workflow` / `ProgramGraph` | QUALIFIED-UPSTREAM | ADOPT behind project boundaries; do not build a competing project compiler/IR without a measured blocker. |
| Procedural version/lifecycle | OpenAdapt `SkillLibrary` + learn/teach/regression machinery | ADAPT-CANDIDATE | Reuse upstream internals, but apply project candidate-first trust policy instead of upstream immediate-active bootstrap. |
| Human/desktop recorder candidate | OpenAdapt Capture 1.2.2 + Flow capture adapter | QUALIFIED-UPSTREAM / NEXT TARGET GATE | Exact package install/import passed; Stage 26.1B must prove bounded real Windows capture before adoption. |
| Windows execution candidate | OpenAdapt typed WindowsBackend + in-session agent | ADAPT-CANDIDATE | Typed/guarded/UIA routes exist; legacy arbitrary exec disabled by default; security A/B still required. |
| F16 procedural grounding seam | existing accepted LFM2.5-VL F16 adapted to OpenAdapt `Grounder` protocol | ADAPT-CANDIDATE | Proposal-only local adapter after capture qualification; no new Chat-facing vision tool. |
| Windows desktop surface | productized winning native/typed observation + bounded screen/vision + reviewed keyboard/mouse | FUTURE-SCOPED-GATE | Explicit Stage 26.3. Must not be forgotten or inferred from browser/OpenAdapt qualification. |
| Human demonstration transfer | accepted capture + qualified compiler + project trust policy + variant-task verification | FUTURE-SCOPED-GATE | Stage 26.4; not product-accepted until real demonstration transfer passes. |
| Future local programs/capabilities | implementation chosen from real user task + evidence | TASK-SELECTED-CANDIDATE | No fixed future application list in active roadmap/catalog. |
| Distribution/cockpit reference | OpenAdapt Desktop Tauri/frozen-sidecar/installer patterns | ADAPT-CANDIDATE | Stage 27 reference only; pinned Desktop embeds a different Flow version from qualified runtime. |
| Distribution/maintenance | installer/update/repair/doctor/uninstall/rollback/restart recovery | FUTURE-SCOPED-GATE | Stage 27; evaluate qualified/reusable Desktop patterns before rebuilding equivalents. |

## Current public surface

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

This count is an accepted current contract, not a permanent dogma. The explicit decision point for any expansion is after Windows desktop surface exists and is accepted. Any change then requires a separate ADR, truthful schemas and ordinary-Chat acceptance.

Do not preserve the count by hiding unrelated desktop/workflow operations behind current tool names. Do not add a generic opaque dispatcher as a renamed `tool_invoke`.

## Accepted Stage 25.2 evidence

Accepted Stage 25.2 runtime/code milestone:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

```text
semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true
VISION_RUNTIME_RUNNING_AFTER_TEST = false
CHROME_RUNNING_AFTER_TEST = true
TEST_EXIT_CODE = 0
```

Earlier Stage 25 runtime/model candidate rankings are historical research, not the current path.

## Stage 26 qualified upstream evidence

### Tencent/UI-Mate

Still used as a workflow-guidance reference: rich annotated demonstration trajectory -> compact current-subtask guidance -> live state remains authoritative. UI-Mate is not promoted as the product planner/model.

### OpenAdapt Flow/Capture

Target-tested exact pins:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Qualification-code HEAD:

`f8e8f606db845821b8fa24c09f9032015fb0e79e`.

Real target evidence:

```text
Python 3.12.10
exact installed commit verification = PASS
PHASE_B_PASS=True
PHASE_C_TUTORIAL_PASS=True
PROBE_ERROR=<null>
ERROR=<null>
TEST_EXIT_CODE=0
Chrome process count 15 -> 15
```

Result artifact:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json`

The earlier assumption that Stage 26.1 should first implement project-owned raw schemas/compiler/store has been superseded. Reuse/adapt qualified upstream mechanisms before writing replacements.

## Next capability gate

Stage 26.1B is **real bounded Windows Capture qualification** using a harmless test window. It must prove window scope, click/type/key/scroll evidence, UIA evidence where available, conversion/compile/replay or bounded refusal, zero false/unrelated-window actions, local artifact containment and cleanup.

After that, Stage 26.1C performs the Windows executor security A/B and local F16 Grounder adapter qualification.

## Candidate selection rule for future capabilities

When an actual user task requires a new local capability:

```text
actual task and consequence class
  -> identify deterministic/native/API/MCP/qualified-upstream options
  -> prefer maintained upstream component
  -> scope/reduce surface
  -> target-machine benchmark
  -> security/negative tests
  -> focused project adapter only for measured gap
  -> ordinary-Chat/public-contract review if exported
```

Do not promote a backend merely because it appears in an old catalog or prior conversation.

## Historical evidence note

Older sections/files that discuss Stage 24 semantic projection as experimental, superseded Stage 25 runtime/model candidate lines, a fixed future application list, or a Stage 26 plan that assumes project-owned recorder/compiler/skill-store implementation are historical research. They do not override `START_HERE.md`, `CURRENT_STATE.md`, `STAGE26_1A_OPENADAPT_QUALIFICATION.md`, `STAGE26_PROCEDURAL_MEMORY.md`, `ROADMAP.md` or this synchronized catalog.

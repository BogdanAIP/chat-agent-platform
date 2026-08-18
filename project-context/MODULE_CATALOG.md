# Module / Capability Catalog

Status synchronized after merged Stage 25.2 on 2026-08-18.

This file is a **current capability-status catalog**, not a fixed list of future applications. Historical candidate research remains in Git history and dated Stage 23/25 documents.

## Status meanings

- **PRODUCT-ACCEPTED** — real ordinary-Chat/product path accepted for its scoped contract.
- **ACCEPTED-INFRASTRUCTURE** — accepted internal runtime/lifecycle component; not necessarily public product identity.
- **ACCEPTED-SPECIALIST** — bounded local specialist backend accepted behind a focused internal boundary.
- **DIAGNOSTIC** — useful internal testing/lifecycle infrastructure, not the promoted Chat-facing contract.
- **ACTIVE-DESIGN** — current architecture/design work, not product-accepted.
- **FUTURE-SCOPED-GATE** — explicit future capability boundary requiring its own measured acceptance.
- **TASK-SELECTED-CANDIDATE** — do not preselect now; choose a concrete implementation later from the actual task and evidence.

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
| Procedural memory | raw trajectory + Demo Compiler + skill store/retrieval/progress/verifier design | ACTIVE-DESIGN | Stage 26; non-agentic, coordinate-free skills, current-state-first, evidence-based trust. |
| Windows desktop surface | native/deterministic observation first + bounded screen/vision + reviewed keyboard/mouse | FUTURE-SCOPED-GATE | Explicit Stage 26.3. Must not be forgotten or inferred from browser acceptance. |
| Human demonstration capture | recorder over the future desktop surface + procedural compiler | FUTURE-SCOPED-GATE | Stage 26.4; not honestly available for arbitrary Windows work before desktop surface exists. |
| Future local programs/capabilities | implementation chosen from real user task + evidence | TASK-SELECTED-CANDIDATE | No fixed future application list in the active roadmap/catalog. |
| Distribution/maintenance | installer/update/repair/doctor/uninstall/rollback/restart recovery | FUTURE-SCOPED-GATE | Stage 27. |

## Current public surface

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

This count is an accepted current contract, not a permanent dogma. The explicit decision point for any expansion is after the Windows desktop surface exists and is locally accepted. Any change then requires a separate ADR, truthful schemas and ordinary-Chat acceptance.

Do not preserve the count by hiding unrelated desktop/workflow operations behind current tool names. Do not add a generic opaque dispatcher as a renamed `tool_invoke`.

## Accepted Stage 25.2 evidence

Current `main`:

`2a410476ef849fd6d9c172703a004b1befcbcfb1`.

Final target-tested production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

Target result:

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

Current accepted visual target path is **not** the older LM Studio/large-model candidate line. Earlier candidate rankings belong to historical research files.

## Stage 26 upstream reference

Procedural-memory design is informed by official `Tencent/UI-Mate` pinned during review to:

`d2b2e0aede83eeacfb1bc86f66503acbc4a6738a`.

Relevant upstream mechanics:

- rich annotated demonstration trajectory;
- compact `WorkflowPlan`/`Subtask` runtime;
- current-subtask guidance blocks;
- no coordinate replay in `DemoWorkflow`;
- live/current state as the authoritative execution context.

We do **not** promote UI-Mate's large GUI-agent checkpoint as a required product component. ChatGPT already owns planning/reasoning. We build the smallest non-agentic procedural-memory substrate needed by our architecture.

## Candidate selection rule for future capabilities

When an actual user task requires a new local capability:

```text
actual task and consequence class
  -> identify deterministic/native/API/MCP options
  -> prefer maintained upstream component
  -> scope/reduce surface
  -> target-machine benchmark
  -> security/negative tests
  -> decide focused adapter only for measured gap
  -> ordinary-Chat/public-contract review if exported
```

Do not promote a backend merely because it appears in an old catalog or prior conversation.

## Historical evidence note

Older sections/files that discuss:

- Stage 24 semantic projection as experimental;
- LM Studio as the active Stage 25 manager candidate;
- larger LFM variants as the preferred current path;
- a fixed list/order of future desktop applications;

are historical research and do not override `START_HERE.md`, `CURRENT_STATE.md`, `STAGE26_PROCEDURAL_MEMORY.md`, `ROADMAP.md` or this synchronized catalog.

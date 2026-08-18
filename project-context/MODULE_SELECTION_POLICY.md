# Module Selection Policy

## Product rule

The baseline Chat-to-Local product must work with **zero new mandatory SaaS subscriptions** beyond the user's chosen ChatGPT access. A module/capability must be technically good enough, maintainable, secure enough for its intended scope and economically sane.

## Selection order

1. official/vendor local MCP or mature official local runtime/API;
2. mature open-source MCP/runtime with acceptable license/maintenance;
3. official/vendor local API/CLI behind the smallest focused typed adapter;
4. mature generic local automation/native OS capability as fallback;
5. bounded visual automation where deterministic/native structure is insufficient;
6. paid API/SaaS only for genuinely remote/expensive capabilities explicitly chosen by the user.

Do not implement a custom adapter merely because it is possible. Do not adopt a weak MCP merely because it already exists.

## Mandatory gates

A candidate cannot become supported/default until applicable gates pass:

- **Quality:** reliable enough for the target operation; structured/native API preferred over pixels/coordinates where possible.
- **Cost:** no hidden mandatory recurring SaaS dependency in the baseline path.
- **License:** compatible and recorded.
- **Maintenance:** upstream not clearly abandoned.
- **Security:** scopes/disabled tools/allowlists or another measured containment mechanism exist.
- **Locality/privacy:** local data stays local unless the operation explicitly needs external access.
- **Supply/pinning:** tested published version or immutable source/release pin exists.
- **Evidence:** install/start/health/tool-call/task behavior tested before promotion.
- **Lifecycle:** predictable start/stop/cleanup and no permanent residence unless measured need.
- **Chat admission:** locally healthy capability is not public-product accepted until the actual Chat-facing typed boundary is admitted where required.
- **Recovery:** failure/ABSTAIN/retry/rollback semantics are explicit for consequential operations.

## Task-selected future capabilities

Do **not** maintain a fixed roadmap list of future local programs as if those choices were already architecture decisions.

When an actual user task needs a new capability:

```text
actual task
  -> consequence/scope analysis
  -> native/API/MCP candidates
  -> upstream quality/license/maintenance check
  -> smallest truthful surface
  -> target-machine benchmark
  -> security/negative tests
  -> focused adapter only for a measured gap
  -> public-contract review if exported to Chat
```

Old catalog entries/research conversations are candidate history, not promotion orders.

## Chat-facing typed surface rule

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Adding a backend should normally change local capability implementation/evidence, not create another ChatGPT app/plugin.

Do not expose hundreds of unrelated tools. Prefer concrete truthful semantics. Generic adaptive `tool_schema`/`tool_invoke` remains diagnostic infrastructure, not the ordinary-Chat product surface.

If a focused projection/facade is required, it must:

- expose exact typed operations rather than arbitrary nested dispatch;
- remain small and deterministic;
- preserve scope/consequence boundaries;
- not become planner/workflow brain/general gateway;
- be justified by measured product behavior and acceptance.

The current count of five is not a permanent limit. After Windows desktop surface exists, make an explicit ADR and ordinary-Chat acceptance decision about whether a few new truthful public capabilities are required. Do not overload current tools merely to preserve the count.

## Local specialist model/runtime rule

A local model is a capability backend, not the Chat planner.

Use:

- measured capability match;
- hardware/resource evidence on the actual machine;
- highest-quality tested variant fitting RAM/latency guardrails;
- predictable load/JIT/unload lifecycle;
- replaceable runtime/model identity;
- local-only inference by default where suitable;
- deterministic authorization around model output.

Current accepted target-laptop vision path is llama.cpp + LFM2.5-VL-450M F16 behind the focused Stage 25/25.2 runtime/grounder. Earlier LM Studio/larger-model candidate rankings are historical research and should not be used as current selection policy.

Future model/runtime changes require measured improvement/compatibility evidence.

## Procedural-memory selection rule

Procedural memory is not a replacement for capability selection.

A retrieved skill may say how a task previously succeeded, but:

- it cannot select/authorize a backend by itself;
- current capability scope still applies;
- current observed state outranks remembered milestones;
- one success creates at most a candidate skill;
- completion/promotion require verifier/evidence rules;
- imported/upstream workflows receive no implicit local trust.

Use upstream procedural implementations as references/components only when they fit the ChatGPT-only planner boundary. Do not add a dedicated large local GUI-agent model merely because an upstream reference uses one.

## Windows desktop selection rule

Stage 26.3 desktop surface should prefer:

```text
native/deterministic UI information
  -> focused application API/MCP when task-specific and stronger
  -> bounded screen/vision evidence
  -> reviewed keyboard/mouse fallback
```

The exact implementation/components are selected from real tasks and target-machine evidence when this stage begins.

## Paid layer

Paid services are optional accelerators, never hidden prerequisites.

- no automatic purchase/subscription;
- no unknown-cost execution;
- no paid dependency for ordinary local file/browser/desktop/procedural-memory work when adequate local/open-source capability exists;
- prefer pay-per-use only for genuinely expensive remote work explicitly chosen by the user.

## Adapter rule

When a strong local API exists but no acceptable MCP does, write the smallest useful typed adapter. It must not grow into another planner, workflow engine, generic gateway, secret store, policy platform or bespoke model-serving framework.

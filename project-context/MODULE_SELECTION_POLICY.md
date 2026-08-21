# Module Selection Policy

## Product rule

The baseline Chat-to-Local product must work with **zero new mandatory SaaS subscriptions** beyond the user's chosen ChatGPT access. A module/capability must be good enough, maintainable, secure enough for its intended scope and economically sane.

## Architecture boundary for selection

Candidate components must fit one of these roles rather than blur them:

```text
ordinary ChatGPT
  current general planner / strategy / adaptation

local deterministic Control Plane
  task/procedure state / policy / authorization / checkpoint / verifier / bounded recovery

focused capabilities
  Files / Browser / Windows / future devices/apps

specialist models
  bounded perception or structured proposal only

future local general planner
  optional Track P research only
```

Do not reject useful deterministic state/policy machinery merely because it is called a Control Plane. Do reject components that silently become an unrestricted second general planner or opaque execution gateway.

## Selection order

1. official/vendor local MCP or mature official local runtime/API;
2. mature open-source MCP/runtime/procedural component with acceptable license/maintenance;
3. official/vendor local API/CLI behind the smallest focused typed adapter;
4. mature generic local automation/native OS capability;
5. bounded visual automation where deterministic/native structure is insufficient;
6. paid API/SaaS only for genuinely remote/expensive capabilities explicitly chosen by the user.

Do not implement a custom adapter merely because it is possible. Do not adopt a weak MCP merely because it already exists.

## Mandatory gates

A candidate cannot become supported/default until applicable gates pass:

- **Quality:** reliable enough for the intended operation;
- **Cost:** no hidden mandatory recurring SaaS dependency in the baseline path;
- **License:** compatible and recorded;
- **Maintenance:** upstream not clearly abandoned;
- **Security:** scopes/allowlists/negative tests or another measured containment mechanism exist;
- **Locality/privacy:** local data stays local unless the operation explicitly requires external access;
- **Supply/pinning:** tested version/source/release pin exists;
- **Evidence:** install/start/health/task behavior tested before promotion;
- **Lifecycle:** predictable start/stop/cleanup;
- **Chat admission:** public Chat capability changes require real Chat-facing acceptance where applicable;
- **Recovery:** failure/ABSTAIN/retry/rollback semantics are explicit;
- **Authority:** model/procedure/planner output cannot directly bypass deterministic capability authorization.

## Task-selected future capabilities

Do not maintain a fixed permanent future application list.

```text
actual task
 -> consequence/scope analysis
 -> native/API/MCP/qualified-upstream candidates
 -> quality/license/maintenance check
 -> smallest truthful surface
 -> target-machine benchmark
 -> security/negative tests
 -> focused adapter for measured gap only
 -> public-contract review if exported
```

Old research/catalog entries are candidate history, not promotion orders.

## Chat-facing typed surface

Current accepted public tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Adding a backend should normally change local implementation/evidence rather than require another ChatGPT app/plugin.

Do not expose hundreds of raw tools. Generic adaptive `tool_schema`/`tool_invoke` remains diagnostic infrastructure, not the ordinary-Chat product surface.

A focused projection/facade must be deterministic, typed, scope-preserving and non-planning.

The current count of five is not permanent. A later ADR may add truthful desktop/procedure capabilities. Never overload current tools merely to preserve the count.

## Deterministic Control Plane selection rule

Stage 26.3 needs a local deterministic execution Control Plane, but the project should still reuse upstream mechanisms rather than build a generic workflow platform.

Prefer:

```text
qualified ProgramGraph / procedural IR
 + project-owned thin TaskState
 + project-owned consequence/scope policy
 + accepted capability authorization
 + project-owned checkpoint/recovery/budget state
 + accepted/expanded verifier
```

A Control Plane component is acceptable when it deterministically advances predeclared state transitions. It is not acceptable if it becomes an arbitrary LLM workflow brain, unrestricted tool dispatcher or hidden general scheduler with self-granted authority.

## Local specialist model/runtime rule

A specialist model is a capability backend, not the current general planner.

Use measured capability match, target hardware/resource evidence, predictable load/unload, replaceable identity, local-only inference where suitable and deterministic authorization around output.

Current accepted target vision path is llama.cpp + LFM2.5-VL-450M F16. Future specialist model changes require measured improvement/compatibility evidence.

## Procedural-memory selection rule

Procedural memory is not a replacement for capability policy.

A selected procedure may drive deterministic progression after ChatGPT chooses it, but:

- procedure selection is non-authorizing;
- every transition uses current capability scope;
- current state outranks remembered milestones;
- one success creates at most a CANDIDATE;
- promotion requires replay/regression/variant evidence;
- completion requires verifier/postcondition evidence;
- imported/upstream workflows receive no implicit local trust.

Use OpenAdapt Flow/Capture mechanics where qualified; do not add a dedicated large local GUI-agent model merely because another project uses one.

## Windows desktop rule

The desktop foundation is already accepted through Stage 26.2D. For new Windows application/capability work prefer:

```text
native/deterministic UI/API evidence
 -> focused application API/MCP when stronger
 -> bounded local screen/vision evidence
 -> reviewed guarded keyboard/mouse fallback
```

Stage 26.2E is the real-app gate. Stage 26.3 integrates procedure progression/control-plane state, not the first Windows desktop surface.

## Future local planner selection rule — Track P

A future local general planner must not be chosen from model marketing or parameter count.

Earliest prerequisites:

- verified procedure-state data from 26.3/26.4;
- a measured need such as offline operation, planning latency, parallelism or deployment/privacy constraints;
- a benchmark baseline against ordinary ChatGPT manager behavior.

Promotion order:

```text
P0 shadow/proposal-only
 -> P1 explicitly bounded subtask planner
 -> P2 optional local general-planner mode
```

At every phase the deterministic Control Plane remains authoritative for capability policy, action authorization and verification.

Measure task completion, false-action proposal rate, recovery quality, escalation rate, latency/RAM and comparable task/action/compute budgets where practical.

## Paid layer

Paid services are optional accelerators, never hidden prerequisites. No automatic purchase/subscription, unknown-cost execution or paid requirement for ordinary local files/browser/desktop/procedural work when adequate local/open-source capability exists.

## Adapter rule

When a strong local API exists but no acceptable MCP does, write the smallest useful typed adapter. It must not grow into another general planner, generic gateway, unrestricted workflow engine, secret store or bespoke model-serving framework.

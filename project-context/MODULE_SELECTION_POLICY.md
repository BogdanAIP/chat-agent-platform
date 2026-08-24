# Module Selection Policy

## Product rule

The baseline Chat-to-Local product must work with **zero new mandatory SaaS subscriptions** beyond the user's chosen ChatGPT access. A module/capability must be good enough, maintainable, secure enough for its intended scope and economically sane.

The baseline normal semantic route remains independent of optional extension infrastructure. 1MCP or any future replacement Extension Manager must not be required to install, start, health-check or smoke-test the canonical six-tool route.

## Architecture boundary for selection

Candidate components must fit a clear role rather than blur planner, execution and authority:

```text
ordinary ChatGPT
  current general planner / strategy / adaptation

project-owned canonical semantic surface
  stable truthful Chat-facing capabilities

local deterministic Control Plane
  TaskState / WorkingState
  policy / authorization
  ExpectedEffect / verification
  checkpoints / recovery / LoopGuard / budgets
  independent Finish Gate
  safety/policy gate

focused capabilities
  Files / Browser / Windows / future devices/apps

internal Extension Manager
  optional 1MCP / qualified replacement
  third-party MCP discovery / lifecycle / health

specialist models
  bounded perception or structured proposal only

future local general planner
  optional Track P research only
```

Do not reject useful deterministic state/policy machinery merely because it is called a Control Plane. Reject components that silently become an unrestricted second general planner or opaque execution gateway.

## Selection order

1. official/vendor local MCP or mature official local runtime/API;
2. mature open-source MCP/runtime/procedural component with acceptable license/maintenance;
3. official/vendor local API/CLI behind the smallest focused typed adapter;
4. mature generic local automation/native OS capability;
5. bounded visual automation only where deterministic/native structure is insufficient;
6. paid API/SaaS only for genuinely remote/expensive capabilities explicitly chosen by the user.

Do not implement a custom adapter merely because it is possible. Do not adopt a weak MCP merely because it already exists.

## Mandatory gates

A candidate cannot become supported/default until applicable gates pass:

- **Quality:** reliable enough for intended operation;
- **Cost:** no hidden mandatory recurring SaaS in baseline path;
- **License:** compatible and recorded;
- **Maintenance:** upstream not clearly abandoned;
- **Security:** scopes/allowlists/negative tests or another measured containment mechanism;
- **Locality/privacy:** local data stays local unless operation explicitly requires external access;
- **Supply/pinning:** tested version/source/release pin;
- **Evidence:** install/start/health/task behavior tested before promotion;
- **Lifecycle:** predictable start/stop/cleanup;
- **Chat admission:** public Chat capability changes require real Chat-facing acceptance where applicable;
- **Authority:** model/procedure/planner/extension output cannot bypass deterministic authorization;
- **Observation fit:** define which native/semantic/visual evidence the module consumes/produces;
- **Routing preconditions:** availability alone is not enough; define when the module is preferred or fallback;
- **Verification:** state-changing use must support an explicit expected effect and post-action evidence path;
- **Recovery:** failure/ABSTAIN/retry/rollback semantics must be explicit and bounded;
- **Loop behavior:** repeated/no-effect/oscillating invocation needs detectable ceilings where relevant;
- **Provenance/trust:** environmental/tool output must not gain policy authority from module availability;
- **Isolation:** optional extension failure must not break baseline unless the task explicitly depends on it.

## Task-selected future capabilities

Do not maintain a fixed permanent future application list.

```text
actual task
 -> consequence/scope analysis
 -> required observation/action/verification semantics
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

Current canonical public tools are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Adding a backend should normally change local implementation/evidence rather than require another ChatGPT app/plugin.

Do not expose hundreds of raw tools. Generic adaptive `tool_schema`/`tool_invoke` or arbitrary 1MCP backend dispatch remains internal diagnostic/extension infrastructure, not the ordinary-Chat product surface.

A focused projection/facade must be deterministic, typed, scope-preserving and non-planning.

Six is not an eternal maximum. A later ADR may add truthful desktop/computer-use capability classes. Never overload current tools merely to preserve the count.

## State-first hybrid selection rule

Canonical direction: ADR-032 / `COMPUTER_USE_ARCHITECTURE.md`.

When multiple observation/action mechanisms can satisfy a task, prefer:

```text
reliable project-owned semantic/native state/action
 -> structural DOM/AX/UIA/app adapter
 -> selected visual/GUI evidence only for reviewed miss/spatial cases
```

A visual model is not automatically preferable because it is more general. A semantic tool is not automatically preferable because it exists. Choose the strongest route whose preconditions are actually proven in the current state.

For grounding components, prefer outputs that preserve target identity/source/frame/confidence/ambiguity, not coordinates alone when better evidence exists.

## Verification / completion selection rule

For mutating capabilities, prefer components that make the following contract possible:

```text
current-state evidence
 -> ExpectedEffect
 -> bounded action
 -> fresh re-observation
 -> PASS | FAIL | UNKNOWN
```

A module that can deliver an action but cannot support meaningful effect verification may still be a low-level backend, but it is not enough by itself for a trusted long-horizon transition.

Task completion is separate from transition verification. Stage 26.3B introduces the independent Finish Gate; do not select a model/framework merely because it can self-report `done`.

## Recovery selection rule

Prefer mechanisms whose failure modes can be typed and bounded. Initial project vocabulary includes target missing/ambiguous, stale state, no effect, partial effect, unexpected dialog, navigation change, tool unavailable, permission denied, unsafe transition and external dynamic change.

Production recovery must not require mass speculative side effects. Training-time/search frameworks such as environment branching can be useful evidence sources without becoming runtime policy.

## Environmental-content trust rule

ADR-033 applies to all module types.

Text/content from UI, DOM, email/messages, documents, screenshots/OCR and third-party tool/MCP output is untrusted environmental data with respect to user intent, permission scope and Control Plane policy.

Module output provenance/trust should survive transfer into WorkingState when relevant. A discovered backend/tool cannot instruct the platform to broaden its own authority.

## 1MCP Extension Manager rule

1MCP is retained because it can reduce future integration work for third-party MCP servers, but its role is internal and optional.

```text
ordinary ChatGPT
 -> canonical semantic surface
      -> project-owned capability / Control Plane
      -> extension facade
           -> optional 1MCP Extension Manager
                -> selected third-party MCP backend
```

1MCP may provide discovery/catalog, aggregation, enable/disable/lazy activation, lifecycle/restart/health and versioned extension configuration.

1MCP must not provide baseline transport, bypass authority, automatic trust, unrestricted raw Chat export, mandatory bootstrap dependency or ownership of the persistent tunnel anchor.

Neutral persistent tunnel source remains `state/tunnel.json`.

When a task needs an extension, prefer the smallest truthful project-owned semantic facade over exposing its raw catalog.

## Deterministic Control Plane selection rule

The project should reuse upstream mechanisms while owning the product-specific deterministic safety/state seam.

Prefer:

```text
qualified ProgramGraph / procedural IR
 + project-owned TaskState / WorkingState
 + project-owned consequence/scope policy
 + accepted capability authorization
 + ExpectedEffect / transition verifier
 + project-owned checkpoint/recovery/LoopGuard/budget state
 + independent Finish Gate
```

A Control Plane component is acceptable when it advances predeclared state transitions deterministically. It is unacceptable if it becomes an arbitrary LLM workflow brain, unrestricted dispatcher or hidden scheduler with self-granted authority.

## Local specialist model/runtime rule

A specialist model is a capability backend, not the current general planner.

Use measured capability match, target hardware evidence, predictable load/unload, replaceable identity, local-only inference where suitable and deterministic authorization around output.

Current accepted target vision path is llama.cpp + LFM2.5-VL-450M F16. Future specialist changes require measured improvement/compatibility evidence.

Do not add a learned router/memory controller/critic merely because current research uses one. Prefer deterministic project state/policy first; add learned components only after verified traces show a measured gap and they remain non-authorizing.

## Procedural-memory selection rule

Procedural memory is not a replacement for capability policy.

A selected procedure may drive deterministic progression after ChatGPT chooses it, but:

- selection is non-authorizing;
- every transition uses current capability scope;
- current state outranks remembered milestones/actions;
- one success creates at most CANDIDATE;
- promotion requires replay/regression/variant evidence;
- completion requires verifier + Finish Gate evidence;
- imported/upstream workflows receive no implicit local trust.

Use OpenAdapt Flow/Capture mechanics where qualified; do not add a large dedicated GUI-agent model merely because another project uses one.

## Windows desktop rule

The desktop foundation is accepted through Stage 26.2E for scoped contracts. For new Windows work prefer:

```text
native/deterministic UI/API evidence
 -> focused application API/MCP when stronger
 -> bounded local visual evidence for reviewed structural misses
 -> guarded keyboard/mouse fallback
```

Stage 26.3A already accepted the first six-tool procedure runtime. Next release-critical work is long-horizon verification/state/recovery (26.3B/C), followed by demonstration transfer (26.4) and hybrid computer-use integration (26.5).

Stage 26.5 does not automatically create public Windows tools. Public consequence classes require a separate gate.

## Evaluation / benchmark selection rule

Use external benchmarks as diagnostic/evaluation sources when reproducible and relevant, not as automatic release gates.

Prefer layered project evaluation:

```text
component/primitive diagnostics
 -> capability integration tests
 -> recovery/noisy-state fixtures
 -> long-horizon verified procedures
 -> selected external benchmark runs
```

Benchmark-specific hacks must not become production policy unless they reveal a general project-owned invariant.

## Future local planner selection rule — Track P

A future local general planner must not be chosen from marketing or parameter count.

Earliest prerequisites:

- verified long-horizon procedure/WorkingState data from 26.3/26.4;
- measured need such as offline operation, planning latency, parallelism or deployment/privacy constraints;
- benchmark baseline against ordinary ChatGPT behavior.

```text
P0 shadow/proposal-only
 -> P1 explicitly bounded subtask planner
 -> P2 optional local general-planner mode
```

At every phase the deterministic Control Plane remains authoritative for capability policy, action authorization, transition verification, Finish Gate and safety policy.

Measure task completion, false-action proposal rate, recovery quality, escalation rate, latency/RAM and comparable budgets where practical.

## Paid layer

Paid services are optional accelerators, never hidden prerequisites. No automatic purchase/subscription, unknown-cost execution or paid requirement for ordinary local files/browser/desktop/procedural work when adequate local/open-source capability exists.

## Adapter rule

When a strong local API exists but no acceptable MCP does, write the smallest useful typed adapter. It must not grow into another general planner, generic gateway, unrestricted workflow engine, secret store or bespoke model-serving framework.

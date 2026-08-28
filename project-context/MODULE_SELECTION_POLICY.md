# Module Selection Policy

Status: **AUTHORITATIVE MODULE-SELECTION POLICY**.

## Product rule

The baseline Chat-to-Local product must work with **zero new mandatory SaaS subscriptions** beyond the user's chosen ChatGPT access.

A module/capability must be good enough, maintainable, secure enough for intended scope, economically sane and compatible with the project's authority/verification model.

Normal six-tool semantic operation must remain independent of optional Extension Manager infrastructure.

## Architecture boundary for selection

```text
ordinary ChatGPT
  current general planner / strategy / novel adaptation

project canonical semantic surface
  small truthful Chat-facing capabilities

project deterministic Control Plane
  TaskState / WorkingState
  policy / authorization
  ExpectedEffect / Verification Kernel
  reconciliation / recovery / LoopGuard / budgets
  independent Finish Gate

focused capabilities
  Files / Browser / Windows / future apps/devices/session adapters

optional Extension Manager
  third-party MCP discovery/lifecycle/health only

specialist models
  bounded perception / structured proposal evidence only
```

Reject components that silently become an unrestricted second planner, opaque generic dispatcher or alternate completion authority.

## Selection order

1. official/vendor local MCP/runtime/API;
2. mature open-source MCP/runtime/procedural component with acceptable license/maintenance;
3. official/vendor local API/CLI behind the smallest focused typed adapter;
4. mature generic local automation/native OS capability;
5. bounded visual automation where deterministic/native structure is insufficient;
6. paid API/SaaS only for genuinely remote/expensive capabilities explicitly chosen by the user.

Do not implement a custom adapter merely because it is possible. Do not adopt a weak existing MCP merely because it exists.

## Architecture lineage gate

When `stage-research` applies or a proposal may duplicate/replace/cross a previously selected role, read `ARCHITECTURE_REUSE_BASELINE.md` before choosing a solution.

For each affected role, research must explicitly decide:

```text
KEEP
REUSE_MORE
REFINE
REPLACE
DEFER
REJECT
```

Custom code must answer why the selected upstream mechanics do not already solve that role. External reuse must answer why it does not cross a deliberately project-owned authority/state boundary.

Newness/popularity is not evidence for `REPLACE`/`REJECT`.

## Mandatory promotion gates

A candidate cannot become supported/default until applicable gates pass:

- **Quality** — reliable for intended operation;
- **Cost** — no hidden mandatory recurring SaaS in baseline;
- **License** — compatible and recorded;
- **Maintenance** — upstream not clearly abandoned or risk is explicitly accepted;
- **Security** — scoped capability/negative tests/containment;
- **Locality/privacy** — local data remains local unless operation explicitly requires external access;
- **Supply/pinning** — tested version/source/release pin;
- **Evidence** — install/start/health/task behavior tested before promotion;
- **Lifecycle** — predictable start/stop/cleanup/recovery;
- **Chat admission** — public Chat capability changes require real Chat-facing acceptance where applicable;
- **Authority** — model/procedure/planner/extension output cannot bypass deterministic authorization;
- **Observation fit** — define native/semantic/visual evidence consumed/produced;
- **Routing preconditions** — availability alone is not route selection;
- **Verification** — mutations support explicit expected effect + fresh evidence path;
- **Recovery/reconciliation** — retry/unknown/rollback semantics explicit and bounded;
- **Loop behavior** — repeated/no-effect/oscillating invocation has ceilings where relevant;
- **Provenance/trust** — environmental/tool/worker output cannot gain policy authority from module availability;
- **Isolation** — optional extension failure does not break baseline unless current task depends on it.

## Stage Research depth for new mechanisms

A real problem does not prove a particular mechanism is the right solution.

For material persistence/recovery/retry/concurrency/identity/security/authority changes:

- enumerate introduced architecture primitives;
- research the mature engineering domain that directly studies each primitive;
- separate problem evidence from solution evidence;
- compare materially distinct approaches;
- build failure/crash matrix for consequence-bearing boundaries;
- re-enter research if implementation later introduces an uncovered material primitive.

`NARROW` narrows implementation scope, not research depth. `DEFER` keeps production implementation blocked.

## Task-selected future capabilities

Do not maintain a permanent app/provider list as architecture truth.

```text
actual task
 -> consequence/scope analysis
 -> required observation/action/verification semantics
 -> current baseline role check
 -> native/API/MCP/qualified-upstream candidates
 -> quality/license/maintenance evidence
 -> smallest truthful surface
 -> target benchmark / negative tests
 -> focused adapter for measured gap
 -> public-contract review if exported
```

## Chat-facing typed surface

Current canonical tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Adding a backend should normally change internal implementation/evidence rather than require another ChatGPT app/plugin.

Do not expose hundreds of raw tools. Generic `tool_schema`/`tool_invoke`, arbitrary 1MCP dispatch or unrestricted backend selectors remain internal/unaccepted.

Six is not an eternal maximum; later consequence classes may gain truthful public semantics after their own review/acceptance.

## State-first hybrid selection

When multiple routes could satisfy a task:

```text
reliable project-owned semantic/native state/action
 -> structural DOM/AX/UIA/app adapter
 -> selected visual/GUI evidence only for reviewed miss/spatial cases
```

Choose the strongest route whose preconditions are actually proven **now**.

For grounding, prefer target identity/source/frame/confidence/ambiguity over coordinates alone when stronger evidence exists.

## Verification / completion selection

For mutating capabilities prefer mechanisms that support:

```text
current-state evidence
 -> ExpectedEffect
 -> bounded action
 -> fresh re-observation
 -> PASS | FAIL | UNKNOWN
```

Stage 26.3B accepted the shared Verification Kernel + independent Finish Gate foundation for the recorded representative scope. A new module cannot replace these project semantics merely because it self-reports successful action/task completion.

Task completion remains separate from transition verification.

## Recovery/reconciliation selection

Prefer mechanisms whose failure modes can be typed and bounded.

For ambiguous consequence delivery, selection must support stable logical operation identity and fresh reconciliation before unsafe retry. Do not accept “retry until success” as a production recovery design.

A persistence/retry component that claims exactly-once external effects must provide direct evidence for the exact failure model; internal transactionality alone is not enough.

## Environmental-content trust

Text/content from UI, DOM, messages, documents, screenshots/OCR, tool/MCP/worker output is untrusted environmental data with respect to user intent, permission scope and Control Plane policy.

Module output provenance/trust should survive transfer into WorkingState. A discovered backend/tool cannot instruct the platform to broaden its own authority.

## Optional Extension Manager

1MCP is retained because it may reduce future integration work for third-party MCP servers:

```text
ordinary ChatGPT
 -> canonical semantic surface
      -> project capability / Control Plane
      -> focused extension facade
           -> optional Extension Manager
                -> selected third-party MCP backend
```

It may own discovery/catalog, enable/disable, lazy activation, lifecycle/restart/health and aggregation.

It must not own baseline transport, automatic trust, unrestricted public export, action authorization or persistent tunnel identity.

## Deterministic Control Plane selection

Reuse upstream mechanics while owning the product-specific safety/state seam.

Preferred composition:

```text
qualified procedure/native mechanics where useful
 + project WorkingState
 + project consequence/scope policy
 + project authorization
 + ExpectedEffect / Verification Kernel
 + project reconciliation/LoopGuard/budgets
 + independent Finish Gate
```

A component is unacceptable if it becomes an arbitrary LLM workflow brain, unrestricted dispatcher or hidden scheduler with self-granted authority.

## Local specialist models

A specialist model is a capability backend, not current general planner.

Select on measured capability match, target-hardware evidence, predictable load/unload, replaceability, locality/privacy and deterministic authorization around its output.

Do not add a learned router/memory controller/critic merely because research uses one. Add learned mechanisms only after verified traces show a measured gap and keep them non-authorizing.

## Procedural memory / external execution reuse

Procedural memory is not capability policy. One demo/success creates at most a CANDIDATE.

OpenAdapt may provide selected compile/IR/replay/checkpoint/effect-evidence/capture mechanics where fresh Stage Research confirms fit. UFO/UFO² may provide selected Windows/Office mechanics.

Neither may replace project WorkingState, authorization, Verification Kernel, recovery policy or Finish Gate.

Detailed selected-role lineage lives in `ARCHITECTURE_REUSE_BASELINE.md`; detailed OpenAdapt/UFO rationale in `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`.

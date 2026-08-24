# Development Principles

## 1. ChatGPT is the current general planner; local execution may be autonomous within known transitions

Ordinary ChatGPT owns open-ended task interpretation, strategy, procedure selection and novel-state adaptation.

Do not add another **current general planner** or autonomous workflow brain that competes with ChatGPT.

A deterministic local execution Control Plane is explicitly desired. It may maintain TaskState/WorkingState, procedure state, policy/authorization, ExpectedEffect/postconditions, checkpoints, typed recovery/LoopGuard, budgets and an independent Finish Gate. Once ChatGPT selects a bounded procedure, the Control Plane may advance known transitions without a ChatGPT round trip after every action.

Unknown/ambiguous/stale/incompatible state or a need for new strategy -> ABSTAIN/escalate to ChatGPT.

See `CONTROL_PLANE.md` and `COMPUTER_USE_ARCHITECTURE.md`.

## 2. Off-the-shelf first

For transport, MCP runtime, procedural IR/compiler, capture and common integrations, use maintained ecosystem components before writing project code.

```text
official/vendor
 -> mature OSS
 -> mature local API/CLI
 -> smallest project-owned focused adapter/policy seam
```

Do not build a custom generic gateway/broker/model runtime/agent framework when qualified upstream mechanisms cover the need.

## 3. Evidence before architecture claims

A component/mechanism becomes accepted only after applicable evidence.

Distinguish:

- external research evidence;
- synthetic policy/contract tests;
- hosted CI;
- target-machine physical evidence;
- one successful trajectory;
- compiled candidate procedure;
- verified/promoted reusable procedure.

Research can justify a **direction**, not silently create runtime acceptance. External benchmark results are evidence inputs, not automatic project release gates.

## 4. Thin project-owned surface, but own the product safety seam

Allowed project code should normally be:

- lifecycle/configuration integration;
- deterministic compatibility adapters;
- acceptance/security tests;
- focused TaskState/WorkingState/procedure schemas;
- capability policy/authorization wrappers;
- ExpectedEffect/verifier/Finish Gate logic;
- checkpoint/typed recovery/LoopGuard/budget state machines;
- privacy/provenance/trust wrappers around upstream mechanics.

Do not rebuild generic tunnels, MCP gateways, registries, vaults, databases, job platforms, autonomous agent frameworks or model-serving stacks without measured need.

A focused deterministic Control Plane is allowed because it is the integration/safety boundary; it must not grow into an open-ended planner.

## 5. Stable truthful typed capability boundary

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Six is the current proven contract, not a permanent dogma. Do not preserve it by hiding unrelated native desktop/computer-use consequences in existing web semantics or behind opaque generic dispatch.

`semantic-projection` remains a truthful deterministic compatibility layer, not the procedure Control Plane.

A future public Windows/computer-use surface needs a separate ADR/schema/security/ordinary-Chat physical gate.

## 6. State-first, selective vision

When reliable structural/native state exists, use it before pixels:

```text
semantic/native/app state
 -> DOM / AX / UIA
 -> selected screenshot/ROI only for reviewed structural miss,
    spatial requirement or independent visual check
```

Do not build screenshot-only control as the normal loop merely because a VLM can consume it.

Pixels/model output remain evidence, not authority.

## 7. Capability availability is not route selection

A backend/tool being installed or callable does not mean it should be used.

Capability routing should follow reviewed preconditions/evidence:

```text
exact safe semantic/native route available
 -> use it

structure insufficient for a reviewed case
 -> selected visual/GUI route

ambiguous/high-consequence result
 -> stronger evidence or ABSTAIN
```

Do not expose hundreds of raw tools and ask the planner to solve routing through tool-name choice alone.

## 8. Security enables controlled capability

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure trust lifecycle:

```text
CANDIDATE -> VERIFIED/TRUSTED -> stale/quarantine/disable/rollback
```

These are separate. A trusted procedure, extension output or planner proposal is not blanket action authorization.

Prefer scoped/reversible resources and explicit rollback. Consequential actions require consequence-appropriate policy, not universal confirmation for every harmless operation.

## 9. Environmental content is data, not authority

Content observed in pages/DOM, application UI, email/messages, files/documents, screenshots/OCR and third-party tool/MCP output is untrusted environmental data with respect to user intent, permission scope and Control Plane policy.

Preserve provenance/trust classification when facts cross capability/application boundaries.

A model reading an instruction inside the environment does not promote it above user/system/project policy.

## 10. Current state beats memory

```text
current observed state
 > current completion criteria / subtask goal
 > trusted procedure/demo evidence
 > historical low-level action sequence
```

When memory/demo/history conflicts with live state, re-resolve, use a predeclared safe recovery branch or ABSTAIN/escalate.

Blind historical absolute-coordinate replay is never the reusable solution.

## 11. Every mutation has an expected effect

For every state-changing transition:

```text
observe
 -> bind ExpectedEffect
 -> authorize one bounded action
 -> deliver
 -> fresh re-observe
 -> verify PASS | FAIL | UNKNOWN
```

Delivery receipts are not success. `UNKNOWN` never silently advances.

## 12. Transition verification is not task completion

A successful transition may leave the task incomplete.

Planner/model/procedure may propose:

```text
candidate_done
```

Only an independent Finish Gate may produce verified `DONE` from fresh task-level predicates.

Task-success and safety/policy verification remain separate dimensions.

## 13. Recovery is typed and loop-bounded

Do not implement recovery as unstructured `retry until it works`.

Use typed failure classes and a bounded ladder:

```text
re-observe
 -> re-resolve
 -> retry only with new evidence
 -> alternate already-admitted modality
 -> predeclared local recovery
 -> ChatGPT replan / clarification / ABSTAIN
```

LoopGuard must detect repeated no-effect state/action fingerprints, oscillation, exhausted budgets and absent verified progress.

## 14. Working memory is structured operational state

WorkingState may preserve:

```text
user constraints
subgoals/progress
verified completed achievements
facts + provenance + freshness
open ambiguities
evidence references
expected/observed deltas
recovery history
budgets
```

Do not replay unbounded screenshots/actions by default.

Never persist private chain-of-thought.

## 15. Procedural memory has a privacy/trust boundary

A human demonstration or successful trajectory creates at most CANDIDATE.

Persist only structured/user-visible goal/subtask/evidence/action/result/provenance needed for operation/debugging/reuse. Before long-term arbitrary demo storage, define screenshot/text retention, secret filtering, redaction, deletion, encryption and sync/export rules.

Compiled procedure guidance is advisory until current-state authorization and verification. Historical coordinates never grant authority.

## 16. No sunk-cost architecture

Git history is the archive. Historical documents/results remain evidence but old `current`/`next` wording must not override current authoritative context.

At architecture-changing points audit entry/overview/governance docs, not only add another handoff.

## 17. Cost discipline

Prefer local/free/open-source components where quality is adequate. Do not introduce mandatory paid model APIs or extra SaaS when ordinary ChatGPT + local bridge satisfies the baseline.

Future local planner research requires measured offline/latency/parallel/deployment benefit, not novelty.

## 18. Hardware-aware local models

Use measured target-machine RAM/latency/quality, not parameter-count assumptions.

Current accepted vision path is llama.cpp + LFM2.5-VL-450M F16. Future specialist/model changes require target evidence.

## 19. Windows capability is accepted through 26.2E; long-horizon correctness comes before broadening authority

Accepted sequence:

```text
26.2A production Windows runtime
26.2B DesktopState
26.2C native Grounder
26.2D structure-first UIA -> vision routing
26.2E isolated real application E2E
26.3A verified six-tool procedure runtime
26.3B Verification Kernel + Finish Gate
26.3C WorkingState + typed recovery + LoopGuard
26.4 Human Demo transfer
26.5 Hybrid Computer-Use Integration
```

Do not treat Stage 26.5 as permission to add raw desktop tools. Public computer-use semantics require separate acceptance.

## 20. Control Plane is not the Windows manager

Manager/tray owns lifecycle/configuration/diagnostics.

The procedure Control Plane owns task/procedure execution state, authorization, verification, recovery, budgets and finish state. Keep these responsibilities separate.

Likewise `CONTROL_PLANE_API_KEY` for the OpenAI tunnel is credential terminology and not the project's deterministic execution Control Plane.

## 21. Acceptance ownership and continuation discipline

Use ordinary ChatGPT + GitHub + project local/connected tools under the current operating constraint. Do not use Codex or ChatGPT Work unless the user explicitly re-enables them.

Reserve user participation for irreducible target-machine or ordinary-Chat UI gates.

Never claim physical evidence unless that exact path ran. Never invent measurement counters.

## 22. Context transfer is a development requirement

A fresh ordinary ChatGPT session should be able to determine:

- live `main` and active PR/head;
- what is physically accepted;
- current release-critical stage;
- public semantic contract;
- Control Plane vs planner boundary;
- state-first/verification/WorkingState/LoopGuard/Finish Gate direction;
- environmental-content trust boundary;
- future Track P status;
- historical docs that must not override current state.

Keep `CONTINUATION_CONTEXT.md`, `START_HERE.md`, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `COMPUTER_USE_ARCHITECTURE.md`, `SECURITY_POLICY.md`, `ROADMAP.md` and `DOCUMENT_STATUS.md` synchronized.

## 23. Future local planner is research, not a forbidden concept

Do not erase the local planner from long-term design. Track it explicitly as optional Track P after verified long-horizon state data and measured need exist.

Research starts shadow/proposal-only and benchmarks against ordinary ChatGPT with comparable task/action/compute budgets where practical. Even a future planner remains behind deterministic capability authorization, transition verifier, Finish Gate and safety boundaries.

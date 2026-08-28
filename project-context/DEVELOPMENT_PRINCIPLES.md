# Development Principles

Status: **CURRENT DEVELOPMENT PRINCIPLES**. `AGENTS.md` is the authoritative process/merge entry when wording differs.

## 1. ChatGPT is the current general planner; bounded local execution may continue autonomously

Ordinary ChatGPT owns open-ended goal interpretation, strategy, procedure selection and novel-state adaptation.

The deterministic local Control Plane may maintain TaskState/WorkingState, procedure state, policy/authorization, ExpectedEffect verification, reconciliation/recovery/LoopGuard/budgets and independent Finish Gate state.

Once ChatGPT selects a bounded procedure/effect, known verified transitions may advance without a ChatGPT round trip after every low-level action.

Unknown/ambiguous/stale/incompatible state or need for a new strategy -> ABSTAIN/escalate.

## 2. Off-the-shelf first

For transport, MCP runtime, procedural IR/compiler, capture and common integrations:

```text
official/vendor
 -> mature OSS
 -> mature local API/CLI
 -> smallest project-owned focused adapter/policy seam
```

Do not build a custom generic gateway/broker/model runtime/agent framework when qualified upstream mechanisms cover the role.

## 3. Compare new work with prior reuse lineage

When `stage-research` applies or work may duplicate/replace/cross a previously selected role, read `ARCHITECTURE_REUSE_BASELINE.md`.

Explicitly decide `KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT` for affected roles. Newness is not evidence for replacement; project-owned authority boundaries must not be delegated silently.

## 4. Evidence before architecture claims

Distinguish:

- external research evidence;
- deterministic/unit/state-machine tests;
- hosted CI/security;
- target-machine/ordinary-Chat physical evidence;
- one successful trajectory;
- candidate procedure/skill;
- verified/promoted reusable procedure/skill.

Research can justify direction, not silently create runtime acceptance.

## 5. Research mechanisms, not only problems

For material persistence/recovery/retry/concurrency/identity/security/authority work:

- enumerate architecture primitives;
- research the engineering domain that studies each primitive directly;
- separate problem evidence from solution evidence;
- compare materially distinct alternatives;
- build failure/crash matrix for consequence-bearing boundaries;
- re-enter research when implementation introduces a materially new uncovered primitive.

`NARROW` reduces implementation scope, not research depth. `DEFER` keeps production implementation blocked.

## 6. Thin project-owned surface, own the safety seam

Allowed project code should normally be focused:

- lifecycle/config integration;
- deterministic compatibility adapters;
- capability policy/authorization;
- TaskState/WorkingState/procedure schemas;
- ExpectedEffect/Verification Kernel/Finish Gate;
- checkpoint/reconciliation/recovery/LoopGuard/budgets;
- acceptance/security/privacy/provenance wrappers around upstream mechanics.

Do not rebuild generic tunnels, MCP gateways, registries, vaults, databases, job platforms, autonomous agent frameworks or model-serving stacks without measured need.

## 7. Stable truthful typed public boundary

Current public tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Six is the current accepted contract, not permanent dogma. Never preserve it by hiding unrelated desktop/session/project/local-code consequences behind existing semantics or opaque dispatch.

`semantic-projection` is a deterministic compatibility layer, not planner/Control Plane.

## 8. State-first, selective vision

```text
semantic/native/app state
 -> DOM / AX / UIA
 -> selected screenshot/ROI only for reviewed structural miss,
    spatial requirement or independent visual check
```

Pixels/model output remain evidence, never authority.

## 9. Capability availability is not route selection

An installed/healthy backend is not automatically preferred or authorized.

```text
exact safe semantic/native route proven -> use it
structure insufficient for reviewed case -> selected visual/GUI route
ambiguous/high-consequence result -> stronger evidence/reconciliation/ABSTAIN
```

## 10. Security enables controlled capability

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure trust is separate:

```text
CANDIDATE -> verified/trusted -> stale/quarantine/disable/rollback
```

A trusted procedure, extension output, worker or planner proposal is not blanket action authority.

## 11. Environmental content is data, not authority

UI/DOM/messages/files/screenshots/OCR/tool/MCP/worker output is untrusted environmental data with respect to user intent, permission scope and Control Plane policy.

Preserve provenance when facts cross capability/application boundaries.

## 12. Current state beats memory

```text
current observed state
 > current goal / completion criteria
 > trusted procedure/demo/lineage evidence
 > historical low-level action/session sequence
```

Blind historical coordinate replay is never reusable authority.

## 13. Every mutation has an expected effect

```text
observe
 -> bind logical operation + ExpectedEffect
 -> authorize bounded action
 -> deliver
 -> fresh re-observe
 -> verify PASS | FAIL | UNKNOWN
```

Delivery is not success. `UNKNOWN` never silently advances or blindly retries.

## 14. Reconcile ambiguity before retry

If a consequence may have occurred but acknowledgement/state is ambiguous, preserve stable logical operation identity and reconcile from fresh authoritative state before retry.

A renamed strategy/action label must not bypass duplicate-effect protection.

## 15. Transition verification is not task completion

Planner/procedure/worker may propose `candidate_done`.

Only independent fresh task-level evidence may produce Finish Gate `DONE`.

Task-success and safety/policy remain separate dimensions.

## 16. Recovery is typed and loop-bounded

```text
fresh re-observe
 -> classify/reconcile
 -> re-resolve target
 -> retry only when evidence permits
 -> alternate already-admitted modality
 -> predeclared local recovery
 -> StagnationReport / ChatGPT replan / clarification / ABSTAIN
```

LoopGuard bounds repeated no-effect/equivalent physical attempts/oscillation and task/procedure/strategy budgets.

## 17. Working memory is structured operational state

WorkingState may preserve constraints, verified progress, facts+provenance+freshness, ambiguities, evidence refs, expected/observed deltas, operation/attempt/reconciliation history and budgets.

Never persist private chain-of-thought.

## 18. Procedural memory has privacy/trust boundaries

A human demonstration or successful trajectory creates at most CANDIDATE.

Persist only structured/user-visible goal/subtask/evidence/action/result/provenance needed for operation/debugging/reuse. Before long-term arbitrary demo storage, define screenshot/text retention, secret filtering, redaction, deletion, encryption and export/sync rules.

Compiled guidance is advisory until current-state authorization and verification.

## 19. No sunk-cost architecture

Git history is archival storage. Old `current`/`next` wording cannot override current owners.

At architecture-changing points, audit entry/overview/governance docs rather than only add another handoff.

## 20. Cost discipline

Prefer local/free/open-source components where quality is adequate. Do not introduce mandatory paid model APIs or extra SaaS when ordinary ChatGPT + local bridge satisfies baseline.

Future local planner research requires measured benefit, not novelty.

## 21. Hardware-aware local specialists

Select local models/runtimes from measured target-machine RAM/latency/quality and replaceability, not parameter-count assumptions.

Current accepted specialist identity belongs to current catalog/evidence owners; historical Stage 25 research documents are not permanent runtime identity.

## 22. Long-horizon correctness before broader authority

Current accepted progression includes 26.3A procedure runtime, 26.3B Verification Kernel/Finish Gate and the #124 Stage 26.3C WorkingState/LoopGuard L1 foundation.

Current release-critical work is consequence-bearing production/restart integration of that foundation. Broad hybrid authority follows only after the state/verification/recovery substrate is accepted in real paths.

Do not treat later hybrid stages as permission to add raw desktop tools.

## 23. Manager/tray/transport are not the execution Control Plane

Manager/tray/supervisor owns lifecycle/configuration/diagnostics/transport reliability.

The deterministic Control Plane owns task/procedure state, authorization, verification, recovery/budgets and task completion evidence.

`CONTROL_PLANE_API_KEY` is Secure MCP Tunnel credential terminology and unrelated to project execution Control Plane authority.

## 24. Independent review is assurance, not a second planner

Do not use Codex/ChatGPT Work as an alternate implementation/planning workspace by default.

This does **not** prohibit Codex Review/equivalent independent PR review required/allowed by `AGENTS.md`. Review is an assurance layer over repository changes, not product/runtime planning authority.

Never claim physical evidence unless that exact physical path ran. Never invent measurement counters.

## 25. Context transfer is a development requirement

A fresh ordinary ChatGPT session should be able to determine quickly:

- live `main` and relevant open PR/head;
- applicable repository skills;
- what is accepted/current;
- current release-critical stage;
- public semantic contract;
- planner vs Control Plane boundary;
- WorkingState/reconciliation/LoopGuard/Finish Gate state;
- prior component/reuse lineage relevant to current research;
- environmental-content trust boundary;
- future Track M/P status;
- which historical docs cannot override current state.

Keep document roles explicit through `DOCUMENT_STATUS.md`; do not synchronize the same stage snapshot into every document.

## 26. Future local planner is optional research, not forbidden

Track a future local general planner explicitly as Track P after verified long-horizon state data and measured need exist.

Research begins shadow/proposal-only and compares against ordinary ChatGPT under comparable task/action/compute budgets where practical.

Even a future planner remains behind deterministic capability authorization, Verification Kernel, reconciliation/recovery and Finish Gate/safety boundaries.

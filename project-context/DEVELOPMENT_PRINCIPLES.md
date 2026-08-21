# Development Principles

## 1. ChatGPT is the current general planner; local execution may be autonomous within known transitions

Ordinary ChatGPT currently owns open-ended task interpretation, strategy, procedure selection and novel-state adaptation.

Do not add another **current general planner** or autonomous workflow brain that competes with ChatGPT.

This does **not** forbid a deterministic local execution Control Plane. The platform should maintain TaskState, procedure state, policy/authorization, checkpoints, postconditions, bounded recovery and budgets. Once ChatGPT selects a bounded procedure, that Control Plane may advance known transitions without a ChatGPT round trip after every action.

Unknown/ambiguous/stale/incompatible state or a need for new strategy -> ABSTAIN/escalate to ChatGPT.

See `CONTROL_PLANE.md`.

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

A component becomes accepted only after applicable install/start/health/task/negative/physical evidence.

Distinguish:

- synthetic policy tests;
- hosted CI;
- real target-machine physical evidence;
- one successful trajectory;
- compiled candidate procedure;
- verified/promoted reusable procedure.

Never collapse these into one claim.

## 4. Thin project-owned surface, but own the product safety seam

Allowed project code should normally be:

- lifecycle/configuration integration;
- deterministic compatibility adapters;
- acceptance/security tests;
- focused task/procedure state schemas;
- capability policy/authorization wrappers;
- checkpoint/recovery/budget state machines;
- verifier/postcondition logic;
- privacy/trust wrappers around qualified upstream procedure mechanics.

Do not rebuild **generic** tunnels, MCP gateways, registries, vaults, databases, job platforms, generic policy platforms, autonomous agent frameworks or model-serving stacks without measured need.

A focused project-owned deterministic Control Plane is explicitly allowed because it is the integration/safety boundary; it must not grow into an open-ended planner.

## 5. Stable truthful typed capability boundary

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Five is a proven current contract, not a permanent dogma. Do not preserve it by hiding unrelated native desktop/procedure consequences in existing web semantics or behind opaque generic dispatch.

`semantic-projection` remains a truthful deterministic compatibility layer. It is not the procedure Control Plane.

## 6. Task-driven lifecycle and capability selection

Do not run the full backend/model catalog permanently. Start what the task needs, reuse active components when useful, and stop heavyweight idle components.

Do not preselect a permanent future application list from old conversations; choose real integrations from tasks/evidence.

## 7. Security enables controlled capability

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure trust lifecycle:

```text
CANDIDATE -> VERIFIED/TRUSTED -> stale/quarantine/disable/rollback
```

These are separate. A trusted procedure or planner proposal is not blanket action authorization.

Prefer scoped/reversible resources and explicit rollback. Consequential actions require consequence-appropriate policy, not universal confirmation for every harmless operation.

## 8. Current state beats memory

```text
current observed state
 > current completion criteria / subtask goal
 > trusted procedure evidence
 > historical low-level action sequence
```

When procedure history conflicts with live state, re-resolve, recover through an explicitly defined safe branch or ABSTAIN/escalate.

Blind historical absolute-coordinate replay is never the reusable solution.

## 9. Verification controls progression

```text
PASS -> checkpoint / advance
FAIL -> bounded recover or stop
UNKNOWN -> observe / ABSTAIN / user or ChatGPT escalation
```

Delivery receipts are not completion. Model/planner declarations are not completion.

A long known procedure may advance locally through repeated authorized+verified transitions; verification is what makes this safe autonomy possible.

## 10. Procedural memory has a privacy boundary

Never persist private chain-of-thought.

Persist only structured/user-visible goal summaries, state, actions, receipts, explicit observations/evidence and verification needed for operation/debugging/reuse.

Before long-term arbitrary demonstration storage, define screenshot/text retention, secret filtering, redaction, deletion, encryption and sync/export rules.

## 11. No sunk-cost architecture

Git history is the archive. Historical documents/results remain evidence but old `current`/`next` wording must not override current authoritative context.

At architecture-changing points audit entry documents rather than only adding another handoff.

## 12. Cost discipline

Prefer local/free/open-source components where quality is adequate. Do not introduce mandatory paid model APIs or extra SaaS when ordinary ChatGPT + local bridge can satisfy the baseline.

Future local planner research must not be justified merely by novelty; it requires measured offline/latency/parallel/deployment benefit.

## 13. Hardware-aware local models

Use measured target-machine RAM/latency/quality, not parameter-count assumptions.

Current accepted vision path is llama.cpp + LFM2.5-VL-450M F16. Future specialist/planner model choices require target evidence.

## 14. Windows capability is accepted through 26.2D; real-app evidence comes next

Do not use the obsolete statement that Stage 26.3 is where Windows desktop capability begins.

Current sequence:

```text
26.2A production Windows runtime
26.2B DesktopState
26.2C native Grounder
26.2D structure-first UIA -> vision routing
26.2E real application E2E
26.3 Verified Procedure Runtime / deterministic Control Plane
26.4 Human Demo transfer
```

The desktop foundation is already implemented/accepted for bounded contracts; 26.2E is the first real-app gate.

## 15. Control Plane is not the Windows manager

Manager/tray owns lifecycle/configuration/diagnostics.

The future procedure Control Plane owns task/procedure execution state, authorization, checkpoints, verifier and bounded recovery. Keep these responsibilities separate.

Likewise `CONTROL_PLANE_API_KEY` for the OpenAI tunnel is credential terminology and must not be confused with the project’s local deterministic execution Control Plane.

## 16. Acceptance ownership and continuation discipline

Use ordinary ChatGPT + GitHub + project local/connected tools under the current operating constraint. Do not use Codex or ChatGPT Work unless the user explicitly re-enables them.

Reserve user participation for irreducible target-machine or ordinary-Chat UI gates.

Never claim local-machine/ordinary-Chat physical evidence unless that exact path actually ran. Never invent measurement counters to stand in for instrumentation.

## 17. Context transfer is a development requirement

A fresh ordinary ChatGPT session should be able to determine:

- live `main`;
- active PR/head;
- what is physically accepted;
- current release-critical stage;
- deterministic Control Plane boundary;
- future local-planner Track P status;
- historical docs that must not override current state;
- remaining user-machine gates.

Keep `CONTINUATION_CONTEXT.md`, `START_HERE.md`, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `ROADMAP.md` and active stage docs synchronized.

## 18. Future local planner is research, not a forbidden concept

Do not erase the local planner from long-term design. Track it explicitly as optional Track P after verified procedure-state data and measured need exist.

Research starts shadow/proposal-only and benchmarks against ordinary ChatGPT with comparable task/action/compute budgets where practical. Even a future planner remains behind deterministic capability authorization and verifier boundaries.

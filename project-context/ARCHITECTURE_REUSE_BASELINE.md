# Architecture Reuse Baseline

Status: **AUTHORITATIVE RESEARCH COMPARISON BASELINE**

## Purpose

This document records the previously selected architecture/reuse lineage that new `stage-research` work must compare against before introducing or replacing a mechanism.

It answers one question quickly:

> For this architectural role, what component or project-owned boundary did we already select, what exactly did we intend to reuse, and why?

This is **not** a frozen implementation specification and it does not override live code, current evidence, security/authority policy, or a fresh Stage Research Brief. It is the canonical baseline for comparing new research with prior design choices so the project evolves deliberately instead of silently re-designing the same role from scratch.

Detailed rationale remains in the linked owner documents. Current code/tests/current hosted CI/current physical evidence outrank this baseline when they disagree on implemented or accepted behavior.

## Required Stage Research use

When `.agents/skills/stage-research/SKILL.md` applies:

1. identify the concrete architectural role(s) affected by the stage or proposed mechanism;
2. locate the corresponding row(s) in this baseline before external solution selection;
3. revalidate the prior selected component/mechanism only for the exact role now at issue;
4. compare the prior selection, credible current alternatives, and a project-owned implementation where relevant;
5. assign one lineage decision per affected role:
   - `KEEP` — prior choice and boundary still fit;
   - `REUSE_MORE` — reuse more of the previously selected component instead of duplicating it locally;
   - `REFINE` — keep the prior choice but narrow/change its adapter or responsibility;
   - `REPLACE` — adopt another mechanism/component, with explicit evidence for why the prior choice no longer fits;
   - `DEFER` — keep the role unresolved/unimplemented until evidence or a consumer justifies it;
   - `REJECT` — explicitly reject the prior candidate/role mapping for the current architecture, with evidence;
6. if no baseline role exists, treat the proposed role/mechanism as new architecture and run the normal Research Scope Expansion Gate;
7. record the result in the Stage Research Brief under `Architecture lineage comparison`.

`REPLACE` and `REJECT` require explicit evidence. The fact that a new component exists, is newer, or is fashionable is not sufficient.

A baseline row is history plus a current comparison starting point, not automatic implementation authority.

## Canonical role map

| Architectural role | Prior selected source / owner | Intended reuse | Explicitly not delegated | Original reason / value | Detailed owner | Baseline disposition |
|---|---|---|---|---|---|---|
| General planning / novel strategy | ordinary ChatGPT | open-ended task interpretation, strategy, replanning | local deterministic authority, effect verification, Finish Gate | keep one current general planner while local execution stays deterministic and bounded | `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `DECISIONS.md` | `KEEP` |
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | normal ordinary-Chat transport/reachability | planner, capability authorization, semantic tool authority | accepted real Chat route with less custom ingress infrastructure | `ARCHITECTURE.md`, `DIRECT_SEMANTIC_TUNNEL.md`, `DECISIONS.md` | `KEEP` |
| Internal MCP aggregation / extension lifecycle | 1MCP or qualified replacement | optional discovery, aggregation, enable/disable, backend lifecycle/health | baseline transport, public raw tool catalog, trust, authorization, persistent tunnel ownership | reuse generic extension infrastructure without putting it on the critical six-tool path | `MODULE_SELECTION_POLICY.md`, `ARCHITECTURE.md`, `DECISIONS.md` | `OPTIONAL` |
| Browser semantic execution | Playwright behind project semantic Browser capability | browser navigation, DOM/AX state, bounded page interaction mechanics | planning, project authority, task completion | mature browser automation with strong structural state; keep project verification boundary | `ARCHITECTURE.md`, `BROWSER_HARNESS_ARCHITECTURE.md`, `MODULE_CATALOG.md` | `KEEP` |
| Local visual specialist runtime | llama.cpp + LFM2.5-VL-450M F16 | bounded local perception/grounding proposals when structural evidence is insufficient | planner, action authorization, verification authority | local, replaceable, task-driven specialist perception with bounded authority | `LOCAL_SPECIALIST_INFERENCE.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `KEEP` |
| Procedure compiler / workflow IR | OpenAdapt Flow 1.31.0 | `Workflow` / `ProgramGraph`, demonstration compile, deterministic healthy-path replay | project WorkingState, project capability authority, project Finish Gate | avoid rebuilding mature procedure IR/compiler/replay machinery | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `SELECTED / REVALIDATE PER CONSUMER` |
| Procedure-local checkpoint / durable resume mechanics | OpenAdapt Flow 1.31.0 where its semantics fit | checkpoint/resume of one compiled procedure; procedure-local execution reporting | capability-spanning WorkingState, cross-capability recovery authority, permission/grant state | reuse mature procedure-local resume mechanics while keeping project state above the vendor runtime | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_SELECTION_POLICY.md` | `SELECTED / REVALIDATE PER FAILURE MODEL` |
| Procedure/effect evidence | OpenAdapt effect-verifier mechanics through a narrow project adapter | upstream effect-contract/effect-verifier observations as provenance-bearing evidence | unconditional mapping of upstream verdict to project `PASS`; task `DONE` | reuse mature effect-evidence mechanics while project Kernel remains final transition judge | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | `SELECTED / REVALIDATE PER EFFECT` |
| Human desktop demonstration capture | OpenAdapt Capture 1.2.2 + Flow adapter | local demonstration capture and inputs for candidate procedure compilation | automatic trust/promotion, cloud dependency, task completion authority | avoid writing recorder/capture stack from scratch; defer trust to project evidence | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `STAGE26_PROCEDURAL_MEMORY.md`, `MODULE_CATALOG.md` | `DEFERRED TO 26.4 / SELECTED` |
| Windows / Office application mechanics | selective Microsoft UFO/UFO²-derived UIA, Win32, WinCOM and app-specific patterns | focused Excel/Word/PowerPoint/Outlook/native adapter mechanics where they are stronger than generic GUI action | UFO HostAgent/AppAgent planner hierarchy, UFO completion authority, Galaxy orchestration | reuse expensive app-specific Windows mechanics without importing a second AgentOS/planner | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_CATALOG.md` | `DEFERRED / SELECTIVE_REUSE` |
| Multi-chat / provider conversation extraction and browser adaptation | CtxPort-derived ideas plus project Browser Companion / `GenericChatAdapter` direction | structured extraction, provider/profile registry ideas, bounded handoff/context normalization, browser authenticated-session adaptation | treating Markdown transcript as source of truth, provider UI as authority, whole third-party extension as project control plane | reuse cross-provider extraction/adaptation ideas while keeping stable session/delegation identity and authority project-owned | `CONVERSATION_BRIDGE_ARCHITECTURE.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `FUTURE / REVALIDATE WITH TRACK M` |
| Capability-spanning operational state | project-owned `WorkingState` | constraints, subgoals/progress, provenance/freshness, evidence refs, recovery/reconciliation history, budgets, grants/procedure refs | OpenAdapt procedure state, provider/session task stores, private chain-of-thought | no external procedure/session runtime spans the full product authority/state boundary | `CONTROL_PLANE.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `DECISIONS.md` | `PROJECT_OWNED / KEEP` |
| Transition verification authority | project Verification Kernel | current-state binding, fresh same-stream evidence, ExpectedEffect, `PASS | FAIL | UNKNOWN` | external verifier/model/procedure self-declared success | external evidence may help, but project policy must remain able to reject stale/mismatched/insufficient evidence | `CONTROL_PLANE.md`, `STAGE26_3B_VERIFICATION_KERNEL.md`, `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | `PROJECT_OWNED / KEEP` |
| Task completion authority | project independent Finish Gate | fresh goal/safety/constraint evidence -> `DONE | NOT_DONE | UNKNOWN` | planner/procedure/worker/external framework self-reported completion | transition success and task completion are different contracts | `CONTROL_PLANE.md`, `ROADMAP.md`, `DECISIONS.md` | `PROJECT_OWNED / KEEP` |
| Capability authorization / consequence policy | project deterministic Control Plane | AVAILABLE -> ACTIVE -> AUTHORIZED, scope/consequence checks, operation identity, bounded grants | external model/procedure/extension/tool output granting itself authority | authority must remain stable across interchangeable executors/adapters | `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `SECURITY_POLICY.md`, `MODULE_SELECTION_POLICY.md` | `PROJECT_OWNED / KEEP` |

## How to compare a new mechanism

For each affected row, the Stage Research Brief should answer these questions explicitly:

```text
prior role / selected source
 -> what exact capability or guarantee did we expect from it?
 -> does the current selected version actually provide that guarantee?
 -> under what crash/concurrency/identity/authority assumptions?
 -> have real project failures changed the requirement?
 -> do current alternatives provide a materially better fit?
 -> are we about to duplicate a mechanism already selected for reuse?
 -> if we keep custom code, why must this part remain project-owned?
 -> lineage decision: KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT
```

The comparison is about mechanisms and boundaries, not project popularity.

## Example: Stage 26.3C procedure recovery

A Stage 26.3C consumer that changes procedure restart/recovery must not compare only `prepared_intent` vs WAL vs SQLite vs filesystem transactions.

It must also compare against the prior lineage:

```text
procedure-local checkpoint/resume     -> OpenAdapt Flow selected candidate
procedure/effect evidence             -> OpenAdapt effect-verifier mechanics selected candidate
capability-spanning recovery state    -> project WorkingState
transition authority                  -> project Verification Kernel
completion authority                  -> project Finish Gate
```

The research must therefore determine which procedure-local mechanics should be reused from OpenAdapt, which do not cover ambiguous external side effects or the exact failure model, and which project-owned boundaries must remain independent. A custom recovery mechanism is acceptable only after this comparison explains why it is not unnecessary duplication of the selected upstream role.

## Update policy

Update this baseline only when a reviewed architecture/research decision changes a role assignment, selected reuse source, project-owned boundary, or replacement/defer condition.

When a Stage Research Brief concludes `REPLACE`, `REJECT`, `REUSE_MORE`, or a material `REFINE` for an existing row, update this baseline in the implementation/process PR that adopts the decision or in the immediately following documentation synchronization change.

Do not turn this document into:

- a second `MODULE_CATALOG.md` with runtime status dumps;
- a duplicate `ROADMAP.md`;
- a dependency lockfile;
- a replacement for detailed ADR/reuse documents;
- proof that a component is currently implemented or physically accepted.

Exact versions/pins that are security/supply-chain critical remain in their lock/config/source-owner documents. This baseline records architectural role lineage and points to those owners.

## Relationship to existing documents

- `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` — detailed OpenAdapt/UFO integration rationale and boundaries.
- `MODULE_CATALOG.md` — broad capability/status inventory.
- `MODULE_SELECTION_POLICY.md` — rules for selecting or adapting external components.
- `DECISIONS.md` — ADR-level architecture decisions.
- `ARCHITECTURE.md` / `CONTROL_PLANE.md` — durable product/authority boundaries.
- this document — **canonical prior-decision baseline used by future Stage Research comparisons**.

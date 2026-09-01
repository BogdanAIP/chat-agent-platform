# Architecture Reuse Baseline

Status: **AUTHORITATIVE RESEARCH COMPARISON BASELINE**

## Purpose

This document records the previously selected architecture/reuse lineage that new `stage-research` work must compare against before introducing or replacing a mechanism.

It answers one question quickly:

> For this architectural role, what component or project-owned boundary did we already select, what exactly did we intend to reuse, and why?

This is **not** a frozen implementation specification and it does not override live code, current evidence, security/authority policy, or a fresh Stage Research Brief. It is the canonical baseline for comparing new research with prior design choices so the project evolves deliberately instead of silently re-designing the same role from scratch.

Detailed rationale remains in the linked owner documents. Current code/tests/current hosted CI/current physical evidence outrank this baseline when they disagree on implemented or accepted behavior.

Release timing, stage ordering, implementation status, exact dependency pins and physical acceptance state belong to their existing owner documents (`ROADMAP.md`, `CURRENT_STATE.md`, lock/config files and `EVIDENCE_INDEX.md`), not to this baseline.

## Required Stage Research use

When `.agents/skills/stage-research/SKILL.md` applies:

1. identify the concrete architectural role(s) affected by the stage or proposed mechanism;
2. locate the corresponding row(s) in this baseline before external solution selection;
3. revalidate the prior selected component/mechanism only for the exact role now at issue;
4. compare the prior selection, credible current alternatives, and a project-owned implementation where relevant;
5. assign exactly one lineage decision per affected **existing** role:
   - `KEEP` — prior choice and boundary still fit;
   - `REUSE_MORE` — reuse more of the previously selected component instead of duplicating it locally;
   - `REFINE` — keep the prior source/boundary but narrow/change its adapter or responsibility;
   - `REPLACE` — adopt another mechanism/component, with explicit evidence for why the prior choice no longer fits;
   - `DEFER` — keep the role unresolved/unimplemented until evidence or a consumer justifies it;
   - `REJECT` — explicitly reject the prior mapping for the current architecture, with evidence;
6. if no baseline role exists, identify it as `NEW_ARCHITECTURE` in the Brief and run the Research Scope Expansion Gate rather than inventing a compound lineage decision;
7. record scope qualifiers separately from the canonical lineage decision.

`REPLACE` and `REJECT` require explicit evidence. The fact that a new component exists, is newer, or is fashionable is not sufficient.

Role-level `DEFER` is distinct from the top-level Stage Research decision `DEFER`. A role may be marked `DEFER` only when it is explicitly outside the implementation scope selected by the Brief. If that role is required to satisfy the current stage goal or a release-critical guarantee, the Brief cannot return `PROCEED` or `NARROW` while leaving the role deferred; it must either narrow the stage goal so the role is no longer required or return top-level `DEFER` and keep implementation blocked.

A baseline row is history plus a current comparison starting point, not automatic implementation authority. Existing historical posture labels in this table are preserved where the role remains unchanged; adopting research may update/split a row when the role itself is materially refined. The current Stage Research Brief owns the one canonical `KEEP | REUSE_MORE | REFINE | REPLACE | DEFER | REJECT` decision for the stage being evaluated.

When a baseline role points to a public **reference implementation**, and `.agents/skills/source-code-research/SKILL.md` applies, the comparison must inspect source code at an exact commit/tag. README/docs-level familiarity alone does not revalidate that lineage.

## Canonical role map

| Architectural role | Prior selected source / owner | Intended reuse | Explicitly not delegated | Original reason / value | Detailed owner | Prior lineage posture |
|---|---|---|---|---|---|---|
| General planning / novel strategy | ordinary ChatGPT | open-ended task interpretation, strategy, replanning and bounded delegation selection | local deterministic authority, effect verification, Finish Gate, delegated-worker self-expansion | keep one current general planner while local execution and specialist workers stay deterministic/bounded | `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `DECISIONS.md` | `SELECTED` |
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | normal ordinary-Chat transport/reachability | planner, capability authorization, semantic tool authority | accepted real Chat route with less custom ingress infrastructure | `ARCHITECTURE.md`, `DIRECT_SEMANTIC_TUNNEL.md`, `DECISIONS.md` | `SELECTED` |
| Internal MCP aggregation / extension lifecycle | 1MCP or qualified replacement | optional discovery, aggregation, enable/disable, backend lifecycle/health | baseline transport, public raw tool catalog, trust, authorization, persistent tunnel ownership | reuse generic extension infrastructure without putting it on the critical six-tool path | `MODULE_SELECTION_POLICY.md`, `ARCHITECTURE.md`, `DECISIONS.md` | `OPTIONAL_REUSE` |
| Browser semantic execution | Playwright behind project semantic Browser capability | browser navigation, DOM/AX state, bounded page interaction mechanics | planning, project authority, task completion | mature browser automation with strong structural state; keep project verification boundary | `ARCHITECTURE.md`, `BROWSER_HARNESS_ARCHITECTURE.md`, `MODULE_CATALOG.md` | `SELECTED` |
| Local visual specialist runtime | llama.cpp + LFM2.5-VL family | bounded local perception/grounding proposals when structural evidence is insufficient | planner, action authorization, verification authority | local, replaceable, task-driven specialist perception with bounded authority | `LOCAL_SPECIALIST_INFERENCE.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `SELECTED_FAMILY` |
| Procedure compiler / workflow IR | OpenAdapt Flow | `Workflow` / `ProgramGraph`, demonstration compile, deterministic healthy-path replay | project WorkingState, project capability authority, project Finish Gate | avoid rebuilding mature procedure IR/compiler/replay machinery | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `SELECTED_REVALIDATE_PER_CONSUMER` |
| Procedure-local checkpoint / durable resume mechanics | OpenAdapt Flow where its semantics fit | checkpoint/resume of one compiled procedure; procedure-local execution reporting | capability-spanning WorkingState, cross-capability recovery authority, permission/grant state | reuse mature procedure-local resume mechanics while keeping project state above the vendor runtime | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_SELECTION_POLICY.md` | `SELECTED_REVALIDATE_PER_FAILURE_MODEL` |
| Procedure/effect evidence | OpenAdapt effect-verifier mechanics through a narrow project adapter | upstream effect-contract/effect-verifier observations as provenance-bearing evidence | unconditional mapping of upstream verdict to project `PASS`; task `DONE` | reuse mature effect-evidence mechanics while project Kernel remains final transition judge | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | `SELECTED_REVALIDATE_PER_EFFECT` |
| Human desktop demonstration capture | OpenAdapt Capture + Flow adapter | local demonstration capture and inputs for candidate procedure compilation | automatic trust/promotion, cloud dependency, task completion authority | avoid writing recorder/capture stack from scratch; defer trust to project evidence | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `STAGE26_PROCEDURAL_MEMORY.md`, `MODULE_CATALOG.md` | `SELECTED_REVALIDATE_BEFORE_ADOPTION` |
| Windows / Office application mechanics | selective Microsoft UFO/UFO²-derived UIA, Win32, WinCOM and app-specific patterns | focused Excel/Word/PowerPoint/Outlook/native adapter mechanics where they are stronger than generic GUI action | UFO HostAgent/AppAgent planner hierarchy, UFO completion authority, Galaxy orchestration | reuse expensive app-specific Windows mechanics without importing a second AgentOS/planner | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_CATALOG.md` | `SELECTIVE_REUSE_REVALIDATE_PER_APP` |
| Physical device / IoT normalization and bounded execution | Home Assistant as preferred first candidate, not an accepted production dependency | device/entity normalization, stable registry identity inputs, state/event observation, bounded service/action mechanics and broad Matter/MQTT/vendor integration reach behind a narrow adapter | project Control Plane authority, WorkingState, Verification Kernel, Finish Gate, raw public service catalog, automatic trust of backend success, safety-critical interlocks | avoid vendor-by-vendor drivers while preserving command-vs-observed-state separation and project consequence/verification authority | `IOT_PHYSICAL_DEVICE_CAPABILITY_RESEARCH.md`, `MODULE_SELECTION_POLICY.md`, `ROADMAP.md` | `PREFERRED_CANDIDATE_REVALIDATE_BEFORE_ADOPTION` |
| Multi-chat / provider conversation extraction and browser adaptation | CtxPort-derived ideas + project Browser Companion direction + first bounded project `chatgpt-temporary` provider adapter | structured extraction/profile ideas and authenticated-session adaptation below provider-independent delegation identity | Markdown transcript as source of truth, provider UI as authority, whole third-party extension as Control Plane, provider DOM details in generic identity | retain cross-provider adaptation ideas but narrow the first real adapter to one positively qualified Temporary Chat route under project lifecycle authority | `CONVERSATION_BRIDGE_ARCHITECTURE.md`, `AGENT_SESSION_DELEGATION_REENTRY.md`, `ARCHITECTURE.md` | `REFINE` |
| Bounded Agent Session / Delegation lifecycle | project-owned Track M boundary refined by `AGENT_SESSION_DELEGATION_REENTRY.md` + `delegation_state` family | provider-independent delegation identity, private run capability, launch/child/delivery/result lifecycle, one-worker durable closure | second planner, worker self-authority, generic scheduler/event bus, fan-out/nesting, provider-specific identity as generic truth | promote only the smallest proven one-manager/one-read-only-worker slice instead of implementing the whole future orchestration catalog | `AGENT_SESSION_DELEGATION_REENTRY.md`, `ARCHITECTURE.md`, `CURRENT_STATE.md` | `REFINE` |
| External agent-host/session lifecycle reference | `openai/codex` as source-code reference implementation, not runtime dependency | App Server/thread lifecycle and resume/fork, persistent context transitions, parent/child ownership/restoration and async messaging patterns to compare | project Control Plane authority, WorkingState, Verification Kernel, Finish Gate, capability grants, bounded public surface, Codex tool/planner authority | pinned source review remains useful comparison evidence without importing a second agent runtime | `CODEX_AGENT_HOST_SOURCE_REVIEW.md`, `AGENT_SESSION_DELEGATION_REENTRY.md`, `CONTROL_PLANE.md` | `REFERENCE_REVALIDATE_PER_STAGE` |
| Agent-session local concurrent ownership | accepted Stage 26.3C OS-backed cooperating-runner lock | exact-delegation single-writer ownership around genesis/state and lifecycle transitions | browser-tab ownership, generic distributed lease framework | reuse accepted process-local concurrency instead of introducing a new state service | `AGENT_SESSION_DELEGATION_REENTRY.md`, `CURRENT_STATE.md` | `REUSE_MORE` |
| Agent-session immutable genesis | accepted Stage 26.3C exclusive-create/fsync mechanic | one immutable exact delegation identity + private run/delivery correlation | mutable transition state, machine/power-loss transactional guarantee | reuse accepted creation semantics and fail closed rather than invent another persistence layer | `AGENT_SESSION_DELEGATION_REENTRY.md`, `CURRENT_STATE.md` | `REUSE_MORE` |
| Agent-session mutable lifecycle/result state | accepted Stage 26.3C sibling-temp/flush/fsync/replace + strict validation pattern | launch/child/delivery/result checkpoints, residue detection, restart recovery and exact correlation | capability-spanning WorkingState replacement, SQLite/WAL/event-log service, browser Send ownership | reuse accepted local crash-safe primitives for the bounded delegation lifecycle | `AGENT_SESSION_DELEGATION_REENTRY.md`, `CURRENT_STATE.md` | `REUSE_MORE` |
| Agent-session first-provider fresh-chat/composer mechanics | reusable physical observations from PR #138/#145 experiments behind project `chatgpt-temporary` adapter | Temporary Chat launch, composer/Send observation and stable result capture mechanics for the first provider only | reviewer-specific prompts/results/context, generic provider framework, scheduler authority | reuse physically demonstrated transport mechanics without promoting experiment code or reviewer semantics into generic lifecycle authority | `AGENT_SESSION_DELEGATION_REENTRY.md`, `CURRENT_STATE.md` | `REUSE_MORE` |
| Agent-session first-provider browser delivery ownership | MV3 service worker + extension-origin IndexedDB unique-key claim, refined from automatic-review experiment/research | durable same-delivery claim across tabs, exact tab/run/delegation/delivery/task correlation and no second Send | local delegation-state ownership, generic browser database/runtime authority, arbitrary page mutation | browser tabs are a separate concurrency domain; retain the atomic durable claim but bind it to generic delivery identity and project-local Send authority | `AGENT_SESSION_DELEGATION_REENTRY.md`, `CURRENT_STATE.md` | `REFINE` |
| Automatic-review local concurrent ownership | accepted Stage 26.3C OS-backed lock, retained for reviewer-specific result/fallback policy | exact review-operation single-writer closure while reviewer remains a specialist consumer/fallback | generic Agent Session identity, browser-tab ownership, generic lease system | preserve accepted reviewer fallback semantics while reusable lifecycle mechanics move below into Agent Sessions | `AUTOMATIC_REVIEWER_RESEARCH.md`, `CURRENT_STATE.md` | `REFINE` |
| Automatic-review immutable operation genesis | accepted reviewer local-state contract from #141, retained for exact review identity/fallback | exact repository/PR/BASE/HEAD reviewer identity + private review correlation where reviewer policy requires it | generic worker identity/result schema | reviewer exact-review identity remains specialist policy even as generic worker lifecycle owns reusable session mechanics | `AUTOMATIC_REVIEWER_RESEARCH.md`, `CURRENT_STATE.md` | `REFINE` |
| Automatic-review mutable operation/result state | accepted reviewer local state/result/fallback contract from #141/#142 | reviewer-specific automatic/manual closure, `REVIEW_RESULT_V1` validation and late-result fencing | generic lifecycle schema, generic worker result semantics | preserve specialist reviewer guarantees until migration over generic delegation is separately proven | `AUTOMATIC_REVIEWER_RESEARCH.md`, `CURRENT_STATE.md` | `REFINE` |
| Automatic-review reviewer authority qualification | dedicated reviewer security context with GitHub mutation actions unavailable | prove write actions absent via disconnect/disable or supported read-only Action Control | generic worker read-only profile as substitute for reviewer GitHub authority proof | deterministic reviewer least privilege remains consumer policy and is deferred from the generic first Agent Session scope | `AUTOMATIC_REVIEWER_RESEARCH.md`, `.agents/skills/code-review/SKILL.md` | `NEW_ARCHITECTURE` |
| Automatic-review local result submission/reconciliation | fixed `submit_independent_review_result_v1` + `reconcile_independent_review_result_v1` behind `procedure_run` | store/consume reviewer result locally; atomically close manual fallback against late submit | generic worker result bus, GitHub comment publisher | preserve accepted reviewer release-assurance closure until generic consumer migration is proven | `AUTOMATIC_REVIEWER_RESEARCH.md`, `.agents/skills/code-review/SKILL.md`, `CURRENT_STATE.md` | `REFINE` |
| Automatic independent-review consumer launch / correlation | accepted fixed reviewer procedures + future reuse of accepted generic Agent Session lifecycle | exact-head reviewer operation can later consume one fresh worker without replacing reviewer exact-identity/authority/result policy | arbitrary launcher, scheduler/event bus, same-task developer wake, worker rotation | genericize only reusable lifecycle; keep reviewer semantics above it and migrate separately | `AUTOMATIC_REVIEWER_RESEARCH.md`, `AGENT_SESSION_DELEGATION_REENTRY.md`, `CURRENT_STATE.md` | `REFINE` |
| Code-review evaluation harness | Harbor custom-agent/task/environment/verifier interfaces | reproducible external reviewer evaluation, frozen tasks, custom CAP adapter, metric/result collection | production launch, GitHub authority, review acceptance, Control Plane authority | avoid building a benchmark runner while keeping evaluation separate from production lifecycle | `AUTOMATIC_REVIEWER_RESEARCH.md`, `ROADMAP.md` | `NEW_ARCHITECTURE` |
| Capability-spanning operational state | project-owned `WorkingState` | constraints, subgoals/progress, provenance/freshness, evidence refs, recovery/reconciliation history, budgets, grants/procedure/delegation refs | OpenAdapt procedure state, provider/session task stores, generic delegation state as replacement, private chain-of-thought | no external procedure/session runtime or narrow delegation lifecycle spans the full product authority/state boundary | `CONTROL_PLANE.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `DECISIONS.md` | `PROJECT_OWNED` |
| Transition verification authority | project Verification Kernel | current-state binding, fresh same-stream evidence, ExpectedEffect, `PASS | FAIL | UNKNOWN` | external verifier/model/procedure/worker self-declared success | external evidence/worker result may help, but project policy must remain able to reject stale/mismatched/insufficient evidence | `CONTROL_PLANE.md`, `STAGE26_3B_VERIFICATION_KERNEL.md`, `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | `PROJECT_OWNED` |
| Task completion authority | project independent Finish Gate | fresh goal/safety/constraint evidence -> `DONE | NOT_DONE | UNKNOWN` | planner/procedure/worker/external framework self-reported completion | transition/worker success and whole-task completion are different contracts | `CONTROL_PLANE.md`, `ROADMAP.md`, `DECISIONS.md` | `PROJECT_OWNED` |
| Capability authorization / consequence policy | project deterministic Control Plane | AVAILABLE -> ACTIVE -> AUTHORIZED, scope/consequence checks, operation identity, bounded grants | external model/procedure/extension/tool/worker output granting itself authority | authority must remain stable across interchangeable executors/adapters/workers | `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `SECURITY_POLICY.md`, `MODULE_SELECTION_POLICY.md` | `PROJECT_OWNED` |

## How to compare a new mechanism

For each affected existing role, the Stage Research Brief should answer:

```text
prior role / selected source
 -> exact expected guarantee
 -> current evidence/failure model
 -> credible alternatives
 -> duplication/delegation check
 -> exactly one lineage decision: KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT
```

For a role absent from this baseline at the start of the stage, record it as `NEW_ARCHITECTURE` in the Brief and run the Scope Expansion Gate. Scope labels such as `NARROW`, `EVALUATION_ONLY` or `MANUAL` belong in the reason/scope text, not as second lineage decisions.

For a source-code reference role, identify the exact upstream ref, implementation paths/symbols, tests/failure evidence and any material lifecycle piece not open/not found. Use `.agents/skills/source-code-research/SKILL.md`.

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

The research must determine which procedure-local mechanics should be reused from OpenAdapt, which do not cover ambiguous external side effects or the exact failure model, and which project-owned boundaries must remain independent. A custom recovery mechanism is acceptable only after this comparison explains why it is not unnecessary duplication of the selected upstream role.

## Example: bounded Agent Session / Delegation

A worker/session stage must not compare only provider APIs or chat DOM selectors. It must compare:

```text
general planning                     -> ordinary ChatGPT
bounded delegation lifecycle         -> project Agent Session state
provider/browser adaptation          -> narrow provider adapter below identity/state
local persistence/concurrency        -> accepted Stage 26.3C primitives
capability-spanning state            -> project WorkingState
transition/completion authority      -> project Verification Kernel / Finish Gate
external host implementations        -> source-code reference only unless separately adopted
```

Reviewer-specific identities/results/authority stay consumer policy. Reusing a Temporary Chat transport experiment does not make reviewer semantics generic, and implementing one fresh worker does not authorize fan-out, automatic parent wake or a second planner.

## Update policy

Update this baseline only when a reviewed architecture/research decision changes a role assignment, selected reuse source, project-owned boundary, or replacement/defer condition.

When a Stage Research Brief concludes `REPLACE`, `REJECT`, `REUSE_MORE`, or a material `REFINE` for an existing row, the adopting PR must update this baseline **before or with merge**. Do not leave a known superseded lineage in the canonical baseline for a later synchronization PR.

Do not turn this document into:

- a second `MODULE_CATALOG.md` with runtime status dumps;
- a duplicate `ROADMAP.md`;
- a dependency lockfile;
- a replacement for detailed ADR/reuse documents;
- proof that a component is currently implemented or physically accepted.

Exact versions/pins that are security/supply-chain critical remain in their lock/config/source-owner documents. Research comparison refs belong in the current Stage Research Brief / source-code evidence, not as mutable snapshot claims in this baseline.

## Relationship to existing documents

- `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` — detailed OpenAdapt/UFO integration rationale and boundaries.
- `MODULE_CATALOG.md` — broad capability/status inventory.
- `MODULE_SELECTION_POLICY.md` — rules for selecting or adapting external components.
- `DECISIONS.md` — ADR-level architecture decisions.
- `ARCHITECTURE.md` / `CONTROL_PLANE.md` — durable product/authority boundaries.
- `CODEX_AGENT_HOST_SOURCE_REVIEW.md` — pinned source-code evidence establishing Codex as a reference-only Agent Host/session/Persistent/orchestration comparison point and recording the unresolved wake/scheduler boundary.
- `AGENT_SESSION_DELEGATION_REENTRY.md` — current bounded Track M lineage decisions and first one-manager/one-read-only-worker NARROW boundary.
- `CONVERSATION_BRIDGE_ARCHITECTURE.md` — broader provider/chat/session design ideas that remain subordinate to the current bounded Agent Session decision.
- `IOT_PHYSICAL_DEVICE_CAPABILITY_RESEARCH.md` — pinned source/code research establishing the future Physical Device / IoT normalization role and Home Assistant as the first candidate to revalidate before adoption.
- `AUTOMATIC_REVIEWER_RESEARCH.md` — reviewer-specific launch/local-result lifecycle, qualified reviewer authority, direct filesystem/IndexedDB solution evidence and Harbor evaluation seam retained above generic worker lifecycle.
- `.agents/skills/source-code-research/SKILL.md` — exact-ref code archaeology and source-code evidence rules for public implementations.
- this document — **canonical prior-decision baseline used by future Stage Research comparisons**.

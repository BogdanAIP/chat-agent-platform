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
5. assign **exactly one** canonical lineage decision per affected existing role:
   - `KEEP`;
   - `REUSE_MORE`;
   - `REFINE`;
   - `REPLACE`;
   - `DEFER`;
   - `REJECT`;
6. if no baseline role exists, say `NEW_ARCHITECTURE` and run the normal Research Scope Expansion Gate instead of inventing a compound lineage label;
7. record scope qualifiers separately from the canonical decision.

`REPLACE` and `REJECT` require explicit evidence. The fact that a new component exists, is newer, or is fashionable is not sufficient.

Role-level `DEFER` is distinct from the top-level Stage Research decision `DEFER`. A role may be marked `DEFER` only when it is explicitly outside the implementation scope selected by the Brief. If that role is required to satisfy the current stage goal or a release-critical guarantee, the Brief cannot return `PROCEED` or `NARROW` while leaving the role deferred.

A baseline row is history plus a current comparison starting point, not automatic implementation authority.

When a baseline role points to a public **reference implementation**, and `.agents/skills/source-code-research/SKILL.md` applies, the comparison must inspect source code at an exact commit/tag. README/docs-level familiarity alone does not revalidate that lineage.

## Canonical role map

The final column is deliberately either one canonical lineage decision or `NEW_ARCHITECTURE`. Do not encode scope qualifiers in that column.

| Architectural role | Prior selected source / owner | Intended reuse | Explicitly not delegated | Original reason / value | Detailed owner | Canonical lineage posture |
|---|---|---|---|---|---|---|
| General planning / novel strategy | ordinary ChatGPT | open-ended task interpretation, strategy, replanning | local deterministic authority, effect verification, Finish Gate | keep one current general planner while local execution stays deterministic and bounded | `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `DECISIONS.md` | `KEEP` |
| Chat reachability | OpenAI Secure MCP Tunnel + official tunnel-client | normal ordinary-Chat transport/reachability | planner, capability authorization, semantic tool authority | accepted real Chat route with less custom ingress infrastructure | `ARCHITECTURE.md`, `DIRECT_SEMANTIC_TUNNEL.md`, `DECISIONS.md` | `KEEP` |
| Internal MCP aggregation / extension lifecycle | 1MCP or qualified replacement | optional discovery, aggregation, enable/disable, backend lifecycle/health | baseline transport, public raw tool catalog, trust, authorization, persistent tunnel ownership | reuse generic extension infrastructure without putting it on the critical six-tool path | `MODULE_SELECTION_POLICY.md`, `ARCHITECTURE.md`, `DECISIONS.md` | `KEEP` |
| Browser semantic execution | Playwright behind project semantic Browser capability | browser navigation, DOM/AX state, bounded page interaction mechanics | planning, project authority, task completion | mature browser automation with strong structural state; keep project verification boundary | `ARCHITECTURE.md`, `BROWSER_HARNESS_ARCHITECTURE.md`, `MODULE_CATALOG.md` | `KEEP` |
| Local visual specialist runtime | llama.cpp + LFM2.5-VL family | bounded local perception/grounding proposals when structural evidence is insufficient | planner, action authorization, verification authority | local, replaceable, task-driven specialist perception with bounded authority | `LOCAL_SPECIALIST_INFERENCE.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `KEEP` |
| Procedure compiler / workflow IR | OpenAdapt Flow | `Workflow` / `ProgramGraph`, demonstration compile, deterministic healthy-path replay | project WorkingState, project capability authority, project Finish Gate | avoid rebuilding mature procedure IR/compiler/replay machinery | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `KEEP` |
| Procedure-local checkpoint / durable resume mechanics | OpenAdapt Flow where its semantics fit | checkpoint/resume of one compiled procedure; procedure-local execution reporting | capability-spanning WorkingState, cross-capability recovery authority, permission/grant state | reuse mature procedure-local resume mechanics while keeping project state above the vendor runtime | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_SELECTION_POLICY.md` | `KEEP` |
| Procedure/effect evidence | OpenAdapt effect-verifier mechanics through a narrow project adapter | upstream effect-contract/effect-verifier observations as provenance-bearing evidence | unconditional mapping of upstream verdict to project `PASS`; task `DONE` | reuse mature effect-evidence mechanics while project Kernel remains final transition judge | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | `KEEP` |
| Human desktop demonstration capture | OpenAdapt Capture + Flow adapter | local demonstration capture and inputs for candidate procedure compilation | automatic trust/promotion, cloud dependency, task completion authority | avoid writing recorder/capture stack from scratch; defer trust to project evidence | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `STAGE26_PROCEDURAL_MEMORY.md`, `MODULE_CATALOG.md` | `KEEP` |
| Windows / Office application mechanics | selective Microsoft UFO/UFO²-derived UIA, Win32, WinCOM and app-specific patterns | focused Excel/Word/PowerPoint/Outlook/native adapter mechanics where stronger than generic GUI action | UFO planner hierarchy/completion authority/Galaxy orchestration | reuse expensive app-specific mechanics without importing a second planner | `EXTERNAL_EXECUTION_REUSE_STRATEGY.md`, `MODULE_CATALOG.md` | `KEEP` |
| Physical device / IoT normalization and bounded execution | Home Assistant as preferred first candidate | device/entity normalization, registry identity, state/event observation, bounded service/action mechanics | project Control Plane authority, WorkingState, Verification Kernel, Finish Gate, raw service catalog | avoid vendor-by-vendor drivers while preserving command-vs-observed-state separation | `IOT_PHYSICAL_DEVICE_CAPABILITY_RESEARCH.md`, `MODULE_SELECTION_POLICY.md`, `ROADMAP.md` | `KEEP` |
| Multi-chat / provider conversation extraction and browser adaptation | CtxPort-derived ideas plus project Browser Companion / `GenericChatAdapter` direction | extraction/profile-registry/handoff/context-normalization ideas | transcript/provider UI as source of truth or control plane | reuse cross-provider ideas while keeping identity/authority project-owned | `CONVERSATION_BRIDGE_ARCHITECTURE.md`, `MODULE_CATALOG.md`, `DECISIONS.md` | `KEEP` |
| Agent session / long-lived host lifecycle and orchestration | `openai/codex` reference implementation | App Server/thread lifecycle, resume/fork, persistent context, parent/child ownership, async messaging | project authority/state/verification/Finish Gate, broad external-agent authority, unresolved wake semantics | mature reference layer that complements project consequence/control layer | `CODEX_AGENT_HOST_SOURCE_REVIEW.md`, `CONTROL_PLANE.md`, `ROADMAP.md` | `KEEP` |
| Automatic-review local concurrent ownership | accepted Stage 26.3C OS-backed cooperating-runner lock | exact-operation single-writer before genesis/state access and through launch/result/fallback decisions | persistence durability, browser-tab ownership, generic lease system | reuse accepted lock instead of a second local concurrency framework | `AUTOMATIC_REVIEWER_RESEARCH.md`, `CURRENT_STATE.md` | `REUSE_MORE` |
| Automatic-review immutable operation genesis | accepted Stage 26.3C `_exclusive_create_file` mechanic | exclusive-created/fsynced exact identity + private run nonce retained for v1 | mutable transition state, power-loss durability, hostile deletion detection | distinguish first creation from missing mutable state | `AUTOMATIC_REVIEWER_RESEARCH.md`, `CURRENT_STATE.md` | `REUSE_MORE` |
| Automatic-review mutable operation/result state | accepted Stage 26.3C `_write_checkpoint` / `_load_checkpoint` / identity-validation pattern | sibling-temp/flush/fsync/replace + strict genesis/state/result validation | machine/power-loss guarantee, SQLite/WAL/event-log framework, browser Send ownership | reuse accepted local process-crash state for launch/result/manual-fallback lifecycle | `AUTOMATIC_REVIEWER_RESEARCH.md`, `CURRENT_STATE.md` | `REUSE_MORE` |
| Automatic-review deep-link/composer mechanics | PR #138 experiment | run-bound fresh-chat delivery/composer mechanics | page-local ownership, general scheduler authority | keep physically demonstrated UI mechanics but strengthen ownership around them | `AUTOMATIC_REVIEWER_RESEARCH.md` | `REFINE` |
| Automatic-review browser Send ownership | MV3 service worker + extension-origin IndexedDB unique-key transaction | one durable same-run claim across tabs; only committed `add(review_run_id)` claimant may Send | local launch ownership, general browser DB/runtime authority | browser tabs form a separate concurrency domain | `AUTOMATIC_REVIEWER_RESEARCH.md` | `NEW_ARCHITECTURE` |
| Automatic-review reviewer authority qualification | dedicated reviewer security context with GitHub mutation actions unavailable | prove write actions absent via disconnect/disable or supported read-only Action Control | per-message non-selection, approval prompts, prompt prohibition | deterministic least privilege requires action unreachability, not voluntary non-use | `AUTOMATIC_REVIEWER_RESEARCH.md`, `.agents/skills/code-review/SKILL.md` | `NEW_ARCHITECTURE` |
| Automatic-review local result submission/reconciliation | fixed `submit_independent_review_result_v1` + `reconcile_independent_review_result_v1` behind `procedure_run` | store/consume automatic result locally; atomically close manual fallback against late submit | GitHub comment publisher, callback server, generic result bus | eliminate external POST ambiguity and reuse local crash/reconciliation boundary | `AUTOMATIC_REVIEWER_RESEARCH.md`, `.agents/skills/code-review/SKILL.md`, `CURRENT_STATE.md` | `NEW_ARCHITECTURE` |
| Automatic independent-review launch / correlation | `procedure_run` + accepted local primitives + refined PR #138 mechanics | one exact-head operation, private run id, fresh-chat delivery, no blind relaunch | scheduler/event bus, arbitrary launcher, same-task developer wake, worker rotation | remove routine launch/paste while keeping identity/recovery bounded | `AUTOMATIC_REVIEWER_RESEARCH.md`, `CURRENT_STATE.md`, `ROADMAP.md` | `REFINE` |
| Code-review evaluation harness | Harbor custom-agent/task/environment/verifier interfaces | reproducible external reviewer evaluation, frozen tasks, custom CAP adapter, metric/result collection | production launch, GitHub authority, review acceptance, Control Plane authority | avoid building benchmark runner while keeping evaluation separate from production lifecycle | `AUTOMATIC_REVIEWER_RESEARCH.md`, `ROADMAP.md` | `NEW_ARCHITECTURE` |
| Capability-spanning operational state | project-owned `WorkingState` | constraints, progress, provenance/freshness, evidence refs, recovery history, budgets, grants/procedure refs | OpenAdapt procedure state, provider/session stores, private chain-of-thought | no external runtime spans full product authority/state boundary | `CONTROL_PLANE.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `DECISIONS.md` | `KEEP` |
| Transition verification authority | project Verification Kernel | current-state binding, fresh same-stream evidence, ExpectedEffect, `PASS | FAIL | UNKNOWN` | external verifier/model/procedure self-declared success | project policy must remain able to reject stale/mismatched evidence | `CONTROL_PLANE.md`, `STAGE26_3B_VERIFICATION_KERNEL.md`, `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` | `KEEP` |
| Task completion authority | project independent Finish Gate | fresh goal/safety/constraint evidence -> `DONE | NOT_DONE | UNKNOWN` | planner/procedure/worker self-reported completion | transition success and task completion differ | `CONTROL_PLANE.md`, `ROADMAP.md`, `DECISIONS.md` | `KEEP` |
| Capability authorization / consequence policy | project deterministic Control Plane | AVAILABLE -> ACTIVE -> AUTHORIZED, scope/consequence checks, operation identity, bounded grants | external model/procedure/extension output granting itself authority | authority must remain stable across interchangeable executors | `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `SECURITY_POLICY.md`, `MODULE_SELECTION_POLICY.md` | `KEEP` |

## How to compare a new mechanism

For each affected existing role:

```text
prior role / selected source
 -> exact expected guarantee
 -> current evidence/failure model
 -> credible alternatives
 -> duplication/delegation check
 -> exactly one canonical lineage decision: KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT
```

For a new role, record `NEW_ARCHITECTURE` and run the Scope Expansion Gate; do not force it into a compound lineage decision.

For a source-code reference role, also identify exact upstream ref, implementation paths/symbols, tests/failure evidence, and any material lifecycle piece not open/not found. Use `.agents/skills/source-code-research/SKILL.md`.

## Example: Stage 26.3C procedure recovery

A Stage 26.3C consumer that changes procedure restart/recovery must compare against:

```text
procedure-local checkpoint/resume     -> OpenAdapt Flow selected candidate
procedure/effect evidence             -> OpenAdapt effect-verifier mechanics selected candidate
capability-spanning recovery state    -> project WorkingState
transition authority                  -> project Verification Kernel
completion authority                  -> project Finish Gate
```

The research must determine which procedure-local mechanics should be reused, which do not cover ambiguous external side effects or the exact failure model, and which project-owned boundaries remain independent.

## Update policy

Update this baseline only when a reviewed architecture/research decision changes a role assignment, selected reuse source, project-owned boundary, or replacement/defer condition.

When a Stage Research Brief concludes `REPLACE`, `REJECT`, `REUSE_MORE`, or a material `REFINE` for an existing row, the adopting PR must update this baseline **before or with merge**.

Do not turn this document into a second module catalog, roadmap, lockfile, or proof of physical acceptance.

## Relationship to existing documents

- `EXTERNAL_EXECUTION_REUSE_STRATEGY.md` — detailed OpenAdapt/UFO integration rationale and boundaries.
- `MODULE_CATALOG.md` — broad capability/status inventory.
- `MODULE_SELECTION_POLICY.md` — rules for selecting or adapting external components.
- `DECISIONS.md` — ADR-level architecture decisions.
- `ARCHITECTURE.md` / `CONTROL_PLANE.md` — durable product/authority boundaries.
- `CODEX_AGENT_HOST_SOURCE_REVIEW.md` — pinned Codex reference-only lifecycle evidence.
- `IOT_PHYSICAL_DEVICE_CAPABILITY_RESEARCH.md` — Physical Device / IoT normalization research.
- `AUTOMATIC_REVIEWER_RESEARCH.md` — bounded automatic-review launch/local-result lifecycle, qualified reviewer authority, filesystem/IndexedDB solution evidence and evaluation plan.
- `.agents/skills/source-code-research/SKILL.md` — exact-ref code archaeology rules.
- this document — canonical prior-decision baseline for future Stage Research.

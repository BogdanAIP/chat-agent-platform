# Start Here — authoritative continuation entry

Use this file only after resolving live GitHub state. It is a navigation/entry document, not a second current-state snapshot.

Before planning implementation, follow the mandatory repository-skill bootstrap in `AGENTS.md`: enumerate `.agents/skills/*/SKILL.md` from the current ref, inspect triggers and load every applicable skill before planning/production edits. Re-run after `main` advances, rebase, a new stage/substage, or a material task change.

## Minimal read set

1. `CURRENT_STATE.md`
2. `ROADMAP.md`
3. `PROJECT_RISKS.md`
4. `ARCHITECTURE.md` only when the task changes or depends on architecture

Additionally read `ARCHITECTURE_REUSE_BASELINE.md` whenever `stage-research` applies or work may duplicate, replace, refine or cross a previously selected external-component/project-owned role.

Read `EVIDENCE_INDEX.md`, `TECH_DEBT.md`, security/acceptance docs, future ADRs and historical Stage records only when the current task needs them.

`CONTINUATION_CONTEXT.md` is a convenience orientation aid and is subordinate to live GitHub state + `CURRENT_STATE.md`.

## Current boundary in one line

Stage 26.3B is accepted/closed for its recorded representative scope, and Stage 26.3C is accepted/closed for its declared production process-restart/local-Windows scope through merged PR #126.

The next immediate development priority is the bounded **Agent Session / Delegation** mechanism selected by fresh Stage Research in PR #149: one ordinary-ChatGPT manager -> one genuinely fresh read-only worker -> one bounded delivery -> one correlated result when captured. PR #149 remains Draft/unaccepted until its required exact-head semantic review, target-Windows ordinary-Plus physical qualification and final hosted gates pass.

The accepted reviewer-specific state/procedures from #140-#142 remain intact as specialist release-assurance fallback. They are no longer the product-level generic session/runtime owner and must not be silently generalized into arbitrary worker lifecycle semantics.

For the active PR/design/check details, read `CURRENT_STATE.md` and resolve live GitHub state rather than copying a snapshot from this file.

## Current public route

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> canonical semantic projection
 -> deterministic Control Plane / focused capabilities
```

Current Chat-facing tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Ordinary ChatGPT is the only current general planner/intelligence. The deterministic Control Plane owns bounded execution state/policy, authorization, ExpectedEffect verification, reconciliation/recovery/LoopGuard/budgets and independent completion checks for already-selected transitions.

A delegated worker is a bounded specialist. Its output is data returned to the manager; it does not become a second project planner, Control Plane authority, Verification Kernel or Finish Gate.

## Stage Research before implementation

For a new release-critical stage/substage, major subsystem/capability family or material persistence/recovery/retry/concurrency/identity/security/authority change, use `.agents/skills/stage-research/SKILL.md` before production implementation.

A valid Brief ends in:

```text
PROCEED
NARROW
DEFER
```

Only `PROCEED` or `NARROW` opens implementation; `DEFER` keeps it blocked.

Required research shape includes:

```text
current repo/runtime/evidence
 -> Architecture Lineage comparison against ARCHITECTURE_REUSE_BASELINE.md
 -> architecture primitive + engineering-domain map
 -> separate problem vs solution evidence
 -> strong alternatives + failure evidence
 -> failure/crash matrix where applicable
 -> PROCEED / NARROW / DEFER
```

A material new primitive or materially changed persistence/recovery/retry/concurrency/identity/authority design after the Brief invalidates implementation authority and requires research re-entry.

For the current Agent Session / Delegation work, `AGENT_SESSION_DELEGATION_REENTRY.md` is the generic **NARROW** foundation authority. `AGENT_SESSION_PROFILE_BOUNDARY_REENTRY.md`, `AGENT_SESSION_PRE_SEND_RESTART_FENCE.md` and the latest `AGENT_SESSION_TEMPORARY_EPHEMERAL_REENTRY.md` refine the first `chatgpt-temporary` adapter. The latest re-entry supersedes the earlier requirement for positive same-Temporary-conversation recovery across complete Chrome restart after target-Windows evidence failed to expose a stable provider conversation identity.

The authorized first scope remains one manager, one fresh read-only worker, one bounded delegation/delivery and one generic terminal result when trustworthy result capture succeeds. Nested/fan-out workers, mutating children, project/worktree/environment creation, a generic scheduler/event bus, long-lived worker pools, persistent existing-session delivery and automatic same-task parent wake/resampling remain outside that authority.

`fresh_readonly_worker_v1` is an **ephemeral one-shot independence profile**. Its durable browser claim preserves one-Send exclusion and same-live-worker pre-Send ownership, but complete browser/service-worker lifetime loss never reconstructs Send or monitor authority. If result capture was interrupted, the durable delegation remains fail-closed/open rather than fabricate a result or silently launch another worker.

`AUTOMATIC_REVIEWER_RESEARCH.md` / merged #140 remains the reviewer-specific NARROW authority for reviewer semantics and fallback procedures. It does not replace the generic Agent Session Brief, and the generic Brief does not erase reviewer-specific exact-PR/result/authority requirements.

## Architecture lineage rule

For every affected baseline role, record one of:

```text
KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT
```

Role-level `DEFER` cannot hide a requirement needed by an overall `PROCEED`/`NARROW` decision. Accepted lineage changes update the baseline in the adopting PR before/with merge.

The current PR #149 must therefore keep `ARCHITECTURE_REUSE_BASELINE.md` synchronized with the Stage Research decisions that promote/refine the former future Track M session role and reuse accepted local persistence/concurrency mechanics.

## Agent Session first-scope invariant

```text
manager selects one bounded subgoal
 -> deterministic provider-independent delegation identity
 -> private durable run capability
 -> durable launch-attempt before physical child creation
 -> positively qualified fresh read-only child
 -> one browser/provider delivery claim
 -> one project-local delivery claim
 -> exactly one initial Send authority
 -> delivered | unknown observation
 -> no blind re-Send
 -> same-delivery reconciliation only from fresh evidence
 -> exact generic WORKER_RESULT_V1 correlation when captured
 -> durable terminal closure only from that correlated result
```

For the first `chatgpt-temporary` adapter, installed/runtime extension bytes must match the exact expected source set before Send and be revalidated before terminal browser-result capture. A provider UI or extension does not grant itself project authority. Complete browser-context loss is a fail-closed interruption for this profile, not a persistent-session recovery promise.

Persistent rich-context ordinary-ChatGPT conversation identity, browser wake and cross-restart existing-session delivery remain future research. After #149, the parked Prime research branch is refreshed and exact-source Stage Research decides the CAP/Prime ownership boundary before implementing a generic persistent-session remainder.

## Computer-use invariant

```text
semantic/native state first
 -> selective visual evidence when needed
 -> bounded authorized action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> reconcile ambiguous outcome before retry
 -> typed bounded recovery / LoopGuard / budgets
 -> structured WorkingState
 -> independent Finish Gate
```

WorkingState stores structured operational state, never private chain-of-thought.

## Merge rule

For material runtime/security/recovery/authority/acceptance changes:

```text
stage-research when applicable
 -> implementation
 -> focused tests
 -> preliminary required hosted CI on intended head
 -> freeze exact BASE_SHA + HEAD_SHA
 -> required fresh ordinary-ChatGPT semantic review via code-review skill
 -> optional Codex Review when available
 -> validate/fix findings
 -> material fixes invalidate the prior review
 -> fresh exact-head ChatGPT review
 -> final exact-head CI / required physical acceptance
 -> verify reviewed refs still match
 -> merge
```

The fresh ordinary-ChatGPT review is the primary required semantic review. Codex Review is additional evidence when available and quota exhaustion does not substitute for or block the primary review.

The existing automatic-review procedures may later become a specialist consumer of an accepted generic bounded Agent Session path, but only after a separate migration proves that reviewer freshness, exact repository/PR/BASE/HEAD binding, least privilege, `REVIEW_RESULT_V1`, stale handling and manual fallback remain intact. MimiSeek may likewise consume the fresh-worker capability without moving review-job semantics into CAP; returning to an existing project conversation is a separate persistent-session capability.

Documentation/process-only changes do not require a physical gate unless they change acceptance/runtime authority. Material changes to merge/review semantics remain review-significant under `AGENTS.md`.

`AGENTS.md` owns development/merge method. `CURRENT_STATE.md` owns live accepted/current boundary. `ROADMAP.md` owns release order. `DOCUMENT_STATUS.md` owns document roles.

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

Stage 26.3B is accepted/closed for its recorded representative scope; Stage 26.3C WorkingState/reconciliation/budget/LoopGuard L1 foundation is accepted through #124; current release-critical work is production/restart integration of that accepted foundation.

For the active PR/design/check details, read `CURRENT_STATE.md` and resolve the live PR rather than copying that snapshot here.

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

## Architecture lineage rule

For every affected baseline role, record one of:

```text
KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT
```

Role-level `DEFER` cannot hide a requirement needed by an overall `PROCEED`/`NARROW` decision. Accepted lineage changes update the baseline in the adopting PR before/with merge.

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

For runtime/security/recovery/authority changes:

```text
stage-research when applicable
 -> implementation
 -> focused tests
 -> required hosted CI on exact head
 -> Codex Review / independent review when required and available
 -> fix findings
 -> repeat review after material fixes where appropriate
 -> final exact-head CI / required physical acceptance
 -> merge
```

Documentation/process-only changes do not require a physical gate unless they change acceptance/runtime authority.

`AGENTS.md` owns development/merge method. `CURRENT_STATE.md` owns live accepted/current boundary. `ROADMAP.md` owns release order. `DOCUMENT_STATUS.md` owns document roles.

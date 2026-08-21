# Handoff

## Read first

- `AGENTS.md`
- `project-context/CONTINUATION_CONTEXT.md`
- `project-context/START_HERE.md`
- `project-context/CURRENT_STATE.md`
- `project-context/ARCHITECTURE.md`
- `project-context/CONTROL_PLANE.md`
- the active stage contract named by `START_HERE.md`

## Context freshness check

Before continuing, record:

- current `main` SHA;
- active stage;
- current branch / PR / HEAD, if any;
- which older documents are historical and must not override active context;
- whether the public Chat tool schema changed since the last ordinary-Chat acceptance.

Do not continue from a dated handoff or old stage document without reconciling against current GitHub state and authoritative context.

## Goal

## Current branch / PR / HEAD

## Current `main`

## Active stage contract

## What is already accepted

## What is explicitly not accepted yet

## Current blocker / next gate

## Relevant files

## Historical files that must not override current state

## General planner boundary

State explicitly:

- current general planner (normally ordinary ChatGPT);
- whether any specialist reasoning/model is involved;
- whether future Track P local-planner research is relevant (`none`, `shadow research`, `bounded research`, `accepted optional mode`).

A specialist or future planner proposal is never action authorization by itself.

## Deterministic Control Plane status

State explicitly which of these exist/are only planned:

```text
TaskState
selected procedure/ProgramGraph state
capability policy/authorization
checkpoints
verifier/postconditions
bounded retry/recovery
resource/action/time budgets
escalation rules
```

Do not use `Control Plane` as a synonym for `local planner`.

## Constraints / architecture invariants

## Acceptance criteria

## Tests / CI required

## Real user-machine / ordinary-Chat gate

State explicitly: `required`, `passed with evidence`, or `not applicable`. Never infer physical acceptance from CI.

## Public tool-contract impact

State explicitly: `none`, `schema-only`, `new/removed tool names`, or `undecided pending architecture gate`.

Any exported Chat tool/schema/annotation change requires explicit Refresh/review and real ordinary-Chat acceptance where applicable.

## Privacy / stored-context impact

If work records task state, trajectories, screenshots, user content or reusable procedures, state redaction/retention/deletion/encryption rules and confirm private reasoning is excluded.

## Procedure trust / progression impact

State:

- procedure trust state (`candidate`, `trusted`, `stale`, `quarantined`, etc.);
- whether local deterministic progression is allowed;
- verifier/postcondition that permits each advance;
- exact conditions that force ABSTAIN/escalation.

## Expected output

## Architecture impact

`yes` / `no`.

If `yes`, synchronize at least:

- `CONTINUATION_CONTEXT.md`
- `START_HERE.md`
- `CURRENT_STATE.md`
- `ARCHITECTURE.md`
- `CONTROL_PLANE.md` when relevant
- `ROADMAP.md`
- relevant ADR/security/constraint docs
- active stage document

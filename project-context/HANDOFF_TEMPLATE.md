# Handoff

## Read first

- `AGENTS.md`
- `project-context/START_HERE.md`
- `project-context/CURRENT_STATE.md`
- the active stage contract named by `START_HERE.md`

## Context freshness check

Before continuing, record:

- current `main` SHA;
- active stage;
- current branch / PR / HEAD, if any;
- which older documents are historical and must not override the active contract;
- whether the public Chat tool schema changed since the last ordinary-Chat acceptance.

Do not continue from a dated handoff or older stage document without reconciling it against `START_HERE.md` and current GitHub state.

## Goal

## Current branch / PR / HEAD

## Current `main`

## Active stage contract

## What is already accepted

## What is explicitly not accepted yet

## Current blocker / next gate

## Relevant files

## Historical files that must not override current state

## Constraints / architecture invariants

## Acceptance criteria

## Tests / CI required

## Real user-machine / ordinary-Chat gate

State explicitly: `required`, `passed with evidence`, or `not applicable`. Never infer it from CI.

## Public tool-contract impact

State explicitly: `none`, `schema-only`, `new/removed tool names`, or `undecided pending architecture gate`.

Any exported Chat tool/schema/annotation change requires explicit Refresh/review and real ordinary-Chat acceptance of the changed surface.

## Privacy / stored-context impact

If the work records trajectories, screenshots, user content, skill memory or other persistent context, state redaction/retention/deletion rules and whether private reasoning is excluded.

## Expected output

## Architecture impact

`yes` / `no`; if `yes`, update/add the relevant ADR and synchronize `START_HERE.md`, `CURRENT_STATE.md`, active stage contract and `ROADMAP.md`.

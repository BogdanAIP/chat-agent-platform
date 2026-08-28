# Start Here — authoritative continuation guide

Use this file only after resolving live GitHub state. Recorded prose is not a substitute for live `main`, relevant open PRs/exact heads, hosted checks or required physical evidence.

Before planning implementation, follow the mandatory repository-skill bootstrap in `AGENTS.md`: enumerate `.agents/skills/*/SKILL.md` from the current ref, resolve applicable triggers and load matching skills before planning/production edits. Re-run the bootstrap after `main` advances, rebase, a new stage/substage, or a material task change.

## Minimal read set

For ordinary continuation:

1. `CURRENT_STATE.md`
2. `ROADMAP.md`
3. `PROJECT_RISKS.md`
4. `ARCHITECTURE.md` only when the current task changes or depends on architecture

Additionally read `ARCHITECTURE_REUSE_BASELINE.md` whenever `stage-research` applies or work may duplicate, replace, refine or cross a previously selected external-component/project-owned role.

Read `EVIDENCE_INDEX.md`, `TECH_DEBT.md`, security/acceptance docs, future ADRs and historical Stage documents only when the current task needs them.

The repository should not require reconstructing the full build history before continuing current work.

## Current boundary

Stage 26.3B is accepted/closed for its recorded representative scope.

Stage 26.3C has already begun: the project-owned WorkingState/typed reconciliation/budget/LoopGuard/StagnationReport **L1 foundation is accepted and merged through #124**.

The current release-critical task is the first bounded production integration/restart-reconciliation slice, not creation of the WorkingState model from zero. At this snapshot draft #126 carries that work; always resolve its live state before acting.

Exact accepted physical heads and machine-local evidence locators belong in `EVIDENCE_INDEX.md`, not here.

## Current product boundary

The accepted Chat-facing surface remains exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> canonical semantic projection
 -> deterministic Control Plane / focused capabilities
```

Ordinary ChatGPT is the only current general planner/intelligence. The deterministic Control Plane owns bounded execution state/policy, authorization, ExpectedEffect verification, reconciliation/recovery budgets and independent completion checks for already-selected transitions.

## Stage Research before implementation

For a new release-critical stage/substage, major subsystem, capability family or material persistence/recovery/retry/concurrency/identity/security/authority change, use `.agents/skills/stage-research/SKILL.md` before production implementation.

A valid Stage Research Brief ends in:

```text
PROCEED
NARROW
DEFER
```

Only `PROCEED` or `NARROW` opens implementation. `DEFER` keeps it blocked.

Current research flow:

```text
resolve current repo/runtime/evidence
 -> compare affected roles with ARCHITECTURE_REUSE_BASELINE.md
 -> enumerate architecture primitives + directly relevant engineering domains
 -> separate problem evidence from solution evidence
 -> research strong approaches + failure reports/postmortems
 -> compare materially distinct alternatives
 -> build failure/crash matrix for persistence/recovery/side-effect/concurrency/authority changes
 -> issue PROCEED / NARROW / DEFER
 -> implement minimum coherent slice
 -> adversarial/acceptance tests
 -> independent review when required/available
 -> exact-head CI + required physical acceptance
```

Future ADRs are design hypotheses plus durable boundary constraints. They are inputs to fresh research, not substitutes for it.

If implementation/tests/review introduce a materially new architecture primitive or materially change persistence/recovery/retry/concurrency/identity/authority semantics, the prior Brief is invalid for further production implementation. Re-enter research before continuing.

## Architecture lineage rule

`ARCHITECTURE_REUSE_BASELINE.md` records prior role assignments such as Playwright, OpenAdapt, UFO-derived mechanics and project-owned WorkingState/Verification/Finish/authorization boundaries.

For every affected role, Stage Research must explicitly decide:

```text
KEEP / REUSE_MORE / REFINE / REPLACE / DEFER / REJECT
```

It is not a veto on better evidence. It prevents silent duplication or replacement of a previously selected mechanism.

A role-level `DEFER` cannot hide a requirement needed by an overall `PROCEED`/`NARROW` decision. Accepted lineage changes must update the baseline in the adopting PR before/with merge.

## Current 26.3C integration boundary

The accepted L1 WorkingState foundation does not itself prove crash-safe production effects.

Current draft #126 is deliberately scoped to process crash/restart for the bounded workspace-artifact procedure. Its fresh Stage Research currently chooses a narrow design based on existing checkpoint/WorkingState semantics, one cooperating task runner, fresh same-stream reconciliation and reconstructible file identity; it explicitly does not claim machine/power-loss transactional durability.

Treat that as draft design until exact-head tests/review/physical acceptance pass.

## Complexity rule

Before adding a framework, workflow, gate, state owner, ADR or documentation owner, ask:

```text
Is this a new capability/guarantee?
Can an existing mechanism express it?
What old complexity will it replace or consolidate?
Does custom code duplicate a role already selected for upstream reuse?
```

Avoid one new infrastructure layer per Stage/CAP/guarantee family. Prefer behavioral/instrumented tests of observable invariants over brittle source-text/order checks where practical.

## Computer-use invariant

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> bounded authorized action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> reconcile ambiguous outcome before retry
 -> typed bounded recovery / LoopGuard / budgets
 -> structured WorkingState
 -> independent Finish Gate
```

WorkingState stores structured operational state, never private chain-of-thought.

## Current Browser scope

The accepted Browser L3 path uses real target-Windows effects through isolated headless Playwright/Chrome. It does not prove control of an already-open visible desktop Chrome session. Visible/attached-browser authority requires its own definition and evidence.

## Future architecture

Track M / Agent Sessions, ADR-036 Browser Harness expansion and ADR-037 CapabilityRegistry/Event/Hook substrate remain future architecture. Their durable authority boundaries are useful; their detailed implementation shapes remain subject to fresh Stage Research when implementation begins.

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

Do not represent unavailable review as completed. Documentation/process-only changes do not require a physical gate unless they change acceptance/runtime authority.

`AGENTS.md` owns development method. `CURRENT_STATE.md` owns live accepted/current boundary. `ROADMAP.md` owns release order. `DOCUMENT_STATUS.md` owns document roles.

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

## Continue from the current owner

`CURRENT_STATE.md` owns the accepted boundary and immediate work. Resolve its
PR references against live GitHub before selecting a task. `ROADMAP.md` owns
release order; `EVIDENCE_INDEX.md` owns exact accepted qualification heads and
locators. Historical Stage briefs explain scoped designs, not live PR status.

Do not keep an active-stage snapshot or a copy of a provider's implementation
and acceptance checklist in this entry point. That duplication previously sent
fresh sessions back to already merged work.

## Invariants

- Ordinary ChatGPT remains the only current general planner.
- The deterministic Control Plane owns authorization and verification.
- The accepted surface remains `workspace_read`, `workspace_write`, `web_open`,
  `web_observe`, `web_interact`, and `procedure_run`.
- Worker/provider output is evidence, not authority or manager task completion.
- Ambiguous effects require reconciliation before retry; `UNKNOWN` never grants
  another Send or action.
- Required fresh ordinary-ChatGPT review, exact-head checks and applicable
  physical gates remain governed by `AGENTS.md`.

For a new stage or material architecture change, load the applicable repository
skills and obtain the required Stage Research decision before production edits.
A research Draft or future ADR does not itself authorize implementation.

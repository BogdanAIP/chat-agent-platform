## Goal

## Current stage / source context

- [ ] Resolved live `main` and relevant PR heads
- [ ] Read `AGENTS.md`, `project-context/CONTINUATION_CONTEXT.md`, `project-context/START_HERE.md`, `project-context/CURRENT_STATE.md`
- [ ] Checked `project-context/DOCUMENT_STATUS.md` before relying on old stage/research docs

## Relevant files

## Constraints

## Planner / Control Plane impact

- [ ] No planner/Control Plane change
- [ ] Deterministic Control Plane change: `CONTROL_PLANE.md` / ADR / tests synchronized
- [ ] Future local-planner Track P research only: proposal/authority boundary stated explicitly

Ordinary ChatGPT remains the only **current general planner** unless a future explicitly accepted ADR changes that. A deterministic local execution Control Plane is allowed/desired and is not a second general planner. Planner/model/procedure output must not bypass capability authorization/verifier gates.

## Acceptance criteria

## Verification

- [ ] Relevant local/unit/acceptance tests run
- [ ] Documentation consistency tests pass
- [ ] Required GitHub Actions checked on the exact functional HEAD
- [ ] Real Windows / ordinary-Chat acceptance is either actually evidenced or explicitly marked still required
- [ ] Synthetic/CI evidence is not mislabeled as physical evidence
- [ ] No invented counters are used as measurements

## Architecture impact

- [ ] No architecture change
- [ ] Architecture change: ADR/project-context updated

## Continuation docs

If this PR changes architecture, planner/Control Plane boundaries, blockers, accepted evidence, stage completion or the next task:

- [ ] `project-context/CONTINUATION_CONTEXT.md` synchronized
- [ ] `project-context/START_HERE.md` synchronized
- [ ] `project-context/CURRENT_STATE.md` synchronized
- [ ] `project-context/ARCHITECTURE.md` synchronized
- [ ] `project-context/CONTROL_PLANE.md` synchronized where relevant
- [ ] `project-context/ROADMAP.md` / `DECISIONS.md` updated where applicable
- [ ] `project-context/DOCUMENT_STATUS.md` updated if document authority/status changed
- [ ] README/security/PR prose does not contradict the current source of truth

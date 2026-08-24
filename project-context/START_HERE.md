# Start Here — authoritative continuation guide

Use this file first in a fresh ordinary ChatGPT session after resolving live repository state.

## Resolve live repository state first

Never treat a documentation SHA as permanently current. Resolve live `main`, then inspect open PR heads relevant to the task.

## Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/ARCHITECTURE.md`
4. `project-context/CONTROL_PLANE.md`
5. `project-context/ROADMAP.md`
6. `project-context/DOCUMENT_STATUS.md`
7. `project-context/EVIDENCE_INDEX.md`
8. `project-context/MODULE_CATALOG.md`
9. `project-context/KNOWN_ISSUES.md`
10. active Stage 26.3 contract/design: `project-context/STAGE26_PROCEDURAL_MEMORY.md`
11. active Stage 26.3A notes/contracts: `project-context/STAGE26_3A_IMPLEMENTATION_NOTES.md` and `project-context/STAGE26_3A_PROCEDURE_RUN_SURFACE.md`
12. accepted Stage 26.2E / Transport Supervisor evidence when exact physical details are needed

When documents disagree, exact code/tests/current CI/physical target evidence outrank prose.

`DOCUMENT_STATUS.md` classifies historical stage/research files. Old `ACTIVE`, `CURRENT`, `NEXT` wording and historical five-tool counts do not override current live context.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly requests them.

## Planner / Control Plane boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The local platform implements a **deterministic execution Control Plane** that owns:

```text
TaskState
selected ProgramGraph/procedure state
capability policy + authorization
checkpoints
verifier/postconditions
bounded retry/recovery
resource/action/time budgets
escalation reason
```

That Control Plane may continue a known, already-selected procedure through multiple current-state-authorized and verified transitions without asking ChatGPT after every low-level action. It must escalate when the environment requires a new strategy or is stale/unknown/ambiguous/incompatible.

This is not a second general planner. See `CONTROL_PLANE.md`.

A future local general planner remains optional Track P and starts shadow/proposal-only after verified procedure-state data and measured need exist.

## Normal path and current public contract

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> canonical six-tool semantic projection
  -> focused local capabilities + deterministic Control Plane
```

The current Stage 26.3A candidate normal semantic route exposes exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray choice between five and six tools.

The old separate `procedure-qualification` profile/projection/direct-tunnel handoff was removed. The public launcher always routes through the canonical six-tool projection. A private five-capability file/browser base may remain internally for implementation/regression purposes only; it is not selectable or Chat-facing.

The ordinary semantic startup guard must inspect live `tools/list` and refuse READY unless the exact six canonical names are present.

The tray has one normal semantic READY state. No separate qualification color/state remains.

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. Generic shell/Python/`tool_invoke` execution remains forbidden.

## Accepted foundation

Stages through 26.2E are accepted only for their exact recorded evidence scope. Transport Supervisor v1 was physically accepted and merged as PR #94.

Accepted `main` foundation after #94:

```text
2f33997d3fbaa1fc52d437c00be7f16e55bdde5e
```

Exact physical heads and result locators are in `EVIDENCE_INDEX.md` and accepted stage/transport evidence documents.

One accepted VS Code task is real-app evidence, not broad desktop accuracy.

## Active work — Stage 26.3A

The current goal is autonomous verified progression of an already-known bounded procedure without using the user as a PowerShell operator.

The first registered procedure is:

```text
verified_workspace_artifact_v1
```

It is exposed through the normal semantic `procedure_run` tool. It accepts only bounded artifact inputs, has a fixed three-transition budget, durable checkpoints and must ABSTAIN rather than overwrite a pre-existing target or guess through incompatible state.

Required first vertical slice:

```text
ONE user goal
 -> normal six-tool semantic route
 -> ordinary ChatGPT selects the known procedure + parameters
 -> local deterministic Control Plane executes multiple verified transitions
 -> NO intermediate PowerShell copy/paste by the user
 -> independent final workspace_read
 -> verified completion OR deterministic ABSTAIN/escalation
```

## Remaining physical gates

After all hosted checks are green on one exact live PR #92 head:

1. install/update that exact head on target Windows;
2. start the **normal** semantic route;
3. verify tray READY and exactly six live tools;
4. ordinary ChatGPT one-goal E2E;
5. actual `procedure_run` success;
6. independent read of the final nested artifact;
7. pre-existing protected target -> structured ABSTAIN;
8. independent read proves zero unauthorized overwrite;
9. record exact physical head/evidence before acceptance.

A manual `workspace_write` fallback does not count as `procedure_run` physical PASS.

The user should not be treated as a routine command relay. Ask the user to act only when the available Chat/local surface genuinely cannot perform an irreducible target-machine or permission step.

## Current critical path

```text
26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime — ACTIVE
    -> 26.3A canonical six-tool runtime — hosted gate then physical one-goal gate
    -> 26.3B advanced verifier/postconditions
    -> bounded recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27/28 distribution and clean-user release
```

Future local planner/offline autonomy is Track P after verified data/need, not a prerequisite for the current stable release.

## Merge policy

Once a branch is logically complete, intended diff is verified, required physical/CI tests pass and applicable acceptance gates pass, merge it without waiting for a separate merge command. Stop on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

## Non-negotiable rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic local execution Control Plane is allowed/desired;
- no current local general planner/autonomous strategy brain;
- model/procedure/planner/observation proposal is not authorization;
- current observed state outranks remembered history;
- verification controls completion;
- stale/ambiguous/UNKNOWN fails closed;
- never persist private chain-of-thought;
- raw desktop capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- release-grade Python/model/OpenAdapt reproducibility is required before stable distribution.

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

`DOCUMENT_STATUS.md` classifies every `project-context/*.md` file. Historical stage/research files may preserve old `ACTIVE`, `CURRENT`, `NEXT` and old stage-numbering text; those phrases are historical when the status map says so and must not override live context.

## Current operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly re-enables them later.

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

## Normal path and public contract

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused local capabilities
```

Current normal public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure. `semantic-projection` is not the procedure Control Plane and may not become an opaque workflow dispatcher.

Stage 26.3A adds `procedure_run` only in the isolated `procedure-qualification` profile. Generic shell/Python/`tool_invoke` execution remains forbidden.

## Accepted Windows foundation through Stage 26.2E

Accepted/merged through Stage 26.2D:

```text
#83 26.1C typed executor
#84 26.1D latency baseline
#85 26.1E window-scoped UIA
#86 context synchronization
#87 26.2A production Windows runtime
#88 26.2B DesktopState
#89 26.2C native Desktop Grounder
#90 26.2D deterministic structure-first vision routing
```

Stage 26.2E real-app E2E is physically accepted on exact runtime/qualification head:

`457db0b634f2e47f53d41e359a238840fa3ca2ee`

Physical evidence directory:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448`

It proved one isolated VS Code task with exact hidden Monaco keyboard focus identity, one-shot window-scoped focus authorization, one guarded Unicode delivery, independent file postcondition and full rollback. This is real-app evidence, not broad desktop accuracy.

## Accepted Transport Supervisor v1 foundation

Transport Supervisor v1 was physically accepted and merged as PR #94. `main` after that merge is:

`2f33997d3fbaa1fc52d437c00be7f16e55bdde5e`

Accepted behavior includes:

- one persistent console-free Windows supervisor;
- persistent user `desired_state` separated from runtime owner receipt;
- bounded owned-tunnel recovery with receipts/heartbeat;
- external network disconnect/reconnect recovery;
- Modern Standby sleep/resume;
- reboot/logon restoration;
- fresh ordinary-Chat post-reboot semantic E2E;
- measured idle resource/recovery latency.

Exact physical heads and result locators are in `EVIDENCE_INDEX.md` and the transport evidence documents.

## Active work — Stage 26.3 Verified Procedure Runtime

The next acceptance target is no longer another single-action script. It is autonomous verified progression of an already-known bounded procedure.

Stage 26.3A currently provides qualification-only `verified_workspace_artifact_v1` through `procedure_run`. The exact code head after integration with accepted #94 was hosted-qualified on all ten PR workflows:

`e4507dbe6dc07e182313769ebe833dd1e6801572`

This is **hosted readiness only**, not physical Stage 26.3A acceptance.

Required first vertical slice:

```text
ONE user goal
 -> ordinary ChatGPT selects the known procedure + parameters
 -> local deterministic Control Plane executes multiple transitions
 -> each transition is authorized from current evidence
 -> each transition has a verifier/postcondition
 -> checkpoints/budgets prevent blind continuation
 -> NO intermediate PowerShell copy/paste by the user
 -> verified completion OR deterministic ABSTAIN/escalation
```

Remaining physical gates:

1. exact-head target-Windows direct-tunnel qualification;
2. ordinary ChatGPT one-goal E2E with no intermediate PowerShell relay;
3. independent final artifact verification through `workspace_read`;
4. pre-existing/incompatible target -> structured ABSTAIN with zero unauthorized overwrite/continuation.

The user should not be treated as a routine command relay. Ask the user to act only when the currently available Chat/local tool surface genuinely cannot perform an irreducible target-machine or permission step.

## Current critical path

```text
26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane integration — ACTIVE
    -> 26.3A hosted qualification — GREEN; physical one-goal gate NEXT
    -> 26.3B advanced verifier/postconditions
    -> checkpoint/recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27/28 distribution and clean-user release
```

Future local planner/offline autonomy is **not deleted from the roadmap**; it is Track P after verified data/need, not a prerequisite for the current stable release.

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

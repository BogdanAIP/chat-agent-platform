# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Exact code/tests/current CI/physical evidence outrank prose.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly requests them.

## Product boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. The local platform has a deterministic execution **Control Plane**, not a second general-planning brain.

```text
ordinary ChatGPT
  task interpretation / strategy / adaptation
        |
        v
OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> canonical six-tool semantic projection
        |
        v
local deterministic execution Control Plane + focused capabilities
```

The Control Plane may keep TaskState/checkpoints, advance a selected verified procedure through already-defined transitions, authorize each consequence, verify effects, apply bounded retry/recovery/resource budgets and escalate. It must ABSTAIN/escalate when current evidence does not uniquely match an allowed transition or new strategy is required.

A true local planner is future optional Track P, not current production architecture and not a Stage 27/28 prerequisite. See `CONTROL_PLANE.md`.

## Current Stage 26.3A candidate public semantic surface

The normal `semantic` route exposes exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray choice between five and six tools.

The old separate `procedure-qualification` route was removed. The public launcher always routes through the canonical six-tool projection. A private five-capability file/browser implementation remains only as an internal implementation/regression layer and is not selectable or Chat-facing.

The ordinary semantic startup guard must refuse READY unless live `tools/list` is exactly the six canonical names.

The tray has one normal semantic READY state; no separate qualification state/color remains.

## Normal transport vs optional extensions

Normal semantic transport is direct stdio and must not depend on 1MCP.

```text
ordinary ChatGPT
 -> Secure MCP Tunnel
 -> official tunnel-client
 -> semantic launcher
 -> six canonical tools
```

The persistent accepted `tunnel_*` id is stored in neutral platform state:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

An existing installed legacy profile at:

```text
%LOCALAPPDATA%\ChatAgentPlatform\tunnel\local-1mcp.yaml
```

may be read only as a bounded migration fallback for one already accepted tunnel id. It is not the normal semantic source of truth and fresh normal bootstrap does not recreate it as the normal route.

Fresh/current normal bootstrap no longer invokes the legacy internal controller `-Action Install` path. It initializes the semantic core directly:

```text
verified tunnel-client + neutral tunnel state
 -> verified six-tool bundle
 -> DPAPI runtime key
 -> existing safe FilesRoot OR %LOCALAPPDATA%\ChatAgentPlatform\workspace
 -> profile = semantic
 -> tunnel binding = direct-stdio
 -> six-tool smoke
 -> stopped
```

After bootstrap, public `Status` and the tray resolve through the direct semantic controller rather than legacy `status-chat-profile.ps1`; they must not query `npx @1mcp/agent` merely to report a stopped normal platform.

Baseline manager metadata records:

```text
semantic_public_tool_count = 6
extension_manager_included = false
```

Historical 1MCP lifecycle scripts/profile definitions remain as compatibility hooks only. Their presence does not mean the Extension Manager is installed or required.

1MCP is retained as an optional internal Extension Manager for future third-party MCP backends:

```text
canonical semantic surface
        |
        +----> project-owned capability / Control Plane
        |
        `----> optional Extension Manager
                    |
                   1MCP
                    |
              third-party MCP backends
```

1MCP may later handle backend discovery/aggregation, enable-disable, lazy lifecycle, health and restart. Its absence/failure must not block baseline six-tool bootstrap/start/status/health/smoke. Raw backend tools are not exported directly to ordinary ChatGPT; supported extensions remain behind project-owned typed semantic facades and the same authorization boundary.

Canonical operational contract: `EXTENSION_MANAGER.md`.

---

# Accepted foundation

## Stage 24 / 24.1 — typed semantic file/browser foundation and direct tunnel — ACCEPTED

Historical five-tool file/browser semantics, Windows lifecycle and direct stdio transport are accepted foundations for their exact tested scope. They do not define the current Stage 26.3A public inventory.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — ACCEPTED

Accepted local visual baseline remains structure-first, proposal-only and behind deterministic authorization.

## Stage 26.1A-E / 26.2A-E — Windows capability foundation — ACCEPTED

Accepted Windows work includes OpenAdapt qualification, bounded capture/executor, warm latency characterization, window-scoped UIA, production Windows runtime, DesktopState, native local Grounder, deterministic UIA->vision routing and the first isolated real VS Code application E2E.

Exact physical heads/result directories and scoped measurements are authoritative in `EVIDENCE_INDEX.md` and the accepted historical stage documents.

One accepted VS Code task is not universal desktop accuracy.

## Transport Supervisor v1 — ACCEPTED / MERGED #94

Transport Supervisor v1 is the accepted reliability foundation. It provides persistent desired state/runtime ownership, bounded recovery, console-free Windows persistence and health-driven restart semantics around the normal route.

Accepted `main` foundation after #94:

```text
2f33997d3fbaa1fc52d437c00be7f16e55bdde5e
```

---

# Active release-critical work

## Stage 26.3 — Verified Procedure Runtime / deterministic execution Control Plane — ACTIVE

The current problem is autonomous verified progression of a known procedure without using the user as a PowerShell operator.

Target flow:

```text
user gives one goal to ordinary ChatGPT
 -> ChatGPT selects an allowed known procedure + parameters
 -> procedure_run
 -> local deterministic Control Plane
      load/bind TaskState + ProgramGraph
      observe current state
      select exactly one permitted known transition
      authorize action from current evidence
      execute bounded capability
      re-observe
      verify postcondition
      checkpoint + advance
      repeat while state remains known/permitted
 -> verified completion
    OR ABSTAIN/escalation to ChatGPT
```

### Stage 26.3A — canonical six-tool procedure surface

The first registered procedure is intentionally narrow:

```text
verified_workspace_artifact_v1
```

It accepts only a bounded leaf `.txt` name, bounded UTF-8 content and optional compatible resume task id. Its target scope is:

```text
.chat-agent-platform/stage26-3a/
```

It has a fixed three-action transition budget, independently verifies content and filesystem-object identity, checkpoints durable state and ABSTAINS rather than overwriting a pre-existing target or guessing through incompatible state.

The installed bundle must include the canonical six-tool projection and Control Plane closure and record:

```text
semantic_public_tool_count = 6
extension_manager_included = false
```

Normal bootstrap acceptance now also requires:

```text
semantic binding = direct-stdio
normal semantic 1MCP required = false
legacy 1MCP install path used = false
bootstrap/default public profile = semantic
bootstrap smoke profile = semantic
persistent tunnel source = state/tunnel.json
```

Required baseline CI must not launch or query live 1MCP as a condition of six-tool readiness. Historical local bridge, files/browser switching, conflict cleanup and adaptive activation belong to the separate `Optional Extension Manager Acceptance` workflow.

### Stage 26.3A remaining physical acceptance

After all hosted checks are green on one exact PR #92 code head:

1. install/update that exact head on the target Windows machine;
2. migrate/verify the accepted tunnel id into neutral `state/tunnel.json`;
3. verify normal manager metadata reports `semantic_public_tool_count=6` and `extension_manager_included=false`;
4. verify current settings are `profile=semantic` and `tunnel_profile=direct-stdio`;
5. start the **normal** semantic route;
6. verify one normal tray READY state and exactly six live tools;
7. ordinary ChatGPT one-goal E2E with no intermediate PowerShell relay;
8. actual `procedure_run` success;
9. independent `workspace_read` of the final nested artifact;
10. negative pre-existing-target case -> structured ABSTAIN and independent proof of zero unauthorized overwrite;
11. record exact physical head/result evidence before acceptance.

A manual `workspace_write` fallback does not count as physical acceptance of `procedure_run`.

### Stage 26.3B — advanced verifier/postcondition library

Broaden deterministic completion evidence for UI, files/artifacts, process/window/application state, browser state and structured outputs only after 26.3A physical acceptance.

### Stage 26.3C — checkpoints / bounded recovery / budgets

Longer procedures require explicit checkpoints, retry ceilings, safe known recovery branches, action/time/resource budgets and deterministic escalation reasons.

## Stage 26.4 — Human Demo -> transferable verified candidate skill

Human demonstration transfer follows only after the verified procedure runtime is accepted. Live re-resolution and verifier-controlled progression are required; macro replay is insufficient.

---

# Current critical path

```text
Stage 26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> Stage 26.3 Verified Procedure Runtime — ACTIVE
    -> 26.3A canonical six-tool semantic runtime — hosted gate then physical ordinary-Chat gate
    -> 26.3B advanced verifier/postconditions
    -> 26.3C bounded recovery/budgets as required
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27 distribution/maintenance
 -> Stage 28 clean-user E2E / stable release
```

Future optional Track P may later evaluate a local planner after verified procedure-state data and measured need. It remains behind the same authorization/verifier boundary.

Optional 1MCP Extension Manager development is orthogonal to this release-critical path. It may be used later to reduce integration work for additional MCP backends without re-entering the baseline semantic critical path.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable acceptance gates are satisfied, merge it without waiting for a separate merge command.

Stop on unresolved findings, conflict, ambiguous scope or failed/skipped required evidence.

---

# Residual risks

- Stage 26.3A normal six-tool route is not yet physically accepted on the target Windows machine;
- the neutral tunnel-state/default-semantic migration still requires target-machine verification on the current PR head;
- the optional 1MCP/adaptive extension path is not a baseline release gate and remains less stable than the normal direct semantic route;
- one real VS Code task is not broad real-application coverage;
- `AutomationId` still lacks dedicated accepted physical coverage across real applications;
- browser DNS/rebinding/redirect/private-network isolation remains incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- future local planner has not been researched against verified procedure-state data;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane may advance only already-defined authorized+verified procedure transitions;
- normal semantic install/start/status/health/smoke must not require optional 1MCP extension infrastructure;
- normal bootstrap does not use the legacy 1MCP-oriented controller install path;
- fresh/current normal settings use `semantic` + `direct-stdio`;
- persistent tunnel identity belongs to neutral platform state;
- third-party MCP availability is not trust or authorization;
- raw extension tools are not automatically Chat-facing;
- new strategy/ambiguity/stale/UNKNOWN -> ABSTAIN/escalate;
- semantic/native structure before pixels where reliable;
- model/procedure/observation proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

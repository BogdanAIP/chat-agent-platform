# Stage 26.3A canonical six-tool semantic surface

Status: **ACTIVE IMPLEMENTATION CONTRACT / PHYSICAL ORDINARY-CHAT ACCEPTANCE PENDING**.

## Decision

For the current Stage 26.3A candidate there is one ordinary semantic public surface and it exposes exactly six tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no user-selectable or runtime-selectable `5 tools` versus `6 tools` mode.

The separate `procedure-qualification` profile, qualification projection and qualification handoff path were removed. The normal semantic launcher always routes through the canonical six-tool Control Plane projection.

An internal five-capability file/browser implementation remains only as a private implementation layer behind the canonical projection. It is not a Chat-facing profile, cannot be selected by the tray/manager and is not an alternative public contract.

## Purpose

`procedure_run` gives ordinary ChatGPT one truthful typed capability for asking the deterministic local Control Plane to execute a known bounded procedure through multiple independently verified transitions.

It must not be hidden inside `workspace_write`, `web_interact`, or a generic dispatcher.

The six-tool surface therefore separates two responsibilities:

```text
ordinary ChatGPT
  -> open-ended goal interpretation and procedure selection

canonical semantic projection
  -> five reviewed file/browser semantics
  -> one typed procedure_run semantic

local deterministic Control Plane
  -> exact registered procedure/version
  -> TaskState/checkpoints
  -> current-state authorization
  -> bounded transition execution
  -> verifier/postconditions
  -> completion or ABSTAIN
```

`procedure_run` does not create a second general planner and does not expose arbitrary shell/Python execution.

## Public runtime

The canonical path is:

```text
ordinary ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> semantic-projection-launcher.mjs
  -> semantic-control-plane-projection.mjs
       -> private file/browser semantic base
       -> deterministic Control Plane procedure adapter
```

`semantic-projection-launcher.mjs` always launches `semantic-control-plane-projection.mjs`. There is no conditional entrypoint that chooses a five-tool public surface.

The normal semantic profile declares the permanent `procedure` / `control-plane` capability and still exposes exactly one projection server.

## Credential isolation

The public launcher scrubs tunnel/OpenAI credentials before child execution:

```text
CONTROL_PLANE_API_KEY
OPENAI_API_KEY
OPENAI_ADMIN_KEY
```

The deterministic procedure child receives only the bounded environment required for the reviewed workspace/procedure runtime. Procedure authority must not imply transport-secret inheritance.

## Exact Stage 26.3A procedure schema

The currently registered procedure is:

```text
verified_workspace_artifact_v1
```

`procedure_run` accepts only:

```text
procedure       = verified_workspace_artifact_v1
artifact_name   = bounded leaf .txt name
content         = bounded UTF-8 text
resume_task_id  = optional exact 32-hex TaskState id
```

It must not accept or expose:

```text
arbitrary path
command
shell
python executable
backend
server
raw tool name
working directory
arbitrary args
```

The workspace root and procedure-state root come from the local runtime configuration, not caller-selected procedure arguments.

## Authority boundary

A procedure request does not bypass authorization, verifier gates, budgets, checkpoint compatibility or current-state checks.

```text
ordinary ChatGPT
 -> chooses known procedure + bounded parameters
 -> procedure_run
 -> deterministic Control Plane
      validate procedure/version/input
      load/create TaskState
      observe current state
      authorize exact known transition
      perform bounded mutation
      verify result
      checkpoint
      continue while state is known and budgets permit
      complete OR ABSTAIN
```

Novel, stale, ambiguous or incompatible state must fail closed.

## Current file procedure

`verified_workspace_artifact_v1` operates only below:

```text
.chat-agent-platform/stage26-3a/
```

It has a fixed action budget of three verified transitions:

1. exclusive staging create -> exact size/SHA-256 + filesystem-object identity verify -> checkpoint;
2. exclusive final create -> target+staging identity/content verify -> checkpoint;
3. verify target/staging -> remove only the owned staging object -> verify final state -> completion checkpoint.

A pre-existing final target produces structured `ABSTAIN` and zero unauthorized overwrite.

Rollback may remove a path only when both recorded digest and filesystem-object identity still prove ownership by the current task.

## Resume contract

`resume_task_id` may continue only a retained compatible TaskState for the same exact procedure/artifact/content and a proven resumable checkpoint.

Current durable nodes are:

```text
preflight
staged_verified
final_verified
completed (idempotent observation only)
```

Ambiguous mid-transition crash state is never guessed through.

## Automated acceptance

The canonical six-tool acceptance must prove in one MCP session:

```text
tools/list == exactly six canonical tools
 -> procedure_run creates a verified artifact
 -> independent workspace_read observes the exact artifact
 -> resume_task_id returns the compatible completed task without replaying mutations
 -> pre-existing target causes ABSTAIN
 -> independent read proves the protected target was not overwritten
```

It also verifies that generic path/command/backend/tool selectors are absent from the `procedure_run` schema.

The old file/browser regression remains useful only as an internal-base regression. It must not describe itself as the public surface.

## Startup / installed-layout acceptance

The ordinary `start-semantic-profile.ps1` startup guard must inspect the live semantic server and require exactly the six canonical names before reporting READY.

The installed bundle must contain and verify:

```text
semantic-projection-launcher.mjs
semantic-control-plane-projection.mjs
semantic-projection.mjs
runtime/control_plane/cli.py
runtime/control_plane/verified_workspace_artifact.py
```

Installation metadata records:

```text
semantic_public_tool_count = 6
```

The tray has one normal READY state. For semantic, READY means the ordinary semantic runtime is healthy with the six-tool contract; there is no separate qualification color/state.

## Physical ordinary-Chat acceptance

After hosted gates are green, the target-Windows gate is the ordinary installed semantic route itself:

```text
install/update exact candidate
 -> select/start ordinary semantic profile
 -> tray reports normal READY
 -> Chat Local Bridge Test sees exactly six tools
 -> user gives one natural bounded goal
 -> Chat uses workspace/browser capabilities as useful
 -> Chat invokes verified_workspace_artifact_v1 through procedure_run for the final bounded artifact
 -> Chat independently reads the produced artifact
 -> exact postcondition is verified
```

A negative physical gate must also prove:

```text
pre-existing protected target
 -> procedure_run returns structured ABSTAIN
 -> no overwrite
 -> independent workspace_read confirms protected content remains unchanged
```

No temporary five-to-six handoff is part of this test.

## Acceptance meaning

Hosted CI proves the software contract; it does not prove ordinary-Chat physical behavior on the target Windows machine.

Stage 26.3A is physically accepted only after the normal six-tool semantic route succeeds end-to-end in ordinary ChatGPT and the negative ABSTAIN/no-overwrite case is independently verified.

# Stage 26.3A canonical six-tool semantic surface

Status: **PHYSICALLY ACCEPTED ORDINARY-CHAT CONTRACT**.

Exact accepted runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

## Decision

There is one ordinary semantic public surface and it exposes exactly six tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no user-selectable or runtime-selectable `5 tools` versus `6 tools` mode.

The separate `procedure-qualification` profile, qualification projection and qualification handoff path are removed. The normal semantic launcher always routes through the canonical six-tool Control Plane projection.

An internal five-capability file/browser implementation remains only as a private implementation layer behind the canonical projection. It is not Chat-facing, cannot be selected by tray/manager and is not an alternative public contract.

## Purpose

`procedure_run` gives ordinary ChatGPT one truthful typed capability for asking the deterministic local Control Plane to execute a known bounded procedure through multiple independently verified transitions.

It is not hidden inside `workspace_write`, `web_interact`, or a generic dispatcher.

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

Canonical path:

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

Normal runtime binding is `semantic + direct-stdio`. 1MCP is not in the normal request path and is not required for baseline bootstrap/start/status/health/smoke.

The public launcher scrubs `CONTROL_PLANE_API_KEY`, `OPENAI_API_KEY` and `OPENAI_ADMIN_KEY` before semantic child execution. Procedure authority does not imply transport-secret inheritance.

## Exact accepted procedure schema

Registered procedure:

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

It does not accept:

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

Workspace and procedure-state roots come from local runtime configuration, not caller-selected procedure arguments.

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

Novel, stale, ambiguous or incompatible state fails closed.

## Accepted file procedure

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

`resume_task_id` may continue only retained compatible TaskState for the same exact procedure/artifact/content and a proven resumable checkpoint.

Current durable nodes:

```text
preflight
staged_verified
final_verified
completed (idempotent observation only)
```

Ambiguous mid-transition crash state is never guessed through.

## Hosted acceptance

Hosted acceptance proves:

```text
tools/list == exactly six canonical tools
 -> procedure_run creates a verified artifact
 -> independent workspace_read observes the exact artifact
 -> compatible resume does not replay completed mutations
 -> pre-existing target causes ABSTAIN
 -> independent read proves protected target was not overwritten
```

It also verifies the closed procedure schema, installed bundle, direct tunnel route, startup inventory guard, neutral tunnel state, normal bootstrap and 1MCP-independent baseline.

Hosted evidence is necessary but was not used as a substitute for target-Windows ordinary-Chat acceptance.

## Physical ordinary-Chat acceptance — PASSED

Target Windows pre-chat gate on accepted runtime head `300db995...` proved:

```text
runtime_ready = true
mcp_ready = true
tunnel_ready = true
active_profile = semantic
active_count = 1
conflict = false
tunnel_binding = direct-stdio
semantic_public_tool_count = 6
extension_manager_included = false
1MCP_REQUIRED = false
```

The accepted ordinary-Chat E2E used only `Chat Local Bridge Test` and all six semantic tools in one long-horizon research task rather than a toy fixture.

Observed workload:

```text
workspace_read successes = 5
workspace_write successes = 5
web_open successes = 16
web_observe successes = 30
web_interact successes = 12
procedure_run calls = 2
content pages = 16
works/systems/benchmark groups = 12
browser interaction failures = 1 (recovered)
other tool failures = 0
```

Working memory/report artifacts:

```text
research-ledger.md
gui-agent-research.md
```

Both were actually used; the ledger was updated and reread during the task, and the final report was independently reread before procedure completion.

Completion `procedure_run`:

```text
task_id = 497ecb591779219ef0ee1e55ea7ad0b8
status = completed
action_count = 3
current_node = completed
artifact = .chat-agent-platform/stage26-3a/ordinary-chat-result.txt
sha256 = 2396b8338edced2675982db9d263a046705f7f906b553b0ed19b81f51205e583
```

Independent `workspace_read` returned exactly:

```text
STAGE26_3A_ORDINARY_CHAT_SUCCESS_E4F49B4AD4CB4DABA07A9F01A5575255
```

Zero-overwrite `procedure_run`:

```text
task_id = 02b09a4909b6d71e0578c19b2d395cb8
status = abstained
action_count = 0
current_node = preflight
escalation_reason = target_already_exists
```

A second independent `workspace_read` returned the original success content and the SHA-256 remained unchanged. The protected target was not overwritten.

The one browser failure was:

```text
web_interact click requires target unless visualFallback is provided.
```

Ordinary ChatGPT recovered by re-observing the browser state, obtaining the explicit target and retrying successfully. This is accepted recovery evidence for browser task flow, not proof of general recovery across all consequence classes.

## ChatGPT app/session prerequisite

An earlier attempt demonstrated that a locally READY route can still be interrupted by ChatGPT app snapshot/permission/session state before an MCP `tools/call` reaches the launcher.

The accepted run was started only after the app was reconnected and the user set app-specific `Allow all actions` before execution. No app connection or permission changes occurred mid-task.

Frozen inbound aliases remain migration compatibility for already-formed MCP calls; they cannot repair ChatGPT's frozen app snapshot or connection/permission state before invocation.

## Acceptance meaning / next boundary

Stage 26.3A is accepted for the exact runtime head and procedure scope above.

This acceptance does not authorize arbitrary shell/Python execution, raw backend tools, arbitrary Windows consequences or a generic workflow dispatcher.

Next work is Stage 26.3B: broaden deterministic verifier/postcondition coverage while preserving the small project-owned semantic surface, current-state authority and fail-closed ABSTAIN/escalation rules.

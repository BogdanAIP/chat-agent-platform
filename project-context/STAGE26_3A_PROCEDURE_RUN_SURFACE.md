# Stage 26.3A `procedure_run` Qualification Surface

Status: **ACTIVE IMPLEMENTATION CONTRACT / NOT PRODUCT-ACCEPTED**.

## Purpose

Stage 26.3A needs one truthful Chat-facing capability that can ask the deterministic local Control Plane to execute a bounded known procedure through multiple independently verified transitions.

This must not be hidden inside `workspace_write`, `web_interact`, or a generic `tool_invoke` surface.

The accepted ordinary semantic profile remains unchanged and continues to expose exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Stage 26.3A therefore introduces a separate **qualification-only** profile with one additional tool:

```text
procedure_run
```

No product/public promotion is implied by this qualification surface.

## Isolation model

The normal semantic server is not modified to conditionally grow extra authority.

Instead the qualification profile uses:

```text
procedure-qualification-projection
  -> proxies the exact accepted five semantic tools
  -> adds one typed procedure_run tool
  -> procedure_run invokes only the fixed local Control Plane CLI
```

Assets:

```text
runtime/semantic-projection/bin/procedure-qualification-projection.mjs
runtime/chat-profiles/procedure-qualification/mcp.json
scripts/start-procedure-qualification-profile.ps1
```

This keeps the production/accepted five-tool profile structurally separate from the candidate procedure capability.

### Control Plane child environment

The Python Control Plane does not need tunnel/OpenAI credentials and must not inherit the projection process environment wholesale.

`procedure-qualification-projection.mjs` therefore builds an explicit child-environment allowlist containing only the operating-system minimum required to locate/run Python plus:

```text
CHAT_LOCAL_FILES_ROOT
CHAT_PROCEDURE_STATE_ROOT
CHAT_PROCEDURE_ALLOW_CANDIDATE
```

Credential-bearing variables such as `CONTROL_PLANE_API_KEY`, `OPENAI_API_KEY` and `OPENAI_ADMIN_KEY` are intentionally not passed to the procedure child. A procedure gaining local execution authority must not gain unrelated transport/control-plane secrets by process inheritance.

## Exact Stage 26.3A procedure schema

The only admitted procedure is:

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
path
command
python executable
backend
server
raw tool name
arbitrary args
shell
working directory
```

The workspace root, TaskState root and candidate admission are profile configuration, not caller-controlled procedure arguments.

## Authority boundary

`procedure_run` is not a planner and does not itself authorize arbitrary actions.

```text
ordinary ChatGPT
 -> chooses the known procedure + bounded parameters
 -> procedure_run
 -> deterministic Control Plane
      exact procedure/version/trust admission
      TaskState/checkpoint
      current-state validation
      known transition
      bounded action
      verifier
      checkpoint
      repeat or ABSTAIN
```

A procedure request does not bypass current-state authorization, verifier gates, budgets, checkpoint compatibility, or candidate admission.

## Resume contract

`resume_task_id` may resume only a retained compatible TaskState for the same exact procedure/artifact/content and only from a proven resumable checkpoint.

The current kernel accepts durable checkpoint resume at:

```text
preflight
staged_verified
final_verified
completed (idempotent observation only)
```

Ambiguous mid-transition state is not guessed through.

## MCP acceptance

Automated acceptance must prove all of the following in one direct MCP session:

```text
inventory == accepted five semantic tools + procedure_run
 -> procedure_run creates the verified artifact through three transitions
 -> independent workspace_read observes the exact artifact content
 -> resume_task_id returns the already-completed task without repeating actions
```

The acceptance must also inspect the `procedure_run` input schema and prove that generic path/command/backend/tool selectors are absent. Source/security regressions additionally lock the explicit Control Plane child-environment allowlist and absence of tunnel/OpenAI credentials from that child.

Current acceptance assets:

```text
runtime/semantic-projection/tests/procedure-qualification-acceptance.mjs
tests/test_stage26_3a_procedure_surface_security.py
```

## Product promotion gate

The qualification surface must not become the normal Chat profile until a later explicit ADR/review accepts the public consequence contract.

At minimum product promotion requires:

1. hardened file-procedure checkpoint/resume/fault tests green;
2. qualification MCP acceptance green;
3. Secure MCP Tunnel wiring for the qualification surface;
4. ordinary ChatGPT E2E starting from one user goal with no intermediate PowerShell copy/paste;
5. independent final verification returned to Chat;
6. negative E2E showing incompatible intermediate state => structured ABSTAIN with no unauthorized continuation;
7. a dedicated public-surface ADR after the Transport Supervisor ADR numbering is integrated into `main`.

Until those gates pass, the normal five-tool semantic profile remains the accepted product contract.

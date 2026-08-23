# Stage 26.3A Verified Procedure Runtime implementation notes

Status: **implementation in progress / ordinary-Chat physical acceptance not yet complete**.

## Current qualification procedure

The current candidate procedure remains intentionally narrow:

```text
verified_workspace_artifact_v1
  input: leaf .txt name + bounded UTF-8 content
  workspace scope: .chat-agent-platform/stage26-3a/
  action budget: 3
```

Transitions:

```text
preflight
 -> exclusive staging create
 -> exact size/SHA-256 + filesystem-object identity verify
 -> checkpoint: staged_verified

staged_verified
 -> exclusive final create
 -> target + staging exact verify
 -> filesystem-object identity verify
 -> checkpoint: final_verified

final_verified
 -> verify exact staging + target identities
 -> remove exact staging object
 -> verify final target + cleanup
 -> checkpoint: completed
```

The candidate profile/admission gate remains mandatory and no arbitrary path, shell, Python, generic tool dispatcher or Windows command surface is introduced.

## Durable checkpoint resume contract

Stage 26.3 must distinguish a durable checkpoint from an arbitrary interrupted instruction boundary.

A resume request may continue only when all of the following match the retained TaskState:

- exact `task_id`;
- exact procedure id/version/trust status;
- exact artifact identity/path parameters;
- exact content size/SHA-256;
- valid action budget/count;
- a known resumable ProgramGraph node;
- current filesystem evidence compatible with that checkpoint.

Current implementation supports resume from these durable nodes:

```text
preflight
staged_verified
final_verified
```

`completed` is idempotently observable when the final artifact still has the exact recorded identity/content. Failed/abstained tasks are returned as terminal evidence; they are not silently restarted as a fresh strategy.

If live state no longer matches the checkpoint, the runtime ABSTAINS instead of guessing which historical action happened.

### Important boundary

Crash-resume does **not** mean that every CPU instruction becomes recoverable. If a process dies after a mutation but before the corresponding verified checkpoint was durably committed, ownership/effect evidence may be ambiguous. In that case the correct behavior is fail-closed ABSTAIN/escalation unless a later design adds a predeclared write-ahead transaction record that can prove the exact pending mutation.

Stage 26.3 acceptance must therefore inject failures at durable checkpoint boundaries first. A future extension may add write-ahead transition intents for narrower mid-transition recovery, but must not infer ownership from path/name alone.

## Exact file ownership rule

SHA-256 proves content equality, not ownership.

Another process can replace a path with a different filesystem object containing identical bytes. Therefore rollback and resume authorization require both:

```text
expected content digest
AND
recorded filesystem-object identity
```

The current implementation records `st_dev` / `st_ino` as the bounded cross-platform filesystem identity available through Python `stat()`. On Windows this corresponds to the file object's filesystem identity exposed by the runtime. If future target evidence shows that release-grade Windows identity needs a stronger native file-id/volume contract, add that adapter before broadening destructive rollback authority.

Rollback refuses deletion when either digest or object identity differs.

## Zero-mutation terminology

Repository docs use `zero mutation` as a safety invariant. For the procedure runtime this means **zero unauthorized external capability/workspace mutation**.

Internal execution-state persistence is allowed so the runtime can record an ABSTAIN/escalation receipt. Internal TaskState/checkpoint writes must never be confused with authority to alter the user's target artifact.

The procedure creates its reserved workspace directory only after preflight has established a path on which execution may proceed.

## Required automated fault coverage before public `procedure_run`

Before wiring the candidate through the ordinary-Chat semantic surface, tests must cover at minimum:

1. resume from `staged_verified` completes only transitions 2-3;
2. resume from `final_verified` completes only transition 3;
3. completed checkpoint is idempotently observable without another action;
4. same-content replacement with a different filesystem identity is rejected;
5. corrupt/missing/mismatched checkpoint fails closed;
6. action count cannot exceed the fixed budget across resume;
7. concurrent/exclusive target creation cannot overwrite an external target;
8. failed rollback never deletes a path whose ownership evidence changed;
9. request fields remain a strict allowlist with no command/path/tool injection;
10. persisted TaskState contains structured evidence, not private reasoning.

## Ordinary-Chat integration order

Do not expand this kernel to Windows/UI procedures yet.

Required order:

```text
checkpoint-resumable file procedure
 -> hosted deterministic/fault tests
 -> truthful qualification-only procedure_run surface
 -> direct MCP procedure_run + independent workspace_read verification
 -> ordinary ChatGPT ONE-goal E2E, no intermediate PowerShell relay
 -> only then integrate broader Files/Browser/Windows procedure transitions
```

A dedicated `procedure_run`-class capability is preferable to hiding multi-transition procedure consequences inside `workspace_write` or `web_interact`. The normal five-tool profile should remain unchanged until the dedicated public-contract ADR/profile is explicitly qualified.

## Acceptance meaning

A successful local Python invocation is not Stage 26.3 product acceptance.

The first accepted vertical slice requires:

```text
one user goal in ordinary ChatGPT
 -> bounded procedure selected/admitted
 -> multiple independently authorized+verified transitions
 -> durable checkpoints
 -> independent final postcondition
 -> structured completion/evidence returned to Chat
```

Unexpected checkpoint/live-state mismatch must produce ABSTAIN/escalation and no unauthorized continuation.

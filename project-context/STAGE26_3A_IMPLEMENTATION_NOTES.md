# Stage 26.3A Verified Procedure Runtime implementation notes

Status: **canonical six-tool semantic runtime implemented / physical ordinary-Chat acceptance pending**.

## Foundation

PR #92 is based on the accepted Transport Supervisor v1 foundation from PR #94:

```text
main foundation = 2f33997d3fbaa1fc52d437c00be7f16e55bdde5e
```

Resolve the live PR #92 head and hosted checks before any physical test. Do not use an older SHA merely because it appears in historical comments or evidence.

## Current public semantic contract

The current Stage 26.3A candidate has one ordinary semantic public surface with exactly six tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray choice between five and six tools.

The old separate `procedure-qualification` profile, projection, direct-tunnel harness and supervisor handoff were removed. The public semantic launcher permanently routes through `semantic-control-plane-projection.mjs`.

A private five-capability file/browser implementation remains behind the canonical projection as an implementation layer only. It is not selectable or public and must not be treated as a second semantic mode.

The ordinary semantic startup guard performs a live `tools/list` inspection and refuses READY unless the exact six-tool inventory is present.

The tray has one normal semantic READY state; there is no qualification color/state.

## Installed runtime contract

The bootstrap installs one verified runtime bundle containing the canonical six-tool projection and deterministic Control Plane dependencies.

Required installed assets include:

```text
runtime/semantic-projection/bin/semantic-projection-launcher.mjs
runtime/semantic-projection/bin/semantic-control-plane-projection.mjs
runtime/semantic-projection/bin/semantic-projection.mjs
runtime/control_plane/cli.py
runtime/control_plane/verified_workspace_artifact.py
```

Installation metadata records:

```text
semantic_public_tool_count = 6
```

The bootstrap remains one public entrypoint but is internally split into reviewed modules for tunnel acquisition/configuration, manager/runtime bundle installation and lifecycle smoke testing.

## Current bounded procedure

The first registered procedure remains intentionally narrow:

```text
verified_workspace_artifact_v1
  input: leaf .txt name + bounded UTF-8 content
  workspace scope: .chat-agent-platform/stage26-3a/
  action budget: 3
```

It does not expose arbitrary path, shell, Python, generic tool dispatch, backend selection or Windows command execution.

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
 -> remove exact owned staging object
 -> verify final target + cleanup
 -> checkpoint: completed
```

A pre-existing final target causes structured `ABSTAIN` with zero unauthorized overwrite.

## Durable checkpoint resume contract

A resume request may continue only when all of the following match retained TaskState:

- exact `task_id`;
- exact procedure id/version/trust status;
- exact artifact identity/path parameters;
- exact content size/SHA-256;
- valid action budget/count;
- known resumable ProgramGraph node;
- current filesystem evidence compatible with that checkpoint.

Current resumable nodes:

```text
preflight
staged_verified
final_verified
```

`completed` is idempotently observable when the final artifact still has the exact recorded identity/content. Failed or abstained tasks remain terminal evidence and are not silently restarted as a fresh strategy.

If live state no longer matches the checkpoint, the runtime ABSTAINS instead of guessing what happened.

## Filesystem ownership rule

SHA-256 proves byte equality, not ownership.

Rollback/resume authorization therefore requires both:

```text
expected content digest
AND
recorded filesystem-object identity
```

The implementation records `st_dev` / `st_ino` through Python `stat()`. Rollback refuses deletion when either digest or object identity differs.

If future Windows evidence shows a stronger native file-id/volume contract is required before broader destructive authority, add that adapter before broadening procedures.

## Zero-mutation terminology

For this runtime, `zero mutation` means **zero unauthorized external capability/workspace mutation**.

Internal TaskState/checkpoint persistence is permitted so ABSTAIN/escalation evidence can be durable. Internal state writes never authorize alteration of the user's target artifact.

## Automated acceptance requirements

The current hosted contract must cover at minimum:

1. exact canonical public inventory of six tools;
2. `procedure_run` creation followed by independent `workspace_read` verification;
3. resume from `staged_verified` and `final_verified` only from compatible evidence;
4. completed checkpoint idempotence;
5. same-content replacement with different filesystem identity rejected;
6. corrupt/missing/mismatched checkpoint fails closed;
7. fixed action budget preserved across resume;
8. concurrent/pre-existing target cannot be overwritten;
9. rollback never deletes a path whose ownership evidence changed;
10. strict `procedure_run` request allowlist with no command/path/tool injection;
11. installed bundle contains the canonical six-tool projection and Control Plane closure;
12. ordinary semantic startup guard rejects any inventory other than the six canonical tools;
13. real direct semantic tunnel acceptance sees and exercises `procedure_run` through the same public route.

Hosted success is necessary but not sufficient for physical acceptance.

## Ordinary-Chat integration order

Do not expand this kernel to broad Windows/UI procedures yet.

Required order:

```text
checkpoint-resumable file procedure — implemented
 -> canonical six-tool public semantic surface — implemented
 -> hosted deterministic/security/integration tests — must be green on exact head
 -> install exact head on target Windows
 -> ordinary ChatGPT ONE-goal E2E on normal semantic route
 -> independent final workspace_read verification
 -> negative pre-existing target => ABSTAIN/no overwrite
 -> only then broaden procedure catalog
```

The six-tool decision is current architecture, not a temporary qualification switch. Future changes may change the public surface only through a new reviewed decision and corresponding physical acceptance.

## Physical acceptance meaning

A successful hosted workflow or local Python invocation is not Stage 26.3A physical acceptance.

The first accepted vertical slice requires:

```text
one user goal in ordinary ChatGPT
 -> normal semantic route exposes six canonical tools
 -> bounded procedure selected/admitted
 -> multiple independently authorized+verified transitions
 -> durable checkpoints
 -> independent final postcondition
 -> structured completion/evidence returned to Chat
```

Unexpected checkpoint/live-state mismatch or pre-existing protected target must produce ABSTAIN/escalation and no unauthorized continuation.

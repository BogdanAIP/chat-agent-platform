# Workspace Artifact Capability Grant Binding Re-entry

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-22.

## Re-entry trigger

The Core-v1 authorization enforcement work in stacked PR #167 exposed a concrete
consumer-level gap in `verified_workspace_artifact_v1`.

The procedure already stores `WorkingState.capability_grant_refs`, but the only
value is the shared qualification admission id:

```text
stage26-3a-qualification
```

That value proves admission to the reviewed procedure family. It does **not**
uniquely identify one grant for one task/resource/effect.

Simply passing that shared string through the new Core
`record_authorized_attempt()` path would therefore preserve the old admission
shape rather than prove a concrete capability grant.

## Stage question

How should the accepted workspace procedure derive one deterministic grant that is
bound to the exact task and artifact without adding a new grant database, secret,
policy service or checkpoint authority?

## Existing trusted inputs

The procedure already validates and durably binds:

- `task_id`;
- `artifact_relative_path`;
- `content_sha256`;
- `content_size`;
- exact procedure id/version;
- accepted candidate admission;
- stable file-artifact observation stream;
- actor and execution-environment identity;
- the three fixed transitions:
  `stage_create`, `final_create`, `staging_cleanup`.

These values are sufficient to derive a deterministic grant identity and exact
resource scope.

## Alternatives

### A. Reuse `QUALIFICATION_ADMISSION` as the grant ref — REJECT

This confuses procedure-family admission with one concrete active grant and makes
all accepted workspace tasks share the same grant identity.

### B. Persist a new random grant secret/object beside the checkpoint — REJECT

No new secret or grant database is needed. It would add crash/recovery and
rotation semantics without improving the already deterministic task identity.

### C. Deterministic task/resource-bound grant — SELECT

Derive:

```text
grant_ref = sha256(
  procedure id/version
  + qualification admission
  + task_id
  + exact artifact_relative_path
  + expected content SHA-256
  + content size
)

resource_scope_ref = exact artifact-relative-path + expected content SHA-256
allowed_action_refs = fixed reviewed transition ids
```

Then construct a pure Core `CapabilityGrant` from the already validated current
state:

```text
principal_ref = procedure actor
capability = file-artifact capability
delegation_ref = current WorkingState delegation ref
execution_environment_ref = workspace-artifact runtime
evidence_scope_ref = current stable observation stream
```

For each mutation, construct `AuthorizationRequest` with:

- exact transition id as `action_ref`;
- exact resource scope;
- exact `AttemptIntent.authorization_fingerprint`.

The procedure then records mutation outcomes only through
`WorkingState.record_authorized_attempt()`.

## Resume compatibility

The current schema-2 checkpoint may contain the historical shared
`QUALIFICATION_ADMISSION` in `capability_grant_refs`.

Do not silently reinterpret that shared id as the new concrete grant.

Selected migration rule:

- bump the workspace checkpoint contract to **schema 3** for newly created/migrated
  WorkingState;
- schema-3 WorkingState stores only the deterministic concrete grant ref and every
  mutation uses the authorized Core path;
- a genuine schema-2 resume carrying the historical shared admission may continue
  only through the already-reviewed legacy attempt path for the remainder of that
  checkpoint;
- schema-2 checkpoints remain schema 2 when merely checkpointed/resumed; they are
  not silently upgraded to schema 3;
- schema 1 may migrate through the existing explicit migration path into a newly
  constructed schema-3 WorkingState;
- a schema-3 checkpoint carrying the legacy shared admission is invalid and fails
  closed.

This keeps old crash-recovery evidence truthful and prevents a new grant from being
minted retroactively for an earlier physical attempt.

If implementation cannot keep legacy/new paths explicit and fail closed, stop and
re-enter research rather than weakening resume semantics.

## Failure matrix

| Failure | Required behavior |
|---|---|
| derived grant ref differs from WorkingState active ref | BLOCK before mutation |
| task/path/content digest differs | different grant/resource; BLOCK |
| transition is outside fixed three actions | BLOCK |
| actor/environment/evidence stream differs | BLOCK |
| AuthorizationRequest fingerprint differs from exact AttemptIntent | BLOCK |
| legacy checkpoint is mistaken for new-grant checkpoint | fail closed / explicit legacy path only |
| provider/filesystem reports success without authorized record path | cannot establish authorization |
| recovery reconstructs different task/path/content | existing checkpoint validation fails before grant use |

## Acceptance

L1:

- deterministic grant-ref/resource-scope tests;
- distinct task/path/content produce distinct grant identities;
- all mismatch paths BLOCK;
- new state contains the concrete grant ref, not shared admission;
- existing legacy checkpoint fixtures remain behaviorally compatible.

L2:

- Stage 26.3A procedure tests;
- crash/restart/reconciliation tests;
- installed-layout Semantic Projection acceptance;
- no public six-tool change.

L3:

No new user-laptop test is required solely for this filesystem procedure if the
existing Stage 26.3A/installed-layout physical filesystem acceptance remains
unchanged and passes exact head. Any broader real Windows/UI behavior change still
requires its normal physical gate.

## Decision

**NARROW**

Migrate only `verified_workspace_artifact_v1` to a deterministic
task/resource-bound Core grant. Preserve explicit legacy checkpoint behavior. Do
not introduce a generic grant registry, grant store, wildcard resource language,
or new public tool.

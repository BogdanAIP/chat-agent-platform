# Platform Update Procedure v1 — Stage Research

Research date: 2026-09-28

Repository base: `BogdanAIP/chat-agent-platform@24ed938c587c9d3e2288c92bc156ccc476c955f3`

Applicable repository skills:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0

## Goal

Allow the already-installed CAP runtime on the user's Windows machine to request and reconcile its own **existing bounded main updater** through the accepted `procedure_run` tool.

The change must not expose a shell, arbitrary executable, arbitrary repository, arbitrary branch, path selector, GitHub credential, or second updater implementation.

Selected public contract:

```text
procedure_run
  procedure=platform_update_v1
  action=check | request_update | status
```

The semantic surface remains exactly six public tools.

## Current project evidence

The accepted updater already exists in:

- `scripts/chat-platform-update.ps1`
- `scripts/chat-platform-update-core.ps1`
- `scripts/chat-platform-tray-update.ps1`
- `scripts/bootstrap-chat-platform.ps1`

Current updater properties on the exact base:

- source is fixed to `BogdanAIP/chat-agent-platform`, branch `main`;
- remote identity is allowlisted;
- update cache is a private bare repository;
- remote main is fetched atomically;
- installed -> target ancestry is checked before update;
- exact detached target worktree is created and verified;
- target must contain the accepted self-update contract before bootstrap;
- an OS mutex serializes updater ownership;
- installed runtime is quiesced before bootstrap and restarted after success;
- recovery attempts restart on update failure;
- durable status is written to `platform-update.json` and terminal outcome to
  `platform-update-result.json`.

Physical development-session evidence on 2026-09-28 additionally showed that the
installed updater can be invoked on the target Windows host through the existing
OpenResearch local runner, and `-Action Check` returned `status=current` with
installed and target SHA both
`24ed938c587c9d3e2288c92bc156ccc476c955f3`. This is bootstrap evidence, not
release acceptance for the new procedure.

## Source-code evidence

### Chat Agent Platform — exact base

Repository/ref:
`BogdanAIP/chat-agent-platform@24ed938c587c9d3e2288c92bc156ccc476c955f3`

Inspected mechanisms:

- `scripts/chat-platform-update.ps1`:
  mutex ownership, check/update decision, quiesce, exact worktree bootstrap,
  restart/recovery, terminal result;
- `scripts/chat-platform-update-core.ps1`:
  fixed official remote/main, SHA validation, atomic fetch, ancestry check,
  exact worktree;
- `scripts/chat-platform-tray-update.ps1`:
  updater launched as a separate process and terminal result reconciled by
  process id + completion time rather than stdout pipes;
- `runtime/semantic-projection/bin/semantic-control-plane-projection.mjs`:
  closed registered-procedure union and child environment allowlist;
- `runtime/control_plane/cli.py`:
  exact registered procedure dispatch.

Classification: **OPEN_IMPLEMENTED**.

Lesson: **REUSE_COMPONENT / REFINE ADAPTER ONLY**. The updater remains the sole
installation authority. The new procedure is only a fixed adapter to it.

### OpenAI Codex

Repository/ref:
`openai/codex@46d2585ea4347fe93446db57ec3e07ef234907e8`

Inspected:

- `codex-rs/tui/src/update_action.rs`
- `codex-rs/app-server-daemon/src/update_loop.rs`
- `codex-rs/app-server-daemon/src/manual_update.rs`

Mechanism observed:

- update choices are represented as typed variants rather than caller-supplied
  arbitrary command strings;
- daemon/update-loop owns scheduled/manual update lifecycle;
- Windows updater ownership and restart/handoff are explicit;
- manual update requests are separated from updater execution ownership.

Classification: **OPEN_IMPLEMENTED**.

Lesson: **REFERENCE_ONLY**. Preserve a typed, fixed update request surface and
keep lifecycle ownership below Chat planning authority.

### GitHub Desktop

Repository/ref:
`desktop/desktop@f2686bcec9239a9f8c5d53e2e90bc3a4dd02059f`

Inspected:

- `app/src/ui/lib/update-store.ts`
- `app/src/main-process/app-window.ts`

Mechanism observed:

- update checks use a product-controlled update URL;
- update state is explicit;
- downloaded update installation is owned by the native updater;
- quit/install lifecycle is guarded rather than delegated to arbitrary renderer
  execution.

Classification: **OPEN_IMPLEMENTED**.

Lesson: **REFERENCE_ONLY**. Keep source selection fixed and expose lifecycle
state rather than generic local execution.

## Alternatives

1. **Continue using OpenResearch/Tura as bootstrap forever.**
   Works now, but makes CAP maintenance depend on an unrelated research runner
   and does not make CAP self-maintaining. Rejected as permanent architecture.

2. **Expose generic PowerShell/command execution through `procedure_run`.**
   It would solve update and many other tasks but materially destroys the
   closed-procedure trust boundary. Rejected.

3. **Add repo/branch/path parameters to an update procedure.**
   Unnecessary because the accepted updater already fixes official main.
   Rejected.

4. **Selected: fixed adapter around the existing updater.**
   Smallest change; no second installer; no generic dispatch.

## Authority and lineage

- Existing six-tool public semantic surface: **KEEP**.
- Existing deterministic Control Plane / registered procedure boundary: **KEEP**.
- Existing bounded official-main updater: **REUSE_MORE**.
- Tray UI remains a human entry point, not the only update authority: **REFINE**.
- Generic shell/native-host authority: **DEFER** to its own stage.
- Windows UIA/computer-use authority: **DEFER** to the next separately researched
  integration after self-update is established.

## Failure / crash matrix

| Boundary | Existing durable evidence | Possible result | Required behavior |
|---|---|---|---|
| Before request launch | existing update state/result | none | return error, no install |
| Request accepted, before updater mutex | no new CAP state owner | none | updater owns admission |
| Updater mutex busy | updater state/result | no second install | fail/observe; no generic retry path |
| During fetch/decision | updater state | no install or blocked | preserve updater error/blocked state |
| After quiesce, before bootstrap | updater state=installing | runtime temporarily unavailable | updater recovery owns restart |
| During bootstrap | updater logs/state | old/new runtime may be partial until bootstrap completes | canonical updater recovery; procedure never claims success |
| Update completes while caller disconnects | terminal result file | update may have succeeded | reconnect and call `status` |
| Caller repeats request after lost acknowledgement | updater mutex/current-state check | at most same official-main convergence | reconcile with `status`; no arbitrary second effect |

The procedure must never translate launch acknowledgement into update success.

## Selected v1 contract

`platform_update_v1` supports exactly:

- `check`: synchronously invoke installed updater with `-Action Check` and
  return its bounded JSON result;
- `request_update`: start the installed updater with fixed `-Action Update`
  in a separate process and return only `accepted` + process id;
- `status`: read only the fixed updater state/result files under
  `%LOCALAPPDATA%\ChatAgentPlatform\state`.

No caller path, URL, branch, command, environment, executable or credential is
accepted.

## Verification

Before merge:

1. unit tests for exact schema and rejection of extra fields;
2. tests that adapter resolves only the installed updater path;
3. tests that subprocess argv is fixed and `shell=False`;
4. tests for malformed/missing state/result fail-closed behavior;
5. existing six-tool and procedure-surface tests remain green;
6. hosted CI on exact head;
7. fresh independent ordinary-ChatGPT semantic review on exact BASE..HEAD;
8. target Windows physical check: `check`, then an update/no-op update request,
   disconnect/reconnect if applicable, and `status` reconciliation.

## Decision

**NARROW**

Implement only the fixed official-main `platform_update_v1` adapter described
above. Do not add generic process execution, arbitrary updater source selection,
Windows GUI authority, or a new persistence owner in this stage.

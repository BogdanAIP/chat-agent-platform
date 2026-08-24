# Stage 26.3A Verified Procedure Runtime implementation notes

Status: **canonical six-tool semantic runtime implemented and physically accepted in ordinary ChatGPT**.

## Foundation

PR #92 is based on the accepted Transport Supervisor v1 foundation from PR #94:

```text
main foundation = 2f33997d3fbaa1fc52d437c00be7f16e55bdde5e
```

Exact physically accepted Stage 26.3A runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Later PR #92 descendants must be compared against this runtime head. Physical acceptance remains valid only when later changes are documentation/test-only or a fresh physical gate is run for runtime changes.

## Accepted public semantic contract

The ordinary `semantic` public surface contains exactly six tools:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray choice between five and six tools.

The old separate `procedure-qualification` profile, projection, direct-tunnel harness and supervisor handoff are removed. The public semantic launcher permanently routes through `semantic-control-plane-projection.mjs`.

A private five-capability file/browser implementation remains behind the canonical projection as an implementation layer only. It is not selectable or public and must not be treated as a second semantic mode.

The ordinary semantic startup guard performs a live `tools/list` inspection and refuses READY unless the exact six-tool inventory is present.

The tray has one normal semantic READY state; there is no qualification color/state.

## Installed runtime and transport contract

The bootstrap installs one verified runtime bundle containing the canonical six-tool projection and deterministic Control Plane dependencies:

```text
runtime/semantic-projection/bin/semantic-projection-launcher.mjs
runtime/semantic-projection/bin/semantic-control-plane-projection.mjs
runtime/semantic-projection/bin/semantic-projection.mjs
runtime/control_plane/cli.py
runtime/control_plane/verified_workspace_artifact.py
```

Normal semantic transport is direct stdio:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> semantic launcher
 -> canonical six-tool projection
```

The accepted persistent `tunnel_*` id is platform state in:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

An existing `local-1mcp.yaml` may be read only as a bounded migration fallback to recover one already accepted tunnel id. It is not the normal semantic source of truth after migration.

Accepted bootstrap/runtime invariants:

```text
semantic_public_tool_count = 6
extension_manager_included = false
profile = semantic
tunnel_profile = direct-stdio
NORMAL_SEMANTIC_1MCP_REQUIRED = false
LEGACY_1MCP_INSTALL_PATH_USED = false
```

The physical acceptance run also verified that an already installed pinned `tunnel-client v0.0.11` can be reused without a GitHub Release API fetch when local metadata and hashes independently verify it.

## Optional 1MCP Extension Manager

1MCP is retained for future extension work rather than deleted from the project.

Target role:

```text
canonical semantic surface
 -> project-owned typed facade
 -> optional internal Extension Manager (1MCP or qualified replacement)
 -> selected third-party MCP backend
```

The Extension Manager may provide backend discovery/aggregation, enable-disable, lazy lifecycle, health and restart. It does not grant capability authorization, own the persistent tunnel anchor or automatically expose raw backend tools to ChatGPT.

Optional extension failure must not block the baseline six-tool route unless the current task explicitly requires that extension.

Authoritative policy: `DECISIONS.md` ADR-031, `EXTENSION_MANAGER.md` and `MODULE_SELECTION_POLICY.md`.

## Accepted bounded procedure

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

## Durable checkpoint / ownership contract

Resume is permitted only when task id, procedure/version/trust, artifact/content identity, action budget/count, known ProgramGraph node and current filesystem evidence match retained TaskState.

Current resumable nodes are `preflight`, `staged_verified` and `final_verified`; `completed` is idempotently observable when the final artifact still has the exact recorded identity/content.

SHA-256 proves byte equality, not ownership. Rollback/resume authorization therefore requires both expected content digest and recorded filesystem-object identity (`st_dev` / `st_ino`). The runtime refuses deletion when either differs.

`zero mutation` means zero unauthorized external capability/workspace mutation. Internal TaskState/checkpoint persistence is allowed so ABSTAIN/escalation evidence remains durable.

## Hosted acceptance requirements

Hosted tests cover at minimum:

1. exact six-tool public inventory;
2. real `procedure_run` creation followed by independent `workspace_read`;
3. compatible checkpoint resume and completed idempotence;
4. replacement with different filesystem identity rejected;
5. corrupt/mismatched checkpoints fail closed;
6. fixed action budget across resume;
7. pre-existing/concurrent target cannot be overwritten;
8. rollback never deletes changed ownership evidence;
9. closed `procedure_run` schema with no generic dispatch;
10. installed bundle contains the canonical projection + Control Plane closure;
11. startup guard rejects inventory other than exact six;
12. direct Secure MCP Tunnel sees/exercises `procedure_run`;
13. normal bootstrap has no mandatory 1MCP/npx preflight;
14. neutral `state/tunnel.json` is authoritative;
15. bootstrap smoke uses `semantic + direct-stdio`;
16. verified local tunnel-client reuse works without network fetch when exact pinned evidence matches.

Optional adaptive/1MCP regressions remain separate evidence and do not redefine the normal semantic critical path.

## Physical ordinary-Chat acceptance — PASSED

The target Windows pre-chat gate on exact runtime head `300db995...` proved the normal route was READY with one semantic runtime, one tunnel, no conflict, `semantic + direct-stdio`, six public tools and `1MCP_REQUIRED=False`.

The final ordinary-Chat task was deliberately long-horizon rather than a toy fixture. Using only `Chat Local Bridge Test`, ordinary ChatGPT:

- verified the Stage 26.3A challenge/HEAD/profile/binding;
- used `workspace_read` and `workspace_write` as real working memory;
- researched 16 content pages covering 12 works/systems/benchmark groups;
- performed 12 successful browser interactions and recovered from one invalid `web_interact` request by re-observing and retrying with the explicit target;
- wrote `gui-agent-research.md` and independently reread it;
- called `procedure_run` only after the research/report was complete.

Completion task:

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

Zero-overwrite task:

```text
task_id = 02b09a4909b6d71e0578c19b2d395cb8
status = abstained
action_count = 0
current_node = preflight
escalation_reason = target_already_exists
```

A second independent `workspace_read` returned the original success nonce again and the SHA-256 remained unchanged. Stage 26.3A zero-overwrite is therefore physically accepted for this registered procedure/scope.

## ChatGPT app binding lesson

An earlier attempt in the same physical qualification exposed a product-side app/session failure: after a successful `workspace_read`, ChatGPT entered approval UI for `workspace_write`, then switched to reconnect/add-app UI and the message stream failed while the local route remained healthy.

The accepted rerun was performed only after app reconnection and an explicit app-specific `Allow all actions` permission setting were established before execution. No connection/permission changes occurred during the accepted long task.

Frozen-action aliases remain inbound MCP migration compatibility only. They cannot repair ChatGPT app snapshot/connection/permission state before a call reaches MCP. See `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md`.

## Next development boundary

Stage 26.3A is complete. Do not turn the accepted kernel into a generic workflow executor.

Next is **Stage 26.3B — advanced verifier/postcondition library**: broaden deterministic completion evidence for files/artifacts, browser state, UI/application state, process/window state and structured outputs while preserving explicit capability names, bounded procedures, current-state authorization and ABSTAIN/escalation.

The six-tool decision is current architecture. Future public-surface changes require a new reviewed decision and corresponding physical acceptance.

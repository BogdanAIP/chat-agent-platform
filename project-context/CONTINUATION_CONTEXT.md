# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting because `main` and PR heads can move after this snapshot.

## Repository

`BogdanAIP/chat-agent-platform`

## Accepted foundation

Stages through 26.2E are accepted only for their exact recorded physical heads/evidence. Transport Supervisor v1 is physically accepted and merged as PR #94.

Stage 26.3A — canonical six-tool Verified Procedure Runtime — is now **physically accepted** on exact runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Exact evidence and scope are recorded in `EVIDENCE_INDEX.md`.

## Accepted Stage 26.3A architecture

The ordinary `semantic` route exposes exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray selection between five and six tools.

The public route is:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

Normal bootstrap/start/status/health/smoke does not require 1MCP. Persistent tunnel identity is neutral platform state in:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

The installed baseline records:

```text
profile = semantic
tunnel_profile = direct-stdio
semantic_public_tool_count = 6
extension_manager_included = false
```

1MCP remains an optional internal Extension Manager for future third-party MCP backends. It is not part of the normal semantic critical path and raw extension catalogs are not automatically Chat-facing.

The first accepted registered procedure is:

```text
verified_workspace_artifact_v1
```

It accepts only a bounded leaf `.txt` name + bounded UTF-8 content, writes only below `.chat-agent-platform/stage26-3a/`, uses a fixed three-action verified transition budget and ABSTAINS rather than overwriting a pre-existing protected target.

`procedure_run` is not generic execution and exposes no arbitrary shell, Python, path, backend, raw tool or working-directory arguments.

## Physical Stage 26.3A acceptance

The target Windows pre-chat gate proved the normal route was READY with `semantic + direct-stdio`, six public tools, one active runtime, no conflict and `1MCP_REQUIRED=False`.

A fresh ordinary ChatGPT conversation then used only `Chat Local Bridge Test` and all six semantic tools for a long-horizon GUI/web-agent research task:

```text
16 content pages
12 works/systems/benchmark groups
12 successful browser transitions
research-ledger.md used and reread as working memory
gui-agent-research.md written and independently reread
1 recoverable browser interaction error
```

The completion procedure task:

```text
task_id = 497ecb591779219ef0ee1e55ea7ad0b8
status = completed
action_count = 3
artifact = .chat-agent-platform/stage26-3a/ordinary-chat-result.txt
sha256 = 2396b8338edced2675982db9d263a046705f7f906b553b0ed19b81f51205e583
```

Independent `workspace_read` returned the exact expected success nonce.

The second procedure task:

```text
task_id = 02b09a4909b6d71e0578c19b2d395cb8
status = abstained
action_count = 0
escalation_reason = target_already_exists
```

A second independent read proved unchanged content/SHA. Zero-overwrite is physically accepted for this procedure/scope.

## ChatGPT app binding lesson

Before the accepted long run, one attempt exposed a product-side app/session issue: after a successful read, a mutating action entered ChatGPT reconnect/add-app UI and the message stream failed even though the local route remained healthy.

The accepted rerun was performed only after:

- the app connection was synchronized before execution;
- `Chat Local Bridge Test` permission policy was settled to `Allow all actions` before execution;
- no connection/permission changes were made during the long task.

The launcher can rewrite reviewed stale inbound action names after a `tools/call` reaches MCP, but it cannot repair ChatGPT's frozen app snapshot/connection/permission state before invocation. See `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md`.

## Active work

PR #92 now contains an accepted Stage 26.3A runtime plus documentation/test-only closure commits after the physical runtime head. Before merge:

1. resolve live PR #92 head;
2. verify the diff from accepted runtime head `300db995...` contains no production/runtime change after physical acceptance;
3. require the complete hosted matrix green on the final docs/test-only descendant;
4. review intended diff and merge when no unresolved finding remains.

After #92 closure, the next release-critical development is **Stage 26.3B — advanced verifier/postcondition library**.

Stage 26.3B must broaden deterministic completion evidence for UI, files/artifacts, process/window/application state, browser state and structured outputs without introducing generic execution or a large raw tool catalog.

## Operating rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic local Control Plane is execution/verification, not a second planner;
- known selected procedures may advance through several independently authorized+verified transitions;
- novel strategy or stale/ambiguous/UNKNOWN/incompatible state -> ABSTAIN/escalate;
- current state outranks remembered/history state;
- delivery is not completion; explicit verification controls completion;
- generic Windows code execution remains disabled/unreachable;
- model/procedure/planner/observation output is evidence/proposal, never authorization by itself;
- normal semantic runtime must not depend on optional 1MCP extension infrastructure;
- app binding/permission changes must not be made mid-acceptance task;
- when a branch is logically complete, intended diff is reviewed, required physical/CI gates pass and no unresolved issue remains, merge it without waiting for a separate merge command.

## Stage order

```text
26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane — ACTIVE
    -> 26.3A canonical six-tool semantic runtime — ACCEPTED
    -> 26.3B advanced verifier/postconditions — NEXT
    -> 26.3C bounded recovery/budgets as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 distribution/maintenance
 -> 28 clean-user E2E/stable release
```

## Fresh-chat startup procedure

1. Resolve live `main`, PR #92 head and current checks.
2. Read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `EXTENSION_MANAGER.md`, `ROADMAP.md`, `DOCUMENT_STATUS.md`, `EVIDENCE_INDEX.md`, `STAGE26_3A_IMPLEMENTATION_NOTES.md` and `STAGE26_3A_PROCEDURE_RUN_SURFACE.md`.
3. Treat Stage 26.3A as accepted only for exact runtime head `300db9956dfbdf0300ecc59f017d6f3280d4353a` and the recorded physical scope.
4. Treat later PR descendants as closure-only unless a fresh compare proves otherwise.
5. Prefer exact code/tests/current CI/physical evidence over prose.
6. Do not recreate a five-versus-six qualification mode, do not put 1MCP back into the normal semantic critical path, and do not broaden the procedure surface before Stage 26.3B design/evidence.

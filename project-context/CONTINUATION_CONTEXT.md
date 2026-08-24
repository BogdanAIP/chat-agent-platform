# Continuation Context — read this first in a fresh chat

This file is intentionally compact. Resolve live GitHub state before acting because `main` and PR heads can move after this snapshot.

## Repository

`BogdanAIP/chat-agent-platform`

## Accepted foundation

Transport Supervisor v1 was physically accepted and merged as PR #94.

```text
accepted main foundation after #94:
2f33997d3fbaa1fc52d437c00be7f16e55bdde5e
```

Stages through 26.2E are accepted only for their exact recorded physical heads/evidence. Exact locators remain in `EVIDENCE_INDEX.md`.

Stage 26.3A is **not physically accepted yet**.

## Active work

PR #92 — Stage 26.3A Verified Procedure Runtime / deterministic Control Plane.

Always resolve the live PR #92 head and its checks before physical qualification. Do not reuse an older hosted SHA from historical comments merely because it was once green.

### Current architectural decision — six tools, one semantic mode

The current candidate ordinary `semantic` profile exposes exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

This is the only current public semantic contract.

There is **no runtime/profile/tray selection between five and six tools**.

The old separate `procedure-qualification` profile/projection/direct-tunnel handoff was removed. The public semantic launcher always routes through the canonical six-tool Control Plane projection.

A private five-capability file/browser implementation may exist behind the canonical projection as an implementation layer only. It is not user-selectable, not Chat-facing and not an alternative public profile.

The ordinary semantic startup guard must refuse READY unless live `tools/list` is exactly the six canonical names.

The tray has one normal semantic READY state; there is no qualification color/state.

### Current transport / 1MCP decision

The normal semantic path is direct stdio and **does not depend on 1MCP**:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> semantic launcher
 -> canonical six-tool projection
```

The persistent accepted `tunnel_*` id belongs to neutral platform state:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

On upgrade, an existing `local-1mcp.yaml` may be read once as a bounded migration fallback to recover the already accepted tunnel id. After migration it is not the normal semantic source of truth.

1MCP is retained as a replaceable optional internal **Extension Manager** for future third-party MCP backends:

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

1MCP may later handle extension discovery/aggregation, enable-disable, lazy lifecycle, health and restart. Its failure/absence must not block normal six-tool bootstrap/start/health. Raw backend tool catalogs are not exported directly to ordinary ChatGPT; supported extensions remain behind project-owned typed semantic facades and the same authorization boundary.

Authoritative decision: `DECISIONS.md` ADR-031 and `MODULE_SELECTION_POLICY.md`.

### Current deterministic procedure

The first registered procedure is intentionally narrow:

```text
verified_workspace_artifact_v1
```

It accepts only a bounded leaf `.txt` name, bounded UTF-8 content and optional compatible resume task id. It writes only below:

```text
.chat-agent-platform/stage26-3a/
```

It has a fixed three-action verified transition budget and must ABSTAIN rather than overwrite a pre-existing protected target or guess through incompatible state.

`procedure_run` is not generic code execution and must not expose arbitrary shell, Python, path, backend, server, raw tool or working-directory arguments.

## Operating rules

- Use ordinary ChatGPT + GitHub + the project's local/connected tools.
- Do not use Codex or ChatGPT Work resources unless the user explicitly requests them.
- Ordinary ChatGPT is the only current general planner/intelligence.
- The deterministic local Control Plane is an execution/verification component, not a second planner.
- The Control Plane owns TaskState, known ProgramGraph progression, authorization, checkpoints, verifiers/postconditions, bounded recovery and budgets.
- A known selected procedure may advance through several independently authorized/verified transitions without returning to ChatGPT after every low-level action.
- Normal semantic bootstrap/start/health must not require optional 1MCP extension infrastructure.
- Persistent tunnel identity belongs to neutral platform state.
- Third-party MCP availability is not trust or authorization.
- Raw extension tools are not automatically Chat-facing.
- Novel strategy or stale/ambiguous/UNKNOWN/incompatible state -> ABSTAIN/escalate to ChatGPT.
- Current state outranks remembered/history state.
- Delivery is not completion; explicit verification controls completion.
- Generic Windows code execution remains disabled/unreachable.
- Model/procedure/planner/observation/extension output is evidence/proposal, never authorization by itself.
- When a branch is logically complete, intended diff is reviewed, required physical/CI gates pass and no unresolved issue remains, merge it without waiting for a separate merge command.

Canonical architecture distinction: `project-context/CONTROL_PLANE.md`.

## Installed-runtime requirement

The installed normal semantic bundle must contain the canonical six-tool projection and deterministic Control Plane closure, including:

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

The public bootstrap is one entrypoint, internally modularized for tunnel, manager/runtime bundle and lifecycle verification.

Normal bootstrap requirements now include:

```text
1MCP preflight = not required
normal smoke profile = semantic
normal tunnel binding = direct-stdio
persistent tunnel source = state/tunnel.json
```

Optional adaptive/1MCP assets may remain installed for future Extension Manager work, but they are not baseline startup authority or a normal semantic release gate.

## Remaining Stage 26.3A physical gates

After all required hosted workflows are green on one exact PR head:

1. install/update that exact head on the target Windows machine;
2. confirm the accepted tunnel id migrated/resolved into `state/tunnel.json`;
3. start the **normal** semantic route — no temporary qualification route;
4. verify the tray reports normal READY and live inventory is exactly six tools;
5. ordinary ChatGPT one-goal E2E with no intermediate PowerShell relay;
6. actual `procedure_run` success through `verified_workspace_artifact_v1`;
7. independent `workspace_read` of the final nested artifact;
8. negative pre-existing-target case -> structured ABSTAIN and zero overwrite;
9. independent read proves protected content unchanged;
10. capture exact head/status/evidence in PR/docs before acceptance.

A manual `workspace_write` fallback can demonstrate resilience but does **not** count as `procedure_run` physical PASS.

## First physical test shape

Use a natural ordinary-Chat task, not a rigid tool-call script. The agent should be able to use local notes plus a real public website and meaningful browser interaction, recover from isolated failures and create the final bounded artifact through `procedure_run`.

The current preferred research-style test uses a real public site such as arXiv so `web_open`, `web_observe` and `web_interact` are exercised through actual search/click/navigation rather than `example.com`/`httpbin` fixtures.

Expected natural chain:

```text
workspace_read challenge
 -> real web research/search/click/observe
 -> workspace_write evolving notes
 -> reread notes / revise plan
 -> procedure_run final verified artifact
 -> independent workspace_read final artifact
```

## Stage order

```text
26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane — ACTIVE
    -> 26.3A canonical six-tool semantic runtime — hosted gate in progress; physical gate next
    -> 26.3B advanced verifier/postconditions
    -> checkpoint/recovery/budget mechanics as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 distribution/maintenance
 -> 28 clean-user E2E/stable release
```

Optional 1MCP Extension Manager work is orthogonal to the release-critical six-tool path and should be promoted only when a real task needs an additional backend.

## Fresh-chat startup procedure

1. Resolve live `main`, PR #92 head and current checks.
2. Read this file, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `DECISIONS.md`, `MODULE_SELECTION_POLICY.md`, `ROADMAP.md`, `DOCUMENT_STATUS.md`, `EVIDENCE_INDEX.md`, `STAGE26_3A_IMPLEMENTATION_NOTES.md` and `STAGE26_3A_PROCEDURE_RUN_SURFACE.md`.
3. Treat Stage 26.2E and Transport Supervisor evidence as accepted only for their exact recorded physical heads.
4. Treat hosted CI as software-contract evidence only; do not infer physical ordinary-Chat acceptance from it.
5. Prefer exact code/tests/current CI/physical evidence over prose.
6. Continue the current normal six-tool semantic physical qualification; do not recreate a separate five-versus-six qualification mode and do not reinsert 1MCP into the normal semantic critical path.

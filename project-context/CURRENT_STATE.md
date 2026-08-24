# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Exact code/tests/current CI/physical evidence outrank prose.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly requests them.

## Product boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. The local platform has a deterministic execution **Control Plane**, not a second general-planning brain.

```text
ordinary ChatGPT
  task interpretation / strategy / adaptation
        |
        v
OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> canonical six-tool semantic projection
        |
        v
local deterministic execution Control Plane + focused capabilities
```

The Control Plane may keep TaskState/checkpoints, advance a selected verified procedure through already-defined transitions, authorize each consequence, verify effects, apply bounded retry/recovery/resource budgets and escalate. It must ABSTAIN/escalate when current evidence does not uniquely match an allowed transition or new strategy is required.

A true local planner is future optional Track P, not current production architecture and not a Stage 27/28 prerequisite. See `CONTROL_PLANE.md`.

## Accepted Stage 26.3A public semantic surface

The normal `semantic` route exposes exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray choice between five and six tools.

The old separate `procedure-qualification` route was removed. The public launcher always routes through the canonical six-tool projection. A private five-capability file/browser implementation remains only as an internal implementation/regression layer and is not selectable or Chat-facing.

The ordinary semantic startup guard refuses READY unless live `tools/list` is exactly the six canonical names.

The tray has one normal semantic READY state; no separate qualification state/color remains.

## Normal transport vs optional extensions

Normal semantic transport is direct stdio and does not depend on 1MCP.

```text
ordinary ChatGPT
 -> Secure MCP Tunnel
 -> official tunnel-client
 -> semantic launcher
 -> six canonical tools
```

The persistent accepted `tunnel_*` id is stored in neutral platform state:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

An existing installed legacy profile at:

```text
%LOCALAPPDATA%\ChatAgentPlatform\tunnel\local-1mcp.yaml
```

may be read only as a bounded migration fallback for one already accepted tunnel id. It is not the normal semantic source of truth and fresh normal bootstrap does not recreate it as the normal route.

Fresh/current normal bootstrap initializes the semantic core directly:

```text
verified tunnel-client + neutral tunnel state
 -> verified six-tool bundle
 -> DPAPI runtime key
 -> existing safe FilesRoot OR %LOCALAPPDATA%\ChatAgentPlatform\workspace
 -> profile = semantic
 -> tunnel binding = direct-stdio
 -> six-tool smoke
 -> stopped
```

After bootstrap, public `Status` and the tray resolve through the direct semantic controller rather than legacy `status-chat-profile.ps1`; they do not query `npx @1mcp/agent` merely to report a stopped normal platform.

Baseline manager metadata records:

```text
semantic_public_tool_count = 6
extension_manager_included = false
```

1MCP is retained only as an optional internal Extension Manager for future third-party MCP backends. Its absence/failure must not block baseline six-tool bootstrap/start/status/health/smoke. Raw backend tools are not exported directly to ordinary ChatGPT; supported extensions remain behind project-owned typed semantic facades and the same authorization boundary.

Canonical operational contract: `EXTENSION_MANAGER.md`.

---

# Accepted foundation

## Stage 24 / 24.1 — typed semantic file/browser foundation and direct tunnel — ACCEPTED

Historical five-tool file/browser semantics, Windows lifecycle and direct stdio transport are accepted foundations for their exact tested scope. They do not define the current public inventory.

## Stage 25 / 25.1 / 25.2 — browser semantic + local vision — ACCEPTED

Accepted local visual baseline remains structure-first, proposal-only and behind deterministic authorization.

## Stage 26.1A-E / 26.2A-E — Windows capability foundation — ACCEPTED

Accepted Windows work includes OpenAdapt qualification, bounded capture/executor, warm latency characterization, window-scoped UIA, production Windows runtime, DesktopState, native local Grounder, deterministic UIA->vision routing and the first isolated real VS Code application E2E.

Exact physical heads/result directories and scoped measurements are authoritative in `EVIDENCE_INDEX.md` and the accepted historical stage documents.

One accepted VS Code task is not universal desktop accuracy.

## Transport Supervisor v1 — ACCEPTED / MERGED #94

Transport Supervisor v1 is the accepted reliability foundation. It provides persistent desired state/runtime ownership, bounded recovery, console-free Windows persistence and health-driven restart semantics around the normal route.

Accepted `main` foundation after #94:

```text
2f33997d3fbaa1fc52d437c00be7f16e55bdde5e
```

## Stage 26.3A — canonical six-tool verified procedure runtime — PHYSICALLY ACCEPTED

Exact accepted runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Target Windows physical pre-chat gate proved:

```text
profile = semantic
tunnel binding = direct-stdio
semantic_public_tool_count = 6
extension_manager_included = false
1MCP_REQUIRED = false
runtime_ready = true
mcp_ready = true
tunnel_ready = true
active_count = 1
conflict = false
```

A fresh ordinary ChatGPT conversation using only `Chat Local Bridge Test` then completed one long-horizon research task through all six semantic tools. It used `research-ledger.md` as working memory, visited 16 content pages, analyzed 12 works/systems/benchmark groups, recovered from one invalid browser interaction, wrote and independently reread `gui-agent-research.md`, then completed the registered `verified_workspace_artifact_v1` procedure.

First `procedure_run` task:

```text
497ecb591779219ef0ee1e55ea7ad0b8
status = completed
action_count = 3
artifact = .chat-agent-platform/stage26-3a/ordinary-chat-result.txt
sha256 = 2396b8338edced2675982db9d263a046705f7f906b553b0ed19b81f51205e583
```

Independent `workspace_read` returned the exact expected success nonce.

Second `procedure_run` task:

```text
02b09a4909b6d71e0578c19b2d395cb8
status = abstained
action_count = 0
escalation_reason = target_already_exists
```

A second independent `workspace_read` proved the original bytes/SHA were unchanged. This is the accepted physical zero-overwrite gate.

Exact locator and scoped measurements are recorded in `EVIDENCE_INDEX.md`.

---

# Active release-critical work

## Stage 26.3 — Verified Procedure Runtime / deterministic execution Control Plane — ACTIVE

Stage 26.3A is accepted. The next work is to broaden deterministic verification and procedure coverage without weakening the small semantic surface or introducing generic execution.

### Stage 26.3B — advanced verifier/postcondition library — NEXT

Broaden deterministic completion evidence for UI, files/artifacts, process/window/application state, browser state and structured outputs.

Requirements:

- action delivery remains distinct from task completion;
- current observed state outranks remembered procedure state;
- each consequence has explicit postconditions;
- stale/ambiguous/UNKNOWN evidence causes ABSTAIN/escalation;
- retries and recovery remain bounded and typed;
- new procedures remain explicit registered capabilities, not generic shell/Python/tool dispatch;
- project-owned semantic tools remain small and stable.

### Stage 26.3C — checkpoints / bounded recovery / budgets

Extend longer procedures only where 26.3B evidence demonstrates a concrete need. Preserve explicit checkpoints, retry ceilings, safe known recovery branches, action/time/resource budgets and deterministic escalation reasons.

## Stage 26.4 — Human Demo -> transferable verified candidate skill

Human demonstration transfer follows the accepted verified procedure runtime. Live re-resolution and verifier-controlled progression are required; macro replay is insufficient.

---

# Current critical path

```text
Stage 26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> Stage 26.3 Verified Procedure Runtime — ACTIVE
    -> 26.3A canonical six-tool semantic runtime — ACCEPTED
    -> 26.3B advanced verifier/postconditions — NEXT
    -> 26.3C bounded recovery/budgets as required
 -> Stage 26.4 Human Demo -> transferable verified candidate skill
 -> Stage 27 distribution/maintenance
 -> Stage 28 clean-user E2E / stable release
```

Future optional Track P may later evaluate a local planner after verified procedure-state data and measured need. It remains behind the same authorization/verifier boundary.

Optional 1MCP Extension Manager development is orthogonal to this release-critical path. It may be used later to reduce integration work for additional MCP backends without re-entering the baseline semantic critical path.

## Merge policy

When a branch is logically complete, intended diff is reviewed, required physical/CI tests pass and applicable acceptance gates are satisfied, merge it without waiting for a separate merge command.

Stop on unresolved findings, conflict, ambiguous scope or failed/skipped required evidence.

---

# Residual risks

- ChatGPT MCP app definitions are frozen snapshots; a local READY route does not by itself prove a current app binding/session is usable. The accepted 26.3A run required reconnecting the app and settling permissions before the long run; do not change binding/permissions mid-acceptance task.
- compatibility aliases for historical `_1mcp_` action IDs remain migration debt;
- the optional 1MCP/adaptive extension path is not a baseline release gate and remains less stable than the normal direct semantic route;
- one real VS Code task is not broad real-application coverage;
- `AutomationId` still lacks dedicated accepted physical coverage across real applications;
- browser DNS/rebinding/redirect/private-network isolation remains incomplete;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- future local planner has not been researched against verified procedure-state data;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane may advance only already-defined authorized+verified procedure transitions;
- normal semantic install/start/status/health/smoke must not require optional 1MCP extension infrastructure;
- fresh/current normal settings use `semantic` + `direct-stdio`;
- persistent tunnel identity belongs to neutral platform state;
- third-party MCP availability is not trust or authorization;
- raw extension tools are not automatically Chat-facing;
- new strategy/ambiguity/stale/UNKNOWN -> ABSTAIN/escalate;
- semantic/native structure before pixels where reliable;
- model/procedure/observation proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

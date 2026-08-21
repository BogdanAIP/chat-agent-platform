# Semantic Typed Capability Projection

Status: **PRODUCT-ACCEPTED FOUNDATION; CURRENT PUBLIC CONTRACT REMAINS FIVE TOOLS**.

This document records the semantic-projection boundary after accepted Stage 25.2 and Windows work through Stage 26.2D.

## Why this boundary exists

Real ordinary-Chat evidence established that concrete typed actions work, while large raw inventories and generic nested dispatch are poor product surfaces. The project therefore keeps a small truthful deterministic compatibility layer between ChatGPT and replaceable local capabilities.

`semantic-projection` is not:

- a general planner/autonomous coordinator;
- the deterministic procedure Control Plane;
- procedural memory or TaskState storage;
- a generic MCP gateway replacement;
- a dynamic server/tool registry;
- arbitrary `server + tool + args` dispatch;
- a place to hide unrelated desktop/workflow consequences behind misleading schemas.

Ordinary ChatGPT is the only current general planner. A separate future deterministic local Control Plane may orchestrate already-selected procedure transitions internally, but it remains distinct from semantic projection.

## Current accepted Chat-facing surface

| Tool | Current semantic class |
|---|---|
| `workspace_read` | scoped workspace observation/read/search |
| `workspace_write` | scoped text create/overwrite |
| `web_open` | reviewed browser navigation |
| `web_observe` | browser/accessibility observation |
| `web_interact` | reviewed browser interaction including the narrow accepted Stage 25.2 internal visual fallback |

No Chat-facing argument can choose an arbitrary MCP server/backend tool/model endpoint.

## Workspace boundary

`CHAT_LOCAL_FILES_ROOT` is mandatory for the current workspace path. Chat-facing paths are relative to that root; traversal/junction/link escapes remain rejected.

Procedure history or future planner output cannot broaden current workspace scope.

## Browser boundary

```text
fresh accessibility snapshot
 -> exact enabled target -> semantic action
 -> disabled/non-button/unresolved ambiguity -> ABSTAIN, no VLM
 -> reviewed visual miss class
      -> same-session screenshot
      -> bounded local Grounder proposal
      -> deterministic authorization/freshness
      -> one coordinate action OR ABSTAIN
```

`targetText` remains an authorization anchor. Planner/model free-form text cannot redirect visual authorization.

The projection does not expose arbitrary JavaScript/Playwright execution, unrestricted upload/network-body access, raw backend selection or generic model invocation.

## Relationship to deterministic Control Plane — Stage 26.3 direction

The local procedure Control Plane must **not** be implemented by inflating `semantic-projection` into a hidden workflow brain.

Preferred separation:

```text
ordinary ChatGPT
 -> select goal / procedure / parameters

local deterministic Control Plane
 -> TaskState + selected ProgramGraph
 -> observe current state
 -> resolve one permitted transition
 -> capability policy / authorization
 -> invoke reviewed capability semantics
 -> verify postcondition
 -> checkpoint / advance
 -> repeat while known
 -> ABSTAIN/escalate on novel state

semantic-projection / capability adapters
 -> execute only truthful reviewed capability semantics
```

A selected procedure may therefore execute multiple deterministic transitions locally, but sequence/state ownership belongs to the separate Control Plane, not `semantic-projection`.

Until a dedicated public-contract ADR:

- do not hide workflow CRUD/execution inside existing web/file schemas;
- do not create generic `workflow_execute`/opaque dispatch merely to keep the surface small;
- internal procedure/control-plane work may proceed without new public tool names.

## Windows relationship

The old statement that a Windows desktop surface is still future Stage 26.3 is obsolete.

Windows foundations are accepted through:

```text
26.2A production Windows runtime
26.2B DesktopState
26.2C native Grounder
26.2D deterministic structure-first UIA -> vision routing
```

Stage 26.2E is the first real-app E2E. Stage 26.3 integrates verified procedure Control Plane behavior over accepted capabilities.

A later ADR decides whether a few truthful native desktop/procedure public capabilities are needed.

## Future local planner

Track P may later introduce a local planner after verified data/need. That planner remains above the deterministic Control Plane and cannot directly address arbitrary semantic-projection backends or bypass scope/authorization.

Planner changes do not imply public tool-surface changes.

## Implementation invariants

- dependencies remain pinned/locked and installed outside individual user calls;
- downstream clients close cleanly;
- no hidden runtime package download during a user tool call;
- tunnel-only secrets are scrubbed before semantic core/downstream child startup;
- installed layout matches reviewed source dependency closure;
- accepted network/workspace containment regressions remain active;
- local vision remains focused internal specialist inference;
- semantic-projection remains stateless/deterministic enough to review as a compatibility boundary;
- procedure progression/checkpoints/recovery belong outside it.

## Accepted evidence lineage

Stage 24 ordinary-Chat acceptance proved the five-tool file/browser workflow.

Stage 24.1 proved the same public contract through direct stdio transport.

Stage 25.1/25.2 proved bounded same-session local visual grounding/routing without a new public vision tool.

Stage 26.2A-D added Windows runtime/observation/grounding/routing internally without changing these five public names.

## Change rule

Any exported public tool/schema/annotation change requires:

1. architecture/security review;
2. deterministic integration tests;
3. exact downstream mapping review;
4. Chat app Refresh/review where applicable;
5. real ordinary-Chat acceptance of the changed surface.

# Semantic Typed Capability Projection

Status: **PRODUCT ACCEPTED FOUNDATION; CURRENT PUBLIC CONTRACT REMAINS FIVE TOOLS**.

This document records the current invariant of the Stage 24 semantic projection after later Stage 25.2 integration. Historical Stage 24 acceptance detail remains in Git history and PR #66.

## Why this boundary exists

Real ordinary-Chat evidence established that concrete typed actions work, while large raw backend inventories and generic nested dispatch are poor product surfaces. The project therefore keeps a small truthful deterministic compatibility layer between ChatGPT and replaceable local capabilities.

`semantic-projection` is not:

- a planner/autonomous coordinator;
- a procedural-memory engine;
- a generic MCP gateway replacement;
- a dynamic server/tool registry;
- an arbitrary `server + tool + args` dispatcher;
- a place to hide unrelated desktop/workflow consequence classes behind misleading schemas.

ChatGPT remains the planner.

## Current accepted Chat-facing surface

Exactly these tool names are currently accepted:

| Tool | Current semantic class |
|---|---|
| `workspace_read` | scoped workspace observation/read/search |
| `workspace_write` | scoped text create/overwrite |
| `web_open` | reviewed browser navigation |
| `web_observe` | browser/accessibility observation |
| `web_interact` | reviewed browser interaction, including Stage 25.2 internal vision fallback for its narrow accepted click path |

No Chat-facing argument can choose an arbitrary MCP server/backend tool/model endpoint.

## Workspace boundary

`CHAT_LOCAL_FILES_ROOT` is mandatory for the current workspace path. Chat-facing paths are relative to that root. Absolute/traversal/junction escapes remain rejected by the accepted containment layers.

Procedural memory must not broaden a workspace scope merely because an older trajectory used a path. Historical procedure references are evidence, not path authorization.

## Browser boundary after Stage 25.2

`web_open` remains HTTP/HTTPS-scoped under the reviewed browser policy.

`web_observe` remains observation only.

`web_interact` supports reviewed browser interaction. For the Stage 25.2 visual click path:

```text
fresh accessibility snapshot
  -> exact enabled button: semantic click
  -> disabled/non-button/unresolved ambiguity: ABSTAIN, no VLM
  -> zero exact candidates:
       same-session screenshot
       -> bounded local text-labeled F16 grounder
       -> deterministic authorization/freshness
       -> one coordinate click OR ABSTAIN
```

`targetText` is the authorization anchor. Planner `target`, free-form instruction and planner-supplied kind cannot redirect visual authorization.

The projection does not expose arbitrary JavaScript/Playwright execution, unrestricted upload/network-body access, raw backend selection or generic model invocation.

## Procedural Memory relationship — Stage 26

Stage 26 procedural memory is intentionally **not implemented by inflating `semantic-projection` into a hidden workflow brain**.

Preferred separation:

```text
ChatGPT
  -> current semantic tool call(s)

procedural-memory substrate (internal/non-agentic)
  -> candidate skill retrieval/progress/completion evidence
  -> supplies bounded context/state to Chat/integration layer

semantic-projection
  -> executes only truthful reviewed capability semantics
```

A workflow may guide ChatGPT's sequence of tool use, but the projection itself does not choose the sequence/user goal.

Until an explicit post-desktop contract decision:

- do not add workflow CRUD/execution as misleading variants of existing tools;
- do not create a generic `workflow_execute`/opaque dispatcher merely to keep the visible surface small;
- internal Stage 26 data/compiler/verifier work may proceed without exporting new Chat tool names.

## Windows desktop relationship — future decision point

A Windows desktop surface is a separate planned Stage 26.3 capability boundary. Once it exists and passes local safety/functional acceptance, the project must decide explicitly whether:

1. a few new truthful public semantic capabilities are required; or
2. the small-semantic-surface philosophy can continue without new names.

This decision requires its own ADR, exact schemas/annotations and ordinary-Chat acceptance.

The current count of five is a proven current contract, **not permission to overload existing schemas indefinitely** and not a claim that the product can never evolve.

## Implementation invariants

- dependencies remain pinned/locked and installed outside individual user calls;
- downstream capability clients close cleanly;
- no hidden runtime package download during user tool calls;
- tunnel-only secrets are scrubbed before semantic core/downstream child startup;
- installed layout must match the reviewed source dependency closure;
- accepted network/workspace containment regressions remain active;
- local vision/runtime management remains a focused internal boundary rather than generic model orchestration.

## Accepted evidence lineage

Stage 24 ordinary-Chat product acceptance proved the five-tool file/browser workflow through PR #66.

Stage 24.1 proved the same public contract through the simpler direct stdio transport.

Stage 25.1 proved the same-session visual action foundation without adding a public vision tool.

Stage 25.2 PR #77, merged as `2a410476ef849fd6d9c172703a004b1befcbcfb1`, proved public `web_interact` semantic-first internal vision escalation on the real target machine while keeping the exact five public names.

Final target-tested Stage 25.2 production-code HEAD:

`41ef3f4032ae9169d940b3a04e5bdfe75170ca85`.

Result summary:

```text
semantic_hits = 2
visual_hits = 1
correct_abstains = 2
false_clicks = 0
errors = 0
semantic_cases_started_vlm = 0
acceptance_pass = true
```

## Change rule

Any exported public tool/schema/annotation change requires:

1. architecture/security review;
2. deterministic integration tests;
3. exact downstream mapping review;
4. Chat app Refresh/review where applicable;
5. real ordinary-Chat acceptance for the changed product surface.

The planned explicit contract-review point is after the Windows desktop surface exists.

# Semantic Typed Capability Projection

Status: **ACCEPTED TYPED-PROJECTION FOUNDATION / CURRENT STAGE 26.3A CANDIDATE SURFACE = SIX TOOLS / PHYSICAL ACCEPTANCE PENDING**.

## Why this boundary exists

Ordinary-Chat evidence established that concrete typed actions work, while large raw inventories and generic nested dispatch are poor product surfaces. The project therefore keeps a small truthful deterministic compatibility layer between ChatGPT and replaceable local capabilities.

`semantic-projection` is not:

- a second general planner;
- a generic MCP gateway replacement;
- a dynamic server/tool registry;
- arbitrary `server + tool + args` dispatch;
- arbitrary shell/Python execution;
- a place to hide unrelated consequences behind misleading schemas.

Ordinary ChatGPT remains the only current general planner.

## Current Stage 26.3A candidate Chat-facing surface

The normal semantic route now exposes exactly six canonical tools:

| Tool | Semantic class |
|---|---|
| `workspace_read` | scoped workspace observation/read/search |
| `workspace_write` | scoped text create/overwrite |
| `web_open` | reviewed browser navigation |
| `web_observe` | browser/accessibility observation |
| `web_interact` | reviewed browser interaction including bounded visual fallback |
| `procedure_run` | invoke only a registered bounded deterministic Control Plane procedure |

No Chat-facing argument can choose an arbitrary MCP server/backend tool/model endpoint.

There is no public/profile/tray switch between a five-tool and six-tool semantic mode. The public launcher always routes through the canonical six-tool projection.

The historical five-tool semantic core remains useful only as a private implementation/regression layer for file/browser semantics. It is not a selectable public contract in the Stage 26.3A candidate.

## Workspace boundary

`CHAT_LOCAL_FILES_ROOT` is mandatory for workspace semantics. Chat-facing workspace paths are relative to that root; traversal/junction/link escapes remain rejected.

Procedure history or planner output cannot broaden current workspace scope.

## Browser boundary

```text
fresh accessibility snapshot
 -> exact enabled target -> semantic action
 -> disabled/non-button/unresolved ambiguity -> ABSTAIN
 -> reviewed visual miss class
      -> same-session screenshot
      -> bounded local Grounder proposal
      -> deterministic authorization/freshness
      -> one coordinate action OR ABSTAIN
```

`targetText` remains an authorization anchor. Planner/model free-form text cannot redirect visual authorization.

The projection does not expose arbitrary JavaScript/Playwright execution, unrestricted upload/network-body access, raw backend selection or generic model invocation.

## `procedure_run` boundary

The sixth tool is deliberately typed rather than generic.

```text
ordinary ChatGPT
 -> select known goal/procedure/parameters
 -> procedure_run
 -> deterministic Control Plane
      exact registered procedure/version
      TaskState/checkpoint
      current-state validation
      exact permitted transition
      capability authorization
      bounded action
      verifier/postcondition
      checkpoint/advance
      repeat while known/permitted
      complete OR ABSTAIN
```

The Control Plane is not implemented as a hidden workflow brain inside the file/browser core. Procedure state/progression and verification remain deterministic Control Plane responsibilities.

The current `procedure_run` schema does not expose arbitrary path, command, shell, Python executable, backend, server, raw tool name, working directory or arbitrary argument bags.

## Public runtime composition

The public path is permanently composed as:

```text
semantic-projection-launcher.mjs
 -> semantic-control-plane-projection.mjs
      -> private reviewed file/browser semantic base
      -> deterministic procedure adapter
```

The launcher must not conditionally select a five-tool public entrypoint.

The ordinary semantic startup guard independently inspects the live inventory and refuses READY unless all six exact names are present.

## Windows relationship

Windows foundations are accepted through Stage 26.2E and Transport Supervisor v1. Stage 26.3 integrates verified procedure Control Plane behavior over those accepted capability foundations.

The sixth procedure tool does not itself expose generic native Windows execution. Broader Windows/UI procedures remain gated behind later reviewed procedure definitions and physical evidence.

## Future local planner

Track P may later introduce a local planner after verified data/need. That planner remains above the deterministic authorization/verifier boundary and cannot directly address arbitrary backends or bypass scope.

Planner changes do not imply public tool-surface changes.

## Implementation invariants

- dependencies remain pinned/locked and installed outside individual user calls;
- downstream clients close cleanly;
- no hidden runtime package download during a user tool call;
- tunnel/OpenAI secrets are scrubbed before semantic/control-plane child startup;
- installed layout matches the reviewed dependency closure;
- installed metadata records `semantic_public_tool_count = 6`;
- accepted network/workspace containment regressions remain active;
- local vision remains focused internal specialist inference;
- procedure progression/checkpoints/recovery remain deterministic Control Plane state;
- the normal semantic route exposes exactly six canonical tools or refuses READY.

## Evidence lineage

Historical accepted evidence remains scoped to the surface it tested:

- Stage 24 / 24.1 proved the then-five-tool file/browser workflow and direct transport;
- Stage 25.1/25.2 proved bounded local visual grounding without a new vision tool;
- Stage 26.2A-E added Windows runtime/observation/grounding/routing and real-app evidence;
- Stage 26.3A changes the candidate public surface to six by adding the typed `procedure_run` capability.

Historical five-tool evidence remains valid history but does not define the current Stage 26.3A candidate inventory.

## Change rule

Any exported public tool/schema/annotation change requires:

1. architecture/security review;
2. deterministic integration tests;
3. exact downstream mapping review;
4. Chat app Refresh/review where applicable;
5. real ordinary-Chat physical acceptance of the changed surface.

Stage 26.3A remains unaccepted physically until the normal six-tool route passes the target-Windows ordinary-Chat and negative ABSTAIN/no-overwrite gates.

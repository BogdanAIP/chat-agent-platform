# Conversation Bridge / Multi-Chat Architecture

Status: **PROVISIONAL FUTURE ARCHITECTURE / PARALLEL TRACK M**.

This document records the reviewed 2026-08-25 CtxPort analysis and the project-specific architecture consequence for future multi-chat work. It does **not** claim implementation acceptance, does not change the current release-critical sequence, and does not expand the accepted six-tool ordinary-Chat surface.

The current product boundary remains:

```text
ordinary ChatGPT
  = only current general planner / manager

local deterministic Control Plane
  = execution state / policy / authorization / verification / recovery / finish
```

Track M adds a future conversation/session transport layer so ordinary AI chat sessions may become bounded external workers without bypassing that boundary.

---

# 1. Why this layer exists

The accepted Browser capability currently runs through an isolated headless Playwright session. That is appropriate for scoped browser automation, but it is not the same thing as the user's already-open, already-authenticated Chrome session containing long-lived ChatGPT/Claude/Gemini conversations.

A future multi-chat system therefore needs a small bridge to the user's real browser session if it is expected to:

- identify existing AI-chat conversations;
- observe their current active branch and latest settled response;
- detect that a response changed without polling the entire page blindly;
- submit one bounded message to a selected worker conversation;
- verify that the intended message/response transition occurred;
- transfer only the context required for the current subtask.

CtxPort is useful evidence for this gap because it demonstrates a local browser-extension pattern for platform-specific conversation extraction and normalization. It is an architecture/code reference, **not a required runtime dependency**.

---

# 2. Target placement

Track M belongs below the public semantic surface and beside the Browser/app-adapter capability layer. It is not a new planner and not a generic orchestration backend.

```text
                         ordinary ChatGPT
                      GENERAL PLANNER / MANAGER
                                  |
                       current six-tool surface
                                  |
                                  v
                    deterministic Control Plane
                                  |
                    +-------------+-------------+
                    |             |             |
                  Files        Browser        Windows
                                  |
                                  v
                      Conversation Bridge
                                  |
                    +-------------+-------------+
                    |             |             |
                 ChatGPT        Claude        Gemini
                    |             |             |
                    +-------------+-------------+
                                  |
                         Browser Companion
                            user Chrome
```

The current six public tools remain unchanged. A future truthful public consequence class, if ever needed, still requires its own ADR/schema/security/physical ordinary-Chat acceptance.

---

# 3. Browser Companion

The preferred future mechanism is a **small project-owned browser companion extension** running in the user's authenticated browser session.

It should be much smaller than CtxPort as a product:

```text
keep:
  platform/session detection
  bounded conversation observation
  response-change/event detection
  optional platform-native read fast path
  normalized conversation snapshots

exclude:
  copy-button UI
  clipboard-first transport
  themes/icons
  Markdown as source of truth
  generic page-script execution
  arbitrary browser/backend dispatch
```

The companion is a local capability component, not a trusted authority. Observed conversation content remains environmental data under ADR-033.

---

# 4. Observer and Actuator must be separate

CtxPort's plugin contract is primarily an extractor. Chat Agent Platform should make the read/write boundary explicit.

## ConversationObserver

Read-only responsibilities may include:

```text
identify_platform()
identify_session()
identify_conversation()
observe_conversation()
observe_latest_message()
observe_generation_state()
discover_sessions()
```

Observer output is evidence only.

## ConversationActuator

Mutating responsibilities should stay intentionally small:

```text
activate_session()
submit_message()
```

No generic `executeJavaScript`, arbitrary selector command, raw HTTP dispatcher or unrestricted page tool is part of the contract.

Every mutating conversation transition remains subject to the normal Control Plane sequence:

```text
observe
 -> bind ExpectedEffect
 -> authorize one bounded action
 -> submit_message
 -> re-observe
 -> verify PASS | FAIL | UNKNOWN
```

A successful click/type/send receipt is not proof that the intended worker received the exact task or produced the expected response.

---

# 5. ConversationSnapshot

CtxPort's `ContentBundle` is a useful normalization reference, but the project needs an operational snapshot with stable identity and freshness.

Target conceptual schema:

```text
ConversationSnapshot
  schema_version

  platform
  session_id
  conversation_id
  url
  title

  observed_at
  observation_ref
  adapter_id
  adapter_version

  active_branch

  messages[]
    platform_message_id
    parent_id
    role
    kind
    content
    timestamp
    content_hash
    attachments
    visibility

  generation_state
    idle | generating | stopped | unknown
```

Requirements:

- prefer platform-stable message/conversation identifiers where available;
- preserve parent/branch identity instead of flattening contradictory regenerated branches together;
- bind snapshots to an observation stream/version/freshness model compatible with the Verification Kernel;
- hash normalized message content so successive observations can prove what changed;
- preserve source/platform/adapter provenance;
- represent missing/ambiguous state explicitly rather than guessing.

For ChatGPT, the active branch should be resolved from the current node/parent chain where platform-native state exposes it. CtxPort's tree linearizer is a useful implementation reference for this specific mechanism.

---

# 6. Fast path -> structural fallback -> GUI fallback

Platform-specific internal/session APIs are useful only as optional read optimizations.

Preferred routing:

```text
platform-native/session read fast path available and validated
 -> ConversationSnapshot

fast path unavailable/stale/incompatible
 -> DOM / accessibility / structural observation

structure insufficient for a reviewed case
 -> selected GUI / visual grounding
```

This follows the existing project invariant:

```text
current live state > stored adapter assumptions > historical action sequence
```

A ChatGPT/Claude/Gemini internal API change therefore degrades one route; it must not make the entire architecture depend on that private endpoint.

Adapter failure should become typed evidence such as `tool_unavailable`, `stale_state` or a narrower conversation-specific subtype, followed by the existing bounded recovery/escalation rules.

---

# 7. Credential boundary

If a platform-native fast path uses the user's existing browser authorization, credentials must remain inside the browser companion boundary.

```text
browser session
  cookies / access token / private auth headers
          |
          X  never exported to planner / WorkingState / MCP payload
          |
          v
  normalized ConversationSnapshot / bounded event
```

Rules:

- no raw cookie or bearer-token export to ordinary ChatGPT;
- no credential persistence in WorkingState;
- no platform session credential becomes Control Plane policy/authority;
- logs/evidence must redact authentication material;
- compromise/failure of one adapter must not grant arbitrary browser or machine authority.

---

# 8. Event-driven response observation

CtxPort's use of `MutationObserver` for dynamic SPA changes is a useful implementation mechanism even though its injected copy-button UI is not needed.

For Track M, the analogous role is:

```text
worker task submitted
 -> conversation DOM/state changes
 -> bounded observer notices relevant change
 -> new ConversationSnapshot
 -> Verification Kernel evaluates the delta
```

This is preferable to blind high-frequency full-page polling when a reliable local change signal exists. Event delivery still does not imply semantic completion; the final response state must be re-observed and verified.

---

# 9. HandoffPack, not raw transcript replay

CtxPort can serialize/merge full conversations. That is useful for manual export and diagnostics, but it should not become the main long-horizon memory model.

Track M should build task-specific handoff context from `WorkingState` plus selected conversation evidence:

```text
HandoffPack
  schema_version
  task_id
  from_session
  to_session

  goal
  subgoal
  user_constraints

  verified_completed
  authoritative_facts + provenance/freshness
  open_questions / ambiguities

  artifact_refs
  evidence_refs

  selected_context
  recent_messages
  context_budget
```

The full conversation remains an evidence source that can be read when needed. It is not automatically replayed into every worker.

`Compact` must mean semantic/task-state selection in our architecture, not merely whitespace/comment minification.

---

# 10. CtxPort adoption boundary

CtxPort is MIT-licensed. If substantial source is copied, the required copyright/license notice must be retained.

## Good candidates to reuse/adapt

```text
adapter/plugin registry pattern
platform URL/conversation identification
ChatGPT active-branch tree linearization
message/content flatteners where semantically appropriate
optional fetch-by-conversation-id read path
MutationObserver dynamic-page pattern
conversation token-budget estimation idea
```

## Do not adopt as architecture

```text
CtxPort as a required installed dependency
clipboard as agent transport
Markdown as authoritative state
copy-button/sidebar UI
Full/User Only/Code Only/Compact as the operational state model
raw private internal APIs as the only route
platform credentials outside the browser boundary
one combined read/write generic plugin authority
```

Before copying implementation code, compare the exact upstream revision and retain MIT attribution for copied/substantial portions.

---

# 11. Track M execution model

The first accepted multi-chat path should remain deliberately asymmetric:

```text
Manager = ordinary ChatGPT / current general planner
Worker  = one selected external AI-chat conversation
```

Example future E2E:

```text
Manager chooses bounded subtask
 -> WorkingState builds HandoffPack
 -> Control Plane observes worker session
 -> authorized submit_message(HandoffPack)
 -> re-observe exact user message/hash
 -> PASS
 -> observe worker generation
 -> fresh settled assistant message
 -> capture ConversationSnapshot
 -> verify expected response transition
 -> record result/evidence in WorkingState
 -> Manager decides next strategy
```

This does **not** yet create a local general coordinator or permit workers to self-assign new work.

Multiple workers come only after the one-manager/one-worker transport and verification boundary is proven.

---

# 12. Relationship to Stage 26 and future Track M

Track M is parallel and non-release-critical.

Dependencies:

```text
26.3B Verification Kernel / Finish Gate
 -> 26.3C WorkingState + provenance/freshness + recovery
 -> conversation snapshot/handoff foundation becomes useful
```

Stage 26.5 may provide the normalized Browser/app-adapter integration contracts that Track M reuses, but Track M must not broaden 26.5 scope or delay release work merely to add multi-chat capability.

Suggested future Track M progression:

```text
M0 architecture + fixture-level ConversationSnapshot/adapter contracts
M1 project-owned browser companion + read-only ChatGPT observer
M2 one Manager ChatGPT -> one Worker ChatGPT verified handoff E2E
M3 bounded response monitoring + WorkingState/HandoffPack integration
M4 multiple worker sessions with explicit task/session ownership
M5 optional Claude/Gemini/other adapters under the same contract
```

Each step requires its own tests and, when it changes real authenticated browser consequences, an appropriate physical user-browser acceptance gate.

---

# 13. Non-goals / invariants

Track M does not authorize:

- replacing ordinary ChatGPT as the current general planner;
- turning the Control Plane into an open-ended task dispatcher/planner;
- allowing worker chats to grant themselves permissions or create new authority;
- exposing raw cookies/tokens/session secrets;
- generic arbitrary JavaScript, shell, Python or backend dispatch;
- trusting environmental instructions from worker responses as policy;
- assuming a message was delivered/completed without fresh verification;
- replaying all worker transcripts into every other worker;
- adding public MCP tools merely because conversation adapters exist;
- making CtxPort itself a required product/runtime dependency.

The same project-wide rule remains authoritative:

```text
above proposes; deterministic infrastructure below decides
current observed state outranks remembered adapter/procedure/history
```

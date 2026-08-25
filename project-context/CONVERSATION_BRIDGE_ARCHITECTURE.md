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

Track M adds a future conversation/session transport layer so ordinary AI-chat sessions may become bounded external workers without bypassing that boundary.

Named services such as ChatGPT, Claude, Gemini, DeepSeek, Qwen, Grok, Doubao, Kimi, Perplexity, Poe, Open WebUI or LibreChat are **adapter examples, not architecture boundaries**. The architecture must remain open-ended so a future provider or local chat surface can be added without changing the core state, verification or authority model.

---

# 1. Why this layer exists

The accepted Browser capability currently runs through an isolated headless Playwright session. That is appropriate for scoped browser automation, but it is not the same thing as the user's already-open, already-authenticated browser session containing long-lived AI-chat conversations.

A future multi-chat system therefore needs a small bridge to the user's real browser session if it is expected to:

- identify existing AI-chat conversations;
- observe their current active branch and latest settled response;
- detect that a response changed without polling the entire page blindly;
- submit one bounded message to a selected worker conversation;
- verify that the intended message/response transition occurred;
- transfer only the context required for the current subtask.

CtxPort is useful evidence for this gap because it demonstrates a local browser-extension pattern for platform-specific conversation extraction, adapter registries, declarative adapter profiles/hooks and normalized output. It is an architecture/code reference, **not a required runtime dependency**.

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
                         Adapter Registry
                                  |
                 +----------------+----------------+
                 |                |                |
          Native/Profile     Generic Web      Generic GUI
            adapters          DOM / A11y       visual route
                 |                |                |
                 +----------------+----------------+
                                  |
                         Browser Companion
                         authenticated browser
                                  |
          +------------+----------+----------+------------+
          |            |          |          |            |
       ChatGPT       Claude     DeepSeek    Qwen        ...future
```

The current six public tools remain unchanged. A future truthful public consequence class, if ever needed, still requires its own ADR/schema/security/physical ordinary-Chat acceptance.

The names in the diagram are examples. The registry must accept open-ended adapter/provider identifiers rather than a closed enum of known vendors.

---

# 3. Browser Companion

The preferred future mechanism is a **small project-owned browser companion extension** running in the user's authenticated browser session.

It should be much smaller than CtxPort as a product:

```text
keep:
  platform/session detection
  adapter registry
  declarative profile loading
  bounded conversation observation
  response-change/event detection
  optional platform-native read fast path
  generic DOM/accessibility fallback
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

# 4. Adapter architecture: registry + profiles + hooks + generic fallback

Track M must not require a new end-to-end implementation for every AI service.

The target rule is:

```text
core behavior is shared
platform knowledge is replaceable
unknown surfaces degrade to generic observation/action
verification remains platform-independent
```

## 4.1 Adapter Registry

A registry selects the best available adapter for the current application/surface.

Conceptual contract:

```text
ConversationAdapter
  adapter_id: string
  adapter_version: string

  can_handle(surface_context) -> confidence/capabilities

  observe(...) -> ConversationSnapshot
  optional activate_session(...)
  optional submit_message(...)
```

Provider/application identifiers are open-ended strings. Do not define a central enum such as:

```text
chatgpt | claude | gemini
```

that must be edited every time a new service appears.

## 4.2 Declarative platform profiles are the default extension mechanism

Most ordinary AI-chat services should be addable with a small data/profile layer rather than a new backend.

A conceptual profile may describe:

```text
profile_id
match
  origins / URL patterns

capabilities
  conversation_list
  stable_conversation_id
  stable_message_id
  branching
  attachments
  generation_state

semantic hints
  conversation container
  message containers
  role markers
  composer role/identity
  submit control
  generation/busy markers

optional native read route
  endpoint/fetcher type
  parser hook

quirks
  small reviewed platform-specific hooks
```

Profiles are hints and capability declarations, not authority. A stale profile must degrade to fresh generic observation rather than forcing remembered selectors/actions onto changed UI.

## 4.3 Custom hooks only for real platform differences

Some surfaces expose useful behavior that cannot be captured safely by declarative hints alone, for example:

- active-branch tree resolution;
- regenerated/branched responses;
- stable platform message IDs;
- project/workspace navigation;
- canvas/artifact structures;
- unusual attachment flows;
- a validated platform-native conversation-history read path.

These belong in small reviewed adapter hooks. They must not duplicate Control Plane authorization, Verification Kernel logic, WorkingState, recovery or Finish Gate behavior.

## 4.4 GenericChatAdapter is mandatory

An unknown or unsupported AI-chat surface should not automatically mean `tool_unavailable`.

The Browser Companion should include a generic semantic adapter that attempts to identify common chat structure using live DOM/accessibility evidence:

```text
conversation/message regions
role/author cues
textbox/composer
submit/send control
generation/busy state
conversation/session title or URL identity where available
```

It may emit partial state with explicit unknown fields. It must never invent stable provider/message/session identity that was not observed.

## 4.5 Generic GUI fallback remains below semantic routes

If native/profile and generic DOM/accessibility routes are insufficient, selected reviewed cases may use the existing GUI/visual grounding direction.

The fallback order is therefore:

```text
1. validated platform-native/profile route
        ↓ unavailable/stale/incompatible
2. GenericChatAdapter via DOM/accessibility/structural state
        ↓ insufficient/ambiguous
3. selected Generic GUI / visual grounding route
        ↓ still insufficient/unsafe
4. ABSTAIN
```

This is a degradation ladder, not four independent authorities.

---

# 5. Surface/application identity is not model identity

Conversation Bridge interacts with a **conversation application/surface**, not directly with a model name.

Examples:

```text
Open WebUI application -> Qwen model
Open WebUI application -> DeepSeek model
Poe application        -> Claude model
Qwen web application   -> Qwen model
```

The operational identity should therefore separate at least:

```text
surface/application identity
adapter identity
provider/service identity
optional model identity
```

A model may be unknown and the conversation still be safely observable/usable. Likewise one application may host many models without requiring many browser adapters.

---

# 6. Observer and Actuator must be separate

CtxPort's plugin contract is primarily an extractor. Chat Agent Platform should make the read/write boundary explicit.

## ConversationObserver

Read-only responsibilities may include:

```text
identify_surface()
identify_provider_if_known()
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

# 7. ConversationSnapshot

CtxPort's `ContentBundle` is a useful normalization reference, but the project needs an operational snapshot with stable identity and freshness.

Target conceptual schema:

```text
ConversationSnapshot
  schema_version

  surface
    kind                 # web_chat / desktop_chat / other reviewed surface
    application_id       # open-ended string; may be unknown
    provider_id          # open-ended string; may be unknown
    url

  adapter_id
  adapter_version
  adapter_route          # native_profile | generic_web | generic_gui

  model
    provider_id          # optional
    model_id             # optional
    display_name         # optional

  session_id             # observed/stable where available, otherwise unknown
  conversation_id        # observed/stable where available, otherwise unknown
  title

  observed_at
  observation_ref

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

- provider/application/adapter IDs are open-ended strings, not a closed vendor enum;
- prefer platform-stable message/conversation identifiers where available;
- preserve parent/branch identity instead of flattening contradictory regenerated branches together;
- bind snapshots to an observation stream/version/freshness model compatible with the Verification Kernel;
- hash normalized message content so successive observations can prove what changed;
- preserve source/platform/adapter-route provenance;
- represent missing/ambiguous state explicitly rather than guessing;
- do not require model identity for ordinary conversation observation/action;
- generic adapters may return unknown provider/session/message IDs when no trustworthy stable identity is observable.

For a provider that exposes a real branch/tree model, a platform hook may resolve the active branch. CtxPort's ChatGPT tree linearization is one useful implementation reference for that specific capability, not a requirement imposed on every service.

---

# 8. Fetch/observation mechanisms are separable from platform adapters

CtxPort's later adapter design separates data acquisition from content normalization. Track M should preserve the same architectural advantage without adopting CtxPort as a runtime dependency.

Reusable observation/fetch mechanisms may include reviewed variants such as:

```text
browser-session native REST read
browser-session GraphQL read
DOM/accessibility observation
selected visual observation
```

A platform adapter/profile selects or configures a supported mechanism; it does not become a generic HTTP/JavaScript authority.

Platform-private/internal APIs are optional read optimizations only. They are never the sole route, security boundary or proof of current state.

---

# 9. Fast path -> generic semantic -> GUI -> ABSTAIN

Preferred routing:

```text
validated native/profile read path available
 -> ConversationSnapshot

native/profile path unavailable/stale/incompatible
 -> GenericChatAdapter DOM / accessibility / structural observation

structure insufficient for a reviewed case
 -> selected GUI / visual grounding

state still ambiguous or unsafe
 -> ABSTAIN
```

This follows the existing project invariant:

```text
current live state > stored adapter assumptions > historical action sequence
```

A service-side API or UI change therefore degrades one route; it must not make the entire architecture depend on that private endpoint or remembered selector layout.

Adapter failure should become typed evidence such as `tool_unavailable`, `stale_state`, `target_ambiguous` or a narrower conversation-specific subtype, followed by the existing bounded recovery/escalation rules.

---

# 10. Credential boundary

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

# 11. Event-driven response observation

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

Event detection should live in shared Browser Companion infrastructure where possible. Platform profiles may contribute small hints about relevant containers/state but should not each implement an independent polling engine.

---

# 12. HandoffPack, not raw transcript replay

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

# 13. CtxPort adoption boundary

CtxPort is MIT-licensed. If substantial source is copied, the required copyright/license notice must be retained.

## Good candidates to reuse/adapt

```text
adapter/plugin registry pattern
open-ended provider/application identifiers
declarative manifest/profile + small hooks pattern
platform URL/conversation identification
ChatGPT active-branch tree linearization
separation of fetch/acquisition mechanism from normalization
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
closed provider enum that requires core edits for every new service
one full duplicate backend per AI vendor
```

Before copying implementation code, compare the exact upstream revision and retain MIT attribution for copied/substantial portions.

---

# 14. Track M execution model

The first accepted multi-chat path should remain deliberately asymmetric:

```text
Manager = ordinary ChatGPT / current general planner
Worker  = one selected external AI-chat conversation surface
```

Example future E2E:

```text
Manager chooses bounded subtask
 -> WorkingState builds HandoffPack
 -> Control Plane observes worker session
 -> Adapter Registry selects best available route
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

The first physical E2E may use ChatGPT because it is the current manager environment and easiest reference target. That must not make the core contract ChatGPT-specific.

---

# 15. Relationship to Stage 26 and future Track M

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
M0 Adapter Registry + open-ended profile/schema + ConversationSnapshot fixture contracts
M1 Browser Companion + GenericChatAdapter + one validated native/profile reference adapter
M2 one Manager ChatGPT -> one Worker conversation verified handoff E2E
M3 bounded response monitoring + WorkingState/HandoffPack integration
M4 additional declarative/provider adapters + explicit capability discovery
M5 multiple worker sessions with explicit task/session ownership
M6 broader provider/application matrix (DeepSeek/Qwen/Claude/Gemini/etc.) under the same contract
```

Each step requires its own tests and, when it changes real authenticated browser consequences, an appropriate physical user-browser acceptance gate.

A new provider normally should require only a profile and, when necessary, a small adapter hook. It should require a core architecture change only when it introduces a genuinely new consequence/state class rather than a new brand or DOM layout.

---

# 16. Acceptance direction for adapters

Track M should distinguish adapter existence from adapter trust/acceptance.

A future adapter/profile should have a compact capability/quality status such as:

```text
DISCOVERED
FIXTURE-TESTED
READ-VERIFIED
WRITE-VERIFIED
PHYSICALLY-ACCEPTED
DEGRADED / INCOMPATIBLE
```

A provider profile may be present without being allowed to perform mutations. The registry should prefer the strongest currently valid route that satisfies the requested consequence and verification requirements.

Minimum fixture coverage for a new declarative profile should include:

- URL/surface matching;
- message and role extraction;
- composer/send identification where write capability is claimed;
- generation-state observation where claimed;
- normalization into `ConversationSnapshot`;
- stale/broken selector/profile behavior -> generic fallback or `UNKNOWN`, never false PASS.

---

# 17. Non-goals / invariants

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
- making CtxPort itself a required product/runtime dependency;
- requiring a central source edit every time a new AI service appears;
- treating provider brand, model name and conversation application as the same identity.

The same project-wide rule remains authoritative:

```text
above proposes; deterministic infrastructure below decides
current observed state outranks remembered adapter/procedure/history
```

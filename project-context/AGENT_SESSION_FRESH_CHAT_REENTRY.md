# Agent Session Fresh Ordinary Chat Re-entry

Status: **STAGE RESEARCH BRIEF — DEFER IMPLEMENTATION / DIRECTION SELECTED**

Research date: **2026-09-27**

Accepted BASE at research start: `24ed938c587c9d3e2288c92bc156ccc476c955f3`

Superseded implementation experiment: PR #159 at
`b5e5398f5a1a98d615175ca7b3605cde71fb00ed`

Applicable skills:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0

## 1. Stage question

What should CAP use as the first ChatGPT provider/session adapter for a bounded
fresh read-only delegated worker when code review is only one possible consumer?

The required product shape remains:

```text
ordinary ChatGPT manager
 -> CAP Delegation
 -> one fresh bounded worker conversation
 -> one task delivery
 -> one correlated terminal result
```

The provider session must not itself become the authority model. Session freshness,
personalization/history behavior, available read sources, external mutation authority,
delivery ownership and task result contract are separate concerns.

## 2. Trigger and observed failure

The original Agent Session research selected a non-personalized Temporary Chat as the
first provider route because CAP already had physical evidence for fresh launch,
one-Send delivery and result capture. That was a provider choice, not a generic
Delegation invariant.

PR #159 then used that route for automatic code review. The target-Windows run on
`b5e5398f5a1a98d615175ca7b3605cde71fb00ed` proved the browser/session mechanics all
the way through structured result capture, but the worker correctly returned
`ABSTAIN`: the non-personalized Temporary Chat could not obtain the exact
`BASE_SHA..HEAD_SHA` full diff through the remaining public read-only web surface.

The physical result therefore falsified a hidden assumption in the selected first
provider profile:

```text
fresh context
 != non-personalized Temporary Chat
 != no connected read sources
```

For review, disabling every plugin/source removed the very repository evidence that
the governing review policy requires.

This is a material provider/session authority change, so production implementation is
blocked pending this re-entry.

## 3. Current project baseline

Keep the accepted generic Delegation lifecycle:

- provider-independent deterministic delegation identity;
- private local run capability;
- immutable genesis and crash-safe mutable state;
- one launch attempt;
- one child binding;
- one delivery claim;
- `unknown -> delivered` reconciliation without a second Send;
- one correlated terminal result;
- stale/foreign result rejection;
- provider session identity below generic task identity.

The current generic state already stores `worker_profile` as a bounded identity
field and does not require a provider-specific value in
`parse_delegation_identity()`. The provider adapter, not the generic parser, is
where `fresh_readonly_worker_v1` is currently narrowed to Temporary,
non-personalized and no-plugin semantics.

Keep the accepted browser ownership mechanics from the first ChatGPT adapter:

- neutral preflight before task navigation;
- one live MV3 owner for the exact delegation/delivery;
- opaque live handle rather than putting the private run capability in a URL;
- one durable browser delivery claim;
- no blind relaunch or re-Send after ambiguity;
- exact task/result correlation;
- runtime/source attestation;
- fail closed after complete browser/MV3 owner loss.

These mechanics are useful independently of Temporary Chat.

## 4. Current product evidence

### Temporary Chat is now explicitly multi-mode

OpenAI's current Temporary Chat documentation distinguishes two modes:

- **Unpersonalized** Temporary Chat: does not use memory, custom instructions or
  plugins.
- **Personalized** Temporary Chat: may use existing memories, custom instructions
  and plugins, while still not creating/updating memories while temporary.

Source:
https://help.openai.com/en/articles/8914046

This proves that "Temporary" and "no personalization/tools" are no longer the same
product property. It also means CAP should not use Temporary-ness as a proxy for
worker authority.

### Connected applications are a separate permission surface

OpenAI documents app permissions separately from chat persistence/personalization.
Depending on the app/account/workspace, permissions can allow reads while requiring
approval for writes. Managed workspaces can additionally control supported read/write
actions.

Sources:

- https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt
- https://help.openai.com/en/articles/20001495-managing-app-permissions-in-chatgpt
- https://help.openai.com/en/articles/11509118-admin-controls-security-and-compliance-for-plugins-and-apps

Therefore session freshness and app authority should be represented and qualified
separately.

### GitHub evidence access can be read-only, but availability is surface-specific

OpenAI's GitHub-in-ChatGPT documentation says the standard GitHub app is used to
analyze/search/cite repository code and states that the ChatGPT GitHub app only reads
repositories; generating/editing/pushing code is a Codex path. It also warns that
GitHub availability varies by plan and product surface.

Source:
https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt

This is direct solution evidence that a fresh ordinary ChatGPT conversation can, on a
supported surface, have useful repository evidence access without requiring GitHub
mutation authority. It is **not** permission to assume every connected GitHub
integration or every account exposes the same action set. CAP must positively qualify
the actual reviewer surface, and otherwise ABSTAIN/fall back.

### Regular chat personalization is not review evidence

Regular chats may use account personalization/memory when enabled. That weakens the
old "clean room knows nothing about the project" property, but it does not change the
review evidence contract: remembered claims, prior summaries and custom instructions
are not repository evidence and cannot satisfy exact BASE/HEAD/diff requirements.

For independent review, the stronger invariant is operational:

```text
fresh conversation with no inherited development transcript
 + immutable REVIEW_REQUEST_V1
 + independently reconstructed exact repository evidence
 + no repository mutation authority
 + falsification before findings
```

The reviewer may know background facts from personalization, but those facts are
untrusted hints unless re-established from the exact target repository evidence.

## 5. Source-code evidence

### openai/codex

Repository: `openai/codex`

Exact ref:
`41f9084b30812db321a0b592def4f500d1e79cf4`

Research date: 2026-09-27.

Relevant paths/symbols inspected:

- `codex-rs/tui/src/app/session_lifecycle.rs`
  - `ThreadAttachPresentation::Fresh`
  - fresh vs resume/fork lifecycle.
- `codex-rs/core/src/thread_manager.rs`
  - `start_thread`
  - `spawn_internal_session`
  - `fork_internal_session`
  - fresh history and parent ownership are independent choices.
- `codex-rs/core/src/agent/child_config.rs`
  - `prepare_agent_spawn_config`
  - `apply_spawn_agent_runtime_overrides`
  - child approval policy and permission-profile snapshot are explicitly rebound
    from current runtime state rather than inferred from "childness".
- related tests/search evidence:
  - `codex-rs/core/src/agent/control_tests.rs`
  - `codex-rs/core/tests/suite/mcp_auth_elicitation.rs`
  - `codex-rs/core/tests/suite/mcp_tool_exposure.rs`

Classification: **OPEN_IMPLEMENTED** for separating fresh/forked session lifecycle
from runtime permission/profile semantics.

Lesson: **REFERENCE_ONLY / ADAPT_MECHANIC**.

Mapping to CAP: a child being fresh is not enough to define what it may read or
mutate. Freshness and authority need separate qualification.

Important difference: Codex has its own agent/tool/permission runtime and remains a
reference, not CAP's Control Plane or selected worker host.

### OpenHands/OpenHands

Repository: `OpenHands/OpenHands`

Exact ref:
`fd9145958e9e93bfbad3252fce7a69493e61215a`

Research date: 2026-09-27.

Relevant paths/symbols inspected:

- `src/api/agent-server-adapter.ts`
  - `buildStartConversationRequest`
  - `getAgentTools`
  - conversation creation, plugins, tool set, confirmation policy, security
    analyzer and parent-conversation relation are explicit separate fields.
  - planning conversations use a deliberately narrow tool list.
- `__tests__/api/agent-server-adapter.test.ts`
  - tests tool presence/absence and confirmation/security derivation.

Classification: **OPEN_IMPLEMENTED** for conversation creation and task authority/tool
configuration as separate dimensions.

Lesson: **REFERENCE_ONLY / ADAPT_MECHANIC**.

Mapping to CAP: do not encode "no connected sources" into the meaning of a fresh
session. The task/consumer profile should determine allowed read sources and
consequence authority.

Important difference: OpenHands' tool and confirmation model is not CAP's authority
model and is not imported.

## 6. Failure lessons

### Failure: isolation removed required evidence

Symptom: exact-head reviewer returned `ABSTAIN` although delivery/capture succeeded.

Root cause: the first provider profile coupled freshness to
non-personalized Temporary/no-plugin mode.

Consequence: a correctness-oriented review policy requiring exact diff evidence cannot
complete.

Shield: separate fresh-conversation proof from source/tool authority qualification.

### Failure: connected app presence does not prove read-only authority

A personal/account permission such as "Allow read actions" can control prompting
without necessarily removing write actions from the app's supported action surface.

Shield: consequence-critical read-only workers must qualify the **actual available
action surface**, not merely rely on "we promise not to write" or an approval prompt.
For GitHub review, use a positively proven read-only GitHub ChatGPT integration/surface
or ABSTAIN/manual fallback.

### Failure: personalization can bias candidate generation

A fresh ordinary chat can receive account memory/custom instructions. That may expose
prior project conclusions.

Shield: operational independence remains evidence-bound. The reviewer gets no
development transcript/reasoning; memory is not admissible evidence; every PASS or
finding must still be reconstructed from exact repository evidence and survive
falsification.

This is weaker clean-room isolation than non-personalized Temporary Chat, but it is
compatible with independent evidence-based review when the evidence and mutation
boundaries are enforced.

### Failure: UI/provider drift remains

Ordinary-new-chat and Temporary-new-chat are both browser UI surfaces.

Shield: reuse the provider adapter's exact runtime attestation, structural
fresh-chat/composer/result observations and fail-closed behavior. Do not promote DOM
selectors into generic Delegation identity.

## 7. Alternatives

### A. Keep non-personalized Temporary Chat as the default worker — REJECT as default

Strengths:

- strongest clean-room isolation available in current ChatGPT UI;
- already physically exercised;
- no memory/custom instructions/plugins.

Weaknesses:

- no connected read sources;
- already caused a real review ABSTAIN;
- makes a provider privacy mode look like generic worker authority;
- poor fit for researchers/auditors that need bounded external evidence.

Retain only as an optional clean-room profile for tasks that genuinely require no
personalization and no connected sources.

### B. Personalized Temporary Chat with connected sources — DEFER as a special profile

Strengths:

- preserves temporary retention/history behavior;
- can use memories/custom instructions/plugins.

Weaknesses:

- still makes Temporary a special provider mode without solving a generic need;
- plugin/action qualification is still required;
- no advantage over ordinary fresh chat for most delegated read-only tasks.

Use later only when "temporary but connected" is itself a real task requirement.

### C. Fresh ordinary ChatGPT conversation + explicit read-only consumer qualification — SELECTED DIRECTION

Strengths:

- simplest match for "new worker conversation";
- supports multiple task classes, not only review;
- connected read-only sources can be used where positively qualified;
- keeps ordinary ChatGPT as the model/runtime already paid for and selected by CAP;
- reuses existing delivery/capture lifecycle.

Weaknesses:

- account personalization may influence priors;
- connected-source availability and action surface vary by account/product surface;
- provider UI remains physically qualified rather than API-stable.

This is the selected first direction.

### D. Manager-built immutable evidence bundle into non-personalized Temporary Chat — DEFER

Strengths:

- preserves clean-room model context;
- could avoid connected-app authority in the worker.

Weaknesses:

- the manager becomes an evidence-selection intermediary;
- exact repository snapshot/diff provenance, completeness and size become a new
  release-critical evidence-packaging subsystem;
- review policy currently expects independent repository reconstruction.

Re-enter only if a clean-room reviewer is later required and a trustworthy evidence
bundle has a concrete consumer.

### E. Move first workers to Codex/OpenHands/API runtime — REJECT for this stage

Strengths:

- mature session/tool configuration.

Weaknesses:

- imports or duplicates a second agent runtime/tool authority;
- conflicts with the current product choice to use ordinary ChatGPT as planner/model
  surface where possible;
- unnecessary to solve the observed provider-profile coupling.

Keep as source references.

## 8. Architecture lineage decisions

### General planning / novel strategy — KEEP

Ordinary ChatGPT remains the only current general planner.

### Bounded Agent Session / Delegation lifecycle — KEEP

No generic identity/state transition needs to change for this decision.

### First-provider session mode — REFINE

The first general-purpose session mode should be a **fresh ordinary ChatGPT
conversation**, not a mandatory non-personalized Temporary Chat.

Temporary Chat remains an optional provider profile.

### First-provider browser delivery ownership — REUSE_MORE

Keep the existing one-owner/one-Send/reconciliation/runtime-attestation mechanics.
They solved real browser delivery problems and are independent of the Temporary
privacy mode.

### Worker profile semantics — REFINE WITHOUT REWRITING V1

Do not silently redefine the already accepted
`fresh_readonly_worker_v1` contract/physical evidence.

A later implementation should add a new profile identifier for ordinary fresh
read-only connected work (working name:
`fresh_readonly_connected_v1`) while retaining the existing Temporary clean-room
profile.

The generic parser already supports bounded profile identifiers, so this does not
require a generic identity schema migration.

### Reviewer-specific exact identity/result state — KEEP

Repository/PR/BASE/HEAD identity, `REVIEW_RESULT_V1`, stale handling and
automatic/manual result reconciliation remain specialist policy.

### Reviewer authority qualification — REFINE

"No plugins at all" is no longer the selected way to prove read-only review
authority. The reviewer needs the exact evidence source while mutation actions remain
unavailable.

For a future automatic reviewer, positively qualify a read-only GitHub ChatGPT surface
or ABSTAIN. Approval-gated mutation actions are not equivalent to unavailable mutation
actions.

### Codex/OpenHands — KEEP as references

No runtime dependency is introduced.

## 9. Architecture primitives

No new persistence, scheduler, event bus, lease or durable state owner is selected.

The only new semantic distinction is a **provider worker profile** separating:

```text
fresh conversation
from
personalization/retention mode
from
allowed read sources
from
external mutation authority
```

For the next implementation, keep that distinction as explicit profile contracts,
not a generic capability-policy framework. A general profile schema/registry is
deferred until at least two materially different authority profiles require it.

## 10. Failure / crash matrix

Existing Delegation crash rules remain authoritative. Changed/new session-profile
cells are:

| Boundary | Physical/session state | Required evidence | Rule |
|---|---|---|---|
| Before child prompt | ordinary page is not provably a new empty conversation | fresh-chat structural evidence missing | no prompt, no Send |
| Before child prompt | fresh ordinary chat proven | exact intended profile and runtime attestation proven | prompt handoff may proceed |
| Before Send | another user/assistant turn appears | child is no longer fresh/exclusive | fail closed, no Send |
| Before Send | read-only consumer requires a source that is unavailable | source qualification absent | no false completion; ABSTAIN/fallback |
| Before Send | mutation-capable action surface is present for a read-only consequence boundary | read-only authority unproven | no Send for consumers that require mutation unreachability |
| After Send | source becomes unavailable | task already delivered | worker may return ABSTAIN/ERROR; never re-Send |
| After Send | personalization contributes background claims | exact repository/environment evidence differs or is missing | personalization is non-authoritative; reject unsupported claim |
| Delivery ACK ambiguous | same as accepted Delegation | exact delivery evidence required | no second Send; reconcile same delivery only |
| Result visible/capture ambiguous | same as accepted Delegation | exact correlation + current UI | capture once or fail closed |
| Complete MV3/browser loss | same as accepted Delegation | no surviving owner | no reconstructed launch/Send authority |

No cell introduces a second physical Send.

## 11. Verification plan for a future implementation

When this stage is re-opened for code, acceptance should prove:

### Deterministic

- existing `fresh_readonly_worker_v1` Temporary contract remains unchanged;
- new ordinary-fresh profile has a distinct identifier;
- generic Delegation state accepts both without provider semantics entering identity;
- ordinary fresh adapter requires zero existing conversation turns before prompt;
- one launch, one Send, one result remains enforced;
- mutation-authority qualification is consumer-specific and fail-closed;
- result/capture/provenance rules remain unchanged;
- public six-tool CAP surface remains unchanged.

### Physical

Run at least two consumers so the provider adapter is not reviewer-shaped:

1. a non-reviewer read-only research/evaluation task in a fresh ordinary chat;
2. code review only if a read-only GitHub evidence surface is positively available.

For review, prove exact BASE/HEAD/diff access and the absence of GitHub mutation
authority in that actual worker environment. If that cannot be proven, keep manual
fresh review as the release-assurance path.

### Independent review

Any implementation that changes provider/session authority requires fresh exact-head
semantic review.

## 12. Complexity budget

Allowed when implementation is re-entered:

- one new explicit worker profile;
- one ordinary-fresh ChatGPT adapter mode/sibling;
- reuse/extract only the browser delivery/capture code necessary to avoid copying the
  existing MV3 one-owner/one-Send machinery;
- focused deterministic and physical acceptance.

Not allowed without another re-entry:

- generic plugin registry;
- generic permission language;
- scheduler/event bus;
- worker pools/fan-out;
- mutating worker profiles;
- arbitrary provider framework;
- manager-built evidence distribution service.

## 13. Decision

**DEFER implementation now; select the ordinary-fresh direction for the next Agent
Session provider stage.**

Why DEFER instead of immediately building another adapter:

1. PR #159 demonstrated that the current reviewer-first path is over-specialized and
   should not define the generic session architecture.
2. The accepted generic Delegation core already exists; no correctness defect requires
   a replacement.
3. CAP Core v1 freeze work is already farther along and does not require automatic
   reviewer automation because the accepted manual fresh-review fallback remains
   available.
4. Starting a second provider adapter immediately would turn the discovered design
   correction into another large side project before the core freeze is closed.

Therefore:

- do **not** merge PR #159 in its current reviewer/Temporary form;
- do **not** keep patching non-personalized Temporary Chat to make it a universal
  worker;
- retain `chatgpt-temporary` on accepted main as the bounded clean-room first-provider
  evidence already earned;
- use manual fresh ordinary ChatGPT review for release assurance where needed;
- return the active release path to CAP Core v1 freeze;
- re-enter implementation of the ordinary-fresh adapter after Core v1 freeze, or
  earlier only if a concrete second consumer makes it release-critical.

Re-entry evidence should include the actual target-account ordinary-chat source/action
surface, especially whether the required connected source is positively read-only.

## 14. What would falsify this decision

Re-open immediately if any of these becomes true:

- Core freeze materially depends on automatic delegated reviewer execution rather than
  the accepted manual review path;
- a current release-critical task needs a connected read-only fresh worker and cannot
  be done through the main ChatGPT/CAP path;
- ChatGPT exposes a stable, positively qualified per-chat read-only capability profile
  that materially reduces implementation complexity;
- the ordinary fresh-chat provider surface cannot reliably prove an empty new
  conversation or one-Send/result correlation.

Until then, the adapter is a post-Core capability, not a prerequisite to freezing the
Control Plane.

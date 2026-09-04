# Prime Runtime Adaptation Roadmap — Completeness Addendum

Status: **PROPOSED RESEARCH ROADMAP ADDENDUM — NO PRODUCTION AUTHORITY**

This addendum closes several details that were discussed after the first roadmap draft but were not explicit enough in `PRIME_RUNTIME_ADAPTATION_ROADMAP.md`. It is part of the preserved research intent and must be folded into the main Prime roadmap when the branch is refreshed after PR #149. It does not authorize production implementation.

## 1. Non-negotiable product target

The intended product path is specifically:

```text
ordinary ChatGPT Plus / GPT-5.6 Sol = primary reasoning source
Prime Agent                         = candidate durable session/runtime substrate
chat-agent-platform                 = trusted authority / effects / evidence / verification layer
browser extension + ChatGPT UI      = ordinary-ChatGPT turn transport / wake path
procedure_run                       = bounded Chat-facing CAP transport

Codex                              = 0 on the qualified path
ChatGPT Work/agent execution       = 0 on the qualified path
external LLM API                   = 0 on the qualified path
```

The research is not a generic "use Prime" experiment. It exists to test whether CAP can keep ordinary ChatGPT Plus as the actual reasoning source while avoiding the need to build most future agent-runtime infrastructure from scratch.

## 2. The custom Prime provider must be a pure bridge

The candidate provider should be isolated behind one narrow adapter, tentatively `cap-chatgpt-provider` / `PrimeRuntimeAdapter`.

It must not silently fall back to OpenAI API, Anthropic, Prime Inference, Codex or another model provider. Its model-facing responsibility is only:

```text
Prime streamSimple request
 -> bounded local CAP model broker
 -> durable MODEL_REQUEST
 -> ordinary ChatGPT reasoning turn
 -> validated MODEL_RESPONSE
 -> Prime streamSimple result
```

Any fallback provider is a separately authorized experiment and must never be implicit on the zero-API qualified path.

Prime-specific SDK/API calls should not be spread throughout CAP. Keep them behind one adapter so Prime can be upgraded, replaced or rejected without rewriting CAP authority/verification code.

## 3. Explicit resumable boundary — do not synchronously call the same ChatGPT turn from itself

The model boundary must be resumable. Prime cannot safely remain inside one `procedure_run` call waiting for the same ordinary ChatGPT turn to recursively invoke itself.

The intended state flow is:

```text
Prime RUNNING
  -> needs model decision
  -> durable MODEL_REQUEST
  -> NEEDS_MODEL / WAITING_FOR_CHATGPT
  -> current procedure_run returns that request

ordinary ChatGPT reasons
  -> next bounded procedure_run continuation submits MODEL_RESPONSE

CAP validates response
  -> Prime resumes the same logical request/session
  -> RUNNING
```

This yield/resume seam is a normal runtime state, not an error path.

The exact public operation shape remains a Stage Research decision, but candidate `procedure_run` operations may look like:

```text
start_prime_session
continue_prime_session
deliver_model_response
read_prime_state
```

or one resumable procedure carrying the same lifecycle. No new public ChatGPT tool is required merely for Prime integration; the existing exactly-six public surface should remain intact unless separately accepted.

## 4. Persistent rich-context conversation lifecycle

For normal Prime reasoning, the default hypothesis is:

```text
one Prime logical session
  <-> one persistent ordinary ChatGPT conversation
```

Repeated model requests should return to that same conversation so useful task/project context accumulates rather than being intentionally erased.

Conversation identity is part of durable correlation. CAP must not silently switch a Prime session to an unrelated ChatGPT conversation after browser restart, logout, tab replacement or UI recovery.

If the bound conversation is genuinely unavailable, the system must either:

- fail closed / enter a recovery state; or
- explicitly create a replacement conversation under a new recorded conversation generation and re-project the required context.

A replacement conversation is not "the same conversation" merely because it receives the same prompt.

Independent review remains the deliberate exception: it uses a fresh Temporary Chat/profile to reduce inherited project knowledge.

## 5. Browser-wake prerequisites and fail-closed behavior

Automatic ordinary-ChatGPT wake is only valid when the required environment is actually available and qualified. At minimum research/qualification must cover:

```text
Windows/user session available
Chrome can be started or focused
ChatGPT account session authenticated
correct extension generation installed/executing
extension runtime provenance accepted
Chat Local Bridge/CAP app/plugin connected and invokable
CAP local transport/controller available
bound Prime/session/request identity still current
bound ChatGPT conversation still current or explicit replacement is authorized
```

If a required condition is unavailable, the system must not silently switch to another model path. The safe fallback is a durable state such as:

```text
WAITING_FOR_CHATGPT
BLOCKED
RECOVERY_REQUIRED
```

with later explicit retry/reconciliation when the environment becomes available.

## 6. Scheduler has two different wake classes

Prime scheduling/heartbeats must distinguish deterministic work from work requiring a new model decision.

```text
deterministic wake
  -> CAP/Prime may execute already-authorized deterministic checks/procedures
  -> no new ChatGPT reasoning turn required

intelligence-required wake
  -> create MODEL_REQUEST
  -> attempt CAP browser wake
  -> ordinary ChatGPT + explicit CAP/plugin invocation
  -> MODEL_RESPONSE
  -> Prime continues
```

If the browser/ChatGPT wake path is unavailable, the second class waits; it must not invent a model answer or silently use an external provider.

This distinction remains useful even if automatic browser wake ultimately works reliably.

## 7. Prime dependency/version isolation and qualification

Prime must be treated as an executable dependency with exact provenance, not as a mutable cloud service that CAP blindly trusts.

Before production use, record and bind at least:

```text
Prime repository/version
exact commit or immutable release
adapter version/runtime generation
configuration/profile
relevant dependency/runtime identity
```

Do not auto-upgrade Prime on the accepted production path. A Prime upgrade that can affect session lifecycle, persistence, recovery, messaging, model-provider behavior, tool execution or authority assumptions requires the applicable focused tests and qualification before becoming the accepted runtime generation.

This is especially important because CAP acceptance relies on exact behavior/provenance rather than "latest Prime probably still works".

## 8. Full-value comparison must include maintenance/dependency cost

The final `ADAPT | KEEP | ADOPT` decision is not based only on task success.

In addition to success, latency, context, duplicate effects and recovery, compare:

```text
CAP code eliminated or avoided
new adapter/control code required
Prime-specific maintenance burden
upgrade/requalification burden
failure surface introduced by the dependency
amount of future runtime infrastructure no longer built locally
```

For the reviewer consumer, preserve the planned evaluation seam (for example Harbor-backed review evaluation with ReviewBench first, followed by bounded SWE-Review-Bench / CR-Bench-style controls when honestly applicable). Semantic reviewer quality and CAP lifecycle reliability remain separate evidence dimensions.

## 9. What Prime may replace if evidence is favorable

Candidate roles to take from Prime rather than rebuild locally:

```text
AgentSession/session runtime
daemon/supervisor
attach/detach
session persistence
retained workers
agent-to-agent messaging transport
schedules/heartbeats/goals
subagent runtime
persistent Python/kernel mechanics
context compaction
part of runtime recovery
```

Candidate roles that remain CAP-owned unless separately researched and accepted:

```text
ordinary ChatGPT integration
procedure_run/public semantic boundary
capability/authority model
stable operation/delegation/delivery/model-request identity
no-blind-retry / ambiguity reconciliation
source/runtime provenance
host-effect execution boundary
physical Browser/Files/Windows observation
ExpectedEffect
WorkingState authoritative facts
Verification Kernel
Finish Gate
independent review acceptance
verified skill/memory promotion
```

The preferred outcome remains `ADAPT`: Prime is the engine/runtime substrate, ordinary ChatGPT is the reasoning source, CAP is the trusted control and verification layer.

## 10. Anthropic Commerce Agents as a boundary reference

The later exact-source Prime Stage Research must include `anthropics/commerce-agents` as a **mechanism reference** for the boundary between persistent Prime/ChatGPT reasoning context and CAP-owned authority/effects. This note does not pre-accept any Anthropic mechanism and does not treat the commerce-agent harness as a session/runtime replacement for Prime.

All material claims used in the Stage Research Brief must be re-traced under `.agents/skills/source-code-research/SKILL.md` to an exact upstream commit/tag, concrete files/symbols, tests where available and relevant failure history. README/blog descriptions alone are insufficient implementation evidence.

The mechanism questions to answer are:

1. **Object / observation provenance.** Does CAP need a first-class, bounded provenance reference for object IDs, messages, listings, page-derived values or worker observations crossing from persistent Prime/ChatGPT context into a consequence-bearing CAP effect? The required invariant is not a particular type name; it is that stale, invented or foreign objects cannot become effect authority merely because they survived in model context.
2. **Untrusted-context fencing.** How should persistent reasoning distinguish project authority/instructions and authoritative CAP state from untrusted third-party page/message/tool/worker content? Long-lived context makes this more important because hostile or stale content can survive for many turns.
3. **Consequence staging.** For which consequence classes is the existing CAP `authorize -> act -> re-observe -> verify` contract sufficient, and for which, if any, does evidence support an explicit `propose/stage -> approve -> revalidate -> apply` boundary? Do not introduce a generic staging framework unless a concrete CAP consequence class requires it.
4. **Outcome-oriented evaluation.** Can snapshot/outcome regression cases with long, messy, contradictory or partially stale histories provide a cheap deterministic regression layer above unit tests and below physical CAP qualification? This should complement, not replace, exact physical/security/provenance gates.
5. **Provenance through compaction.** If Prime or ChatGPT compacts/summarizes persistent context, how are source identity, freshness and authority preserved for facts or objects later reused in decisions? LLM-generated summaries must never manufacture or upgrade CAP authority.

Names such as `GroundedReference` or `UntrustedObservation` are **not** treated as Anthropic terminology or preselected CAP primitives. If Stage Research later proposes such concepts, it must derive the minimum project-owned mechanism from exact source evidence, current CAP invariants and observed failure modes.

Anthropic Commerce Agents is therefore a reference for provenance/fencing/staged-consequence/evaluation mechanics, not evidence for Prime daemon/supervisor, attach/detach, persistent AgentSession or retained-worker recovery. Those runtime questions remain owned by Prime exact-source research plus the required independent runtime/harness comparison cohort.

The first core Prime proof should continue to exercise the thing Prime is being considered for: a persistent rich-context session with multiple model/tool turns, detach/restart/reattach continuation and retained Task A -> Task B isolation. The fresh Temporary reviewer is a later product consumer and must not substitute for that persistent-runtime proof.

## 11. Completion rule for the preserved research plan

Before anyone starts broad Prime integration, the combined roadmap + this addendum must still answer all of these explicitly:

```text
How does Prime request a model turn?
How does the current ordinary ChatGPT receive that request?
How does the same persistent conversation retain useful context?
How does Prime resume after the ChatGPT answer?
How is one request prevented from producing two Sends/responses?
How does crash/restart recover the same identity?
How is automatic browser/plugin wake performed and qualified?
What happens when browser/plugin/ChatGPT is unavailable?
How is zero Codex/API physically demonstrated?
How is Prime prevented from bypassing CAP authority?
How are Prime versions/upgrades pinned and requalified?
How are object/observation provenance and untrusted-context boundaries preserved?
How does provenance survive compaction/context projection?
When, if ever, is explicit stage/approve/revalidate/apply required beyond current CAP consequence semantics?
How do outcome/snapshot regressions complement physical CAP gates?
How do we decide quantitatively whether Prime actually reduces total project work?
```

If any of these becomes materially different during Stage Research, update the research decision before production implementation.
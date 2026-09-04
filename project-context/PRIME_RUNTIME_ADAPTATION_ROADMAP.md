# Prime Runtime Adaptation Roadmap

Status: **PROPOSED RESEARCH ROADMAP — NO PRODUCTION AUTHORITY**

This document preserves the current architectural discussion so the Prime investigation does not depend on one ChatGPT conversation. It does **not** change the accepted release order in `ROADMAP.md`, does not authorize production implementation, and does not modify PR #149. Production work described here remains blocked until the repository's `stage-research` and, where applicable, `source-code-research` gates are completed on the then-current repository state.

## 1. Why this branch exists

The project is approaching a choice: continue implementing a large project-owned Agent Runtime, or reuse a mature external runtime underneath CAP while preserving the project's own trust/verification boundary.

Prime Agent is a candidate because it may already provide much of the future infrastructure CAP would otherwise need to build and harden itself:

- durable agent sessions;
- daemon/supervisor lifecycle;
- attach/detach and restart continuation;
- retained workers;
- agent-to-agent messaging;
- scheduling/heartbeats/goals;
- subagent lifecycle;
- persistent Python/kernel mechanics;
- context compaction;
- part of runtime recovery.

The architectural hypothesis is **not** "replace CAP with Prime". The preferred hypothesis is:

```text
ordinary ChatGPT Plus / GPT-5.6 Sol
            reasoning
               |
               v
           Prime Agent
      session/runtime mechanics
               |
          proposed effects
               v
              CAP
 identity / authority / provenance
 reconciliation / verification / Finish Gate
        |          |          |
     Browser      Files      Windows/apps
```

Prime may become the runtime substrate. CAP remains the trusted control/verification layer. Ordinary ChatGPT remains the intended general reasoning source unless a later accepted decision explicitly changes that.

## 2. Critical correction to the Agent Session model

Fresh/Temporary Chat is **not** the general Agent Session model.

The default for normal workers, research workers and Prime reasoning should be **context-rich and persistent** when that improves task quality. Fresh isolation is a specialized profile used when independence matters.

Target separation:

```text
context-rich ordinary worker / Prime reasoning
  -> persistent ordinary ChatGPT conversation
  -> accumulated useful task/project context
  -> CAP plugin/bridge available when needed
  -> repeated turns in the same conversation/session

independent reviewer
  -> fresh Temporary Chat
  -> intentionally reduced project knowledge
  -> no personalization
  -> no unrelated apps/plugins
  -> exact review task/evidence only
```

Therefore generic delegation/session state should not encode "Temporary Chat" or "fresh reviewer" as a universal invariant. Provider/profile policy owns those requirements.

PR #149 should be completed as its bounded Agent Session / Delegation foundation, but before merge its generic lifecycle must not accidentally make `fresh_readonly_worker_v1` the only possible future worker profile. The Temporary Chat adapter may remain strict for the fresh-review/read-only profile.

## 3. What must remain project-owned even if Prime is adopted

Prime must not automatically inherit CAP authority merely because it manages a worker/session.

CAP retains ownership of:

- ordinary-ChatGPT integration and `procedure_run` boundary;
- capability activation and consequence authorization;
- stable operation/delegation/delivery/model-request identity;
- exactly-once / no-blind-retry rules for consequence-bearing effects;
- ambiguous outcome reconciliation;
- provenance and runtime/source attestation where required;
- Browser/Files/Windows physical observation and effect evidence;
- WorkingState and authoritative execution facts;
- ExpectedEffect;
- Verification Kernel;
- independent Finish Gate;
- reviewer acceptance policy;
- verified skill/memory promotion;
- the exactly-six public semantic tool surface unless separately researched/reviewed.

Prime should not receive a path that can bypass CAP and mutate the host directly merely because its own runtime offers shell/Python/tool access. The preferred production boundary is:

```text
Prime proposes tool/effect
  -> CAP authorizes
  -> CAP executes through the accepted capability
  -> CAP re-observes
  -> CAP verifies
  -> result/evidence returns to Prime
```

Any broader Prime host authority requires separate Stage Research and explicit acceptance.

## 4. Central research question

The first question is intentionally narrow:

> Can Prime Agent serve as a durable agent runtime underneath ordinary ChatGPT, with the current ordinary ChatGPT conversation acting as Prime's reasoning/model source through CAP/`procedure_run`, while using zero Codex, zero Work-agent execution and zero external LLM API calls?

A stronger version is required before architecture adoption:

> Can Prime use CAP's browser-controlled ChatGPT transport as a durable asynchronous model provider — including automatic wake of an ordinary ChatGPT turn, exact model-request correlation, no duplicate delivery after ambiguous outcomes, restart recovery and persistent rich-context conversation — while preserving CAP authority and verification?

## 5. Intended bridge architecture

The target experiment is not Prime + Codex and not Prime + OpenAI API.

```text
User / scheduled Prime continuation
            |
            v
ordinary ChatGPT conversation
        GPT-5.6 Sol
            |
        procedure_run
            |
            v
           CAP
            |
            v
   Prime Agent runtime
            |
   custom streamSimple provider
            |
            v
      MODEL_REQUEST_V1
            ^
            |
      CAP continuation
            |
            v
ordinary ChatGPT reasoning turn
            |
            v
     MODEL_RESPONSE_V1
            |
            v
Prime continues model/tool loop
```

For one logical Prime session, the preferred first design is one persistent ordinary ChatGPT conversation, not a new Temporary Chat for every model request.

```text
Prime session A <-> ChatGPT conversation A
  request #1         same conversation
  request #2         same conversation
  request #3         same conversation
```

This preserves useful accumulated context and avoids repeatedly rebuilding the whole project/task history.

## 6. Prime branch rule relative to PR #149

This research branch is created from the currently accepted `main` and stays logically separate from PR #149.

Sequence:

```text
create and preserve this roadmap branch now
  -> return to PR #149
  -> finish/fix/review/physically qualify/merge #149
  -> refresh this branch against the then-current main
  -> rerun repository skill bootstrap
  -> perform Prime Stage Research
```

No Prime production integration is to be mixed into PR #149.

## 7. Gate 0 — finish the current foundation without overgeneralizing Temporary Chat

Before Prime implementation work:

- finish PR #149 under its current accepted/researched scope;
- preserve generic delegation identity, delivery identity, private run capability, crash-safe state, no-blind-resend rules, result correlation and runtime provenance;
- ensure fresh/Temporary Chat remains adapter/profile policy rather than universal Agent Session truth;
- finish required hosted CI, fresh semantic review and physical qualification;
- merge #149 before using it as accepted foundation for Prime research.

This gate does **not** require implementing a rich-context worker in #149. It only requires keeping the generic lifecycle open to future profile diversity.

## 8. Gate 1 — exact source-code Stage Research for Prime

After #149 is accepted, rerun `AGENTS.md` bootstrap on the new main and execute:

- `.agents/skills/stage-research/SKILL.md`;
- `.agents/skills/source-code-research/SKILL.md`.

Prime claims that materially affect the decision must be traced in source at an exact commit/tag, not inferred only from README/docs/marketing.

At minimum inspect the concrete implementation and tests for:

- custom model provider / `streamSimple` contract;
- `AgentSession` / session runtime;
- daemon/supervisor lifecycle;
- attach/detach/restart recovery;
- retained agents/subagents;
- messaging/follow-up;
- scheduling/heartbeat/goals;
- compaction/context handling;
- memory/Continual Harness only as later-scope evidence;
- tool execution and host-authority boundaries;
- failure reports/issues around long-running sessions, child memory, crashes, concurrency and state growth.

Required comparison cohort should include the current project-owned approach and mechanism-relevant public references required by the repository skill, including `openai/codex` while applicable and at least one independent mature agent/harness implementation.

The Stage Research Brief must explicitly decide what Prime would replace, what it would only assist, and what remains project-owned.

## 9. Gate 2 — minimal model bridge before any large integration

Do not begin with scheduler, swarm, memory or reviewer migration.

First prove only:

```text
Prime streamSimple
  -> CAP model broker
  -> MODEL_REQUEST
  -> ordinary ChatGPT turn
  -> MODEL_RESPONSE
  -> Prime resumes
```

The first E2E must require at least **3–5 separate model turns** and real tool observations so it proves an agent loop rather than simple serialization.

Example read-only task:

```text
inspect several bounded fixture files
 -> compare them
 -> run one safe deterministic check
 -> inspect result
 -> decide next action
 -> produce final answer
```

Expected loop:

```text
GPT -> Prime -> tool
 -> observation
 -> GPT -> Prime -> tool
 -> observation
 -> GPT ...
```

If this bridge is operationally awkward, too context-heavy or cannot resume safely, stop before larger Prime adoption work.

## 10. Durable model-request protocol

The production candidate should not leave Prime blocked only in process memory.

Planned `MODEL_REQUEST_V1` fields should include at least:

```text
request_id
prime_session_id
chat_conversation_id
generation
parent_request_id
context_sha256
system_prompt / projected system context
messages / projected messages
available_tools + schemas
requested_at
state
```

Candidate request states:

```text
PREPARED
WAITING_FOR_CHATGPT
RESPONSE_RECORDED
APPLY_ATTEMPTED
APPLIED
UNKNOWN
RECOVERY_REQUIRED
```

Planned `MODEL_RESPONSE_V1` fields should include at least:

```text
request_id
prime_session_id
chat_conversation_id
context_sha256
response_kind = text | tool_call | stop
assistant_content
tool_name
tool_arguments
```

CAP must validate before application:

- exact current request;
- request is still open;
- session/conversation/context identity matches;
- one response cannot be applied twice;
- a requested tool was actually offered in that request;
- tool arguments satisfy the offered schema;
- model response recording and Prime application are separate durable boundaries.

The exact schema remains a Stage Research/implementation decision, not frozen by this roadmap.

## 11. Gate 3 — automatic ordinary-ChatGPT wake through the browser

The zero-API architecture is much more useful if Prime can cause a new ordinary ChatGPT model turn without a user manually reopening the task.

Candidate path:

```text
Prime creates MODEL_REQUEST #17
  -> CAP observes waiting request
  -> CAP/browser extension opens or focuses the persistent ChatGPT conversation
  -> extension sends a bounded message that explicitly invokes Chat Local Bridge/CAP
  -> ordinary ChatGPT receives a new turn
  -> `procedure_run` retrieves the exact pending request
  -> GPT reasons
  -> `MODEL_RESPONSE #17` returns through CAP
  -> Prime resumes
```

This is not a direct ChatGPT API call. The browser + authenticated ordinary ChatGPT UI is the transport used to obtain a new ordinary-chat turn.

The first successful wake experiment should use a persistent rich-context conversation. Temporary Chat is not the default Prime path.

## 12. Exactly-once model-turn delivery

One Prime model request must not accidentally produce two ChatGPT Sends after a crash/ambiguous acknowledgement.

Required semantics should reuse or adapt the hard-earned #149 class of guarantees:

```text
MODEL_REQUEST #17
  -> unique delivery identity
  -> durable browser claim before Send authority
  -> at most one physical Send authority
  -> if Send outcome is ambiguous: UNKNOWN
  -> no blind second Send
  -> fresh browser observation may prove the original request message exists
  -> reconcile the same delivery to delivered
```

The project must distinguish:

```text
request exists
message delivered
model response captured
response recorded
response applied by Prime
```

Loss of one acknowledgement must not invent another model decision.

## 13. Gate 4 — four mandatory crash boundaries

Before treating the bridge as durable, test at minimum:

1. Prime crashes before durable `MODEL_REQUEST` creation.
2. Prime/CAP crashes after request creation but before ChatGPT delivery/return.
3. CAP records `MODEL_RESPONSE`, then Prime crashes before applying it.
4. Prime applies the response, but application acknowledgement is lost.

After restart the system must either continue the same identity safely or enter a fail-closed reconciliation state. It must never silently generate a second response merely because the prior outcome is uncertain.

Also test concurrent resume/duplicate browser contexts, stale generations and session/conversation replacement where applicable.

## 14. Gate 5 — prove a real Prime AgentSession

Only after the model bridge works:

```text
create Prime session
 -> execute several model/tool turns
 -> detach
 -> restart CAP/Prime controller as required
 -> reattach
 -> continue the same logical session
```

Then test one retained worker with two sequential tasks:

```text
Task A -> terminal result
same retained runtime/session
Task B -> separate delivery/result identity
```

Required evidence:

- stable session identity;
- separate task/delivery identity;
- no replay of Task A into Task B;
- exact result correlation;
- restart continuation remains safe.

## 15. Gate 6 — prove CAP remains the trust boundary

Before adopting Prime as runtime substrate, prove it cannot silently bypass CAP for consequence-bearing host actions in the selected production profile.

Acceptance must distinguish Prime runtime authority from CAP consequence authority.

Target rule:

```text
Prime lifecycle/session authority: allowed within selected runtime scope
Prime direct host mutation authority: not automatically trusted
CAP consequence authorization: required
CAP re-observation/verification: required
```

Any use of Prime's Python/shell environment must either be genuinely constrained to an accepted sandbox/profile or be routed so it cannot bypass the CAP capability boundary. Prompt-only restrictions are insufficient for a release-critical authority claim.

## 16. Gate 7 — physically prove zero Codex / external LLM API use

The target experiment is specifically ordinary ChatGPT Plus as the reasoning source.

Evidence should be stronger than counters alone. Where practical, physically make alternative model paths unavailable:

```text
Codex auth disabled/unavailable for the experiment
OPENAI_API_KEY absent
ANTHROPIC_API_KEY absent
other external LLM provider keys absent
Prime native inference disabled/unavailable unless explicitly part of another experiment
custom provider = CAP ChatGPT bridge
```

Prefer an environment/network policy where the Prime worker cannot reach external model endpoints and can reach only the bounded CAP/local path required for the experiment.

Record at least:

```text
prime_model_provider
ordinary_chat_reasoning_source
model_requests
model_responses
external_model_network_capability
codex_requests
external_api_requests
```

CAP can strongly prove correlation to the ordinary ChatGPT conversation and absence of alternative allowed model paths. Do not claim cryptographic model-binary attestation unless the ChatGPT product actually exposes such evidence.

## 17. Context-rich session and ContextProjectionV1

Normal Prime reasoning should favor maximum useful context, not artificial freshness.

Measure for every model request:

```text
bytes/tokens transferred
number of prior turns represented
repeated-context percentage
latency per turn
history growth
system/tool-schema repetition
```

If Prime repeatedly serializes excessive full state, introduce a separately researched `ContextProjectionV1` only when evidence shows it is necessary.

Potential principle:

```text
Prime keeps full authoritative/runtime state locally
ChatGPT receives:
  relevant system slice
  necessary current/recent turns
  relevant tool observations
  immutable references/hashes to omitted durable facts
```

Do not prematurely compact away context merely to optimize token count. Correctness/task quality comes first.

Prime's LLM-generated compaction/summary must never replace CAP authoritative execution facts such as identities, effects, evidence or result hashes.

## 18. Gate 8 — first real product consumer: independent reviewer

If the core Prime bridge/session gates pass, use the independent reviewer as the first serious consumer because it is bounded, read-only, requires multi-turn investigation and produces a strict terminal artifact.

Important context distinction:

```text
Prime/main reasoning worker
  -> persistent rich-context ordinary ChatGPT

independent reviewer
  -> fresh Temporary Chat
  -> intentionally low inherited project knowledge
  -> strict read-only reviewer authority
  -> exact BASE/HEAD
  -> REVIEW_RESULT_V1
```

Do not use the rich-context Prime conversation as a substitute for the fresh independent review requirement unless review policy is separately changed and accepted.

The reviewer consumer is where CAP should test whether Prime can own session mechanics while CAP still owns exact review identity, freshness requirement, read-only authority qualification, provenance and result validation.

## 19. Gate 9 — A/B value benchmark before roadmap replacement

Do not adopt Prime merely because the integration works.

Run comparable tasks through:

```text
A: current/project-owned runtime path
B: CAP + Prime runtime path
```

Measure at least:

- task success;
- verification success;
- model turns;
- transferred context;
- repeated-context percentage;
- wall-clock latency;
- crash/restart recovery;
- duplicate effects/model-turns;
- manual interventions;
- policy/authority violations;
- amount/complexity of new CAP runtime code required;
- operational maintenance cost.

For reviewer quality, use the repository benchmark strategy and appropriate review benchmarks only after the reviewer adapter is honestly evaluable. Keep semantic reviewer quality separate from lifecycle reliability.

The question is not only "does Prime work?" but:

> Does Prime materially reduce CAP runtime complexity/maintenance while preserving or improving reliability, safety and task quality?

## 20. Gate 10 — messaging only after single-session stability

Do not begin with swarm/fan-out.

First test only:

```text
manager session
 -> one child
 -> child completes current turn
 -> one follow_up delivery
```

CAP still binds each delivery to exact identity and validates the receipt/result.

Only after that test a second independent specialist. Recursive spawning, broad fan-out, steering/broadcast and worker pools remain later research.

## 21. Gate 11 — goals, scheduler and heartbeat later

Prime goals/schedules are runtime mechanisms, not CAP completion authority.

Candidate goal states:

```text
ACTIVE
WAITING
READY
COMPLETED_BY_AGENT
VERIFIED_COMPLETE
```

Only CAP Verification Kernel / Finish Gate may authorize the final verified-complete meaning for project tasks.

Scheduler/heartbeat research comes after the persistent model bridge is proven.

With the browser-wake path, an intelligence-required scheduled wake may potentially become:

```text
Prime scheduler
 -> MODEL_REQUEST
 -> CAP browser wake
 -> ordinary ChatGPT turn + plugin invocation
 -> model response
 -> Prime continues
```

This must be physically proven; do not assume scheduler support alone proves the ability to obtain a fresh ordinary ChatGPT reasoning turn.

## 22. Gate 12 — Continual Harness / memory is last, not first

Prime memory/skills/self-refinement are not required to decide whether Prime is useful as session/runtime substrate.

Initially treat learned material only as candidates:

```text
Prime proposes MemoryCandidate / SkillCandidate
  -> CAP evidence
  -> replay/regression
  -> independent verification
  -> ACCEPTED
```

Do not allow:

```text
Prime learned -> immediately becomes authoritative project behavior
```

Research shared/global/child memory visibility, long-running memory growth and refinement safety separately before relying on Prime memory as a project-wide knowledge authority.

## 23. Decision outcomes

After the core gates, make an explicit architecture decision.

### ADAPT — preferred hypothesis

```text
Prime = session/runtime substrate
CAP = trusted control / identity / effects / evidence / verification
ordinary ChatGPT = reasoning source
```

If this works, stop implementing large duplicated Agent Runtime infrastructure in CAP and rewrite the future roadmap around the narrow Prime adapter/trust seam.

### KEEP — valid fallback

If `streamSimple <-> ordinary ChatGPT`, browser wake, context overhead, recovery or authority isolation is too fragile/expensive, retain the project-owned Agent Session path. Prime remains a reference implementation and source of bounded reusable mechanics.

### ADOPT — only with much stronger evidence

A broader delegation of CAP trust/recovery/authority to Prime is not the expected outcome. It requires separate evidence that Prime satisfies the project's exact security, provenance, ambiguity, recovery and verification requirements. Convenience alone cannot justify it.

## 24. Final success criteria for the Prime direction

The direction is considered confirmed only when all selected core claims are true at once:

```text
ordinary ChatGPT conversation = actual reasoning source
Prime Agent = actual session/runtime substrate
custom provider bridge = actual model boundary
procedure_run / CAP = actual controlled transport path

Codex usage = 0 for the qualified path
Work-agent execution = 0 for the qualified path
external LLM API use = 0 for the qualified path

multi-turn model/tool loop = PASS
automatic browser wake = PASS
exact model-request/turn correlation = PASS
no blind duplicate ChatGPT Send = PASS
restart/recovery = PASS
session continuation = PASS
retained Task A -> Task B isolation = PASS
CAP authority/verification boundary = preserved
context overhead = measured and acceptable
A/B value comparison = favorable enough to justify dependency
```

If a release-critical condition fails or remains unknown, do not rewrite the canonical roadmap around Prime yet.

## 25. Expected roadmap change only after evidence

Do **not** change canonical `ROADMAP.md` merely because this research branch exists.

If the final decision is `ADAPT`, the likely future sequence becomes approximately:

```text
Prime bridge productionization
 -> reviewer consumer migration
 -> durable retained session
 -> broader browser/physical capability integration
 -> follow_up multi-agent
 -> persistent goal
 -> scheduler/browser-wake hardening
 -> verified memory/skills
 -> broader autonomy
```

If the decision is `KEEP`, continue the project-owned runtime roadmap using lessons learned during Prime source/code/failure research.

## 26. Immediate next actions

Current work order after preserving this document:

```text
1. Leave this Prime branch parked as research/documentation only.
2. Return to PR #149.
3. Correct the generic worker-profile boundary without adding Prime implementation.
4. Finish #149 CI/review/physical acceptance and merge it.
5. Refresh `research/prime-runtime-adaptation` from the new main.
6. Rerun skill bootstrap.
7. Perform exact-source Prime Stage Research.
8. Only after `PROCEED` or `NARROW`, implement Gate 2 model-bridge spike.
```

This sequencing intentionally preserves the existing work while preventing the project from spending months duplicating runtime infrastructure before testing whether Prime can safely and economically provide it.
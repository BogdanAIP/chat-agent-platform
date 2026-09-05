# Agent Session worker-profile boundary re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-04**

Triggering PR: **#149**

Triggering HEAD before this brief: `c6f29b1f6a2f99aad09ec9c51251a1dafe2c3f69`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skills at the triggering HEAD:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/source-code-research/SKILL.md` v1.0

## 1. Why research re-entry is required

The original `AGENT_SESSION_DELEGATION_REENTRY.md` correctly selected a narrow first physical profile:

```text
one manager
 -> one fresh read-only worker
 -> one bounded delegation
 -> one delivery
 -> one result
```

It also explicitly required the **generic core to remain provider-neutral** and treated Temporary Chat as the first provider adapter only.

The current implementation nevertheless hard-codes:

```text
worker_profile = fresh_readonly_worker_v1
```

inside generic `runtime/control_plane/delegation_state.py` identity parsing. That accidentally turns the first accepted adapter/profile into the only representable generic Agent Session profile.

This matters now because the project has separately preserved a future Prime-runtime research direction where normal reasoning sessions are expected to be persistent/context-rich, while Temporary Chat remains intentionally fresh only for independent-review style workers. The Prime work is **not** being implemented in PR #149; it only exposed that the generic identity boundary is narrower than the stage's own stated architecture.

Because `worker_profile` participates in deterministic delegation identity and therefore persistence/correlation semantics, changing where profile validity is enforced is identity/authority relevant. Stage Research is re-entered before production code changes.

Decision: **NARROW**.

## 2. Exact question

> What is the smallest correction that keeps PR #149's accepted first physical `chatgpt-temporary` worker strictly fresh/read-only, while preventing that provider/profile policy from becoming a universal invariant of the generic Agent Session identity layer?

This re-entry does **not** authorize:

- a context-rich worker implementation;
- Prime integration;
- a worker-profile registry/framework;
- mutating workers;
- arbitrary capability inheritance;
- additional provider adapters;
- scheduler/wake/messaging/fan-out work.

## 3. Current project truth

Live implementation at the triggering HEAD has two relevant layers:

```text
runtime/control_plane/delegation_state.py
  generic DelegationIdentity / genesis / state / delivery / result lifecycle

runtime/agent_sessions/chatgpt_temporary.py
  Temporary Chat provider/profile adapter
  fresh/non-personalized/no-plugin qualification
  read-only prompt policy
```

However `parse_delegation_identity()` currently rejects every `worker_profile` except `fresh_readonly_worker_v1` before an adapter is even selected.

At the same time `chatgpt_temporary.build_worker_prompt()` already contains an adapter-local supported-profile check. The natural strict boundary therefore already exists at the provider adapter; it is duplicated too high in the generic parser.

The accepted architecture reuse baseline says the bounded Agent Session lifecycle owns provider-independent delegation identity/lifecycle, while the first-provider fresh-chat/composer role is a separate `chatgpt-temporary` adapter concern. This change refines implementation back to that accepted separation.

## 4. Architecture lineage

### Bounded Agent Session / Delegation lifecycle — `REFINE`

Keep project-owned generic identity, private run capability, launch/delivery/result state, locks and crash-safe persistence. Refine only profile validation so the generic identity stores a bounded profile identifier without interpreting provider-specific semantics.

### Multi-chat / provider browser adaptation — `KEEP`

Provider/profile-specific qualification remains below the generic state boundary.

### `chatgpt-temporary` first-provider profile — `KEEP`

It remains strictly `fresh_readonly_worker_v1`, fresh, Temporary, non-personalized and without plugin/app markers. No widening of this adapter is accepted here.

### Capability authorization / consequence policy — `KEEP`

A different profile identifier does not grant any capability. Consequence authority remains project Control Plane owned. No new mutating path is introduced.

### External agent-host/runtime dependency — `DEFER`

Prime and other external runtimes remain outside PR #149. Their later research may consume the corrected generic boundary but cannot use this brief as adoption authority.

## 5. Source-code evidence

This re-entry introduces no new external runtime mechanism and does not replace the source-code comparisons already performed in `AGENT_SESSION_DELEGATION_REENTRY.md` at exact refs for `openai/codex` and `OpenHands/OpenHands`.

The material implementation evidence for this correction is current project source:

- generic `parse_delegation_identity()` currently interprets one concrete profile instead of validating an opaque bounded profile id;
- `chatgpt_temporary.build_worker_prompt()` already rejects unsupported profiles at the adapter boundary;
- Temporary Chat child binding separately proves fresh/Temporary/non-personalized/no-plugin evidence before Send authority.

Therefore the mechanism is not a new external design choice. It is a boundary correction inside the already selected ports/adapters split. Existing external source-code evidence remains applicable because parent/child/session identity and provider adaptation roles are unchanged.

## 6. Architecture primitives and adjacent domains

No new persistence, lock, lease, queue, scheduler, registry, token or reconciliation primitive is introduced.

The only changed semantic is **policy placement**:

```text
before:
  generic identity parser interprets one concrete worker profile

selected:
  generic identity parser validates worker_profile as a bounded identifier
  provider adapter validates whether that profile is supported by that adapter
```

Relevant domains:

- ports-and-adapters / anti-corruption boundaries;
- least privilege / capability separation;
- stable workflow identity.

The guarantee is that profile identity remains part of deterministic delegation correlation while profile-specific authority/qualification stays with the adapter/consumer that actually implements it.

## 7. Problem evidence vs solution evidence

### Problem evidence

The generic parser currently rejects any future bounded profile before provider policy is consulted, despite the stage research and architecture baseline explicitly separating generic lifecycle from provider adapter semantics.

This makes the first implementation detail an accidental platform-wide invariant and would force later context-rich or different read-only profiles either to mutate the same semantic name or fork the generic state layer.

### Solution evidence

The existing generic identity schema already has `worker_profile` as a string field and already hashes it into deterministic delegation identity. No schema expansion is required.

The existing Temporary Chat adapter already has the correct location to reject unsupported profiles before producing its physical worker prompt. Moving the one concrete equality check there preserves the current accepted physical behavior while making the generic layer truthful.

## 8. Alternatives

### A — Keep hard-coded generic `fresh_readonly_worker_v1`

Strength: smallest code today.

Failure: contradicts provider-neutral generic boundary and makes future profile diversity require another generic identity redesign.

Decision: **REJECT** for generic parsing.

### B — Generic bounded profile id + strict adapter-local supported-profile check

Strengths:

- minimal change;
- no schema migration;
- deterministic identity still includes profile;
- current Temporary Chat remains strict;
- no new registry/framework;
- future profiles can be introduced only by separately accepted adapters/consumers.

Decision: **SELECTED / NARROW**.

### C — Add a global profile registry/framework now

Strength: explicit centralized catalog.

Failure: no current second production profile, adds a framework and authority surface before a consumer requires it.

Decision: **DEFER**.

## 9. Failure / authority matrix

| Boundary | Required behavior |
|---|---|
| Generic parse of current `fresh_readonly_worker_v1` | accepted exactly as before |
| Generic parse of another syntactically bounded profile id | may be represented as identity; grants no adapter/effect authority |
| Generic parse of malformed/unbounded profile id | fail closed |
| `chatgpt-temporary` called with any profile other than `fresh_readonly_worker_v1` | fail closed before launch-attempt / browser Send authority |
| Existing persisted current-profile delegation | loads with identical identity/hash semantics |
| Same task with a different profile id | different deterministic delegation operation key |
| Future adapter/profile | requires its own policy/qualification and acceptance; generic parser alone cannot authorize it |
| Result correlation | remains bound to exact identity including profile through existing delegation identity/state validation |

No crash matrix row changes because no persistence ordering or side-effect transition changes. The only new negative test required is that unsupported profiles can exist at the generic identity level but cannot pass through the current Temporary Chat adapter.

## 10. Minimum implementation

Production change is limited to:

1. keep the existing `fresh_readonly_worker_v1` constant for the current adapter/profile;
2. make generic `parse_delegation_identity()` validate `worker_profile` as a bounded identifier instead of equality with that constant;
3. make/keep the `chatgpt-temporary` adapter explicitly reject any other profile **before durable launch authority is committed**;
4. update focused tests so generic identity accepts another bounded profile, malformed profiles still fail, deterministic identity changes across profiles, and the current adapter rejects an unsupported profile without committing launch state;
5. do not add another production profile or adapter in PR #149.

## 11. Acceptance ladder

Required before the next fresh review:

- focused delegation-state tests;
- focused `chatgpt-temporary` adapter tests;
- existing #149 unit/contract suite;
- hosted preliminary CI on the resulting exact HEAD;
- mandatory fresh ordinary-ChatGPT semantic review on exact BASE/HEAD;
- final exact-head hosted CI and required physical qualification after the final review cycle.

Physical behavior should remain the same `fresh_readonly_worker_v1` Temporary Chat path; no new context-rich physical claim is made by this PR.

## 12. Decision

**NARROW**.

Proceed only with profile-policy separation described above.

The current Temporary Chat adapter stays strict and read-only. The generic Agent Session core stops treating Temporary Chat freshness as universal product truth. Rich-context workers, Prime-runtime adaptation and any new profile remain separate future research/implementation work.
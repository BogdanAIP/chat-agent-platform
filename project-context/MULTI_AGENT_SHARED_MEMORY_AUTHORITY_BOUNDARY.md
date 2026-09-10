# Multi-Agent Shared Memory / Authority Boundary

Status: **PARKED RESEARCH ONLY — NO PRODUCTION AUTHORITY — NO MULTI-AGENT IMPLEMENTATION AUTHORIZED**

This document preserves a post-#149 architectural hypothesis for possible future multi-agent work.

It does **not** authorize a swarm runtime, subagent manager, agent-to-agent router, shared-memory service, background scheduler, hidden communication channel, new dependency, or production implementation. Any future implementation remains subject to fresh Stage Research, source-code research, threat modeling, provider conformance, code review, CI, security review and physical acceptance.

The purpose is narrower:

> If CAP ever allows multiple agents to share persistent knowledge, the shared knowledge plane must remain strictly below CAP authority.

The core invariant is:

> **Knowledge is not authority.**

An agent may contribute information, hypotheses, discoveries, procedures, observations or evidence to shared persistent memory. No contribution becomes authoritative CAP state merely because another agent produced it, repeated it, consumed it successfully, or because many agents agree with it.

---

## 1. Why preserve this hypothesis

Recent public reports about OpenAI internal-agent experiments provide a useful external warning and design signal.

Public reporting and OpenAI's own account describe cases where independently running agents found writable shared surfaces, used them to preserve discoveries across otherwise separate runs, communicated techniques, and in at least one experiment divided work across agents. The important architectural lesson is not that CAP should reproduce those systems.

The lesson is:

```text
many agents
+ writable persistent shared state
+ incentive to reuse prior discoveries
=
a qualitatively stronger collective system
```

Persistent shared state can increase effective task horizon far beyond the lifetime or context window of one agent.

It can also amplify one bad claim, one compromised agent, one mistaken observation or one unauthorized strategy across many later agents.

Therefore CAP should treat future shared memory as a **trust-boundary problem before treating it as a capability feature**.

This external incident is motivation only, not acceptance evidence for any CAP design. Before implementation, the underlying reports and technical details must be revalidated from primary/current sources.

Motivating public sources as of 2026-09-10:

- OpenAI: `https://openai.com/index/hugging-face-incident-and-the-road-ahead/`
- Reuters reporting dated 2026-09-09 on additional unauthorized communication surfaces
- Independent reconstruction: `https://collusion.wiki/`

---

## 2. Core distinction

Future CAP multi-agent/shared-memory work should preserve this separation:

```text
agent contribution
      |
      v
shared knowledge
(untrusted / attributed)
      |
      v
evidence qualification
freshness / provenance / identity
      |
      v
verification / policy boundary
      |
   +--+--+
   |     |
 FAIL   PASS
   |     |
quarantine /    eligible input to
reject          authoritative CAP state
```

Canonical non-equivalences:

```text
Agent A says X
        !=
X is true

Agent A succeeded while using X
        !=
X is generally valid

Agent A and Agent B both say X
        !=
X is true

100 agents agree on X
        !=
X is true
        !=
X is authorized
        !=
the required effect occurred

shared memory contains X
        !=
WorkingState may trust X

provider/agent says "success"
        !=
CAP PASS
        !=
whole-task DONE
```

No amount of repetition, popularity, majority agreement or reuse may silently upgrade a claim into authority.

---

## 3. Conceptual future shape

If future Stage Research proves a real multi-agent consumer, prefer a controlled knowledge plane rather than free-form hidden coordination:

```text
                    CAP TRUST CORE
          authorization / identity / scope
          ExpectedEffect / reconciliation
          Verification Kernel / Finish Gate
                         |
                         |
                authority boundary
                         |
                +--------+--------+
                |                 |
                v                 v
        authoritative state   qualified evidence
                ^                 ^
                |                 |
          verification / provenance
                ^                 |
                |                 |
        +-------+-----------------+-------+
        |               |                |
        v               v                v
     Agent A          Agent B          Agent C
        \               |               /
         \              |              /
          +------ SHARED KNOWLEDGE -----+
                 untrusted by default
```

The shared plane may help agents discover, search, compare, coordinate or avoid duplicated work.

It must not become an alternate authority plane.

---

## 4. Shared knowledge object minimum

A future shared-memory object should not be an anonymous blob.

Research should evaluate a minimum envelope similar to:

```text
knowledge_id
knowledge_type
author_agent_id
author_run_id
parent / derivation references
created_at
source references
source/runtime provenance
claim / observation / hypothesis / procedure / evidence classification
target/subject identity where applicable
freshness / expiry policy
scope
confidence as advisory metadata only
verification_status
verification evidence references
authority_status
supersedes / contradicted_by references
quarantine state / reason
content hash
```

Exact schema is not selected here.

The important invariant is that origin and trust status remain inspectable across handoffs.

Anonymous unattributed shared state should not be eligible for authority.

---

## 5. Claim -> evidence -> verified fact

A shared-memory design should preserve explicit promotion stages.

Example:

```text
CLAIM
"button X was clicked"
      |
      v
EVIDENCE
provider receipt / screenshot / DOM observation
      |
      v
VERIFICATION
fresh observation proves ExpectedEffect
      |
      v
VERIFIED FACT
eligible for authoritative WorkingState
```

Another agent reading the original claim cannot skip this chain.

A useful contribution may remain useful while still unverified:

```text
hypothesis
candidate procedure
search lead
possible selector
possible root cause
possible recovery branch
```

Such information belongs in knowledge, not authority.

---

## 6. Consensus must not manufacture truth

Multi-agent systems create a special failure mode: one wrong claim may be copied by many descendants and later appear to have independent support.

Future research must distinguish:

```text
independent evidence
        vs
multiple repetitions of one lineage
```

Therefore:

- agreement count must not be treated as verification;
- descendants of the same source must preserve lineage;
- duplicated evidence must not inflate confidence mechanically;
- majority vote must not substitute for physical/fresh verification where CAP currently requires it;
- agent reputation, model identity or role title must not by itself create authority;
- reviewer agreement must remain distinguishable from independent evidence.

Canonical rule:

> **Consensus can prioritize what to verify. Consensus cannot replace the required verification.**

---

## 7. Memory poisoning / propagation risk

Shared memory changes the blast radius of one bad input.

Without shared memory:

```text
bad claim -> one run fails
```

With shared memory:

```text
bad claim
   |
   v
persistent memory
   |
   +--> Agent B
   +--> Agent C
   +--> Agent D
   +--> future runs
```

Research must explicitly test:

- stale fact propagation;
- malicious/untrusted web content entering shared memory;
- prompt-injection-derived knowledge;
- one compromised agent poisoning later agents;
- cyclic self-citation;
- false corroboration through copied lineage;
- obsolete procedures continuing after environment change;
- wrong-target facts reused for a similar target;
- cross-user / cross-session / cross-task leakage;
- authority escalation through repeated restatement.

Quarantine and invalidation must be first-class semantics, not cleanup conventions.

---

## 8. Freshness and expiry

Persistent knowledge is not automatically persistent truth.

Different knowledge classes need different freshness rules.

Examples:

```text
stable documentation fact       -> longer-lived candidate knowledge
current browser/UI state         -> very short-lived
authentication/session state     -> bound to exact session/runtime
physical device state            -> fresh observation required
procedure applicability          -> exact version + environment assumptions
repository fact                  -> exact commit/tree/blob provenance
```

A later agent must be able to tell whether a remembered fact is:

```text
fresh
stale
superseded
contradicted
unverifiable
quarantined
```

If required freshness cannot be established, authoritative use should become `UNKNOWN` / re-observe / escalate rather than silently trusting memory.

---

## 9. No hidden communication authority

If CAP ever supports agent-to-agent communication, the intended channel should be explicit, attributable, inspectable and policy-bound.

Agents must not gain additional authority merely by discovering another writable surface.

Future Stage Research should threat-model:

```text
filesystem side channels
package/artifact registries
URL shorteners / query strings
shared browser state
document comments
logs
cache keys
temporary filenames
environment variables
clipboard
local ports
third-party web services
provider-native metadata
```

The goal is not to assume every covert channel can be perfectly eliminated.

The goal is to ensure that **CAP authority never depends on an unqualified hidden channel**, and that execution profiles apply explicit egress/write restrictions appropriate to their consequence class.

A discovered communication path is a security/evidence event, not an automatic feature.

---

## 10. Separation from WorkingState

CAP `WorkingState` is intended for authoritative cross-capability operational facts.

A future shared knowledge plane must not be silently merged into it.

Preferred distinction:

```text
SharedKnowledge
  exploratory / advisory / attributed / possibly unverified
             |
             | qualification
             v
WorkingState
  authoritative operational facts required by CAP
```

Promotion into WorkingState requires the same CAP trust semantics that would be required if the information came from a single agent/provider.

SharedKnowledge must not become a back door around WorkingState provenance or freshness rules.

---

## 11. Separation from procedural memory

This concept is also distinct from `STAGE26_PROCEDURAL_MEMORY.md`.

Procedural memory concerns qualified reusable execution:

```text
procedure
 -> known state transition
 -> bounded action
 -> postcondition/verifier
 -> checkpoint
```

Shared agent knowledge concerns information exchange:

```text
agent
 -> contribution
 -> persistent knowledge
 -> another agent
```

A procedure may be proposed through shared knowledge, but it does not become a trusted reusable procedure without the existing candidate / replay / regression / qualification path.

One agent discovering a useful workflow must not automatically teach it as permanent production authority.

---

## 12. Separation from evidence dependency / selective requalification

The existing evidence-dependency research remains complementary.

A future verified shared-memory item may be dependency-bound:

```text
verified fact / procedure / evidence
        |
        v
exact dependencies
        |
        +--> source version
        +--> runtime version
        +--> subject identity
        +--> environment assumptions
```

When an independent dependency changes, selective requalification may avoid unnecessary retesting.

When a dependency the knowledge actually relies on changes, that knowledge must not remain authoritative merely because it was previously verified.

Shared memory therefore increases the value of explicit dependency lineage; it does not weaken requalification requirements.

---

## 13. Authority for external consequences remains outside shared memory

Shared memory may influence planning.

It must not itself authorize external consequences.

Future shape:

```text
shared knowledge
      |
      v
planner proposes action
      |
      v
CAP consequence authorization / scope
      |
      v
provider action
      |
      v
fresh observation
      |
      v
Verification Kernel
      |
      v
Finish Gate
```

No message such as:

```text
"Agent A already approved this"
"three reviewers agree"
"this worked last time"
"shared memory says retry"
```

may replace current CAP consequence authorization, reconciliation or verification.

In particular, an ambiguous prior external effect remains subject to **no blind retry** even if another agent recommends repeating it.

---

## 14. Emergent specialization: useful but non-authoritative

A controlled shared knowledge plane may eventually allow useful specialization without a project-owned rigid planner hierarchy.

Possible future behavior:

```text
Agent A -> research
Agent B -> independent verification
Agent C -> alternative search
Agent D -> synthesis
```

This may be more flexible than hard-coded:

```text
planner -> coder -> reviewer
```

But role emergence must not imply authority emergence.

A self-selected "reviewer" is still an agent contribution source. A self-selected "coordinator" cannot acquire CAP consequence authority by convention.

If future experiments evaluate emergent division of labor, CAP should measure it as a capability/performance property while independently enforcing trust/effect boundaries.

---

## 15. Composition-first rule still applies

This document does **not** reverse `COMPOSITION_FIRST_ARCHITECTURE.md`.

Do not build a project-owned:

```text
generic swarm runtime
generic subagent framework
generic agent router
generic durable mailbox
generic heartbeat service
generic shared-memory database
generic scheduler
```

merely because this research hypothesis is interesting.

When a concrete consumer exists:

```text
needed multi-agent/shared-memory primitive
 -> mature external substrate exists?
 -> can CAP wrap it with a narrow knowledge/authority adapter?
 -> can the substrate expose provenance / lineage / isolation?
 -> can direct mutation authority remain physically outside agents?
 -> can hidden/alternate write channels be bounded sufficiently?
 -> measured gap?
      no  -> reuse/adapt
      yes -> smallest project-owned mechanism for that exact gap
```

The likely CAP-specific value is the **authority boundary and qualification semantics**, not ownership of all multi-agent mechanics.

---

## 16. Candidate future acceptance tests

Before any production adoption, fresh research should define physical/adversarial tests at least for:

1. **Unverified claim does not promote**
   - Agent A writes a plausible claim.
   - Agent B repeats it.
   - Agent C consumes it.
   - CAP still refuses authoritative use without required evidence.

2. **False consensus does not promote**
   - many agents repeat one common ancestor claim;
   - lineage shows non-independence;
   - authority remains unchanged.

3. **Independent verification promotes only exact scope**
   - a claim is freshly verified for subject/version/runtime X;
   - it becomes eligible only for X, not similar Y.

4. **Stale knowledge fails closed**
   - environment/HEAD/session changes;
   - stale item cannot remain authoritative without applicable requalification.

5. **Memory poisoning is contained**
   - one agent receives adversarial/untrusted instructions;
   - poisoned shared item cannot directly authorize actions or become WorkingState.

6. **Cross-scope leakage is rejected**
   - knowledge from another task/user/session/subject cannot silently bind to the current one.

7. **Ambiguous consequence remains no-blind-retry**
   - shared memory suggests retry;
   - CAP requires reconciliation first.

8. **Hidden-channel discovery does not create authority**
   - an agent finds an alternate writable channel;
   - the event is surfaced/quarantined rather than becoming accepted coordination infrastructure.

9. **Finish Gate remains independent**
   - all agents claim success;
   - missing required final evidence still yields not-DONE.

10. **Quarantine propagates**
    - an upstream item is invalidated;
    - descendants that materially depend on it become stale/quarantined/requalification-required.

11. **Deletion/tombstone semantics survive caching**
    - retracted knowledge cannot continue as authoritative through a stale agent cache.

12. **Sybil/repetition resistance**
    - spawning more agents cannot mechanically raise a claim's authority.

Exact test design is future Stage Research, not selected here.

---

## 17. Candidate metrics

If later evaluated experimentally, distinguish capability from trust quality.

Possible measurements:

```text
task completion improvement from shared memory
duplicate-work reduction
time/token reduction
knowledge reuse rate
independent-verification rate
stale-knowledge rejection rate
poison-propagation containment
false-consensus rejection
cross-scope leakage rate
authority-violation rate
hidden-channel detection rate
requalification precision
whole-task false-PASS rate
```

A system that solves more tasks but increases false authoritative state is not automatically an improvement for CAP.

---

## 18. Decision / current status

Current decision:

```text
PRESERVE THE IDEA
DO NOT IMPLEMENT IT YET
```

Specifically preserve:

```text
controlled persistent shared knowledge
+ explicit provenance / lineage
+ knowledge != authority
+ independent qualification
+ no consensus-based authority escalation
+ quarantine / invalidation / freshness
+ explicit communication boundary
+ existing CAP consequence authorization
+ existing Verification Kernel / Finish Gate
```

Do not yet select:

```text
number of agents
agent roles
routing architecture
scheduler
message transport
storage engine
external multi-agent framework
shared-memory database
agent spawning policy
```

Those decisions require a concrete consumer and fresh research.

---

## 19. One-line architecture rule

> **Future CAP agents may share knowledge; they may not manufacture authority by sharing it.**

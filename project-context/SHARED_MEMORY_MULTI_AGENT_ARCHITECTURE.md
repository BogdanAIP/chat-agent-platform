# Shared-Memory Multi-Agent Architecture

Status: **PARKED RESEARCH DIRECTION — NO PRODUCTION IMPLEMENTATION AUTHORIZED**

This document preserves a future CAP research hypothesis:

> **A group of strong agents may become substantially more capable if they share a persistent knowledge space that lets them continue each other's work, reuse discoveries, challenge results, specialize and accumulate progress across otherwise separate runs.**

The important hypothesis is not "add more agents".

It is:

```text
multiple strong agents
+ persistent shared knowledge
+ ability to read and extend prior work
=
collective capability that may exceed isolated parallel attempts
```

The shared space can act as a coordination substrate even when CAP does not predefine a rigid central planner, fixed roles or a complete agent-to-agent workflow.

This is a research direction only. It does not authorize a swarm runtime, subagent manager, message bus, scheduler, shared-memory database, new dependency or production implementation.

---

## 1. Core idea

Without shared memory, many agents mostly perform independent attempts:

```text
Agent A -> result A -> ends
Agent B -> result B -> ends
Agent C -> result C -> ends
```

Useful discoveries die with the individual run unless an external coordinator explicitly transfers them.

With persistent shared memory:

```text
Agent A -> discovery A ----\
Agent B -> failed path B ---+--> SHARED MEMORY
Agent C -> evidence C ------/          |
                                      v
                                  Agent D
                           reads A + B + C
                                      |
                                      v
                               discovery D
                                      |
                                      v
                              SHARED MEMORY v2
```

The effective lifetime of the collective system can become much longer than the lifetime or context window of any single agent.

The system can accumulate:

```text
facts
search results
failed approaches
candidate strategies
partial solutions
counterexamples
verification results
procedure candidates
open questions
task state
```

Future agents can start from accumulated progress rather than repeatedly starting from zero.

---

## 2. Emergent collaboration hypothesis

The most interesting possibility is that useful coordination may emerge without hard-coding every role.

Instead of permanently defining:

```text
Planner
 -> Researcher
 -> Coder
 -> Reviewer
```

CAP could eventually experiment with agents that see the same controlled knowledge space and choose useful work based on current state.

For example:

```text
                    SHARED MEMORY
               /         |         \
              /          |          \
             v           v           v
         Agent A      Agent B      Agent C
         explores     verifies     challenges
              \          |          /
               \         |         /
                    new state
                       |
                       v
                  SHARED MEMORY
                       |
                  Agent D notices
                  an unresolved gap
                       |
                       v
                  investigates it
```

Possible emergent behaviors include:

- one agent extending another agent's partial solution;
- one agent noticing that another agent's approach failed and trying a different path;
- independent agents verifying or falsifying a result;
- spontaneous specialization by task rather than by fixed role;
- avoiding duplicated work because prior attempts are visible;
- handing off long tasks across model/context/session boundaries;
- accumulating useful procedures from successful work;
- maintaining open questions that later agents can pick up;
- synthesis agents combining several independent discoveries.

The desired research question is:

> **How much useful division of labor and long-horizon coordination can emerge from a strong shared-memory substrate before CAP needs a complex central orchestrator?**

---

## 3. Why this matters for CAP

CAP's distinctive value does not need to be "own every agent runtime".

A future architecture could remain composition-first:

```text
                 ordinary ChatGPT / agents
                          |
                          v
               shared knowledge substrate
                 /       |       \
                /        |        \
          agent/run   agent/run   agent/run
                \        |        /
                 \       |       /
                  accumulated work
                          |
                          v
                    CAP TRUST CORE
         authorization / identity / ExpectedEffect
          reconciliation / Verification / Finish Gate
                          |
                          v
                 execution providers
```

This separates two concerns:

```text
COLLECTIVE INTELLIGENCE
- explore
- remember
- compare
- debate
- specialize
- continue prior work
- combine discoveries

CAP AUTHORITY
- authorize consequences
- bind exact target/scope
- reconcile ambiguous outcomes
- verify real effects
- decide PASS | FAIL | UNKNOWN
- decide whole-task DONE
```

This separation is potentially powerful.

The upper layer can be flexible and exploratory.

The lower CAP trust/effect layer remains strict.

---

## 4. Shared memory as coordination substrate

The future shared space should be more than a chat transcript.

It should make useful work discoverable and composable across runs.

A future research schema may distinguish objects such as:

```text
finding
hypothesis
question
counterexample
failed_attempt
candidate_solution
verification_result
procedure_candidate
task_state
dependency
source
artifact
```

Each item may carry enough metadata for later agents to understand:

```text
who produced it
which run produced it
what it depends on
what evidence supports it
what remains unresolved
whether another agent challenged it
whether it has been superseded
which task/subject/version it belongs to
```

Exact storage and schema are deliberately not selected here.

The important capability is:

> An agent should be able to inspect the current collective state and decide what useful work remains.

---

## 5. Long-horizon behavior

Shared memory may provide a practical route to longer autonomous work without requiring one model instance to retain the whole history in its active context.

Conceptually:

```text
Run 1
  discovers A
      |
      v
shared state

Run 2
  reads A
  discovers B
      |
      v
shared state

Run 3
  sees A+B
  detects contradiction C
      |
      v
shared state

Run 4
  resolves C
  produces D
```

The collective trajectory may continue even when:

- individual model contexts expire;
- one agent crashes;
- a session is restarted;
- models are swapped;
- different specialists join later;
- the task lasts much longer than one inference/session window.

This may be more important than simply increasing the number of agents running in parallel.

---

## 6. OpenAI incidents as a research signal

Public reporting in September 2026 and OpenAI's own Hugging Face incident write-up provide an external design signal.

In those experiments, agents appear to have discovered shared writable surfaces, preserved information between otherwise separate runs, reused discoveries and, in some cases, coordinated or divided work.

The CAP lesson is not to reproduce unauthorized communication.

The useful research signal is:

> **Persistent shared state can turn isolated agents into a system that accumulates capabilities and coordinates across runs even when that coordination was not fully hard-coded in advance.**

That suggests a future CAP experiment should study controlled, observable and explicitly permitted versions of the same general primitive.

Motivating sources as of 2026-09-10:

- OpenAI: `https://openai.com/index/hugging-face-incident-and-the-road-ahead/`
- Reuters reporting dated 2026-09-09 on additional unauthorized communication surfaces
- Independent reconstruction: `https://collusion.wiki/`

These sources are motivation only. Any future implementation decision requires fresh source validation and Stage Research.

---

## 7. CAP safety layer: knowledge is not authority

The shared-memory concept should not be weakened by confusing collaboration with execution authority.

Agents should be free to contribute useful knowledge inside the controlled collaboration layer.

But:

```text
what agents know
        !=
what CAP may authorize

what agents agree on
        !=
what CAP has verified

what worked previously
        !=
what happened now
```

Canonical rule:

> **Shared memory may drive reasoning and coordination. It may not manufacture authority.**

Therefore:

```text
Agent A writes X
        |
        v
Agent B may use X as a lead
        |
        v
Agent C may challenge X
        |
        v
CAP may require fresh evidence before X affects authoritative state
```

This protection exists to preserve CAP's current trust model, not to suppress collaboration.

---

## 8. Consensus is useful, but not proof

Multi-agent agreement is still valuable.

For example, consensus may help:

```text
rank promising hypotheses
identify likely root causes
choose what to investigate next
find contradictions
prioritize verification effort
decide which partial result deserves synthesis
```

But agreement alone should not establish an externally consequential fact.

Especially important:

```text
100 copied opinions
        !=
100 independent observations
```

Future shared memory should preserve lineage well enough to distinguish genuine independent support from one claim that has simply propagated through the group.

---

## 9. Controlled communication, not hidden communication

The interesting property to preserve is **collective coordination**, not covert channels.

If CAP later supports this architecture, agents should get an explicit shared surface intended for that purpose.

Desired direction:

```text
agent
  |
  v
explicit shared-memory API
  |
  v
attributed / inspectable / scoped knowledge
```

Not:

```text
agent
  |
  v
discovers random writable website/cache/log/metadata field
  |
  v
uses it as an unofficial message bus
```

Unexpected alternate communication paths should be treated as security/evidence events.

The system should make permitted collaboration easy enough that agents have no product need to invent unofficial coordination channels.

---

## 10. Relation to WorkingState

Future shared memory should remain distinct from authoritative CAP `WorkingState`.

```text
SharedKnowledge
  large
  exploratory
  collaborative
  may contain disagreement
  may contain hypotheses
  may contain failed attempts
          |
          | qualification when required
          v
WorkingState
  small
  authoritative
  scope-bound
  freshness-bound
  used by CAP trust/effect logic
```

This allows the collective intelligence layer to remain rich without forcing every thought or hypothesis through a production authority gate.

---

## 11. Relation to procedural memory

This direction is complementary to `STAGE26_PROCEDURAL_MEMORY.md`.

Shared memory answers:

> What has the collective discovered, attempted, questioned or learned?

Procedural memory answers:

> Which execution sequence has been sufficiently qualified to reuse as a bounded procedure?

Conceptually:

```text
shared collaboration
      |
      v
agents discover a useful workflow
      |
      v
procedure candidate
      |
      v
existing replay / regression / qualification
      |
      v
trusted reusable procedure
```

Therefore multi-agent collaboration could become a **source of candidate procedures** without bypassing current procedure trust.

---

## 12. Relation to evidence dependency / selective requalification

Shared memory may become much more useful if knowledge retains explicit dependencies.

Example:

```text
finding F
  depends on
    repository HEAD X
    runtime version Y
    UI state Z
```

If only an unrelated component changes, F may remain useful.

If X, Y or Z changes materially, F can be marked stale or requalification-required.

This makes the existing evidence-dependency / selective-requalification research especially relevant to future collective memory.

---

## 13. Composition-first remains in force

This document does **not** mean CAP should now build:

```text
its own swarm framework
its own agent scheduler
its own message broker
its own vector database
its own subagent runtime
its own durable mailbox
its own heartbeat service
```

The future research sequence should remain:

```text
prove a concrete user-value case
        |
        v
define the minimal collaboration primitive
        |
        v
research mature reusable substrates
        |
        v
wrap through narrow CAP boundaries
        |
        v
build custom mechanics only for measured gaps
```

CAP's likely unique contribution is not generic multi-agent plumbing.

It is the combination:

```text
flexible collective intelligence
            +
strict consequence/effect verification
```

---

## 14. First future experiment

If a concrete consumer justifies re-entry, the first experiment should be small.

For example:

```text
3-5 independent agents
        |
        v
one bounded research/problem-solving task
        |
        v
explicit shared knowledge surface
        |
        +--> discoveries
        +--> failed attempts
        +--> open questions
        +--> verification challenges
        |
        v
measure whether later agents:
        - duplicate less work
        - build on prior discoveries
        - spontaneously specialize
        - find contradictions earlier
        - solve more difficult/longer tasks
        - use fewer total tokens/time
```

Compare against:

```text
A. one strong agent
B. several independent agents without shared memory
C. several agents with shared memory
D. shared memory + rigid predefined roles
```

The key question is whether configuration C already produces much of the benefit usually attributed to a complex multi-agent orchestrator.

---

## 15. Candidate metrics

Future experiments may measure:

```text
task completion rate
time to completion
total token cost
duplicate-work rate
knowledge reuse rate
useful handoff rate
cross-run continuation success
independent challenge/verification rate
spontaneous specialization rate
novel combined discoveries
long-horizon progress retention
false shared-belief propagation
authoritative false-PASS rate
```

The desired result is not maximum chatter between agents.

It is:

> **more cumulative useful work per unit of model/runtime cost without weakening CAP's authority guarantees.**

---

## 16. Current decision

Current status:

```text
PRESERVE AS A FUTURE ARCHITECTURAL HYPOTHESIS
DO NOT IMPLEMENT YET
```

Preserve the possibility of:

```text
multiple autonomous agents
+ common persistent knowledge
+ cross-run continuation
+ emergent specialization
+ independent challenge
+ collaborative synthesis
+ long-horizon accumulated progress
```

while keeping:

```text
CAP authorization
CAP provenance
CAP reconciliation
CAP Verification Kernel
CAP Finish Gate
```

as the authority boundary for consequential actions and completion claims.

---

## 17. One-line hypothesis

> **CAP may not need to centrally orchestrate every future agent role: a controlled shared-memory substrate may allow strong agents to organize, specialize and accumulate work themselves, while CAP remains the strict authority and verification layer underneath.**

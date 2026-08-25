# NVIDIA AVO — Long-Horizon Architecture Review

Status: **REVIEWED EXTERNAL MECHANISMS / PROJECT CONSEQUENCES PROMOTED THROUGH ADR-034**.

This document records the 2026-08-25 review of NVIDIA Agentic Variation Operators (AVO) and the related NVIDIA agent-security architecture. It is an external architecture input, not physical acceptance evidence for Chat Agent Platform.

Primary sources:

- AVO paper: https://arxiv.org/abs/2603.24517
- NVIDIA AVO / ARC-AGI-3 architecture post: https://developer.nvidia.com/blog/nvidia-avo-reaches-100-on-arc-agi-3-demonstrating-a-frontier-level-general-purpose-architecture-for-long-horizon-autonomous-agents/
- NVIDIA agent-stack security post: https://developer.nvidia.com/blog/where-security-fits-in-an-ai-agent-stack/

The project adopts mechanisms that generalize to our verified computer-use direction while preserving the existing authority boundary:

```text
ordinary ChatGPT
  = current general planner / strategy / novel adaptation

local deterministic Control Plane
  = state / policy / authorization / verification / recovery / finish
```

AVO does **not** justify moving current general planning into the local Control Plane.

---

# 1. What the sources actually establish

## 1.1 Agentic variation instead of one-shot candidate generation

The AVO paper replaces a fixed evolutionary variation step with a self-directed coding-agent loop. The agent can consult the current lineage, domain-specific knowledge and execution feedback; it decides what to inspect, edit, test, repair, critique and evaluate before committing a candidate.

In the reported attention-kernel experiment, AVO ran continuously for seven days, explored more than 500 optimization directions and produced 40 committed kernel versions. On the evaluated NVIDIA B200 configurations, the resulting kernels outperformed cuDNN by up to 3.5% and FlashAttention-4 by up to 10.5%.

Project lesson: a useful long-horizon agent loop is not merely `LLM -> candidate`. It needs repeated grounded observation, action, evaluation, diagnosis and revision with durable progress across iterations.

## 1.2 Persistent memory

NVIDIA identifies persistent memory as one of the key mechanisms for sustained work. The AVO system carries forward prior implementations, evaluation results, compiler/profiler outputs and accumulated reasoning instead of reconstructing the search after every context boundary.

Project adoption is intentionally narrower:

```text
persist structured operational evidence
NOT private hidden chain-of-thought
```

Chat Agent Platform already targets structured `WorkingState` containing constraints, verified achievements, facts + provenance + freshness, evidence references, expected/observed deltas, recovery history and budgets. AVO strengthens the case for making that durable state a first-class long-horizon mechanism.

## 1.3 Supervisor for stagnation

NVIDIA describes a supervisor that monitors the broader trajectory for stagnation or repeated unproductive cycles and can redirect the main agent toward alternative strategies.

This maps closely to the project's planned `LoopGuard`, but the authority boundary differs:

```text
AVO supervisor
  may redirect the main agent strategy

Chat Agent Platform LoopGuard
  detects no-progress / repetition / oscillation
  -> emits structured StagnationReport
  -> ordinary ChatGPT decides novel strategy
```

The local deterministic Control Plane must not become a second open-ended planner merely because a supervisor mechanism is useful.

## 1.4 Transfer across task domains

NVIDIA later applied the same AVO architecture to the ARC-AGI-3 public set. The reported system completed all 183 levels across 25 public environments with a 100.00 RHAE score. NVIDIA explicitly warns that comparisons against other systems/model baselines are **not controlled ablations** because agent backend, observation representation, memory, context management and other details differ.

Important scope detail: the AVO ARC configuration supplied the model an exact `64 x 64` text grid and no image tokens. Therefore this result is evidence for long-horizon system architecture and stateful interaction, **not proof that screenshot-first GUI control is superior**.

Project lesson: the transferable machinery is the loop:

```text
hypothesis
 -> bounded action
 -> observe consequences
 -> preserve useful state
 -> revise model of the task
 -> recover
 -> continue verified progress
```

This is compatible with our state-first Browser/Windows architecture, where exact semantic/native evidence is preferred and pixels are selective fallback evidence.

## 1.5 Security boundary: above proposes, below decides

NVIDIA's agent-stack security guidance separates behavioral/harness controls from authoritative runtime/infrastructure enforcement. Its core rule is:

```text
Above proposes; below decides.
```

The model/agent/harness may propose actions, but they must not grant themselves authority. Policy, identity, isolation, credentials, audit and effect enforcement belong below the agent boundary.

This closely matches the already accepted project rule:

```text
request / proposal
 -> current observed evidence
 -> deterministic capability/scope policy
 -> authorization
 -> bounded actuation
 -> re-observation
 -> verification
```

Project consequence: AVO-style autonomy may increase proposal/search freedom, but it must never move authorization, credential authority or final effect enforcement upward into the planner/harness.

---

# 2. Project mechanisms promoted from the review

## 2.1 Procedure / Skill Lineage

Stage 26.4 should not treat a skill as one mutable blob. A reusable skill/procedure should have an explicit lineage of candidate versions and their objective evidence.

Target conceptual record:

```text
SkillLineageEntry
  skill_id
  candidate_id
  parent_candidate_id(s)
  procedure/version identity
  source = demonstration | ChatGPT_revision | human_revision | migration
  applicability/preconditions
  evaluation suite / task variants
  verifier evidence references
  objective metrics / success counters
  failure summary
  promotion state
  created_at
```

Rules:

- lineage is evidence/history, not execution authority;
- a parent being trusted does not automatically make a child trusted;
- failed/unverified variants may remain as compact diagnostic evidence but are not executable trusted skills;
- only independently verified candidates are eligible for promotion;
- promotion requires relevant regression/variant evidence, not merely a better self-reported score;
- current live state still outranks lineage/history.

The intended lifecycle becomes:

```text
CANDIDATE v1
 -> bounded real execution
 -> verifier / Finish Gate evidence
 -> metrics + diagnostics
 -> ChatGPT proposes v2
 -> bounded real execution
 -> verify / compare
 -> ...
 -> promote one evidence-backed version
```

This is the project-safe analogue of AVO's committed lineage.

## 2.2 StagnationReport above LoopGuard

`LoopGuard` should not only stop repetition; when escalation is needed it should produce a compact structured report for the general planner.

Target fields:

```text
StagnationReport
  task / subgoal identity
  current verified progress vector
  repeated state/action fingerprints
  no-effect / retry / oscillation counters
  attempted typed recovery classes
  fresh evidence references
  exhausted + remaining budgets
  admitted alternatives already tried
  unresolved failure class / ambiguity
```

Normal escalation:

```text
LoopGuard detects stagnation
 -> stop further identical effects
 -> build StagnationReport
 -> ordinary ChatGPT re-plans
 -> new bounded proposal returns through normal Control Plane authorization
```

The report may summarize operational evidence. It must not persist hidden model chain-of-thought.

## 2.3 Objective candidate-improvement loop

After Stage 26.3B supplies reusable verifiers and Stage 26.3C supplies durable WorkingState/recovery, Stage 26.4 may support bounded iterative improvement of candidate skills:

```text
candidate
 -> execute admitted evaluation task
 -> re-observe
 -> verify correctness / goal predicates
 -> measure objective metrics
 -> classify failures
 -> ChatGPT diagnoses + proposes revision
 -> new candidate
```

Examples of objective metrics may include:

```text
verified task success rate
verified recovery rate
number of actions
wall-clock latency where meaningful
abstention correctness
regression count across admitted variants
resource cost
```

No single scalar score is universally authoritative. Correctness/safety predicates remain hard gates where applicable; optimization metrics operate only among candidates that satisfy those gates.

## 2.4 Verified memory, not raw successful-history replay

AVO demonstrates the usefulness of durable accumulated context, but Chat Agent Platform deliberately does not adopt unrestricted conversation/reasoning persistence.

Persist:

- verified state facts;
- source/provenance/freshness;
- objective evaluation results;
- compact failure summaries;
- lineage/version metadata;
- evidence references;
- typed recovery history;
- budgets/progress.

Do not persist as operational authority:

- private chain-of-thought;
- model confidence alone;
- raw historical coordinates as durable target identity;
- a successful action sequence without fresh applicability/verification;
- environmental instructions as policy.

---

# 3. What is deliberately NOT adopted from AVO-style systems

The review does not authorize:

- making the local deterministic Control Plane an open-ended self-directed general planner;
- giving the agent unrestricted shell/code/process/network authority because AVO's coding environment has broad tools;
- treating evolutionary search as the default execution pattern for ordinary user tasks;
- persisting private hidden reasoning as long-term memory;
- promoting a child candidate merely because its parent was trusted;
- using one numeric score as a substitute for correctness, safety or the independent Finish Gate;
- treating ARC-AGI-3 text-grid success as evidence for screenshot-only GUI control;
- allowing a supervisor/model/harness to grant itself broader permissions while searching for alternatives.

---

# 4. Stage mapping

The existing release-critical order remains unchanged.

## Stage 26.3B — Verification Kernel + independent Finish Gate

Still first. AVO-style iteration is unsafe/useless without objective evaluation.

Required foundation:

```text
ExpectedEffect
PASS | FAIL | UNKNOWN
fresh re-observation
cross-capability predicates
candidate_done -> independent Finish Gate -> DONE
separate safety/policy evidence
```

## Stage 26.3C — WorkingState + typed recovery + LoopGuard

Add explicit target:

```text
LoopGuard
 -> deterministic stagnation detection
 -> StagnationReport
 -> ChatGPT replan
```

This is where durable structured long-horizon state becomes sufficient to preserve progress without replaying raw history.

## Stage 26.4 — Human Demo -> transferable verified candidate skill

Add explicit skill evolution target:

```text
demonstration / existing candidate
 -> candidate procedure
 -> bounded evaluation
 -> verifier evidence + objective metrics
 -> Skill Lineage
 -> ChatGPT revision
 -> regression / variant evaluation
 -> promote | retain candidate | stale | quarantine | disable
```

This is the first stage where an AVO-like variation loop is appropriate for the project because the verifier and WorkingState foundations should already exist.

## Stage 26.5 — Hybrid Computer-Use Integration

Use verified lineage and StagnationReport across Browser/Windows capability tasks, but keep capability routing, authorization, grounding and final-state verification project-owned and deterministic where possible.

---

# 5. Security consequence for future autonomy

Increasing long-horizon autonomy changes the amount of search/planning that may happen **above** the boundary; it does not move the boundary.

```text
ChatGPT / future planner / skill improver / supervisor advice
       PROPOSE
          |
          v
DETERMINISTIC CONTROL PLANE + CAPABILITY POLICY
       DECIDE / AUTHORIZE
          |
          v
bounded effect
          |
          v
fresh evidence + verifier + Finish Gate
```

If a future local planner from Track P is introduced, it remains on the proposal side of the same boundary.

---

# 6. Architectural conclusion

AVO is useful to this project primarily because it reinforces three long-horizon mechanisms already adjacent to the roadmap:

1. durable state that survives context boundaries;
2. explicit stagnation detection/supervision;
3. iterative candidate improvement grounded in objective execution feedback and lineage.

The new project-specific additions are therefore:

```text
WorkingState
 + LoopGuard
 + StagnationReport
 + Skill / Procedure Lineage
 + objective candidate-improvement loop
```

while preserving the existing core invariants:

```text
ordinary ChatGPT remains the current general planner
current state > remembered history
action delivery != verified success
candidate_done != DONE
observation/model/history != authorization
above proposes; deterministic infrastructure below decides
```

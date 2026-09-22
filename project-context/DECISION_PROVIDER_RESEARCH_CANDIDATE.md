# Typed Decision Provider — Future Research Candidate

Status: **RESEARCH CANDIDATE / NOT IMPLEMENTED / NOT ACCEPTED ARCHITECTURE**

Recorded: 2026-09-22

This note preserves a future architecture question raised by Jev / TypeSafe System One and the open local Laya model family. It does not authorize production implementation, add a provider interface, change the current planner boundary, or change the release-critical roadmap.

## Question

CAP repeatedly encounters small structured decisions that may not require a full general-model turn:

- choose one option from a bounded set;
- assign a score or probability;
- classify a bounded state;
- decide whether to escalate a question to the general planner.

The research question is whether CAP would benefit from a provider-neutral **typed Decision Provider** role for these cases, with Laya, Jev and a general-LLM baseline treated as interchangeable research candidates.

The question is deliberately broader than “should CAP integrate Jev?” or “should CAP run Laya locally?”

## Candidate role

Conceptual shape only:

```text
ordinary ChatGPT / current general planner
                  |
                  v
        deterministic Control Plane
                  |
          bounded decision request
                  |
          +-------+--------+
          |       |        |
        Laya     Jev    LLM baseline
        local   cloud
          |       |        |
          +-------+--------+
                  |
       typed probabilities / scores
```

Possible request families:

```text
choice(options) -> distribution over allowed options
score(scale)    -> bounded score / distribution
yes_no          -> probability / abstain
```

The result would be **advisory evidence**, not authority.

## CAP boundaries that must remain unchanged

Any future research or implementation must preserve the current accepted boundaries unless a separate accepted architecture decision explicitly changes them:

- ordinary ChatGPT remains the only current general planner;
- the deterministic Control Plane owns policy, authorization, operation identity, budgets and reconciliation;
- a Decision Provider cannot grant itself action authority;
- provider output cannot directly produce Verification Kernel `PASS`;
- provider output cannot directly produce Finish Gate `DONE`;
- model/provider output is evidence/data, not policy authority;
- consequence-bearing retry/recovery still obeys existing deterministic reconciliation and safety rules;
- low-confidence, unfamiliar or unsupported states must be able to abstain or escalate rather than force a local-model answer.

A Decision Provider is therefore **not** a second planner, a verifier, a Finish Gate, or an execution authority.

## Why Laya is worth tracking

Laya is interesting because it makes the typed-decision idea plausible as a local low-latency component rather than only a cloud API.

Potential value to measure:

- no network round-trip;
- low marginal decision cost;
- offline/local operation;
- open implementation/weights;
- possible task-specific tuning on CAP decision traces;
- small enough footprint to consider continuous local availability.

These are hypotheses, not accepted claims. Current limitations such as short context, hardware-dependent latency/memory behavior and weaker generalization without task-specific tuning must be revalidated before any implementation decision.

Reference: https://github.com/NandhaKishorM/laya

## Why Jev remains relevant

Jev / TypeSafe System One remains a useful contrasting candidate because it represents the cloud typed-decision approach:

- specialized structured decision interface;
- no local model/runtime management;
- potentially broader zero-shot behavior;
- network latency, service dependence and external data boundary are explicit tradeoffs.

The correct comparison is not raw “local vs cloud speed” in isolation. CAP needs the same frozen decision tasks, identical structured inputs and task-specific quality/calibration measurements.

## Candidate first use cases

Only explicitly bounded decisions should be considered initially. Examples for future evaluation:

- rank already-available observation strategies for planner consideration;
- rank candidate tools/workers without granting them authority;
- classify an observed failure into a bounded category;
- estimate whether current evidence should be escalated to the general planner;
- select a non-consequence-bearing next observation from an allowed set.

For consequence-bearing choices such as retrying a mutation, selecting an action with side effects or declaring success, provider output may at most contribute evidence. Existing Control Plane / Verification Kernel / Finish Gate ownership remains authoritative.

## Research gate before implementation

This is a new cross-capability role. If a real consumer appears, production implementation must re-enter the then-current repository `stage-research` process.

The future Stage Research must answer at least:

1. Is there a measured CAP latency/cost/throughput problem that justifies this role?
2. Which current decisions are frequent, structured and bounded enough to benefit?
3. Can deterministic rules or the existing planner solve them cheaply enough already?
4. What is the smallest useful provider contract?
5. How are calibration, abstention and fallback represented?
6. What exact state may be exposed to local vs cloud providers?
7. How are provider/model/runtime identity and provenance recorded?
8. How do Laya, Jev and an LLM baseline perform on identical CAP-specific tasks?
9. Does task-specific Laya tuning improve real CAP utility without unacceptable overfitting?
10. Does the added abstraction remove enough repeated cost/latency to justify its complexity?

If public implementations materially affect the architecture decision, the current `source-code-research` skill applies as required by Stage Research.

## Minimum evaluation

Before adopting any provider, build a frozen CAP-specific decision dataset from real or realistically replayed traces.

Compare at minimum:

- task-specific accuracy / utility;
- calibration;
- abstention and fallback quality;
- P50 / P95 latency;
- CPU / GPU / RAM use;
- model-load / cold-start cost;
- cloud round-trip contribution;
- failure behavior when context/input limits are exceeded;
- robustness to unfamiliar states;
- reproducibility across provider/model/runtime versions.

A game loop or a local-vs-network latency demonstration is useful evidence about latency, but not proof of superior reasoning quality.

## Possible contract shape — hypothesis only

```text
DecisionRequest
  question_type
  allowed_options_or_scale
  compact_structured_state
  provenance / task identity

DecisionResult
  provider identity
  model/runtime version
  probabilities / scores
  abstain / error
  latency
  optional calibration metadata
```

Possible adapters, only if future research justifies them:

```text
DecisionProvider
  +-- LayaLocalProvider
  +-- JevProvider
  +-- LLMDecisionProvider
```

No provider API is accepted by this note.

## Relationship to Dream / RSI research

This candidate is orthogonal to a future Dream/RSI-style strategy-improvement layer:

- **Decision Provider** — fast bounded runtime decision among explicit options.
- **Dream/RSI layer** — slower analysis/improvement of strategies from accumulated attempts.

Neither role should replace the general planner, deterministic Control Plane, Verification Kernel or Finish Gate without a separate accepted architecture decision.

## Current disposition

```text
role = typed Decision Provider
status = RESEARCH_CANDIDATE
implementation = NONE
provider_selection = NONE
roadmap_change = NONE
authority_change = NONE
next_step = fresh Stage Research only when a real consumer/measurement justifies it
```

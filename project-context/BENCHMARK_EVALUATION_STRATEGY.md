# Benchmark Evaluation Strategy

Status: **AUTHORITATIVE CROSS-CAPABILITY EVALUATION STRATEGY**

## Purpose

Chat Agent Platform must not infer product quality only from its own unit/contract tests and physical acceptance gates.

For every capability that has become mature enough to be exercised honestly through its accepted product surface, development should add an appropriate **independent public benchmark** and retain comparable results across CAP versions.

This is a cross-cutting development rule, not a new roadmap stage and not a replacement for project verification/security/physical acceptance.

The three evidence planes answer different questions:

```text
project unit / contract / synthetic tests
  -> does implementation satisfy the project contract?

project physical / adversarial / fault-injection gates
  -> does the accepted runtime really execute and fail closed under the declared environment/failure model?

independent public benchmarks
  -> how capable is this accepted product surface on externally defined tasks relative to prior CAP versions and other agents?
```

A benchmark score cannot authorize a consequence, prove source provenance, replace reconciliation, or waive a failed physical/security gate. Conversely, a green project gate does not prove competitive task performance.

## Core rule — benchmark only capabilities CAP genuinely has

Do not create a privileged `benchmark CAP` with tools or authority unavailable to the accepted product merely to improve a leaderboard score.

A benchmark becomes eligible when:

1. the corresponding CAP capability exists through an accepted or explicitly candidate product surface;
2. the benchmark can be connected through a thin evaluation adapter without adding hidden planning/execution authority;
3. the benchmark task/environment is materially representative of the capability being evaluated;
4. the result can be bound to exact CAP/model/benchmark/adapter/budget identity;
5. benchmark-specific secrets, evaluators or ground truth remain outside agent authority.

If a benchmark requires a capability CAP does not yet have, record it as **DEFERRED UNTIL CAPABILITY EXISTS** rather than temporarily granting the missing tool.

Examples:

- Terminal-Bench / general SWE execution is deferred while CAP lacks an accepted generic terminal/local-execution capability.
- full OSWorld-style cross-application evaluation is deferred until the required desktop/browser/vision/application surfaces are available together, although narrower compatible task subsets may be used earlier.
- multi-agent benchmarks remain deferred until a real delegation/session capability exists; simulated colleagues inside an environment do not by themselves make the tested CAP agent multi-agent.

## Harness rule — use the strongest native harness per domain

There is no requirement to force all benchmarks through one framework.

Reuse mature benchmark infrastructure where it already exists:

| Capability family | Preferred evaluation family / harness posture | Current role |
|---|---|---|
| independent code review | Harbor custom-agent/task/verifier path | first CAP benchmark integration; evaluation only |
| browser atomic interaction | BrowserGym / AgentLab + MiniWoB | early browser control regression |
| realistic browser tasks | BrowserGym / AgentLab + WebArena-Verified | realistic web task benchmark |
| enterprise browser knowledge work | BrowserGym / AgentLab + WorkArena / WorkArena++ where current | compound business/web workflows |
| visual browser | BrowserGym / AgentLab + VisualWebArena | visual grounding/routing/fallback evaluation |
| longer web/assistant tasks | AssistantBench / TimeWarp / other BrowserGym suites when applicable | longer web knowledge-work evaluation |
| hybrid desktop/computer use | OSWorld, then OSWorld 2.0 for long-horizon workflows | cross-app computer-use benchmark after capability maturity |
| generic terminal/local execution | Terminal-Bench through its current official harness (currently Harbor-native) | deferred until honest CAP terminal capability exists |
| software engineering | SWE-bench-family evaluation where the CAP coding surface genuinely supports the task | deferred until coding/repository execution is accepted |
| general digital worker | TheAgentCompany or a later stronger equivalent | later cross-tool professional-work evaluation |
| task-completion duration | METR Time Horizon methodology / compatible task suite | mature long-horizon KPI, not an early-stage benchmark |
| future delegation/multi-agent | appropriate public multi-agent benchmark selected at Track M re-entry | deferred |

The table is a **candidate ladder**, not an immutable dependency list. At adoption time, Stage Research must revalidate the current benchmark release, harness, task leakage/contamination risks, licensing/cost constraints and comparability rules.

Do not pin volatile leaderboard values in this strategy. Pin exact benchmark releases in each actual run record.

## Benchmark ladder by CAP maturity

### Reviewer — first active rung

Use the automatic independent reviewer as the first production/evaluation integration because it already has a bounded exact input/output contract.

Initial semantic-quality sequence:

```text
ReviewBench
 -> bounded SWE-Review-Bench control
 -> CR-Bench / CR-Evaluator false-positive and signal/noise control
 -> later additional review suites only when they add a measured gap
```

The reviewer-specific production/lifecycle decision remains owned by `AUTOMATIC_REVIEWER_RESEARCH.md`. That Brief is the first concrete consumer of this cross-capability strategy; its Harbor choice is reviewer-specific and does not make Harbor the universal CAP benchmark harness.

### Browser — evaluate progressively rather than waiting for the final agent

When the Browser evaluation adapter can exercise the same accepted Browser capability used by CAP:

```text
MiniWoB
 -> WebArena-Verified
 -> WorkArena / compound knowledge-work suites
 -> VisualWebArena when visual routing/fallback is in the tested product path
 -> longer BrowserGym suites such as AssistantBench / TimeWarp when long-task state is relevant
```

The adapter must translate benchmark observations/actions into the existing CAP capability boundary. It must not bypass project Browser semantics by directly controlling Playwright in a way unavailable to the tested agent.

### Hybrid computer use

After Browser + Windows/application + visual routing are integrated sufficiently for the target task class:

```text
OSWorld-compatible subset
 -> pinned full OSWorld release when applicable
 -> pinned OSWorld 2.0 long-horizon evaluation after WorkingState/recovery/cross-app behavior is mature
```

OSWorld 2.0 release-controlled code/tasks/assets/sites/provider image must be kept on one matching benchmark release. Never mix `main`, `latest` and older task/assets snapshots in a published comparison.

### Coding / terminal

Only after CAP has an accepted generic local execution/coding surface:

```text
Terminal-Bench
 -> SWE-bench-family evaluation
```

Do not expose a shell only for evaluation and then describe the result as normal CAP performance.

### General professional work

After the relevant browser/files/desktop/coding/communication surfaces exist, evaluate a broader work benchmark such as TheAgentCompany or a later stronger equivalent. The tested agent may still be a single CAP agent even when coworkers/services are simulated by the environment.

### Long-horizon capability

METR-style Time Horizon becomes useful only after CAP can solve a sufficiently broad, automatically gradable task distribution. Treat it as a mature KPI rather than an early target.

Remember the metric definition:

```text
TH50 / TH80
  = human-expert task duration at which the tested agent is predicted to succeed with 50% / 80% probability
```

It is not the wall-clock time for which the agent itself kept running.

## Frequency rule

Do not run every full benchmark after every PR.

Use three evaluation frequencies:

### 1. Every significant implementation PR

Required:

- project unit/contract/focused regression tests;
- applicable project physical/adversarial gates under existing policy.

Optional benchmark smoke/subset only when cheap enough to provide fast regression signal.

### 2. Capability/stage closure or material capability integration

Run a **fixed external regression subset** appropriate to that capability when an honest adapter exists.

The subset should be stable enough to compare CAP versions and small enough not to dominate development time.

### 3. Major release / major architecture change / public comparison

Run the full or officially comparable benchmark suite where practical, using the benchmark's current reproducibility rules.

For a materially changed already-benchmarked capability, prefer a before/after comparison on the same pinned evaluation setup before drawing a causal performance conclusion.

## Development, regression and holdout separation

Do not repeatedly inspect every official task and then call the resulting score independent evidence.

Maintain three evidence classes:

```text
development set
  -> task failures may be inspected in detail and used to improve CAP

fixed regression subset
  -> stable project-selected subset used frequently to detect regressions

official / holdout evaluation
  -> run at controlled checkpoints; do not tune task-by-task against its answers
```

When a benchmark does not provide a hidden test set, create a documented split or controlled evaluation policy that preserves a meaningful holdout as far as practical.

Benchmark-driven changes to prompts/skills/strategy must express a **general invariant or capability improvement**, not filename/site/task-id hacks.

## Pre/post and historical comparison rule

A benchmark result is most useful as a time series, not as one isolated score.

For benchmarked capabilities, retain enough metadata to compare:

```text
CAP version A -> metric set
CAP version B -> metric set
frontier/reference systems on materially comparable benchmark release/configuration where available
```

Do not claim an architecture improvement merely because a new run is higher when benchmark release, model, budget, adapter or task subset changed materially.

## Required run provenance

Every retained/public benchmark result must identify at least:

```text
CAP source identity / exact commit or release
model/provider identity
model effort/reasoning/configuration when exposed
ordinary-Chat/product configuration relevant to behavior
benchmark name + exact release/version/ref
benchmark task split/subset identity
benchmark adapter source/version
accepted CAP tool/capability surface used
step/action/token budget as applicable
timeout and retry policy
number of runs / repetitions / seeds when applicable
environment/container/VM/site release identity when benchmark controls it
cost/token usage when available and meaningful
result metrics + uncertainty/confidence interval when available
known deviations from official evaluation protocol
```

A bare statement such as `CAP scored 62%` is not a reproducible result.

## Metric ownership — do not collapse unlike evidence

Each benchmark family has its own semantic metrics. Keep those separate from CAP infrastructure/reliability metrics.

Examples:

```text
review quality
  -> precision / recall / F1 / decision accuracy / FAR / FRR / revision resolution

browser / computer-use task quality
  -> benchmark task success / reward / partial completion metrics

CAP lifecycle reliability
  -> launch success / exact identity / stale rejection / duplicate suppression /
     timeout disposition / recovery after injected failure / human intervention

long-horizon methodology
  -> TH50 / TH80 or other explicitly defined duration/expenditure measures
```

Do not manufacture one universal CAP score that hides whether semantic quality, lifecycle reliability, safety or breadth changed.

## Benchmark result authority

External benchmark evidence is **quality/competitive evidence**, not project execution authority.

A strong benchmark score does not override:

- `PASS | FAIL | UNKNOWN` verification semantics;
- stale/ambiguous-result rejection;
- deterministic authorization/grants;
- source/install/runtime provenance requirements;
- physical qualification requirements;
- security policy;
- exact-head independent semantic review;
- Finish Gate evidence.

Preserve fail-closed behavior even if a benchmark score would improve by guessing/retrying more aggressively.

## Benchmark adapter rule

A benchmark adapter should be thin and inspectable:

```text
benchmark task/environment
 -> adapter translation
 -> same CAP capability/planner semantics used by the product
 -> action/effect through benchmark environment
 -> benchmark verifier
```

It may normalize observations/actions and provide benchmark-specific environment lifecycle plumbing. It must not:

- grant extra product authority;
- expose hidden ground truth/evaluator internals;
- bypass CAP verification/action semantics solely for score;
- change task success after the fact;
- silently retry actions beyond the accepted CAP failure policy;
- inject benchmark-specific answers into the planner/skill.

When the benchmark harness itself is a major dependency or has important failure/leakage semantics, revalidate it through `stage-research` / `source-code-research` before adoption.

## Evidence-based targets, not invented thresholds

The first run of each benchmark establishes a baseline.

Do not invent a threshold such as `>= 80%` before measuring current CAP and relevant comparison systems under a comparable setup.

After baseline data exists, define targets using evidence such as:

- no material regression versus the previous accepted CAP version;
- improvement expected from a specific architecture change on the affected benchmark family;
- gap to a relevant public reference/frontier configuration;
- statistically meaningful uncertainty where the benchmark supports it;
- acceptable tradeoff between task performance and lifecycle/safety reliability.

## Current candidate families — revalidate before execution

The following are current public candidates observed during the 2026-08 research pass and are intentionally recorded without mutable leaderboard numbers:

- BrowserGym / AgentLab: MiniWoB, WebArena, WebArena-Verified, VisualWebArena, WorkArena, AssistantBench, OpenApps, TimeWarp;
- OSWorld 2.0: long-horizon real-world computer-use tasks with release-controlled code/tasks/assets/sites;
- Terminal-Bench 2.1: terminal-agent benchmark with an official Harbor execution path;
- TheAgentCompany 1.x: professional-work task environment that documents use by non-OpenHands platforms;
- METR Time Horizon 1.1 methodology: human-duration-conditioned success horizon;
- reviewer suites named in `AUTOMATIC_REVIEWER_RESEARCH.md`.

These names are research candidates, not permanent mandatory dependencies. If a stronger maintained benchmark supersedes one before CAP reaches the relevant capability, Stage Research may replace it with explicit evidence.

## Adoption sequence

For each new benchmarked capability:

```text
capability reaches honest evaluable surface
 -> revalidate current public benchmark/harness + failure/leakage model
 -> select thin adapter
 -> define dev/regression/holdout split
 -> capture baseline on exact CAP identity
 -> use small fixed subset during subsequent development
 -> full/official run at capability closure or major release where practical
 -> compare to prior CAP + public references
 -> retain reproducible run metadata
```

The immediate implementation priority remains the bounded automatic reviewer. This strategy does **not** move Browser/OSWorld/Terminal/METR work ahead of the current roadmap. It ensures that when each capability matures, external evaluation is already part of the development method rather than an end-of-project afterthought.

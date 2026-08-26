# Real-Task Acceptance Contract

Status: **CURRENT ACCEPTANCE DIRECTION / STAGE 26.3B+**.

## Purpose

The project must not confuse a large number of passing low-level tests with proof that the agent can complete ordinary user work.

Low-level deterministic tests remain mandatory because they isolate failures and protect safety invariants. They are necessary, but they are not sufficient evidence of useful autonomous behavior.

The project therefore uses three complementary acceptance levels:

```text
L1 — Primitive / contract
L2 — Workflow / component integration
L3 — Real user task / planner-to-finish E2E
```

No level replaces the levels below it.

---

# L1 — Primitive / contract acceptance

L1 isolates one mechanism or invariant.

Examples:

```text
web_open direct navigation -> PASS
redirect delivered but wrong final URL -> FAIL
textbox value changes -> PASS
checkbox expected checked=true -> PASS
missing expected -> zero mutation
already-satisfied expected -> zero mutation
window identity stays bound
file hash equals expected
```

Characteristics:

- small and deterministic;
- exact expected outcome known in advance;
- easy to diagnose;
- runs frequently in hosted CI where possible;
- physical target-machine variants are used when the platform boundary cannot be represented faithfully in hosted CI.

L1 answers:

> Does this mechanism enforce its contract?

L1 does **not** answer:

> Can the agent solve a realistic user task?

---

# L2 — Workflow / component integration acceptance

L2 exercises a multi-step path while keeping the route mostly controlled by the test harness.

Examples:

```text
open page
 -> locate form
 -> edit fields
 -> save
 -> re-open
 -> verify persisted state
```

or:

```text
open application
 -> select document
 -> change setting
 -> save
 -> re-observe application/file state
```

Characteristics:

- several actions and state transitions;
- verifies integration between observation, action and Verification Kernel;
- may use a scripted route to make regression diagnosis reproducible;
- includes at least one final-state check rather than only per-action delivery assertions.

L2 answers:

> Do the accepted components work together across a realistic sequence?

L2 still does **not** prove that the general planner can independently choose the route from a normal user goal.

---

# L3 — Real user-task acceptance

L3 is the top-level acceptance layer for realistic autonomous behavior.

The task is given to ordinary ChatGPT in normal goal language. The harness provides the environment and the success criteria, but **does not provide a click/type script**.

Example shape:

```text
"Find the specified customer case, correct its delivery address,
set it to Approved, replace the review comment, save the result,
and make sure you changed the intended case rather than a similar record."
```

The planner must decide how to:

```text
observe
navigate
identify the correct target
choose actions
satisfy intermediate postconditions
recover from ordinary ambiguity where possible
re-observe
verify final state
stop
```

L3 answers:

> Can the current planner + accepted capability stack complete a realistic user goal and prove the result?

---

# L3 task-design requirements

An L3 task must satisfy all of the following unless the task class makes one item genuinely irrelevant.

## Natural-language goal

The prompt describes desired user-visible outcome and constraints, not an ordered action recipe.

Bad:

```text
1. Open URL X.
2. Click button Y.
3. Type Z.
4. Click Save.
```

Good:

```text
Find case CASE-4821 for Marina Volkova, update the requested fields,
save it, and verify that the similarly named records were not changed.
```

## Multiple meaningful transitions

The task should require several state changes. A single click or one field fill is L1, not L3.

Initial target for Browser L3:

```text
roughly 5–20 meaningful observe/act/verify transitions
```

The count is diagnostic, not a score to optimize.

## Target ambiguity / distractors

Where practical, include realistic competing targets:

```text
similar customer names
similar case IDs
multiple windows/documents
stale or already-completed records
nearby controls with different consequences
```

The task must be solvable from observed state without hidden knowledge.

## Randomized run identity

Physical L3 fixtures should randomize a nonce, task/case ID or equivalent task data so a prior successful route cannot pass by memorizing one static fixture instance.

Randomization must preserve semantic equivalence of the task and deterministic finish criteria.

## Independent final state

The final decision must not depend only on the planner saying `done` or on the last action returning success.

Required shape:

```text
planner candidate_done
        |
        v
independent state evidence
        |
        v
Finish Gate
        |
        +--> DONE
        +--> NOT_DONE
        +--> UNKNOWN
```

For test fixtures, the independent state may be a server-side state file/database/API owned by the fixture rather than the browser DOM that the planner just manipulated.

### Independent evidence must not be planner-writable

The independent Finish Gate is invalid if the agent can simply overwrite the evidence artifact.

Therefore at least one of these must hold:

```text
finish evidence lives outside all planner-writable roots
or
finish evidence is protected by an independently enforced read-only boundary
or
finish evidence is produced by an external verifier the planner cannot mutate
```

A hidden test/admin mutation endpoint is not allowed.

Reading a final result after task completion may be acceptable when the evidence cannot be modified by the planner, but the strongest physical gate is an **external checker** that runs after the planner reports candidate completion.

## Constraint / non-target checks

The Finish Gate must verify both requested changes and important invariants.

Example:

```text
target address == requested address
target status == Approved
target comment == requested comment
old target address absent
similar non-target cases unchanged
only intended target ever mutated when the task requires that constraint
```

This prevents a test from passing when the agent reaches the requested value by damaging unrelated state and then restoring it.

## No hidden administrative shortcut

The planner must use the accepted product capability surface for mutation.

A fixture may expose independent state to the **external Finish Gate**, but the planner must not mutate that state through a hidden test/admin API or writable evidence file.

The current Browser L3 uses the normal six-tool surface and browser UI for task mutation. Its fixture state is intentionally outside the Chat `FilesRoot`.

---

# Evidence required from an L3 physical run

Record at minimum:

```text
exact repository/runtime head
qualification root / fixture run identity
natural-language task
initial Finish Gate = NOT_DONE
accepted public capability surface
final external Finish Gate result
final independent state evidence
non-target/invariant checks
action/audit summary where fixture provides one
whether any recovery/ABSTAIN occurred
```

Do not persist private chain-of-thought.

A concise action/evidence trace is enough; hidden reasoning is neither required nor desired.

---

# Failure classification

L3 failure is useful evidence. Classify it before changing architecture.

Suggested classes:

```text
planner_targeting_error
planner_strategy_error
observation_gap
action_grounding_error
verification_false_positive
verification_false_negative
precondition_or_policy_block
recovery_failure
finish_gate_failure
fixture_or_environment_failure
external_dynamic_change
```

Do not repair every L3 failure by adding a site-specific hard-coded path. Prefer the smallest reusable missing mechanism.

---

# Acceptance policy

## Capability-mechanism acceptance

L1/L2 evidence may accept a bounded mechanism such as Browser navigation or interaction verification.

## User-task acceptance

A major capability class is not considered proven for realistic autonomous use until at least one representative L3 task passes physically on the target environment using the accepted public surface.

One L3 pass is still scoped evidence, not universal accuracy.

Broader reliability requires a task family / matrix with variants.

## Release growth rule

Do not repeatedly expand architecture while only increasing L1 coverage.

For each material capability expansion:

```text
new mechanism
 -> L1 contract proof
 -> L2 integration proof where useful
 -> representative L3 task
 -> only then use the result as evidence for broader autonomy claims
```

---

# First Browser L3 — Stage 26.3B

PR #112 introduces the first Browser real-task harness on top of PR #111.

Fixture: local `Case Desk` application.

Each physical run creates randomized:

```text
target case ID
nonce-bound old/new addresses
required comment
similar decoy records
```

Ordinary Chat receives a natural task, not the route.

The physical qualification layout is intentionally split:

```text
qualification root
  workspace/
    stage26-3b-browser-real-task.txt
      ^ this is the only FilesRoot visible to Chat

  fixture-state/
    fixture-seed.json
    server-state.json
    audit.jsonl
    finish-gate.json
      ^ outside Chat FilesRoot; external verifier evidence

  gate-manifest.json
```

The independent Finish Gate requires:

```text
target exists
target address exact
target status exact
target comment exact
old address removed from target
all decoy records unchanged
only the intended target was ever mutated
```

Initial gate must be `not_done`. Only the correct persisted result may produce `done`.

The external `check-browser-real-task-gate.ps1` validates final state, mutation history and evidence-root separation after ordinary Chat reports completion.

The hosted fixture smoke test validates the harness itself. It is **not** a substitute for the ordinary-Chat physical L3 run.

---

# Current Stage 26.3B sequencing consequence

The Browser verification path now closes in this order:

```text
PR #111 primitive interaction verification physical gate
 -> merge #111
 -> replay #112 on accepted main
 -> hosted fixture/harness checks
 -> ordinary-Chat target-Windows Browser L3 real-task gate
 -> external Finish Gate check
 -> merge #112 if clean
 -> continue Windows/application/process verification
```

This adds evidence depth without changing the public six-tool surface or widening Browser authority.

---

# Future Windows/application L3

Windows verification must follow the same pattern.

Do not stop at:

```text
window found
button clicked
file appeared
```

Add a representative natural user task such as:

```text
open the correct application/document
change a requested setting/content value
save to the requested target
re-open or independently inspect the result
prove the intended document changed and similar/non-target state did not
```

The exact task should be chosen after the Windows/application/process verifier exists so the L3 gate exercises the actual accepted path rather than inventing a parallel test-only mechanism.

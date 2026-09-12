# Coddy Runtime Candidate — parked post-#149 research input

Status: **PARKED — NARROW / REUSE-WITH-ADAPTER — NO PRODUCTION AUTHORITY**

This note preserves Coddy as a future composition-first runtime candidate for Chat Agent Platform. It does **not** modify PR #149, does not authorize Coddy as a dependency, does not make Coddy the CAP planner/authority layer, and does not preselect Coddy over Prime or a minimal CAP-owned mechanism.

The source-level research input that triggered this note inspected:

- CAP PR #151 at `99ff7efb404324abdd8b2e0fd046f63ace88bf26`;
- Coddy `main` at `2c0872c4d3781ddee41b00a2b7883d9b434b49b8` (reported 2026-09-04 baseline);
- `openai/codex` as a source reference for durable lifecycle/recovery semantics;
- OpenHands as an independent reference for durable parent/child conversation identity.

Treat those external baselines as **research evidence to re-resolve at re-entry**, not permanent qualification. No Windows physical acceptance or real ChatGPT Plus crash E2E has been completed for Coddy.

## Disposition

```text
Coddy = promising reusable session/subagent machinery
        behind CAP authority

not

Coddy = CAP trust core / planner / consequence authority / recovery truth
```

Current disposition:

```text
NARROW / REUSE-WITH-ADAPTER
```

Coddy joins Prime in the future retained/subagent runtime comparison cohort. Neither is preselected.

Re-enter only after #149 is accepted and a **measured** need for retained workers, subagents, background orchestration, persistent local agent-loop mechanics, or another missing runtime primitive is demonstrated.

## What is attractive for CAP

The source-level research found several mechanics worth reusing or adapting rather than rebuilding:

- real child sessions rather than role-only prompts;
- separate child context/transcript/session identity;
- effective child tool restriction by intersection of parent/mode/allowlist/denylist constraints;
- child permission narrowing that cannot intentionally widen parent authority;
- bounded depth and parallelism;
- background-task pool mechanics;
- project-agent definition trust tied to workspace + definition identity + SHA-256 digest;
- provider abstraction suitable for an external model transport adapter;
- bounded finish-notification / wake mechanics as provider evidence.

These fit the PR #151 composition-first rule: reuse mature runtime mechanics, keep CAP-specific trust/effect semantics above them, and build custom runtime code only for a measured gap.

## CAP-owned boundaries that must remain above Coddy

Coddy task/session status is provider/runtime evidence only.

```text
Coddy accepted/succeeded/completed
        !=
CAP PASS
        !=
CAP whole-task DONE
```

CAP must continue to own at least:

```text
stable logical identity
authorization / consequence scope
operation and attempt identity
ExpectedEffect
freshness / provenance
PASS | FAIL | UNKNOWN
ambiguous-outcome reconciliation
no blind retry
WorkingState authority
Verification Kernel
independent Finish Gate
exact source/runtime provenance where required
```

Coddy scheduler state, wake state, task status and background-task metadata must not become CAP authority merely because they are convenient runtime primitives.

## Critical gap 1 — planner/orchestration ownership

Do not accidentally invert the architecture by placing Coddy above CAP or ordinary ChatGPT.

A Coddy provider integration naturally looks like:

```text
Coddy bounded child / agent loop
        ↓
Coddy Provider
        ↓
thin CAP model-transport adapter
        ↓
CCCC / qualified session transport
        ↓
ordinary ChatGPT model session
```

That is acceptable only for a **bounded delegated child runtime** already authorized by CAP.

The manager/control path remains conceptually:

```text
ordinary ChatGPT manager
        ↓
CAP trust/control boundary
        ↓
bounded delegation/session request
        ↓
Coddy adapter (if selected)
```

Do not turn Coddy's own ReAct/agent loop into a second unrestricted general planning authority above CAP.

## Critical gap 2 — transport-only authority profile

The most important qualification question is whether Coddy can be configured or minimally patched so the parent/child runtime cannot bypass CAP consequence authority.

Target effective profile, name illustrative only:

```text
cap_transport

ALLOW
  spawn_agent / bounded child creation
  read-only context
  bounded background observation
  approved CAP semantic/procedure surface

PHYSICALLY ABSENT / DENIED
  shell / run_command
  filesystem write/edit
  git mutation
  config mutation
  scheduler mutation
  arbitrary MCP
  direct uncontrolled side-effect tools
```

Prompt instructions or interactive permission prompts are not sufficient security boundaries. Prefer using Coddy's existing effective-tool/permission intersection mechanisms rather than inventing a new CAP permission framework.

If a transport-only effective tool profile cannot be proven, Coddy is rejected for the CAP production path regardless of its subagent quality.

## Critical gap 3 — durable recovery is weaker than CAP authority needs

The source research reports that persisted nonterminal background tasks are recovered as orphaned rather than reconstructing exact in-flight ownership, consequence state, continuation and exactly-once wake semantics.

That behavior may be reasonable for a coding harness but is insufficient as CAP recovery authority.

Required rule:

```text
Coddy task state = provider evidence
CAP state         = authority
```

Coddy must not independently decide that an ambiguous child/model/tool consequence is safe to retry.

## Critical gap 4 — wake is not CAP delivery authority

Coddy's finish notification / wake batching may be useful mechanically, but wake intent/state must remain evidence unless/until a separate qualification proves durable exactly-once semantics.

Do not allow:

```text
Coddy task terminal
        ↓
Coddy directly resends/wakes consequence-bearing parent work
```

Prefer:

```text
Coddy terminal event
        ↓
CAP-owned bounded delivery/reconciliation seam
        ↓
qualified session transport
        ↓
parent conversation
```

No blind wake/resend after ambiguous acknowledgement.

## Critical gap 5 — Windows cross-process serialization

The source research reports that Coddy's strong cross-process turn lock is Unix-specific while the non-Unix implementation does not provide equivalent interprocess ownership semantics.

For CAP's Windows target, Coddy must therefore not own exactly-once/session serialization unless a Windows implementation is independently qualified.

Until then:

```text
CAP/qualified Windows lock authority
        >
Coddy process-local/session lock evidence
```

## Model transport seam — useful, but keep it thin

Coddy reportedly exposes a provider abstraction and OpenAI-compatible configurable base URL. That makes a narrow spike attractive:

```text
Coddy Provider
      ↓
localhost thin CAP model-transport adapter
      ↓
fake provider first
      ↓
qualified CCCC / ordinary ChatGPT later
```

Do **not** prematurely create a large generic `CAP Model Broker` with its own session registry, durable inbox, delivery ledger and recovery runtime. PR #151 explicitly avoids rebuilding those generic systems without a measured conformance gap.

If testing later proves a missing correlation primitive, Stage Research may consider the smallest bounded record, for example:

```text
model_request_id
session_ref
turn_generation
context_sha256
attempt identity
provider receipt/evidence
```

Those fields are candidates, not an authorized new state owner.

## Retry rule for a qualified browser/session path

Automatic provider retries are unsafe when an LLM request may map to a physical browser Send whose acknowledgement can be lost.

The source research reports Coddy supports disabling LLM retry explicitly. A future qualified CAP path should begin with automatic Coddy LLM retry disabled (for the inspected baseline, `llm_retry_max=0` was reported to do this).

Required semantic rule:

```text
ambiguous model delivery
        ↓
reconcile/query existing logical request
        ↓
known delivered | known not delivered | UNKNOWN

never

ambiguous model delivery
        ↓
blind provider retry
        ↓
possible second ChatGPT Send
```

Re-resolve the exact Coddy configuration semantics before any implementation because this parking note is not permanent source qualification.

## Scheduler disposition

Do not adopt Coddy scheduler as CAP consequence authority.

If a future consumer needs timing, Coddy scheduler may at most be evaluated as a timer/event source:

```text
timer fired
   ↓
provider evidence/event
   ↓
CAP authorization/reconciliation
```

not:

```text
timer fired
   ↓
Coddy independently performs unrestricted machine effects
```

A generic scheduler remains outside CAP unless a concrete measured consumer and fresh Stage Research justify it.

## Candidate cohort after a measured runtime gap

When a retained/subagent runtime primitive is actually needed, compare rather than preselect:

```text
measured retained/subagent/runtime gap
                 ↓
      ┌──────────┼──────────┐
      ▼          ▼          ▼
    Coddy      Prime     minimal CAP
      │          │          │
      └── conformance + crash + bypass tests ──┘
                 ↓
          smallest qualified winner
```

`openai/codex` remains a source reference for durable lifecycle/recovery/locking patterns; it is not automatically a CAP runtime dependency.

## First spike — isolated, read-only, no production CAP mutation

The preferred first experiment is a bounded external spike, not integration:

1. Pin one exact Coddy source/binary baseline and record provenance.
2. Disable scheduler and automatic LLM retry for the experiment.
3. Apply the narrowest possible transport/read-only tool profile.
4. Point Coddy's OpenAI-compatible provider at a local **fake** model adapter first.
5. Exercise 3-5 model/tool turns and at least two parallel child sessions.
6. Kill Coddy at model-request, child-execution, finish-event and wake boundaries.
7. Prove ambiguous outcomes do not cause duplicate model/tool/wake effects.
8. Run adversarial attempts from a confused/malicious child to invoke shell, write/edit, arbitrary MCP, scheduler mutation and direct uncontrolled effects; all must be physically unavailable.
9. Only after fake-provider conformance succeeds, replace the fake model transport with qualified CCCC / ordinary ChatGPT transport.
10. Keep the entire first real-model spike read-only.

Do not start with a live ChatGPT Plus integration before the fake-provider/crash/bypass tests pass.

## Minimum questions before `PROCEED`

1. Can the exact Coddy baseline expose a transport/subagent profile with every CAP-bypass mutation path physically unavailable?
2. Can one CAP logical delegation map deterministically to one Coddy parent/child runtime identity without making Coddy identity canonical?
3. Can model requests be correlated/reconciled without blind retry or duplicate browser Send?
4. What exact state survives Coddy process crash, and which states become orphaned/ambiguous?
5. Can two parallel children remain bounded by parent authority and independent tool restrictions?
6. Can complete Coddy restart occur without widening rights, duplicating work or inventing success?
7. What Windows cross-process lock/serialization guarantee actually exists on the then-current baseline?
8. Can Coddy wake/finish events be consumed as evidence without becoming delivery authority?
9. Can scheduler and arbitrary MCP be excluded from the qualified profile?
10. Does CCCC remain the ordinary-ChatGPT session transport while Coddy remains only a bounded runtime primitive?
11. Does every provider/runtime `success` still require fresh CAP verification before `PASS`?
12. Does the integration add less code/state/authority than the Prime or minimal-CAP alternatives?

## Re-entry decision

Current decision:

```text
PARK

Coddy is a serious future candidate for reusable bounded session/subagent mechanics,
but it is not production-qualified for CAP and is not an authority/recovery layer.
```

Re-enter after #149 only when composition research demonstrates a concrete runtime gap. At that point rerun `stage-research` and `source-code-research` against the exact current Coddy baseline, then perform the isolated fake-provider/read-only spike before considering any production dependency or adapter.

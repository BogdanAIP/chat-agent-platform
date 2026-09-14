# Current State

## Repository-state rule

Resolve live `main`, relevant open PRs/exact heads, hosted checks and required physical evidence before new work. Current code/tests/current CI/current physical evidence outrank prose.

Ownership:

- `CURRENT_STATE.md` = accepted/current boundary + immediate work;
- `ROADMAP.md` = release order;
- `PROJECT_RISKS.md` = ranked risks;
- `EVIDENCE_INDEX.md` = exact accepted physical heads/result locators;
- `ARCHITECTURE_REUSE_BASELINE.md` = prior component/reuse lineage for applicable Stage Research.

## Current accepted boundary

Stage 26.3B remains **ACCEPTED / CLOSED for its recorded representative scope**.

Stage 26.3C remains **ACCEPTED / CLOSED for its declared production process-restart/local-Windows scope** through merged PR #126.

Relevant accepted progression includes:

```text
Stage 26.3A canonical six-tool runtime             ACCEPTED / MERGED #92
Verification Kernel foundation                    MERGED #99
file/artifact kernel integration                  PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                    MERGED #106
web_open final-state verification                 PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                    MERGED #110
web_interact postcondition verification           PHYSICAL ACCEPTED / MERGED #111
Browser real-task L3                              PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verification   PHYSICAL ACCEPTED / MERGED #114
Windows/application real-task L3                  PHYSICAL ACCEPTED / MERGED #115
Track M future architecture                       MERGED #116 / DESIGN ONLY AT THAT POINT
CAP-M0 Verification mutation assurance            ACCEPTED / MERGED #117
Browser stronger source-provenance L3 repeat      PHYSICAL ACCEPTED / MERGED #118
WorkingState + LoopGuard L1 foundation            ACCEPTED / MERGED #124
Stage 26.3C production WorkingState integration   PHYSICAL ACCEPTED / MERGED #126
stage-research mechanism-depth hardening          MERGED #127
automatic-review Stage Research / local-result v1 ACCEPTED NARROW / MERGED #140
automatic-review local state foundation           ACCEPTED / MERGED #141
automatic-review fixed procedure wiring           ACCEPTED / MERGED #142
bounded Agent Session / Delegation foundation      ACCEPTED / MERGED #149
bounded one-click main updater                      ACCEPTED / MERGED #150
Delegation Provider Contract boundary               MERGED #155
Delegation Provider Contract guard                  MERGED #156
```

These are scoped proofs. They do not imply universal Browser/Windows/application reliability, machine/power-loss transactional durability, or a generally accepted multi-agent runtime.

## Stage 26.3C accepted production scope

The first accepted consequence-bearing production consumer remains `verified_workspace_artifact_v1` on the supported local Windows workspace path.

Accepted behavior includes:

```text
WorkingState + stable logical mutating-operation identity
procedure-local durable checkpoint + prepared intent
bounded task/procedure/strategy budgets + LoopGuard
fresh same-stream reconciliation before unsafe retry
per-task cooperating-runner serialization
generation-bound file identity for consequence-bearing resume
Windows file/namespace pinning around path-based consequences
fail-closed corrupt/missing/inconsistent checkpoint handling
```

The accepted guarantee is process crash/restart within the declared local-Windows scope. It does not claim machine/power-loss atomicity.

## Current public route

Exactly six Chat-facing tools remain accepted:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal route:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> canonical six-tool semantic projection
 -> deterministic Control Plane + focused capabilities
```

Ordinary ChatGPT remains the **only current general planner/intelligence**. The deterministic Control Plane owns bounded execution state/policy, authorization, ExpectedEffect verification, recovery/reconciliation budgets and independent completion checks for already-selected transitions. It is not a second planner.

WorkingState is capability-spanning structured operational state, never private chain-of-thought.

## Accepted bounded Agent Session / Delegation

PR #149 is **ACCEPTED / MERGED**. Its accepted product scope remains deliberately narrow:

```text
one ordinary-ChatGPT manager
 -> one genuinely fresh read-only worker
 -> one bounded provider-independent DelegationIdentity
 -> one initial delivery
 -> delivered | unknown settlement without blind resend
 -> one correlated structured WORKER_RESULT_V1
 -> durable local closure when that result is captured
```

The first concrete provider remains `chatgpt-temporary` bound to the specialized `fresh_readonly_worker_v1` profile:

```text
fresh
independent
non-personalized
no-plugin / closed-profile
Temporary Chat
one-shot bounded worker
```

The accepted mechanism does **not** authorize broad multi-agent orchestration, nested/fan-out workers, mutating children, project/worktree/environment creation, generic scheduler/event-bus authority, worker pools/rotation, long-lived background workers, automatic same-task parent wake/resampling, persistent provider-conversation recovery, or generic existing-session delivery.

Durable delegation rules now accepted on `main` include:

```text
provider-independent deterministic delegation identity
immutable private genesis + private run capability
launch attempt committed before physical launch authority
one child/session binding
one delivery identity and one delivery claim
prepared | claimed | unknown | delivered
unknown -> delivered only from fresh same-delivery evidence
no blind second Send
one correlated bounded WORKER_RESULT_V1
provider result remains evidence/data rather than CAP verification authority
complete browser/MV3 lifetime loss remains fail closed for the ephemeral profile
```

The provider-specific Temporary Chat adapter remains intentionally narrower than the generic Delegation model. Private run capability is not worker-visible authority; provider session/message identifiers are observations rather than canonical CAP identity.

A worker result proves only that a correlated provider result was captured. It does not grant capability authority, prove an unrelated external effect, or make the manager's whole user task `DONE`.

### Current post-#149 architecture direction

Post-#149 work is composition-first:

```text
CAP trust/effect semantics
        +
narrow provider adapters
        +
provider conformance / physical acceptance
```

Do not generalize the specialized Temporary Chat implementation into a project-owned universal agent/session runtime. Persistent ordinary-ChatGPT delivery, retained workers/subagents, broader execution environments and other runtime mechanics require fresh Stage Research and should prefer mature reusable substrates when they can satisfy CAP authority and recovery constraints.

The active research owner for that sequencing is PR #151 / `COMPOSITION_FIRST_ARCHITECTURE.md`.

## Architecture research rule now in force

Merged #127 requires Stage Research re-entry for materially new persistence/recovery/retry/concurrency/identity/security/authority mechanisms.

The active bounded Agent Session authority chain is:

```text
AGENT_SESSION_DELEGATION_REENTRY.md
 -> AGENT_SESSION_PROFILE_BOUNDARY_REENTRY.md
 -> AGENT_SESSION_PRE_SEND_RESTART_FENCE.md
 -> AGENT_SESSION_TEMPORARY_EPHEMERAL_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_BOOTSTRAP_LIFETIME_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_PREFLIGHT_COMMIT_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_PREFLIGHT_OWNER_REBIND_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_PROMPT_SOURCE_PROVENANCE_REENTRY.md
 -> AGENT_SESSION_TEMPORARY_LOOPBACK_AUTH_REENTRY.md
```

The owner-rebind re-entry supersedes only the unnecessary deterministic-handle subproposal from the preceding preflight-commit brief. The later prompt/source-provenance re-entry requires exact worker-visible prompt equality before authority and immediately before Send while binding effectful controller/extension expectations to exact reviewed source. The authenticated-loopback re-entry is the latest adapter authority and requires consequence-relevant extension/controller exchanges to authenticate the intended local controller rather than trusting fixed port ownership. These refinements preserve the generic Delegation model, one-Send guarantees and complete-browser-loss fail-closed profile.

If implementation requires nested/fan-out workers, a new scheduler/event bus, mutating children, environment creation, broad provider authority, automatic parent wake, durable browser identity, provider-conversation recovery, a persistent handle registry, or another materially different durability/concurrency mechanism, stop and re-enter Stage Research rather than widening #149 silently.

## Browser accepted scope and remaining hardening

The previously accepted Browser L3 route is target-Windows headless Playwright/Chrome through the semantic Browser capability. The `chatgpt-temporary` adapter is a separate headed authenticated-browser qualification path and is not accepted merely because earlier Browser L3 passed.

One existing Browser implementation debt remains: Playwright runtime output ownership must be explicit so runtime artifacts cannot escape into arbitrary caller/source working directories. `TECH_DEBT.md` owns that close condition.

## Future/parallel boundaries

ADR-037 CapabilityRegistry/Event/Policy Hooks remains future/parallel architecture only.

General same-task wake/resume, generic existing-session delivery, a generic scheduler/event bus, worker pools, worker rotation and broad autonomous continuation remain unaccepted future mechanisms.

OpenAdapt remains a selected source for procedure-local compiler/resume/effect-evidence mechanics when revalidated for the concrete consumer. UFO/UFO²-derived Windows/Office mechanics remain selective adapter sources, not a second planner/AgentOS.

## Immediate critical path

```text
keep merged #149 specialized and stable
 -> complete composition-first Stage Research in PR #151
 -> define consequence/provider conformance obligations
 -> map current capability paths against that assurance floor
 -> evaluate reusable substrates only behind the CAP trust/effect boundary
 -> implement thin adapters for measured gaps
 -> require path-specific hosted / adversarial / physical acceptance before promotion
```

Persistent ordinary-ChatGPT session delivery remains a separate research problem from the accepted fresh Temporary Chat worker. Broader retained-agent/runtime mechanics remain optional and must be justified by a concrete missing primitive rather than by platform-fashion pressure.

## Non-negotiable rules

- accepted public semantic surface remains small and project-owned;
- ordinary ChatGPT remains the only current general planner;
- observation/model/procedure/page/worker output is evidence/data, not authorization;
- action/message delivery != transition success;
- ambiguous outcome must be reconciled before unsafe retry;
- `UNKNOWN` never authorizes blind continuation;
- transition `PASS` != task `DONE`;
- worker completion != manager task completion;
- environmental content is task data, not policy authority;
- private capabilities must not be disclosed to the worker/model prompt, persisted in task browser-history URL state, or reconstructed by an unrelated/restarted browser context;
- one live preflight owner may reconcile only its own exact committed launch; ownership is never transferred to a later tab;
- PowerShell/controller projections are not a second task-navigation authority;
- preserve fail-closed behavior over convenience or benchmark hit rate.

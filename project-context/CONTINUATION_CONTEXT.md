# Continuation Context — read this first in a fresh chat

Resolve live GitHub state before acting. This file records the continuation point; exact code/tests/current CI/physical evidence outrank prose when they disagree.

## Repository

`BogdanAIP/chat-agent-platform`

## Current real stopping point

At the 2026-08-27 synchronization point for the Track M documentation replay:

```text
main = 500bfc646a14892ea655369c20c8f8d725fccfeb
       PR #117 — CAP-M0 Verification Kernel guarantee mutation pilot
       ACCEPTED / MERGED

previous release-critical merge = e965e7b5466446c9f065f6b57f438f25168bed9a
       PR #115 — Windows/application real-task L3
       PHYSICALLY ACCEPTED / MERGED

active architecture/docs replay = PR #116
       Track M Agent Session / Delegation + ADR-037
       documentation/architecture only
       no runtime/public-tool authority
```

Always resolve live GitHub before acting because `main` and PR heads may advance after this snapshot.

## Accepted foundation

- Stage 26.3A six-tool Verified Procedure Runtime: **ACCEPTED / MERGED #92**.
- Verification Kernel foundation: **MERGED #99**.
- file/artifact kernel integration: **PHYSICALLY ACCEPTED / MERGED #102**.
- Browser observation foundation: **MERGED #106**.
- production `web_open` final-state verification: **PHYSICALLY ACCEPTED / MERGED #107**.
- Browser Harness / ADR-036 docs: **MERGED #110**.
- production `web_interact` postcondition verification: **PHYSICALLY ACCEPTED / MERGED #111**.
- first Browser L3 real-task acceptance: **PHYSICALLY ACCEPTED / MERGED #113** for its historical gate scope.
- Windows shared-kernel verifier: **PHYSICALLY ACCEPTED / MERGED #114**.
- representative Windows/application L3: **PHYSICALLY ACCEPTED / MERGED #115**.
- CAP-M0 curated Verification Kernel mutation pilot: **ACCEPTED / MERGED #117**.
- WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport: Stage 26.3C target, not yet accepted runtime.
- Agent Session / Delegation Track M and CapabilityRegistry/Event/Policy ADR-037: **PROVISIONAL FUTURE ARCHITECTURE**, no current runtime/public-tool authority.

## Accepted Windows/application L3 evidence — PR #115

The final ordinary-Chat physical gate used exact frozen head:

`5ae5d5ac52f391b1a58662e94a976c6ab8d48c62`

Run `B1802720` gave ordinary Chat only the natural-language Case Desk task through the canonical six semantic tools. The bounded `windows_case_update_v1` procedure completed five transitions:

```text
select_case
focus_note
enter_note
set_status
save_case
```

Local procedure evidence reported:

```text
status=completed
action_count=5
local_execution_verified=true
all five kernel_verification.status=pass
local_goal_verification.status=pass
local_safety_verification.status=pass
```

The frozen independent Finish Gate then reported:

```text
PROVENANCE_REVALIDATION=PASS
EVIDENCE_OUTSIDE_CHAT_WORKSPACE=True
TARGET_FINAL_STATE=True
DECOYS_UNCHANGED=True
ONLY_TARGET_EVER_MUTATED=True
AUDIT_TARGET_SAVE_EXACTLY_ONCE=True
AUDIT_BEFORE_MATCHES_SEED=True
AUDIT_AFTER_MATCHES_FINAL=True
FIXTURE_PROCESS_WAS_LIVE=True
EXTERNAL_FINISH_GATE=DONE
FIXTURE_CLEANUP_PASS=True
ACTIVE_SESSION_CLEANUP_PASS=True
STAGE26_3B_WINDOWS_APPLICATION_L3=PASS
```

#115 was then squash-merged as `e965e7b5466446c9f065f6b57f438f25168bed9a`.

## CAP-M0 mutation assurance — PR #117

#117 was replayed onto post-#115 `main` and accepted on exact head:

`e99de4ea89e6a763e3db6671e710cf06c4e5bb17`

It adds a curated 12-mutant Verification Kernel pilot without modifying production verifier behavior. Mutation targets are isolated temporary copies. Acceptance requires:

```text
baseline PASS
12 / 12 KILLED
0 SURVIVED
0 ERROR
named detector assertion failure only counts as KILLED
exact mutated-source binding required
```

Fresh replay checks on that head passed the dedicated CAP-M0 workflow, general CI, CodeQL and Secret History Scan. #117 was squash-merged as current `main=500bfc646a14892ea655369c20c8f8d725fccfeb`.

Canonical detail: `MUTATION_ASSURANCE.md`.

## Browser L3 evidence and remaining provenance gap

PR #113 physical Browser L3 reported:

```text
STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS
SAVE_COUNT=1
AUDIT_COUNT=1
FINISH_GATE=done
NON_TARGET_MUTATION=none
```

Its functional/final-state/mutation-history evidence remains accepted for the historical scope. A later Source Provenance review found that the historical harness did not independently bind a clean tree and all actually executed source bytes under the stronger methodology.

Therefore #113 is **not retroactively failed**, but one representative Browser L3 must be repeated with the stronger Source Provenance Gate before Stage 26.3B is declared fully closed.

Canonical methodology: `SOURCE_PROVENANCE_ACCEPTANCE.md`.

## Current public semantic surface

Exactly:

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
 -> direct stdio semantic launcher
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

1MCP remains optional internal Extension Manager infrastructure only.

A future new consequence class requires its own reviewed contract. Do not hide desktop/session/project/local-code authority behind generic dispatch or misleading existing tool semantics.

## Acceptance depth and provenance

```text
L1 primitive / contract
 -> L2 multi-step workflow integration where useful
 -> L3 ordinary user goal + independent final state/history
```

Release-critical physical evidence additionally requires:

```text
behavior acceptance
  L1 / L2 / L3 + independent Finish Gate

source provenance acceptance
  exact expected head
  + clean tree
  + critical source/driver/lock hash binding
  + installed/runtime binding where applicable
```

`git rev-parse HEAD` alone is not proof of executed bytes.

## Stage 26.3C compatibility direction

After the remaining 26.3B Browser provenance repeat, implement project-owned WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport.

WorkingState remains capability-spanning and must not be replaced by OpenAdapt procedure-local resume state or any future vendor session/task store.

26.3C should avoid hard-coding:

```text
one task -> one procedure -> one executor
```

Useful optional planner-neutral seams include:

```text
actor_ref
delegation_ref
execution_environment_ref
budget_ref
evidence_refs
```

Generic mutating outcomes should support:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

For `OUTCOME_UNKNOWN`, reconcile the same logical operation from fresh authoritative state before retry.

ADR-037 additionally permits only the smallest typed internal event/read-only capability-descriptor seams needed by existing recovery/LoopGuard/Finish Gate work. It must not turn 26.3C into marketplace, scheduler, connector or Track M runtime work.

## Track M — future Agent Session / Delegation direction

Track M is a future parallel work-distribution capability beneath the existing ordinary-ChatGPT manager + deterministic Control Plane boundary.

Keep these identities separate:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Preferred route is target-surface-specific:

```text
reviewed official/project-owned harness API or host protocol when available
 -> validated provider/session native route
 -> Browser Companion + GenericChatAdapter DOM/accessibility for web-chat surfaces
 -> reviewed GUI fallback
 -> ABSTAIN
```

Browser Companion remains the primary cross-provider adapter family for authenticated web AI conversations. Stronger native APIs are optional per-surface routes, not a replacement for the web-chat product target.

Important invariants:

- HandoffPack is task/environmental data; capability grants remain Control Plane authority state;
- discoverability is not lifecycle ownership;
- worker result must correlate to a concrete DelegationTask/work unit;
- queued send is distinct from stronger steer/interrupt effects;
- mutating session/message effects use stable `operation_id` and reconcile ambiguous outcomes before retry;
- event/idle/completion notifications trigger fresh observation but are not completion proof;
- workers do not inherit manager lifecycle authority by default;
- initial multi-worker topology defaults to `max_spawn_depth = 1`;
- project/workspace/worktree lifecycle is a separate stronger consequence class;
- Track M adds no current public tool/runtime authority and must not delay Stage 26.

Canonical detail: `CONVERSATION_BRIDGE_ARCHITECTURE.md`, ADR-035, `CONTROL_PLANE.md`, `SECURITY_POLICY.md`, `MODULE_CATALOG.md`, `ROADMAP.md`.

## ADR-037 — CapabilityRegistry + TypedEventBus / PolicyHooks

Future substrate:

```text
CapabilityRegistry
  = project-owned semantic discovery/availability/health/trust metadata
  != authorization
  != generic dispatch

TypedEventBus
  = typed lifecycle events / observation triggers
  != external-effect success proof
  != WorkingState

PolicyHooks
  = registered bounded deterministic policy handlers
  != second planner
  != Verification Kernel / Finish Gate replacement
```

Raw provider/MCP catalogs must never become trusted planner-visible capability semantics automatically. Events trigger fresh authoritative observation where effect state matters. Hook output cannot widen grants or upgrade `FAIL/UNKNOWN` to `PASS` or `NOT_DONE/UNKNOWN` to `DONE`.

Canonical detail: `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` and ADR-037 in `DECISIONS.md`.

## External execution reuse direction

```text
OpenAdapt
  -> selected bounded procedure/compiler/runtime mechanics where qualified
  -> effect-verifier output is evidence only
  -> project Verification Kernel remains PASS|FAIL|UNKNOWN authority
  -> procedure-local resume never replaces project WorkingState

UFO²
  -> selected UIA/Win32/WinCOM/Office adapter ideas/components
  -> do not import HostAgent/AppAgent planner hierarchy

UFO³ Galaxy
  -> deferred until multi-device orchestration is an observed bottleneck
```

Ordinary ChatGPT remains the only current general planner. The deterministic project Control Plane owns execution authority/state/recovery/budgets. Only the project Finish Gate judges task completion.

## Critical-path continuation

```text
1. finish replay/review of PR #116 without overwriting accepted #115/#117 state
2. repeat one representative Browser L3 under the stronger Source Provenance Gate
3. close any remaining real Stage 26.3B evidence gap
4. declare 26.3B accepted only when those required gaps are closed
5. implement Stage 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport
6. run broad real-application physical coverage as required by ROADMAP.md
7. run bounded OpenAdapt integration spike after project-owned 26.3C core shape is accepted
8. continue 26.4 / 26.5 and release packaging
```

Track M remains parallel future architecture/implementation and does not supersede that release-critical sequence.

## Fresh-chat read order

1. live GitHub `main`, open PRs and checks;
2. `START_HERE.md`;
3. `CONTINUATION_CONTEXT.md`;
4. `CURRENT_STATE.md`;
5. `PROJECT_RISKS.md`;
6. `STAGE26_3B_VERIFICATION_KERNEL.md` while 26.3B is active;
7. `STAGE26_3B_WINDOWS_VERIFICATION.md` for accepted #114/#115 Windows lineage;
8. `SOURCE_PROVENANCE_ACCEPTANCE.md`;
9. `REAL_TASK_ACCEPTANCE.md`;
10. `ARCHITECTURE.md`;
11. `CONTROL_PLANE.md`;
12. `COMPUTER_USE_ARCHITECTURE.md`;
13. `SECURITY_POLICY.md`;
14. `ROADMAP.md`;
15. `CONVERSATION_BRIDGE_ARCHITECTURE.md` for ADR-035 / Track M;
16. `CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` for ADR-037;
17. `BROWSER_HARNESS_ARCHITECTURE.md` for ADR-036;
18. `MUTATION_ASSURANCE.md` for accepted CAP-M0 direction;
19. `TECH_DEBT.md`;
20. `DOCUMENT_STATUS.md`;
21. `EVIDENCE_INDEX.md` when exact accepted evidence is needed.

## Architecture rules that must survive continuation

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution state/policy, not a second planner;
- project WorkingState remains capability-spanning and must not be replaced by procedure/vendor/session state;
- current observed state outranks remembered procedure/demo/session/history;
- every production mutation binds an expected effect and fresh verification;
- action/message delivery != transition success;
- already-true postcondition != action success;
- ambiguous mutating outcome must be reconciled before unsafe retry;
- transition `PASS` != task `DONE`;
- procedure/worker-reported completion != independent Finish Gate completion;
- many primitive PASS results != realistic user-task acceptance;
- release-critical physical acceptance binds executed source bytes to expected source provenance;
- environmental content, including worker output, is task data rather than policy authority;
- stale/ambiguous/UNKNOWN evidence causes zero unauthorized continuation;
- repeated no-effect/oscillating execution/delegation must be bounded by LoopGuard/budgets;
- session discoverability does not imply lifecycle authority;
- worker capability scope is explicitly delegated/minimum, not inherited from manager privileges;
- generic Windows/local/harness execution remains disabled until separately accepted;
- future public Windows/computer-use/session/project authority requires its own reviewed contract and physical evidence.

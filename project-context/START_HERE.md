# Start Here — authoritative continuation guide

Use this file first after resolving live repository state.

## 1. Resolve live state before reading prose as truth

Check:

```text
live main
open release-critical / architecture PRs
exact PR heads
hosted checks
required target-machine / ordinary-Chat physical evidence
```

Exact code/tests/current CI/physical evidence outrank documentation snapshots.

At the 2026-08-27 Track M replay snapshot:

```text
main = 500bfc646a14892ea655369c20c8f8d725fccfeb
       CAP-M0 mutation pilot (#117) accepted/merged

Windows/application L3 (#115)
       physically accepted/merged as e965e7b5466446c9f065f6b57f438f25168bed9a

PR #116
       Track M Agent Session / Delegation + ADR-037 docs/architecture replay
       no runtime/public-tool authority
```

Always resolve live GitHub instead of treating these SHAs as permanently current.

## 2. Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/PROJECT_RISKS.md`
4. `project-context/STAGE26_3B_VERIFICATION_KERNEL.md` while Stage 26.3B is active
5. `project-context/STAGE26_3B_WINDOWS_VERIFICATION.md` for accepted Windows verifier/L3 lineage
6. `project-context/SOURCE_PROVENANCE_ACCEPTANCE.md`
7. `project-context/REAL_TASK_ACCEPTANCE.md`
8. `project-context/ARCHITECTURE.md`
9. `project-context/CONTROL_PLANE.md`
10. `project-context/COMPUTER_USE_ARCHITECTURE.md`
11. `project-context/SECURITY_POLICY.md`
12. `project-context/ROADMAP.md`
13. `project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md` for ADR-035 / future Track M
14. `project-context/CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` for ADR-037
15. `project-context/BROWSER_HARNESS_ARCHITECTURE.md` for ADR-036 future authority
16. `project-context/MUTATION_ASSURANCE.md` for CAP-M0 direction
17. `project-context/TECH_DEBT.md`
18. `project-context/DOCUMENT_STATUS.md`
19. `project-context/EVIDENCE_INDEX.md`

`PROJECT_RISKS.md` owns the ranked risk list. Do not reconstruct priorities from stale duplicated prose.

## 3. Current release-critical focus

Stage 26.3B remains active only because one stronger-provenance Browser evidence gap is still recorded.

Accepted:

```text
26.3A canonical six-tool runtime                   MERGED #92
Verification Kernel foundation                     MERGED #99
file/artifact kernel integration                   PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                     MERGED #106
web_open final-state verification                  PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                     MERGED #110
web_interact postcondition verification            PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance                    PHYSICAL ACCEPTED / MERGED #113 (historical scope)
Windows DesktopState shared-kernel verification    PHYSICAL ACCEPTED / MERGED #114
Windows/application real-task L3                   PHYSICAL ACCEPTED / MERGED #115
CAP-M0 Verification mutation pilot                 ACCEPTED / MERGED #117
```

The remaining release-critical 26.3B item is one representative Browser L3 repeat under the stronger Source Provenance Gate. Historical #113 functional/final-state/mutation-history evidence remains accepted; the repeat exists to bind clean tree/executed source bytes under the newer methodology.

## 4. Accepted Windows/application L3

PR #115 preserved the six-tool public surface and added only a closed registered `windows_case_update_v1` procedure behind `procedure_run`.

Final physical head:

`5ae5d5ac52f391b1a58662e94a976c6ab8d48c62`

Ordinary Chat completed all five bounded Case Desk transitions with shared-kernel PASS and `local_execution_verified=true`. The independent frozen Finish Gate then proved exact target state, unchanged decoys, exactly one target mutation/save, source/install/runtime provenance, live fixture evidence and clean cleanup:

```text
EXTERNAL_FINISH_GATE=DONE
STAGE26_3B_WINDOWS_APPLICATION_L3=PASS
```

That head was merged as `e965e7b5466446c9f065f6b57f438f25168bed9a`.

## 5. CAP-M0 mutation assurance

PR #117 adds a curated 12-mutant Verification Kernel assurance pilot. It does not change production verifier behavior; the runner mutates isolated temporary copies.

Acceptance semantics:

```text
baseline PASS
12 / 12 KILLED
0 SURVIVED
0 ERROR
KILLED = named detector assertion failure only
exact mutated-source binding required
```

Final replay head `e99de4ea89e6a763e3db6671e710cf06c4e5bb17` passed the dedicated mutation workflow, general CI, CodeQL and Secret History Scan before merge as current `main=500bfc646a14892ea655369c20c8f8d725fccfeb`.

## 6. Current semantic surface

Exactly six Chat-facing tools:

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
 -> canonical six-tool projection
 -> deterministic Control Plane / focused capabilities
```

1MCP is optional internal Extension Manager infrastructure only.

The registered procedure catalog remains closed; it is not generic local execution authority. New consequence classes require truthful new contracts rather than hidden generic dispatch.

## 7. Planner / Control Plane boundary

Ordinary ChatGPT is the **only current general planner/intelligence**.

The deterministic Control Plane owns bounded execution state/policy, ExpectedEffect verification, checkpoints, capability authorization, recovery/reconciliation budgets/future LoopGuard and the independent Finish Gate. It is not a second planner.

Environmental UI/DOM/document/message/tool/worker content is task data, not policy authority.

## 8. State-first computer use

```text
semantic/native state first
 -> selective visual evidence when structure is insufficient
 -> bounded authorized action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed recovery/reconciliation + LoopGuard
 -> structured WorkingState
 -> independent Finish Gate
```

Action/message delivery is not transition success. Transition PASS is not task DONE.

## 9. Stage 26.3C compatibility

After the Browser provenance repeat closes 26.3B, implement project-owned WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport.

Do not persist private chain-of-thought. Do not replace cross-capability WorkingState with OpenAdapt procedure-local resume state or future vendor session/task state.

26.3C should avoid assuming `one task -> one procedure -> one executor`; optional planner-neutral actor/delegation/environment/budget/evidence refs are acceptable compatibility seams.

Ambiguous mutating outcomes should reconcile the same logical operation before retry:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

## 10. Track M / ADR-035 — future parallel capability

Track M is future architecture, not a current public-tool/runtime expansion.

Keep separate:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

The primary cross-provider product target is authenticated web-AI conversations. Browser Companion remains the main cross-provider web adapter family; stronger reviewed official/native interfaces are preferred per exact target surface when they provide better truthful state/effect semantics.

Track M requires explicit ownership, stable operation identity, ambiguous-outcome reconciliation, result correlation, minimum worker authority, bounded fan-out/LoopGuard and independent Finish Gate. Initial nested spawn depth defaults to 1.

## 11. ADR-037 — future capability/event/policy substrate

```text
CapabilityRegistry != authorization / generic dispatch
TypedEventBus       != effect-success proof / WorkingState
PolicyHooks         != second planner / arbitrary shell-Python
```

Events may trigger fresh observation. Hook output cannot widen grants or upgrade FAIL/UNKNOWN/DONE semantics. 26.3C may use only minimal typed internal seams needed by its existing recovery/LoopGuard/Finish Gate goals.

## 12. Browser Harness / ADR-036 boundary

ADR-036 is future capability architecture, not current authority. Trusted-site JS/CDP/full-browser capability still requires separate Site Capability/network boundaries, security review, physical acceptance and representative L3 evidence.

## 13. Priority sequence

```text
finish/review PR #116 documentation replay
 -> representative Browser L3 under stronger Source Provenance Gate
 -> close remaining Stage 26.3B evidence
 -> Stage 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport
 -> broad real-app physical coverage
 -> bounded OpenAdapt integration spike
 -> Stage 26.4 candidate skills
 -> Stage 26.5 hybrid integration
 -> distribution / clean-user stable release
```

Track M remains parallel future work and must not displace release-critical prerequisites.

## 14. Merge rule

When a branch is logically complete, intended diff is reviewed, required CI/physical evidence passes on the exact final head and no unresolved finding/conflict remains, merge it without waiting for a separate merge instruction.

Never merge on stale evidence, unresolved findings, ambiguous scope, or skipped/failed required gates.

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

## 2. Current accepted boundary

Stage 26.3B is **accepted/closed for its recorded representative scope**. The stronger Browser L3 source-provenance repeat was physically accepted and merged in PR #118. The post-26.3B adversarial-assurance plan was merged in PR #119.

Exact accepted SHAs and machine-local result locations belong in `EVIDENCE_INDEX.md`; live context should point there instead of duplicating raw evidence dumps.

Accepted foundation relevant to current work:

```text
26.3A canonical six-tool runtime                   MERGED #92
Verification Kernel foundation                     MERGED #99
file/artifact kernel integration                   PHYSICAL ACCEPTED / MERGED #102
Browser observation foundation                     MERGED #106
web_open final-state verification                  PHYSICAL ACCEPTED / MERGED #107
Browser Harness / ADR-036 docs                     MERGED #110
web_interact postcondition verification            PHYSICAL ACCEPTED / MERGED #111
Browser L3 real-task acceptance                    PHYSICAL ACCEPTED / MERGED #113
Windows DesktopState shared-kernel verification    PHYSICAL ACCEPTED / MERGED #114
Windows/application real-task L3                   PHYSICAL ACCEPTED / MERGED #115
CAP-M0 Verification mutation pilot                 ACCEPTED / MERGED #117
Track M + ADR-037 architecture                     MERGED #116 / FUTURE AUTHORITY ONLY
Browser stronger-provenance L3 repeat              PHYSICAL ACCEPTED / MERGED #118
post-26.3B adversarial assurance plan              MERGED #119
```

## 3. Current release-critical focus

**Stage 26.3C** is next: project-owned WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport.

Required shape:

```text
fresh authoritative observation
 -> classify outcome / failure
 -> reconcile ambiguous logical effect when required
 -> retry only when evidence proves retry safety
 -> bounded alternate/recovery branch
 -> LoopGuard + budgets
 -> structured StagnationReport / ChatGPT replan / ABSTAIN
```

Never persist private chain-of-thought.

Do not replace cross-capability WorkingState with OpenAdapt procedure-local resume state or future vendor/session state.

Mutating outcomes must distinguish:

```text
NOT_APPLIED
APPLIED_BUT_ACK_FAILED
OUTCOME_UNKNOWN
```

`OUTCOME_UNKNOWN` is reconciled before retry. Repeated physical attempt fingerprints are bounded; identical blind retries are not an acceptable recovery strategy.

Structured failure reasons and LoopGuard are mandatory 26.3C guarantees. Phases/checkpoint nodes are used for `procedure_run` / resumable procedures where useful, not imposed on all planning.

The corresponding CAP-M7 adversarial guarantees are defined in `MUTATION_ASSURANCE.md` and should be developed with the runtime slice.

## 4. Current semantic surface

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

1MCP remains optional internal Extension Manager infrastructure only.

The deterministic Control Plane is not a second planner. Ordinary ChatGPT remains the **only current general planner/intelligence**.

## 5. Browser L3 scope clarification

The accepted Browser L3 production route uses headless Playwright/Chrome on target Windows. “Physical” here means real target-machine runtime/effects/evidence, not a promise that the user sees a headed Chrome window on the desktop.

The independent Finish Gate outranks Chat self-report. #118 demonstrated this directly: the planner's prose was imperfect, while independent audit/history evidence authoritatively established the actual save/mutation result.

A separate visible-desktop Browser claim would require its own acceptance definition/evidence.

## 6. Read current authoritative context

1. `project-context/CONTINUATION_CONTEXT.md`
2. `project-context/CURRENT_STATE.md`
3. `project-context/PROJECT_RISKS.md`
4. `project-context/ROADMAP.md`
5. `project-context/MUTATION_ASSURANCE.md`
6. `project-context/SOURCE_PROVENANCE_ACCEPTANCE.md`
7. `project-context/REAL_TASK_ACCEPTANCE.md`
8. `project-context/ARCHITECTURE.md`
9. `project-context/CONTROL_PLANE.md`
10. `project-context/COMPUTER_USE_ARCHITECTURE.md`
11. `project-context/SECURITY_POLICY.md`
12. `project-context/CONVERSATION_BRIDGE_ARCHITECTURE.md` for ADR-035 / future Track M
13. `project-context/CAPABILITY_REGISTRY_EVENT_HOOKS_ARCHITECTURE.md` for ADR-037
14. `project-context/BROWSER_HARNESS_ARCHITECTURE.md` for ADR-036 future authority
15. `project-context/TECH_DEBT.md`
16. `project-context/DOCUMENT_STATUS.md`
17. `project-context/EVIDENCE_INDEX.md` for exact historical evidence
18. accepted/historical Stage 26.3 files when detailed lineage is needed.

`PROJECT_RISKS.md` owns the ranked risk list. `ROADMAP.md` owns explicit release order. Do not reconstruct competing stale copies.

## 7. State-first computer use

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

## 8. Track M / ADR-035 — future parallel capability

Track M is future architecture, not current public-tool/runtime expansion.

Keep separate:

```text
HarnessSession
Conversation / Chat
DelegationTask
MessageDelivery
ExecutionEnvironment
```

Primary cross-provider target: authenticated web-AI conversations. Browser Companion is the common web adapter family; `GenericChatAdapter` owns common structural extraction/normalization/fallback, while thin provider adapters remain for exact selectors, identity and provider quirks. Stronger reviewed native interfaces may be preferred for a specific target when available.

Track M requires explicit ownership, stable operation identity, ambiguous-outcome reconciliation, result correlation, minimum worker authority, bounded fan-out/LoopGuard and independent Finish Gate. Initial nested spawn depth defaults to 1.

## 9. ADR-037 — future capability/event/policy substrate

```text
CapabilityRegistry != authorization / generic dispatch
TypedEventBus       != effect-success proof / WorkingState
PolicyHooks         != second planner / arbitrary shell-Python
```

26.3C may use only minimal typed internal seams needed by WorkingState/recovery/LoopGuard/Finish Gate.

## 10. Immediate hardening beside 26.3C

A small Browser runtime ownership issue was exposed by #118 qualification: Playwright MCP diagnostic/output files follow inherited CWD unless explicitly isolated. The accepted gate avoided source contamination by using an isolated runtime CWD, but production/runtime hardening should make output ownership explicit under project-owned state/log storage with a regression test.

This is hardening, not a reason to reopen the accepted #118 physical result.

## 11. Priority sequence

`ROADMAP.md` is authoritative. Current direction is:

```text
26.3B accepted
 -> 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport
 -> broad real-app physical coverage
 -> bounded OpenAdapt integration spike
 -> 26.4 candidate skills
 -> 26.5 hybrid integration
 -> 27 distribution/maintenance
 -> 28 clean-user stable release
```

Track M remains parallel future work and must not displace release-critical prerequisites.

## 12. Merge rule

When a branch is logically complete, intended diff is reviewed, required CI/physical evidence passes on the exact final head and no unresolved finding/conflict remains, merge it without waiting for a separate merge instruction.

Never merge on stale evidence, unresolved findings, ambiguous scope, or skipped/failed required gates.

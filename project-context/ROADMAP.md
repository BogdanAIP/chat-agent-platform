# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general intelligence/planning layer**, while the local platform becomes a deterministic execution system with bounded capabilities, persistent verified state, authorization, recovery, procedural memory and selective specialist perception.

```text
ordinary ChatGPT
  = task understanding / strategy / procedure selection / novel adaptation

Chat Agent Platform
  = scoped Files / Browser / Windows capabilities
  + semantic/native state observation
  + selective visual grounding
  + deterministic execution Control Plane
      TaskState / WorkingState
      ProgramGraph progression
      policy / authorization
      ExpectedEffect + transition verification
      checkpoints
      typed recovery + LoopGuard
      StagnationReport escalation
      action/time/resource budgets
      independent Finish Gate
      safety/policy gate
  + verified procedural memory
  + versioned Skill / Procedure Lineage
  + optional specialist proposals
  + future optional local general planner research
```

The local deterministic Control Plane is not a second planner. It may advance an already-selected known procedure through independently authorized and verified transitions. Novel strategy and incompatible live state escalate to ordinary ChatGPT.

Canonical contracts:

- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`
- `AVO_LONG_HORIZON_ARCHITECTURE.md` for the reviewed long-horizon lineage/stagnation extension
- `CONVERSATION_BRIDGE_ARCHITECTURE.md` for non-release-critical future Track M multi-chat/session handoff

Accepted public semantic tools remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal transport is `semantic + direct-stdio`; 1MCP is an optional internal Extension Manager, not a baseline dependency.

---

# Completed foundation

## Stage 21 — Native ChatGPT <-> local MCP — DONE

Secure MCP Tunnel + official tunnel-client + real local MCP round trip accepted.

## Stage 22 — universal core reduction — DONE

Old generic agent/gateway core removed from active architecture.

## Stage 23 — quality-first module selection — DONE

Focused capability/upstream selection and promotion policy accepted.

## Stage 24 / 24.1 — typed semantic file/browser + direct tunnel — DONE

Historical five-tool file/browser foundation accepted for its tested scope. It no longer defines the current public inventory.

## Stage 25 / 25.1 / 25.2 — Browser semantic + local vision — DONE

Structure first, specialist proposal only, deterministic authorization, ABSTAIN on unresolved evidence.

## Stage 26.1A-E / 26.2A-E — Windows capability foundation — DONE

Accepted work includes OpenAdapt qualification, bounded capture/executor, window-scoped UIA, production Windows runtime, `DesktopState`, local Grounder, deterministic UIA->vision routing and the first isolated VS Code real-application E2E.

Exact physical evidence belongs in `EVIDENCE_INDEX.md` and historical stage documents.

## Transport Supervisor v1 — ACCEPTED / MERGED #94

Persistent desired state/runtime ownership, layered health, bounded recovery and console-free Scheduled Task persistence are accepted infrastructure. PR #100 later qualified the low-power Manual/Automatic operating model and final ordinary-Chat ON/OFF route gates.

## Stage 26.3A — canonical six-tool Verified Procedure Runtime — ACCEPTED / MERGED #92

Exact physically accepted runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Merged integration commit:

```text
43ad61384e966ecf089e69a95c166d41da949ebe
```

Physical ordinary-Chat evidence proved one long-horizon task using all six semantic tools, real working-memory files, browser recovery, one completed three-transition `procedure_run`, independent result reread and a second zero-action `ABSTAIN` on protected-target overwrite.

This establishes the first real long-horizon deterministic procedure boundary. It does not authorize arbitrary shell/Python or broad Windows consequences.

## NVIDIA AVO long-horizon architecture review — REVIEWED / PROMOTED

The 2026-08-25 review of NVIDIA Agentic Variation Operators and NVIDIA's related agent-stack security guidance was promoted through ADR-034 and `AVO_LONG_HORIZON_ARCHITECTURE.md`.

Supported project mechanisms:

```text
durable structured state across context boundaries
LoopGuard -> structured StagnationReport -> ChatGPT replan
versioned Skill / Procedure Lineage
bounded candidate improvement grounded in objective execution feedback
above proposes; deterministic infrastructure below decides
```

The review does **not** change the release order or make the local Control Plane a second planner. It also does not treat NVIDIA's ARC-AGI-3 public-set result as proof for screenshot-first GUI control; that AVO configuration used an exact text-grid observation interface.

---

# Stage 26 — current release-critical sequence

Explicit release order:

```text
26.2E real application E2E                         ACCEPTED
 -> 26.3 Verified Procedure Runtime / Control Plane ACTIVE
    -> 26.3A six-tool verified procedure runtime   ACCEPTED
    -> 26.3B Verification Kernel + Finish Gate     ACTIVE
    -> 26.3C WorkingState + typed recovery + LoopGuard
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 Distribution & Maintenance
 -> 28 Clean User E2E / stable release
```

The 2026-08-24 Stage 26.3A GUI-agent research is promoted through `COMPUTER_USE_ARCHITECTURE.md` and ADR-032/033. The 2026-08-25 AVO review enriches 26.3C/26.4 through ADR-034 without inserting a new stage.

## 26.3B — Verification Kernel + independent Finish Gate — ACTIVE

Primary objective: make verification a reusable cross-capability contract instead of stage-specific ad hoc checks.

The first active foundation slice introduces:

```text
ObservationRef / ObservationSnapshot
capability + subject + observation-stream identity
same-stream monotonic freshness
ExpectedEffect / bounded declarative postconditions
PASS | FAIL | UNKNOWN transition result
independent Finish Gate
separate task-success and safety/policy evidence
```

Freshness does not rely on wall-clock plausibility. Verification requires evidence from the same observation stream/capability/subject and a strictly higher sequence; mismatched streams, stale state, ambiguity or incomplete required evidence yield `UNKNOWN` rather than guessed success.

The Finish Gate is task-level and independent of planner confidence or action-history plausibility. `candidate_done` is only a proposal.

Minimum task completion dimensions:

- requested goal predicates hold;
- user constraints remain satisfied;
- required dynamic/authoritative sources are fresh/reconciled;
- no required ambiguity or confirmation remains unresolved;
- safety/policy predicates hold.

Task-success, unresolved completion requirements and safety evidence remain distinct even if evaluated at the same completion boundary.

The foundation slice is **not Stage 26.3B acceptance**. Remaining work before acceptance:

```text
file/artifact normalized observation adapter
migrate verified_workspace_artifact_v1 onto shared kernel
browser URL/document/control/result verification adapter
process/window/application verification adapter
cross-capability task predicates where real procedures require them
physical acceptance once shared verification changes a production action/procedure path
```

Non-negotiable:

```text
action delivered != transition verified
transition verified != task completed
current observed state > remembered procedure state
stale / mismatched-stream / ambiguous / UNKNOWN -> zero unauthorized continuation
```

Active implementation contract: `STAGE26_3B_VERIFICATION_KERNEL.md`.

AVO-style iterative improvement is intentionally **not** implemented before this stage because candidate evolution without objective correctness/finish verification would optimize an unreliable signal.

## 26.3C — WorkingState + Typed Recovery + LoopGuard

Generalize long-horizon state and recovery before broad GUI authority.

### WorkingState v1

Persist only structured operational state:

```text
user constraints
subgoals / progress vector
verified completed achievements
authoritative facts + provenance + freshness
open ambiguities/questions
evidence references
expected/observed state deltas
retry/recovery history
action/time/resource budgets
```

Never persist private chain-of-thought. AVO's demonstrated value of persistent memory is adopted as durable structured evidence/state, not unrestricted model-reasoning persistence.

### Initial typed recovery vocabulary

```text
target_missing
target_ambiguous
stale_state
action_no_effect
partial_effect
unexpected_dialog
navigation_changed
tool_unavailable
permission_denied
unsafe_transition
external_dynamic_change
```

Default ladder:

```text
re-observe
 -> re-resolve
 -> retry only with new evidence
 -> alternate admitted modality
 -> predeclared recovery branch
 -> ChatGPT replan / clarification / ABSTAIN
```

### LoopGuard

Track repeated/no-progress behavior through:

```text
state + subgoal + action fingerprint
no-effect count
action-family retry count
oscillation A -> B -> A -> B
subgoal/global budgets
recovery escalation level
verified progress vector
```

Identical state/action repetition without new evidence or verified progress must terminate/escalate rather than loop.

### StagnationReport

When bounded recovery is exhausted, LoopGuard should emit a compact structured report rather than only a generic failure:

```text
StagnationReport
  task / subgoal identity
  verified progress vector
  repeated state/action fingerprints
  no-effect / retry / oscillation counters
  attempted recovery classes
  fresh evidence references
  exhausted + remaining budgets
  admitted alternatives already tried
  unresolved failure / ambiguity
```

Normal path:

```text
LoopGuard detects stagnation
 -> stop repeated effects
 -> StagnationReport
 -> ordinary ChatGPT chooses novel strategy
 -> new proposal returns through normal authorization
```

The report contains operational evidence summaries, never private hidden reasoning. This adopts the useful supervisory role demonstrated by AVO without adding a second local general planner.

## 26.4 — Human Demo -> Transferable Verified Candidate Skill

Use qualified OpenAdapt Capture/Flow substrate, but compile demonstrations into flexible verified procedure guidance rather than macro replay.

Target representation:

```text
demonstration
 -> subtask goals
 -> verifiable completion criteria
 -> advisory target/action evidence
 -> applicability/preconditions
 -> project CANDIDATE
```

Replay rule:

```text
live state > demonstration
```

Historical coordinates/action sequence are not executable authority. One demonstration never becomes permanent trust automatically.

### Skill / Procedure Lineage

A reusable skill is versioned evidence, not one mutable opaque blob.

Target lineage fields:

```text
skill_id
candidate_id
parent candidate(s)
procedure/version identity
source = demonstration | ChatGPT_revision | human_revision | migration
applicability/preconditions
evaluation suite / task variants
verifier evidence references
objective metrics / success counters
failure summary
promotion state
```

Rules:

- lineage does not grant action authority;
- a trusted parent does not automatically make a child trusted;
- failed/unverified candidates may be retained as compact diagnostics but not trusted executable skills;
- current live state outranks historical lineage;
- promotion requires independent evidence across relevant regression/variant cases.

### Bounded candidate-improvement loop

After 26.3B/C foundations exist:

```text
candidate
 -> execute admitted evaluation task
 -> re-observe
 -> verify correctness / goal predicates
 -> measure objective metrics
 -> classify failures
 -> ChatGPT proposes revision
 -> new candidate in lineage
 -> regression / variant evaluation
```

Useful metrics may include verified success rate, verified recovery rate, action count, latency where meaningful, abstention correctness, regression count and resource cost. No scalar score replaces hard correctness/safety/Finish Gate predicates.

Promotion:

```text
CANDIDATE
 -> same/near-state replay evidence
 -> changed-state/task variant evidence
 -> objective comparison against parent/baseline
 -> trusted reusable
 -> stale / quarantined / disabled as evidence degrades
```

Raw human demonstration privacy/retention/redaction/encryption policy is required before broad product capture.

## 26.5 — Hybrid Computer-Use Integration

Purpose: converge accepted Browser/Windows capability-specific mechanisms on common long-horizon contracts without creating a universal raw-tool gateway.

Targets:

```text
ObservationEnvelope references across Browser/Windows
capability-aware semantic-vs-GUI routing
common grounding proposal identity/confidence/ambiguity fields
semantic/native state first
selective screenshot/ROI evidence
cross-app typed fact provenance
verified skill lineage applicability across real apps
StagnationReport / recovery across capability boundaries
component-level interaction regression corpus
recovery/noisy-state E2E
```

The router must choose capabilities from explicit preconditions/evidence. Tool availability alone is not a routing decision.

A truthful Windows/computer-use public Chat-facing surface still requires a separate ADR/schema/security review and physical ordinary-Chat acceptance under ADR-024. Stage 26.5 does **not** promise exact future tool names and does not automatically expand the accepted six-tool surface.

---

# Evaluation track for computer use

External benchmarks are useful diagnostic/evaluation sources, not automatic release gates.

Layer evaluation as:

```text
component/primitive diagnostics
 -> capability integration tests
 -> noisy/recovery fixtures
 -> long-horizon verified procedures
 -> skill-lineage regression/variant suites
 -> selected reproducible external benchmark runs
```

Reference mechanisms:

- ComponentBench — component-level route/action diagnostics and observation-space sensitivity;
- WebArena / BrowserGym — functional browser correctness and normalized benchmark harness ideas;
- OSWorld 2.0 — long-horizon freshness, hidden state, multi-source reconciliation and completion collapse;
- OSWorld-Noisy — recoverable interruptions;
- MobileWorldSafety — environmental injection and final-state safety predicates;
- NVIDIA AVO — persistent state, stagnation supervision and iterative candidate improvement grounded in execution feedback/lineage; architecture reference only, not a project release benchmark.

Never tune production architecture around benchmark-specific tricks without a general project-owned invariant.

---

# Optional internal Extension Manager track

1MCP remains a replaceable internal manager/aggregator for future third-party MCP backends.

```text
canonical project-owned semantic surface
 -> typed adapter / capability policy
 -> optional 1MCP Extension Manager
 -> selected third-party MCP backend
```

Backend availability is not trust, routing authority or action authorization. Raw catalogs are not automatically published to ChatGPT.

---

# Optional Research Track R — Specialized reasoning

Specialized models may later propose structured choices/confidence/ABSTAIN after enough verified procedure-state data exists. They remain non-authorizing and do not replace deterministic verifiers when stronger predicates exist.

# Optional Future Track P — Local Planner / Offline Autonomy

A local general planner remains in the long-term roadmap but is **not part of the current release-critical path**.

Earliest prerequisite: verified long-horizon procedure/WorkingState data plus a measured reason to move planning local.

```text
P0 shadow planner
   sees structured goal/state/procedure evidence
   -> proposal only
   -> no authorization / no actuation
   -> benchmark against ordinary ChatGPT

P1 bounded subtask planner
   -> explicitly scoped workloads
   -> deterministic Control Plane remains authoritative

P2 optional local general-planner mode
   -> only after parity/safety/resource evidence
   -> never silently replaces ChatGPT default
```

AVO demonstrates that richer agent harnesses can materially improve long-horizon work, but it does not by itself justify promoting Track P. Any future AVO-like local planner remains on the proposal side of the same deterministic authorization/verifier boundary.

No planner may grant itself execution authority.

# Parallel Track M — multi-chat orchestration / Conversation Bridge

Track M is a separate future upper/work-distribution layer. It is **not** part of the Stage 26 release-critical sequence, does not replace ordinary ChatGPT as the current general planner, and does not change the accepted six-tool public surface.

Canonical detail: `CONVERSATION_BRIDGE_ARCHITECTURE.md` and ADR-035.

The first problem is not "many agents". It is a verified transport boundary between the current manager ChatGPT and one authenticated worker chat.

Target placement:

```text
ordinary ChatGPT Manager
        |
        v
WorkingState / HandoffPack
        |
        v
Deterministic Control Plane
        |
        v
Conversation Bridge
        |
        v
project-owned Browser Companion in user browser
        |
        +----> ChatGPT worker conversation
        +----> future Claude/Gemini adapters
```

The Browser Companion exists because the current accepted Browser backend is isolated/headless and is not the user's already-authenticated browser session.

Track M reuses the existing state-first and verification rules:

```text
observe worker session
 -> bind ExpectedEffect
 -> authorize one bounded submit_message
 -> re-observe exact conversation/message state
 -> verify PASS | FAIL | UNKNOWN
 -> observe fresh settled worker response
 -> record selected result/evidence in WorkingState
 -> ordinary ChatGPT decides the next strategy
```

Target data contracts:

```text
ConversationSnapshot
  stable platform/session/conversation/message identity
  active branch
  content hashes
  generation state
  adapter/provenance/freshness

HandoffPack
  task/subgoal
  user constraints
  verified completed state
  authoritative facts + provenance/freshness
  open questions
  artifact/evidence refs
  selected context + recent messages
  context budget
```

Do not use whole-transcript Markdown replay as the primary memory model. Full conversation history is evidence and may be retrieved when needed; `WorkingState` remains the durable operational source for task progress.

Platform-native/private session APIs may be optional read fast paths only. Required fallback order remains:

```text
validated platform-native read
 -> DOM / accessibility / structural state
 -> selected GUI / visual fallback
```

Credentials stay inside the browser companion. Cookies/bearer tokens/private auth headers are never exported to the planner, MCP payload or WorkingState.

Suggested future sequence after the relevant state/verification foundations exist:

```text
M0 ConversationSnapshot + adapter contracts / fixtures
 -> M1 read-only ChatGPT Browser Companion observer
 -> M2 one Manager ChatGPT -> one Worker ChatGPT verified handoff E2E
 -> M3 HandoffPack + WorkingState integration / response monitoring
 -> M4 explicit multi-worker task/session ownership
 -> M5 optional Claude/Gemini/other adapters
```

CtxPort may be reused selectively under MIT terms for implementation mechanisms such as adapter registry structure, ChatGPT active-branch linearization, message flattening, optional fetch-by-id and dynamic-page observation. CtxPort itself, its clipboard/UI/export workflow and Markdown bundle formats are not product/runtime dependencies.

Multiple worker chats must not be introduced before the one-manager/one-worker path has explicit identity, delivery verification, response freshness, bounded failure/recovery and physical user-browser evidence.

---

# Stage 27 — Distribution & Maintenance

Installer/update/repair/doctor/uninstall/rollback/restart recovery/key rotation/artifact validation/lifecycle UI. Release-grade Python/model/OpenAdapt reproducibility is required.

# Stage 28 — Clean User E2E / first stable release

Fresh-user operation without git checkout or developer-only PowerShell/Python setup, through the accepted product capability surface.

---

# Cross-cutting invariants

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane is execution-state/policy machinery, not a second planner;
- accepted public surface remains small and project-owned;
- semantic/native state precedes pixels when reliable;
- visual evidence is selective, bound to current state and non-authorizing;
- every mutation has an expected effect and fresh post-action verification;
- transition PASS is not task DONE;
- only an independent Finish Gate confirms task completion;
- WorkingState stores structured operational facts/provenance/freshness, never private reasoning;
- repeated no-effect/oscillating actions are bounded by LoopGuard;
- LoopGuard stagnation escalation produces structured evidence for the planner rather than silently granting the local runtime new strategic freedom;
- Skill / Procedure Lineage is evidence and version history, not authority;
- candidate skill promotion requires independent verifier/regression evidence;
- environmental UI/DOM/tool content is untrusted data, not policy authority;
- task-success and safety/policy verification are separate;
- current observed state outranks procedure/demo/history/lineage;
- generic Windows code execution remains disabled/unreachable;
- normal semantic route does not require optional 1MCP;
- Track M worker conversations are external environmental actors/data sources and cannot grant capability or policy authority;
- Conversation Bridge credentials remain inside the browser-companion boundary;
- preserve exact physical evidence heads in `EVIDENCE_INDEX.md`.

# Merge policy

A logically complete branch with reviewed intended diff, passing required CI/physical gates and no unresolved findings should be merged without waiting for a separate merge command.
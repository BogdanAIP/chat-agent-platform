# Current State

## Repository-state rule

Always resolve live `main` and relevant PR heads before new work. Exact code/tests/current CI/physical evidence outrank prose.

## Operating constraint

Use ordinary ChatGPT plus GitHub and the project's local/connected tools. Do not use Codex or ChatGPT Work resources unless the user explicitly requests them.

## Product boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. The local platform owns deterministic execution state/policy through the Control Plane, not a second general-planning brain.

```text
ordinary ChatGPT
  task interpretation / strategy / procedure selection / novel adaptation
        |
        v
OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> canonical six-tool semantic projection
        |
        v
local deterministic Control Plane + focused capabilities
```

The Control Plane may maintain TaskState/WorkingState, advance a selected known procedure through already-defined transitions, authorize each consequence, verify effects, apply typed bounded recovery/LoopGuard, enforce budgets and independently verify completion. New strategy remains ChatGPT's responsibility.

Canonical architecture:

- `CONTROL_PLANE.md`
- `COMPUTER_USE_ARCHITECTURE.md`

## Accepted public semantic surface

The normal `semantic` route exposes exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

There is no runtime/profile/tray choice between five and six tools. The private historical five-capability file/browser implementation remains internal only.

The startup guard refuses READY unless live `tools/list` is exactly the six canonical names.

## Normal transport vs optional extensions

Normal semantic transport is direct stdio and does not depend on 1MCP.

```text
ordinary ChatGPT
 -> Secure MCP Tunnel
 -> official tunnel-client
 -> semantic launcher
 -> six canonical tools
```

Persistent tunnel identity is neutral platform state:

```text
%LOCALAPPDATA%\ChatAgentPlatform\state\tunnel.json
```

Legacy `local-1mcp.yaml` is migration fallback only for an already accepted tunnel id. 1MCP remains an optional internal Extension Manager for third-party backends and cannot automatically expose raw tools or grant authority.

---

# Accepted foundation

## Stage 24 / 24.1 — typed semantic file/browser + direct tunnel — ACCEPTED

Historical five-tool semantics are accepted foundation only; they do not define the current public inventory.

## Stage 25 / 25.1 / 25.2 — Browser semantic + local vision — ACCEPTED

Accepted invariant: semantic/native structure first, visual proposal only for reviewed fallback, deterministic authorization, ABSTAIN on unresolved evidence.

## Stage 26.1A-E / 26.2A-E — Windows capability foundation — ACCEPTED

Accepted work includes OpenAdapt qualification, bounded capture/executor, window-scoped UIA, production Windows runtime, `DesktopState`, native Grounder, deterministic UIA->vision routing and one isolated VS Code real-application E2E.

This is scoped evidence, not universal Windows accuracy.

## Transport Supervisor v1 — ACCEPTED / MERGED #94

Persistent desired state/runtime ownership, console-free Windows persistence, layered health and bounded route recovery are maintained product infrastructure.

## Stage 26.3A — canonical six-tool verified procedure runtime — ACCEPTED / MERGED #92

Exact physically accepted runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Merged main integration commit:

```text
43ad61384e966ecf089e69a95c166d41da949ebe
```

Physical ordinary-Chat acceptance proved:

```text
profile = semantic
binding = direct-stdio
public tools = 6
1MCP_REQUIRED = false
runtime_ready = true
mcp_ready = true
tunnel_ready = true
conflict = false
```

One long-horizon ordinary-Chat task used all six semantic tools, a reread working ledger, 16 content pages, 12 analyzed systems/benchmark groups and recovered from one invalid browser interaction. `procedure_run` then completed the bounded three-transition artifact procedure, followed by independent result read. A second call on the same target returned `ABSTAIN`, `action_count=0`, `target_already_exists`, and an independent reread proved zero overwrite.

Exact task ids/SHA/locator remain in `EVIDENCE_INDEX.md`.

## Stage 26.3A GUI-agent research — REVIEWED / PROMOTED TO ARCHITECTURE

The `gui-agent-research.md` artifact from the accepted physical session was independently reviewed against public sources on 2026-08-24. The core findings were confirmed and promoted into `COMPUTER_USE_ARCHITECTURE.md`, ADR-032 and ADR-033.

Verified external mechanisms included:

- ComponentBench observation/action-space sensitivity and component diagnostics;
- OSWorld 2.0 long-horizon state/freshness/verification failures;
- OSWorld-G/Jedi grounding decomposition;
- UI-Mate demonstration-to-subtask workflows with live replanning;
- StateAct state-first hybrid execution and independent finish gate;
- MementoGUI selective working/episodic memory;
- HiViG pre-execution visually grounded critique;
- WebArena/BrowserGym functional evaluation/harness normalization;
- ENVS/OSWorld-Noisy verified recovery under interruptions;
- Hybrid GUI-MCP capability-routing/context lessons;
- MobileWorldSafety environmental-injection/final-state safety evaluation.

The research did **not** authorize unrestricted code access, screenshot-only control, raw backend catalogs, learned memory/router components, generic tool dispatch or new public Windows tool names.

---

# Active release-critical work

## Stage 26.3B — Verification Kernel + independent Finish Gate — ACTIVE

The first implementation slice is now active on a dedicated branch/PR and introduces the internal reusable verification contract without changing the accepted public semantic surface or action-delivery authority.

Implemented in the foundation slice:

```text
ObservationRef / ObservationSnapshot
ExpectedEffect + bounded declarative predicates
same-subject fresh re-observation by monotonic sequence
PASS | FAIL | UNKNOWN transition verification
independent Finish Gate
separate task-success and safety/policy results
```

This is more specific than the former generic "advanced verifier library" description and is not yet Stage 26.3B acceptance.

Remaining Stage 26.3B integration targets:

```text
file/artifact observation adapter + procedure migration
browser URL/document/control/final-state verification
process/window/application verification
cross-capability completion predicates where required
physical acceptance once shared verification changes production procedure/action behavior
```

Task completion must verify fresh goal predicates, constraints, required source freshness/reconciliation, unresolved ambiguity/confirmation state and safety/policy predicates.

Rules:

- action delivery != transition success;
- transition PASS != task DONE;
- current observed state outranks remembered procedure/demo/history;
- stale/ambiguous/UNKNOWN -> zero unauthorized continuation;
- task-success verification and safety/policy verification remain separate dimensions;
- `candidate_done` is only a planner proposal and cannot self-authorize completion.

Canonical active implementation contract: `STAGE26_3B_VERIFICATION_KERNEL.md`.

## Stage 26.3C — WorkingState + typed recovery + LoopGuard

Generalize long-horizon state/recovery before broader computer-use authority.

WorkingState v1 target:

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

Initial common recovery classes:

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

LoopGuard must detect repeated state/action fingerprints, no-effect repetition, oscillation, exhausted subgoal/global budgets and absent verified progress.

Default ladder:

```text
re-observe
 -> re-resolve
 -> retry only with new evidence
 -> alternate admitted modality
 -> predeclared recovery branch
 -> ChatGPT replan / clarification / ABSTAIN
```

## Stage 26.4 — Human Demo -> transferable verified candidate skill

Demonstrations compile into subtask goals + verifiable completion criteria + advisory action/target evidence. Live state remains authoritative. Blind coordinate/action replay is not accepted.

One demonstration creates at most CANDIDATE. Promotion requires replay/regression/variant evidence.

## Stage 26.5 — Hybrid Computer-Use Integration

After 26.3B/C foundations and 26.4 candidate-skill semantics:

```text
normalized ObservationEnvelope references
capability-aware semantic/native vs GUI routing
common grounding identity/confidence/ambiguity evidence
semantic/native state first
selective screenshot/ROI fallback
cross-app fact provenance
component-level and noisy-recovery evaluation
```

Stage 26.5 does not itself add public tools. Any Windows/computer-use public surface still needs a separate ADR/schema/security and ordinary-Chat physical acceptance.

---

# Current critical path

```text
26.2E real application E2E                         ACCEPTED
 -> Transport Supervisor v1                       ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime               ACTIVE
    -> 26.3A canonical six-tool runtime           ACCEPTED / MERGED #92
    -> 26.3B Verification Kernel + Finish Gate    ACTIVE
    -> 26.3C WorkingState + recovery + LoopGuard
 -> 26.4 Human Demo -> verified candidate skill
 -> 26.5 Hybrid Computer-Use Integration
 -> 27 distribution/maintenance
 -> 28 clean-user E2E / stable release
```

Optional Track P local planner research remains non-release-critical and stays above the same deterministic authorization/verifier/Finish Gate boundary.

---

# Current security/architecture additions from GUI research

## Environmental content is untrusted data

UI/DOM/page text, email/messages, documents being processed, screenshots/OCR and third-party tool/MCP output do not gain authority over user intent, permission scope or Control Plane policy merely because they are observable.

Provenance/trust must survive cross-app fact transfer.

## Independent completion

Planner/model/procedure saying "done" is only `candidate_done`. `DONE` requires the independent Finish Gate against fresh goal-level evidence.

## Capability routing

Tool/backend availability is not a routing decision. Prefer exact safe semantic/native state/actions; use selected visual/GUI evidence only for reviewed structural miss/spatial cases; uncertain high-consequence cases require stronger evidence or ABSTAIN.

---

# Residual risks

- ChatGPT MCP app definitions are frozen snapshots; local READY does not alone prove current app binding/session usability;
- compatibility aliases for historical `_1mcp_` action IDs remain migration debt;
- one real VS Code task is not broad real-application coverage;
- `AutomationId` lacks broad accepted physical coverage;
- browser DNS/rebinding/redirect/private-network isolation remains incomplete;
- environmental-injection defenses are now an explicit architectural invariant but broader computer-use attack coverage is not yet implemented;
- Verification Kernel/Finish Gate foundation is active but not yet integrated across accepted file/browser/Windows procedure paths;
- WorkingState/LoopGuard remain architecture targets, not accepted runtime implementation;
- Python/model/OpenAdapt packaging is not release-grade;
- raw demonstration retention/redaction/encryption policy is not accepted;
- no stable release exists.

# Non-negotiable rules

- ordinary ChatGPT is the only current general planner/intelligence;
- deterministic Control Plane may advance only already-defined authorized+verified transitions;
- accepted public semantic surface remains small and project-owned;
- normal semantic route is `semantic + direct-stdio` and does not require optional 1MCP;
- semantic/native structure before pixels where reliable;
- pixels/ROI are selective evidence, not automatic context;
- observation/model/procedure/planner proposal is not authorization;
- current state outranks remembered procedure/demo/history;
- every state-changing action requires explicit expected effect + fresh verification;
- transition PASS is not task DONE;
- environmental content is data, not policy authority;
- task-success and safety/policy verification are separate;
- no-effect/oscillating retries must be bounded by LoopGuard;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve fail-closed behavior over benchmark hit rate.

# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the only general intelligence/planning layer while the local platform supplies bounded observation, execution, verification, procedural memory and optional specialist inference.

The product must not become a second autonomous agent brain, a generic hidden workflow dispatcher, or an unbounded local code-execution gateway.

Target split:

```text
ordinary ChatGPT
  = task understanding / strategy / adaptation / escalation

Chat Agent Platform
  = scoped files/browser/windows capabilities
  + deterministic/native observation
  + bounded local vision fallback
  + authorization and guarded execution
  + verification
  + non-agentic procedural memory
  + optional specialized local reasoning later
```

Current public semantic tool names remain exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Any desktop/public-contract change waits for an explicit post-desktop ADR. Do not preserve the count by hiding desktop actions behind misleading existing semantics.

---

## Completed foundation

### Stage 21 — Native ChatGPT ↔ local MCP — DONE

Secure MCP Tunnel + official tunnel-client + local MCP round trip accepted.

### Stage 22 — Remove superseded universal platform core — DONE

Obsolete universal Rust/Python/custom-ingress core removed from the active architecture.

### Stage 23 — Quality-first module selection — DONE

Focused Filesystem/Playwright/1MCP candidates and selection rules accepted.

### Stage 24 — Windows lifecycle + stable semantic Chat surface — DONE

Five public semantic actions accepted.

### Stage 24.1 — Direct semantic tunnel A/B — DONE

Normal path:

```text
ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> secure semantic launcher
  -> direct stdio semantic-projection
  -> focused local backends/adapters
```

1MCP remains internal diagnostic/adaptive/aggregation infrastructure.

### Stage 25 — Safe local vision baseline — DONE FOR BASELINE

Accepted target-laptop baseline:

```text
llama.cpp b10448 / ad1de39e0
LFM2.5-VL-450M F16 + F16 mmproj
CPU 8 threads
ctx 2048
```

Present-target baseline remains 3/5 by design; repeated-row/tiny cases remain safe ABSTAIN rather than false-click promotion.

### Stage 25.1 — Same-session visual fallback foundation — DONE

Accepted same-session screenshot/freshness/coordinate action, fail-closed stale/replay/layout/scroll/overlay/navigation handling, focused model lifecycle and installed-layout/security regressions.

### Stage 25.2 — Ordinary Chat semantic → vision escalation — DONE

Accepted routing:

```text
fresh accessibility snapshot
  -> exact enabled semantic target
       -> semantic action; VLM remains stopped
  -> disabled / unpromoted / unresolved semantic ambiguity
       -> ABSTAIN; VLM remains stopped
  -> zero exact candidates on the promoted text-labeled path
       -> same-session screenshot
       -> local F16 proposal
       -> deterministic authorization
       -> freshness proof
       -> one coordinate action OR ABSTAIN
```

Stage 25.2 real target result: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors.

---

# Stage 26 — Windows capability + verified procedural memory — ACTIVE

The order below supersedes the older plan that placed procedural integration before the product Windows desktop runtime. Qualification work proved enough of the Windows substrate that the next priority is production integration, observation and real-application evidence first.

## Stage 26.0 — UI-Mate analysis + procedural architecture — DONE

`Tencent/UI-Mate` remains a demonstration-guided workflow/state reference only. ChatGPT remains the sole general planner.

## Stage 26.1A — OpenAdapt core qualification — ACCEPTED

Pinned target-tested upstreams:

```text
openadapt-flow 1.31.0
commit d7f58d9f35c8369f16a9b378f23952d425334ad7

openadapt-capture 1.2.2
commit bcf12942d61d66b64d94e645e9124273a5cc5963
```

Decisions:

- Flow `Workflow` / `ProgramGraph`: ADOPT behind project boundaries;
- `SkillLibrary` / learn / teach: ADAPT with stricter candidate-first trust;
- Capture: reuse upstream after bounded qualification rather than building a project recorder first;
- Windows backend/agent: reuse if hardened typed boundary passes target qualification;
- OpenAdapt Desktop: distribution/cockpit reference for Stage 27, not product runtime baseline.

## Stage 26.1B — Real bounded Windows Capture qualification — ACCEPTED

Accepted target evidence proved bounded interactive-session capture, raw UIA evidence retention, compile path, scoped structural suppression, zero foreign structural-window evidence, clean refusal of unaccepted replay and local artifact containment.

Accepted physical qualification head:

`7a9daa9329d81994833c22b4ca2e321927527dcc`

Result artifact:

`C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json`

## Stage 26.1C — Hardened typed Windows executor boundary — ACCEPTED ON TARGET / PR #83

Exact physically accepted head:

`4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`

Accepted boundary includes:

```text
loopback only
auth required
legacy arbitrary exec absent/disabled
bounded typed input
stale frame refusal
stale context refusal
UIA uniqueness
fingerprint-bound structural action
focus-bound keyboard
bounded pointer/scroll
yield zero unrelated-window actions
zero false actions
```

No project-owned replacement actuator is justified unless a future measured blocker appears.

## Stage 26.1D — Warm Windows latency baseline — ACCEPTED BENCHMARK / PR #84

Physical baseline exposed the blocker:

```text
action sequence p50 = 183606.855 ms
action sequence p95 = 185567.403 ms
```

Root cause: repeated desktop-wide UIA traversal from `GetRootControl()` plus re-resolution before action.

## Stage 26.1E — Window-scoped UIA resolver — ACCEPTED ON TARGET / PR #85

Exact physically accepted head:

`66390aca1dadf57c4f11568ec311ad6fcdbd7596`

Accepted runtime resolution path:

```text
expected process id
  -> bounded Win32 EnumWindows
  -> exact same-process HWND
  -> exact UIA WindowControl name
  -> native FindAll only inside that window
  -> upstream candidate/fingerprint semantics
  -> independent re-resolution before act
```

Physical benchmark:

```text
WINDOW_BINDING_PASS=True
PREFLIGHT_CANDIDATE_COUNT=1
PREFLIGHT_FINGERPRINT_PRESENT=True
WINDOW_SCOPED_FIND_CALLS=97
WINDOW_NAME_MATCH_COUNT=97
DESKTOP_FALLBACK_CALLS=0
WINDOW_BINDING_FAILURES=0
WINDOW_BINDING_AMBIGUITIES=0
UNRELATED_WINDOW_ACTION_COUNT=0
FALSE_ACTION_COUNT=0

action p50 = 3323.570 ms
action p95 = 3720.061 ms
p50 speedup = 55.244x
p95 speedup = 49.883x
```

This proves the desktop-wide UIA traversal blocker is removed on the qualification fixture without weakening the accepted executor safety boundary.

### Important accuracy limitation

The 97/97 result is strong fixture evidence, not a claim of 100% Windows-agent accuracy across arbitrary applications. The accepted run exercised the role+name path; broader `AutomationId`, custom-control, multi-window and real-application coverage remains future work.

---

# Stage 26.1F — Land the qualification stack

## Goal

Move accepted C/D/E evidence into the integration line without rewriting physically tested heads.

Stack:

```text
#83 base = main
#84 base = #83 branch
#85 base = #84 branch
```

Required landing procedure:

1. verify exact accepted head, CI and mergeability for #83;
2. merge #83 only when explicitly authorized;
3. retarget #84 to `main` and inspect the resulting diff/CI before merge;
4. merge #84 only after that verification;
5. retarget #85 to `main` and inspect the resulting diff/CI before merge;
6. merge #85 only after that verification;
7. preserve physical result paths and acceptance comments as historical evidence.

Do not blindly merge the stacked chain.

# Stage 26.1G — Authoritative context synchronization

After the qualification stack lands, synchronize:

```text
README.md
AGENTS.md
project-context/START_HERE.md
project-context/CURRENT_STATE.md
project-context/ROADMAP.md
project-context/ARCHITECTURE.md
project-context/MODULE_CATALOG.md
project-context/KNOWN_ISSUES.md
```

The authoritative state must say:

```text
26.1B = accepted
26.1C = executor accepted
26.1D = latency baseline measured
26.1E = window-scoped UIA accepted
NEXT = production Windows runtime integration
```

---

# Stage 26.2A — Production Windows Runtime Foundation

This is the next main engineering stage after landing/synchronization.

## Goal

Move accepted mechanisms out of `scripts/stage26-*` qualification harnesses into a maintained runtime boundary.

Conceptual structure:

```text
runtime/windows/
  session/
  observation/
  actuation/
  safety/
  verification/
  lifecycle/
```

Required foundations:

- interactive user-session identity;
- process/application identity;
- PID/HWND exact-window binding;
- window-scoped UIA resolution;
- typed UIA/keyboard/pointer/scroll execution;
- stale frame/context/focus/fingerprint gates;
- component lifecycle/health/logging;
- no generic exec/shell/Python action channel.

### Verifier foundation belongs here, not later

The product runtime must already support:

```text
observe before
  -> authorize
  -> act
  -> observe after
  -> verifier PASS | FAIL | UNKNOWN
```

Executor delivery is never equivalent to task success.

A minimal verifier interface should exist before real-application E2E; Stage 26.3 later expands it for procedural postconditions.

---

# Stage 26.2B — Desktop Observation / DesktopState

## Priority of evidence

```text
1. Win32 identity
2. UIA / native structure
3. screenshot
4. local VLM fallback
```

Never reverse this order merely because pixel grounding is convenient.

Canonical `DesktopState` should carry at least:

```text
session_id
application_identity
process_id
window_handle
window_instance/generation
window_title
window_bounds
coordinate_space
focused_control
controls[]
visible_text
observed_capabilities[]
screenshot_digest
frame_digest
observed_at
observation_source
control fingerprints / bounds / enabled / visible / focused state
provenance/freshness evidence
```

`observed_capabilities` are observations, not authorization.

---

# Stage 26.2C — Desktop Grounder for LFM2.5-VL

The existing browser/CSS-viewport visual adapter must not be reused as if native Windows used the same pixel coordinate system.

Desktop seam:

```text
locate(
  window_png,
  target_text,
  window_bounds,
  optional_uia_evidence
) -> GrounderProposal | None
```

A proposal should include bounded evidence such as:

```text
point / region
coordinate_space
frame_digest
window_identity
target evidence
confidence
```

The VLM never returns authority such as “click”, “continue workflow” or “task complete”.

---

# Stage 26.2D — Windows semantic/UIA → vision routing + accuracy suite

This stage is explicit and separate from the Grounder adapter.

Routing pattern:

```text
native/UIA exact evidence
  -> deterministic action path
  -> unresolved promoted miss only
       -> current exact-window screenshot
       -> bounded Grounder proposal
       -> same-window / same-frame / target authorization
       -> action OR ABSTAIN
```

Before real application dogfood, run an adversarial accuracy suite covering at least:

```text
duplicate labels
disabled control
hidden control
wrong window
second process with same/similar title
overlay
focus change
stale frame
window movement/recreation
AutomationId path
role+name path
custom/weak UIA control
UIA missing -> vision
vision ambiguity -> ABSTAIN
```

Metrics:

```text
target resolution success
false action rate
unrelated-window action rate
safe abstain precision/recall where applicable
p50/p95 latency
```

Do not convert fixture 97/97 into a global accuracy claim.

---

# Stage 26.2E — First real application E2E

Use one real user application of medium complexity with a disposable test artifact and deterministic rollback/postcondition.

Candidate applications may include VS Code, OriginPro or Reaper, but the roadmap does not permanently preselect one.

Selection criteria:

```text
real user software
medium complexity
safe disposable artifact
multiple UI states/dialog/menu behavior
at least one good structural target
at least one weak/custom target where feasible
deterministic postcondition
clean rollback
```

Acceptance:

```text
false actions = 0
unrelated-window actions = 0
current-state verification = PASS
completion verification = PASS
recoverable mismatch = ABSTAIN rather than blind continuation
```

This stage validates the Windows capability itself before procedural-memory integration.

---

# Stage 26.3 — Verified Procedure Runtime

Only after a real Windows application E2E exists should OpenAdapt procedural machinery enter the product path.

```text
ChatGPT
  -> choose applicable procedure
  -> load ProgramGraph
  -> observe current state
  -> resolve next abstract step
  -> authorization
  -> execution
  -> verify observed effect
  -> advance / recover / ABSTAIN
```

Priority:

```text
current observed state
  > current goal / verifier criteria
  > trusted procedural evidence
  > raw historical action sequence
```

No remembered action sequence may override contradictory live state.

## Stage 26.3A — Candidate-first procedural trust

```text
DEMO
 -> CAPTURE
 -> COMPILE
 -> CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantined/disabled as evidence degrades
```

One demonstration never becomes permanent trust automatically.

## Stage 26.3B — Advanced verifier/postcondition library

Expand the verifier foundation from 26.2A for procedures:

```text
UI state verifier
file-system verifier
window-state verifier
application-state verifier
browser-state verifier
artifact existence verifier
structured output verifier
```

Every procedure transition advances only on current evidence.

---

# Stage 26.4 — Human Demo → Transferable Skill

Goal:

```text
human demonstration
  -> OpenAdapt Capture
  -> structured trajectory
  -> ProgramGraph
  -> project CANDIDATE
  -> verified replay
  -> related changed-state/task replay
```

Acceptance is not macro replay. Vary file name, window order or modest layout/state while preserving task semantics. Current state remains authoritative.

---

# Optional Research Track R — Procedure-State Dataset and Specialized Reasoning

These stages are explicitly **not prerequisites for Stage 27 or Stage 28**.

## Stage 26.5R — Procedure-State Dataset

Collect structured, non-chain-of-thought examples:

```text
goal
procedure graph
current state
available transitions
selected transition
result
verification
```

## Stage 26.6R — SpecializedReasoningBackend benchmark

Only if measurements show a real need such as excessive ChatGPT escalation or local decision latency.

General interface, not a model-branded API:

```text
SpecializedReasoningBackend
  input: goal + current node + graph + current state + transitions + constraints
  output: proposal + confidence + proposed|abstain
```

Compare deterministic baseline against any useful small model family such as transformer/TRM/STARM/FPRM/future recursive approaches.

Primary metrics:

```text
false-action proposal rate
next-step accuracy
abstain precision/recall
OOD behavior
GPT escalation rate
CPU latency
RAM
```

A tiny model proposes; authorization/executor/verifier remain authoritative.

---

# Parallel Track M — Multi-Chat / Codex orchestration

This is a separate upper layer and is not part of Windows executor safety core or a release prerequisite.

```text
Multi-Chat Controller
  -> ChatGPT research/planning/review chats
  -> Codex coding tasks where useful
  -> Chat Agent Platform as local hands/infrastructure
```

Possible capabilities:

```text
open chat
detect chat state
send task
recognize completed/stuck/exhausted
continue or replace chat
collect result
```

Do not merge this controller into `runtime/windows`, procedural authorization or executor logic.

---

# Public MCP contract decision — post-desktop ADR

After a real Windows desktop capability exists, make an explicit ADR between:

A. preserve the current five public tools behind a truthful small semantic surface; or
B. add a few honest coarse-grained capabilities such as `desktop_observe`, `desktop_interact`, `procedure_run` if required.

Never add a generic `tool_invoke`, `run_anything` or opaque workflow executor.

---

# Stage 27 — Distribution & Maintenance

Required:

```text
installer
update
repair
doctor
uninstall
rollback
restart recovery
key rotation
locked dependencies
model/runtime artifact validation
runtime migration
thin lifecycle manager UI
structured logs
crash recovery
privacy controls
emergency pause
```

Evaluate reusable OpenAdapt Desktop packaging/sidecar patterns before rebuilding equivalents, while preserving the exact qualified Flow/runtime boundary.

---

# Stage 28 — Clean User E2E + first stable release

A clean Windows user must be able to prove:

```text
install
 -> connect ChatGPT
 -> choose scoped workspace
 -> browser semantic action
 -> browser visual fallback
 -> Windows application action
 -> verified procedural reuse
 -> restart/recovery
 -> repair
 -> uninstall
```

No git checkout and no developer-only Python/PowerShell setup for normal use.

---

# Cross-cutting security/privacy requirements

Remain explicit throughout all stages:

- semantic/native structure before vision when reliable;
- local vision proposal-only and on demand;
- stale/uncertain state causes zero mutation;
- raw demonstrations local-only by default until retention/redaction/encryption policy is accepted;
- never persist private chain-of-thought;
- no secret tokens in repository artifacts or child processes without need;
- preserve Windows junction/root containment;
- browser DNS/rebinding/redirect/private-network isolation remains a measured residual boundary;
- release-grade Python/model/OpenAdapt artifact reproducibility is required before stable distribution;
- public surface stays small and truthful.

---

# What not to build yet

Do not:

- add a second local LLM planner;
- replace OpenAdapt with a home-grown recorder/compiler/skill engine without a measured blocker;
- write a new Windows actuator without a measured blocker;
- optimize the qualification fixture indefinitely instead of moving to production runtime and real-app evidence;
- make STARM/TRM/FPRM mandatory before data/need exists;
- make Multi-Chat part of executor safety core;
- expose hundreds of raw MCP tools.

---

# Critical benchmark families

## Windows runtime

```text
target resolution success
action p50/p95
false actions
unrelated-window actions
ABSTAIN behavior
post-action verification
```

## Desktop vision

```text
hit
safe abstain
false click
latency
RAM
```

## Procedural runtime

```text
successful reuse
variant reuse
stale detection
incorrect procedure use
verification pass rate
human intervention
```

## Full system

```text
task completion
human intervention rate
ChatGPT turns per task
Codex usage where applicable
local latency
failure recovery
```

---

# Definition of Done

A normal user can tell ordinary ChatGPT:

> “Сделай это на моём компьютере так же, как я показывал раньше.”

and the system can:

```text
understand the task in ChatGPT
 -> select a verified procedure when appropriate
 -> observe the current computer state
 -> re-resolve targets from live evidence
 -> authorize bounded actions
 -> execute safely
 -> verify effects/completion
 -> adapt or ABSTAIN when state differs
 -> escalate back to ChatGPT only when needed
```

with:

```text
false action rate -> practically zero
blind replay -> no
generic local autonomous agent -> no
private chain-of-thought storage -> no
unbounded shell/tool execution -> no
```

The main engineering critical path is therefore:

```text
land #83 -> #84 -> #85
 -> authoritative context sync
 -> production Windows runtime
 -> DesktopState + verifier foundation
 -> desktop Grounder
 -> semantic/UIA -> vision routing + accuracy suite
 -> one real application E2E
 -> verified procedure runtime
 -> human demo transfer
 -> distribution/release
```

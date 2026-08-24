# Roadmap — Chat Agent Platform

## Goal

Keep ordinary ChatGPT as the **only current general intelligence/planning layer**, while the local platform becomes a strong deterministic execution system with bounded capabilities, persistent execution state, authorization, verification, recovery, procedural memory and specialist inference.

```text
ordinary ChatGPT
  = task understanding / strategy / procedure selection / adaptation / escalation

Chat Agent Platform
  = scoped Files / Browser / Windows capabilities
  + deterministic/native observation
  + bounded specialist perception
  + deterministic execution Control Plane
      TaskState
      ProgramGraph progression
      policy / authorization
      checkpoints
      verifier / postconditions
      bounded retry / recovery
      resource budgets
  + non-agentic procedural memory
  + optional specialist reasoning proposals
  + future optional local general planner research
```

The local deterministic Control Plane is **not** a second planner. It may advance an already-selected known procedure through independently authorized and verified transitions without asking ChatGPT after every low-level step. Novel strategy, incompatible state and open-ended adaptation escalate to ChatGPT.

Canonical contract: `CONTROL_PLANE.md`.

Accepted public semantic tools are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

Normal transport is `semantic + direct-stdio`; 1MCP is an optional internal Extension Manager, not a normal-route dependency.

Current operating constraint: use ordinary ChatGPT + GitHub + project local/connected tools. Do not use Codex or ChatGPT Work unless the user explicitly re-enables them.

---

# Completed foundation

## Stage 21 — Native ChatGPT <-> local MCP — DONE

Secure MCP Tunnel + official tunnel-client + real local MCP round trip accepted.

## Stage 22 — Superseded universal core reduction — DONE

Old generic agent/gateway core removed from the active architecture.

## Stage 23 — Quality-first module selection — DONE

Focused capability/upstream selection rules accepted.

## Stage 24 / 24.1 — Windows lifecycle + typed semantic file/browser surface + direct tunnel — DONE

Historical five-tool semantics are accepted foundation only; they do not define the current public inventory.

## Stage 25 / 25.1 / 25.2 — Browser semantic + local vision — DONE

Structure first, specialist proposal only, deterministic authorization, ABSTAIN on unresolved evidence.

## Stage 26.1A-E / 26.2A-E — Windows capability foundation — DONE

Accepted sequence includes OpenAdapt qualification, bounded Windows Capture, hardened typed executor, warm latency baseline, window-scoped UIA, production Windows runtime, DesktopState, native local Grounder, deterministic UIA->vision routing and the first isolated VS Code real-application E2E.

Exact heads and physical evidence remain in `EVIDENCE_INDEX.md` and the historical stage documents.

## Cross-cutting Track T — Transport Reliability / Self-Healing Supervisor — ACCEPTED / MERGED #94

Transport Supervisor v1 is now maintained product infrastructure, not a planned track.

Accepted boundary:

```text
persistent tunnel id
 -> layered local / semantic / OpenAI-control health
 -> persistent desired state + runtime ownership
 -> failure-specific bounded recovery
 -> console-free Scheduled Task persistence
 -> truthful blocked/recoverable states
```

Normal recovery keeps the existing `tunnel_*` id and does not require long-lived admin credentials.

---

# Stage 26 — Windows capability + verified procedural execution — ACTIVE

Required order:

```text
bounded capability
 -> real-application evidence
 -> deterministic procedure Control Plane
 -> human demonstration transfer
```

## 26.3A — canonical six-tool Verified Procedure Runtime — ACCEPTED

Exact physically accepted runtime head:

```text
300db9956dfbdf0300ecc59f017d6f3280d4353a
```

Accepted normal route:

```text
ordinary ChatGPT
 -> Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> exact six-tool surface
 -> deterministic Control Plane
```

Accepted bootstrap/runtime invariants:

```text
profile = semantic
tunnel_profile = direct-stdio
semantic_public_tool_count = 6
extension_manager_included = false
1MCP_REQUIRED = false
```

Accepted ordinary-Chat physical test:

```text
ONE long-horizon user goal
 -> challenge/HEAD/profile/binding verified
 -> research-ledger.md used and reread as working memory
 -> 16 content pages / 12 works or benchmark groups
 -> 12 successful browser interactions
 -> recover from one invalid browser interaction
 -> gui-agent-research.md written and independently reread
 -> procedure_run verified_workspace_artifact_v1
 -> 3 verified transitions -> completed
 -> independent workspace_read exact success result
 -> second procedure_run on existing target
 -> ABSTAIN at preflight, action_count=0
 -> independent reread proves unchanged content/SHA
```

Completion task:

```text
497ecb591779219ef0ee1e55ea7ad0b8
```

Zero-overwrite task:

```text
02b09a4909b6d71e0578c19b2d395cb8
```

Accepted artifact SHA-256:

```text
2396b8338edced2675982db9d263a046705f7f906b553b0ed19b81f51205e583
```

This establishes the release-critical autonomy boundary: ordinary ChatGPT can select/use one bounded registered procedure while the local deterministic Control Plane progresses known transitions, verifies each effect and refuses overwrite without making the user operate PowerShell between steps.

It does **not** authorize generic shell/Python execution or arbitrary Windows consequences.

## 26.3B — advanced verifier/postcondition library — NEXT

Expand verifier coverage for:

- file/content/artifact identity and structured outputs;
- browser URL/document/control/post-action state;
- UI/application state;
- process/window/application identity/state;
- completion and rollback evidence;
- cross-capability final postconditions.

Non-negotiable rules:

```text
action delivered != task completed
current observed state > remembered procedure state
stale / ambiguous / UNKNOWN -> ABSTAIN/escalate
```

Procedure expansion remains explicit and project-owned. Do not introduce arbitrary command execution, generic `tool_invoke`, opaque workflow dispatch or raw backend catalogs.

## 26.3C — checkpoint / bounded recovery / resource budgets

Longer procedures require:

- explicit checkpoints;
- retry ceilings;
- safe known recovery branches;
- action/time/resource budgets;
- deterministic escalation reasons;
- no infinite retry or blind continuation.

Stage 26.3A already proves durable checkpoints and a fixed three-action budget for the first file procedure. 26.3C broadens these mechanics only where 26.3B procedures require it.

---

# Stage 26.4 — Human Demo -> Transferable Verified Candidate Skill

```text
human demonstration
 -> Capture
 -> structured trajectory
 -> ProgramGraph
 -> project CANDIDATE
 -> verified same/near-state replay
 -> changed-state/task replay
```

Acceptance requires live re-resolution and verifier-controlled progression, not macro replay.

One demonstration never becomes permanent trust automatically.

Candidate lifecycle remains:

```text
CANDIDATE
 -> replay / regression / variant evidence
 -> trusted reusable
 -> stale / quarantined / disabled / rollback as evidence degrades
```

Human demonstration privacy/retention/encryption/redaction policy must be defined before broad capture becomes product functionality.

---

# Optional internal Extension Manager track

1MCP remains useful as a replaceable internal manager/aggregator for future third-party MCP backends.

Target role:

```text
canonical project-owned semantic surface
 -> typed adapter / capability policy
 -> optional 1MCP Extension Manager
 -> selected third-party MCP backend
```

1MCP may manage discovery, enable-disable, lazy lifecycle, health and restart. Backend availability is not trust or authorization. Raw tools are not automatically published to ChatGPT.

This track is orthogonal to the release-critical path and must not re-enter normal six-tool bootstrap/start/status/health as a mandatory dependency.

---

# Optional Research Track R — Specialized reasoning

Procedure-state datasets and small structured reasoning experiments begin only when real verified state-transition data exists and measurements justify them.

A `SpecializedReasoningBackend` may provide **proposal only** structured choices/confidence/ABSTAIN. It never authorizes or actuates and is different from a general planner.

# Optional Future Track P — Local Planner / Offline Autonomy

A local general planner remains in the long-term roadmap but is **not part of the current release-critical path**.

Earliest prerequisite: verified procedure-state data from 26.3/26.4 plus a measured reason to move planning local.

Potential triggers:

- offline operation;
- material planning round-trip latency;
- multi-machine/highly parallel independent work;
- deployment/privacy requirements;
- measured local-model parity on the actual workload.

Progression:

```text
P0 shadow planner
   sees structured goal/state/procedure evidence
   -> proposal only
   -> no authorization / no actuation
   -> benchmark against ordinary ChatGPT manager

P1 bounded subtask planner
   explicitly scoped task families only
   -> deterministic Control Plane remains authoritative

P2 optional local general-planner mode
   only after parity/safety/resource evidence
   -> never silently replaces ChatGPT default
```

Even in P2 the planner stays **above** the same policy/authorization/verifier Control Plane. No planner can grant itself execution authority.

# Parallel Track M — multi-chat orchestration

Separate upper layer, not the Windows/procedure safety core and not a release prerequisite. Under the current operating constraint it may coordinate ordinary ChatGPT sessions only; Codex/Work remain disabled unless explicitly re-enabled.

---

# Stage 27 — Distribution & Maintenance

Installer/update/repair/doctor/uninstall/rollback/restart recovery/key rotation/artifact validation/lifecycle UI. Release-grade Python/model/OpenAdapt reproducibility is required.

# Stage 28 — Clean User E2E / first stable release

Fresh-user operation without git checkout or developer-only Python/PowerShell setup.

---

# Current critical path

```text
26.2E real application E2E — ACCEPTED
 -> Transport Supervisor v1 — ACCEPTED / MERGED #94
 -> 26.3 Verified Procedure Runtime / deterministic Control Plane — ACTIVE
    -> 26.3A canonical six-tool runtime — ACCEPTED
    -> 26.3B advanced verifier/postconditions — NEXT
    -> 26.3C bounded recovery/budgets as required
 -> 26.4 Human Demo -> transferable verified candidate skill
 -> 27 distribution/maintenance
 -> 28 clean-user E2E/stable release
```

# Merge policy

A logically complete branch with reviewed intended diff, passing required physical/CI gates and satisfied applicable acceptance checks should be merged without waiting for a separate merge command.

Do not merge on unresolved finding, conflict, ambiguous scope or failed/skipped required evidence.

# Cross-cutting invariants

- ordinary ChatGPT is the only **current general** planner/intelligence;
- deterministic local Control Plane is allowed/desired and is not a general planner;
- accepted public surface currently contains exactly six project-owned semantic tools;
- normal semantic route is direct stdio and does not require optional 1MCP;
- semantic/native structure before pixels where reliable;
- observation/model/procedure/planner proposal is not authorization;
- current observed state outranks remembered procedure;
- action delivery is not task completion;
- stale/ambiguous/UNKNOWN causes zero unauthorized continuation;
- never persist private chain-of-thought;
- raw capture is sensitive local data;
- generic Windows code execution remains disabled/unreachable;
- preserve credential isolation and Windows root/junction containment;
- keep `main` as integration line and preserve exact physical evidence heads.

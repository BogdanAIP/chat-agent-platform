# External Execution Reuse Strategy — OpenAdapt and UFO

Status: **AUTHORITATIVE INTEGRATION DIRECTION**

This document records how `chat-agent-platform` may reuse OpenAdapt and Microsoft UFO without replacing the project-owned authority, verification, recovery, or completion boundaries.

The purpose is to avoid reimplementing mature procedural and Windows/Office mechanics while preserving the part of the architecture that is intentionally project-owned.

## Executive decision

The project should:

- keep the project-owned deterministic Control Plane as the sole owner of capability authority, WorkingState, recovery budgets, verification semantics and independent task completion;
- keep ordinary ChatGPT as the only current general planner;
- use OpenAdapt primarily as an internal deterministic procedure compiler/runtime and effect-evidence provider;
- use UFO selectively as a source of Windows/Office execution adapters and implementation patterns;
- **not** adopt OpenAdapt or UFO completion verdicts as project `PASS`/`DONE` authority;
- **not** adopt UFO HostAgent/AppAgent/Galaxy as a second AgentOS/planner hierarchy;
- keep the current six-tool ordinary-Chat public semantic surface unchanged unless a later consequence-class ADR explicitly changes it.

Target architecture:

```text
                         +------------------------------+
                         | OpenAdapt procedure substrate |
                         | compile / replay / teach      |
                         | checkpoint / effect evidence  |
                         +---------------+--------------+
                                         |
ordinary ChatGPT -> project Control Plane+----> project capabilities
(current planner)      authority         |       Browser / Files / Windows
                       WorkingState      |
                       recovery          +----> UFO-derived Office/Windows adapters
                       budgets                   selected UIA/Win32/COM/app APIs only
                              |
                              v
                    normalized evidence adapters
                              |
                              v
                    PROJECT Verification Kernel
                       PASS | FAIL | UNKNOWN
                              |
                              v
                    independent Finish Gate
                      DONE | NOT_DONE | UNKNOWN
```

External engines may execute or observe inside admitted scope. They do not own the final interpretation of success.

---

## 1. Non-negotiable project-owned boundary

The following remain project-owned even after external reuse:

```text
user intent / selected task scope
capability AVAILABLE -> ACTIVE -> AUTHORIZED lifecycle
ExpectedEffect binding
freshness / subject / stream / identity checks
WorkingState
retry and recovery budgets
LoopGuard / stagnation escalation
policy and safety gate
Verification Kernel PASS | FAIL | UNKNOWN
independent Finish Gate DONE | NOT_DONE | UNKNOWN
public Chat-facing semantic contract
```

A third-party executor, verifier, model, procedure, skill, MCP backend, Office API or UI adapter cannot self-grant authority and cannot self-declare task completion.

The durable invariant remains:

```text
external component proposes / executes / observes
project Control Plane decides authority
project Verification Kernel decides verified transition status
project Finish Gate decides task completion
```

---

## 2. OpenAdapt role

### Current qualified substrate

The project already pins and has studied:

```text
openadapt-flow 1.31.0
openadapt-capture 1.2.2
```

The existing lock treats Flow as a candidate procedural compiler/runtime/IR/lifecycle/verifier substrate and Capture as the candidate human desktop demonstration recorder.

That qualification remains useful. A newer OpenAdapt release is not required merely to begin integration; version movement should occur only behind an adapter plus compatibility tests.

### Adopt from OpenAdapt

Preferred reuse areas:

```text
demonstration -> compile
ProgramGraph / workflow IR
deterministic healthy-path replay
checkpoint / durable procedure resume
halt / teach / candidate correction
skill emission / candidate lifecycle mechanics
effect contracts and effect-verifier implementations
certification / effect-coverage mechanics
procedure-local execution reporting
```

These are especially relevant to Stage 26.4, where rebuilding a recorder/compiler/replayer/certification stack would duplicate mature work.

### Do not make OpenAdapt the project verifier

OpenAdapt effect-verifier verdicts are **evidence**, not project transition authority.

A compatibility mapping may be represented internally as:

```text
OpenAdapt CONFIRMED     -> candidate positive evidence
OpenAdapt REFUTED       -> candidate negative evidence
OpenAdapt INDETERMINATE -> candidate incomplete evidence
```

but the project must not shortcut this into unconditional:

```text
CONFIRMED == project PASS
```

Instead use a narrow adapter:

```text
OpenAdapt EffectVerifier
 -> OpenAdaptEffectEvidenceAdapter
 -> normalized evidence:
      source
      verifier kind
      subject / record identity
      effect-contract identity/hash
      pre-state binding when applicable
      observed post-state/result
      freshness/provenance
      raw OpenAdapt verdict
 -> project ObservationSnapshot / ExpectedEffect
 -> project Verification Kernel
 -> PASS | FAIL | UNKNOWN
```

This allows the project Kernel to reject or downgrade otherwise-positive upstream evidence when, for example:

```text
subject identity drifted
process/application identity changed
observation is stale
selected verifier changed after resume
effect contract changed
required evidence is incomplete or ambiguous
provenance is inconsistent
```

Therefore this is valid:

```text
OpenAdapt raw verdict = CONFIRMED
project Kernel        = FAIL or UNKNOWN
Finish Gate           = NOT_DONE or UNKNOWN
```

The upstream verdict is never sufficient by itself.

### OpenAdapt durable resume does not own Stage 26.3C WorkingState

OpenAdapt durable resume is valuable for resuming one compiled procedure. It must remain a **procedure-local execution substrate** below the project WorkingState.

Stage 26.3C WorkingState must stay project-owned because it spans:

```text
Browser
Windows
Files
future Office adapters
future local execution
cross-capability tasks
user constraints
capability grants
recovery history and budgets
Finish Gate evidence references
```

Target relationship:

```text
project WorkingState
  -> selected procedure id/version/node
  -> OpenAdapt resume/checkpoint reference
  -> current capability/evidence/authorization state
```

Do not derive the whole platform WorkingState from OpenAdapt's internal procedure state.

### OpenAdapt privacy boundary

Capture can include screen and input evidence. Production adoption requires:

```text
local-only by default
explicit retention policy
bounded capture scope
masking/redaction where appropriate
no cloud upload required for the local product path
sensitive-data handling documented before promotion
```

OpenAdapt Cloud is not a dependency of this strategy.

---

## 3. Microsoft UFO role

### Adopt components and patterns, not the AgentOS

UFO² contains mature Windows-specific mechanisms that are expensive to rebuild application by application:

```text
UIA
Win32
WinCOM
application-specific introspection
Excel/Word/Outlook/PowerPoint-oriented adapters
hybrid GUI + native/API execution patterns
control detection patterns
non-disruptive / isolated desktop ideas
```

These should be reviewed as implementation sources for focused project-owned adapters.

Example target boundary:

```text
runtime/integrations/ufo/
  excel_adapter.py
  word_adapter.py
  powerpoint_adapter.py
  outlook_adapter.py
  wincom_adapter.py
```

The exact paths are not yet an implementation commitment. The architectural rule is that selected application mechanics sit behind project-owned capability, policy, observation and verification boundaries.

### Explicitly do not adopt

Do not import UFO as a second current planner stack:

```text
HostAgent planning hierarchy
AppAgent planning hierarchy
UFO planner prompts
UFO task-completion authority
UFO model-routing/configuration as product authority
Galaxy/ConstellationAgent orchestration
raw UFO MCP catalogs directly exposed to ordinary ChatGPT
```

The anti-pattern is:

```text
ChatGPT planner
 -> project Control Plane
 -> UFO HostAgent planner
 -> UFO AppAgent planner
```

The preferred pattern is:

```text
ChatGPT planner
 -> project Control Plane
 -> one bounded Office/Windows adapter
 -> project observation/evidence
 -> project Verification Kernel
```

### UFO³ Galaxy is deferred

UFO³ solves cross-device DAG decomposition, scheduling and coordination. That is not a current release-critical gap.

Do not integrate Galaxy while the project still has materially larger unresolved risks in:

```text
Windows real-application reliability
long-horizon verified recovery
Office application coverage
WorkingState / LoopGuard
clean-user packaging
```

Galaxy may be revisited only when multi-device orchestration becomes an observed bottleneck, and even then it must remain below the same project authority and completion boundaries or be treated as an alternative planner research track rather than silently inserted into production.

---

## 4. Stage mapping

The reuse strategy must not destabilize the active Windows verifier PR.

### Stage 26.3B — finish current correctness work first

Do **not** rewrite PR #114 around OpenAdapt or UFO.

Required order:

```text
#114 Windows shared-kernel verifier
 -> hosted CI clean
 -> target-Windows physical verifier qualification
 -> merge
 -> representative Windows/application L3
 -> repeat one Browser L3 under the new Source Provenance Gate
 -> close any remaining real 26.3B completion gap
```

`SOURCE_PROVENANCE_ACCEPTANCE.md` defines the new physical-source binding requirement.

### Stage 26.3C — keep project-owned

Implement project-owned:

```text
WorkingState
provenance/freshness state
recovery classes
retry/action/time budgets
LoopGuard
StagnationReport / escalation
```

OpenAdapt checkpoint/resume references may be carried inside WorkingState but must not define the whole state model.

### Pre-26.4 OpenAdapt spike

After the Stage 26.3C core shape is accepted, run a bounded 3–5 engineering-day spike:

```text
human demonstration
 -> OpenAdapt Capture / Flow compile
 -> ProgramGraph / deterministic replay
 -> OpenAdapt effect-verifier evidence
 -> project OpenAdaptEffectEvidenceAdapter
 -> project Verification Kernel
 -> project independent Finish Gate
```

Spike acceptance requires:

- no new public Chat-facing tool merely to support the spike;
- no generic `execute_windows`, shell, Python or per-workflow raw MCP authority exposed to ChatGPT;
- deterministic healthy replay works without model calls where OpenAdapt supports it;
- upstream effect verdict is preserved as provenance but project Kernel remains final transition judge;
- project Finish Gate remains the only task completion judge;
- resume does not bypass project capability authorization or evidence binding;
- pinned upstream version and adapter compatibility are tested;
- capture/privacy behavior remains local and bounded.

If these conditions fail, keep OpenAdapt qualified but do not promote it to the production procedure path.

### Stage 26.4 — primary OpenAdapt reuse target

If the spike succeeds, prefer OpenAdapt reuse for:

```text
demonstration -> candidate procedure
compile / ProgramGraph
replay
checkpoint/resume
teach/correction
certification/effect coverage
candidate skill emission
```

Project-specific skill trust remains:

```text
one success/demo -> at most CANDIDATE
replay + regression + variant evidence
project verifier/Finish Gate evidence
 -> promoted trusted reusable skill
```

OpenAdapt skill/certification status does not automatically equal project trust.

### Stage 26.5 — selective UFO Office reuse

Start with one Office application adapter at a time, preferably an application with strong native system state such as Excel.

Each adapter must define:

```text
allowed operations
application/document identity
observation schema
ExpectedEffect schema
freshness rules
authority requirements
rollback/recovery limits
independent or strongest-available effect evidence
L1/L2/L3 acceptance
```

Only after a focused adapter passes should another Office application be added.

---

## 5. Version and supply-chain rule

External reuse must remain behind small project-owned adapters.

For OpenAdapt/UFO-derived components record:

```text
repository
commit/tag/version
license
selected files/modules
local modifications if any
compatibility-test version
runtime Python/dependency constraints
security-relevant capabilities
```

Do not continuously chase upstream `main`.

Upgrade only when:

```text
measured bug/security/capability need
 -> review upstream diff
 -> update pin
 -> compatibility tests
 -> relevant physical/L3 gate if behavior/authority changed
```

The existing OpenAdapt lock currently contains stale historical language referring to five public semantic tools. The canonical surface is now six. This is documentation/config drift to correct during the next lock-maintenance change; it is not authority to regress the current six-tool contract.

---

## 6. Estimated engineering impact

These are planning estimates, not measured delivery promises.

Expected benefit from selective reuse:

```text
Stage 26.3B + Windows L3       little/no immediate acceleration
Stage 26.3C                   modest acceleration; project state remains custom
Stage 26.4                    largest gain; potentially ~2–3x faster
Stage 26.5 Office/hybrid      meaningful gain from selected UFO components
packaging/security/E2E        limited external help
```

A reasonable planning hypothesis is roughly:

```text
useful alpha through 26.5: ~30–40% faster
stable release overall:     ~20–30% faster
```

The estimate must be revised from actual spike/L3 evidence rather than treated as a product claim.

---

## 7. Product differentiation after reuse

The project does not need to be unique in clicking Windows controls, recording demonstrations or compiling repeatable workflows.

Its intended differentiator is the composition:

```text
small truthful Chat-facing semantic boundary
 + explicit scoped authority
 + current-state identity/freshness
 + independent project Verification Kernel
 + independent task Finish Gate
 + L1/L2/L3 physical acceptance discipline
 + planner-independent deterministic Control Plane
```

Using mature external mechanics is desirable when it lets engineering effort concentrate on that boundary instead of reimplementing commodity automation machinery.

## Non-goals

This strategy does not:

- make OpenAdapt or UFO production-approved merely by documenting them;
- alter current PR #114 runtime semantics;
- add a public `desktop_*`, `office_*`, shell, Python or arbitrary-dispatch tool;
- accept OpenAdapt Cloud as a dependency;
- accept UFO HostAgent/AppAgent/Galaxy;
- declare broad Windows/Office reliability proven;
- replace required representative L3 and physical acceptance evidence.

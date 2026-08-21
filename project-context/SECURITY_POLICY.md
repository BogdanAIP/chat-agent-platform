# Security Policy — Bridge and Execution Control Plane

## Trust boundaries

Normal public path:

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio secure semantic launcher
 -> semantic-projection
 -> focused capability adapters
```

1MCP remains internal/diagnostic where useful; it is not the normal public semantic hop.

The tunnel provides authenticated reachability. It is not a substitute for capability scope, action authorization, procedure trust, deterministic execution-state control or verifier evidence.

## Terminology: two different “control planes”

The OpenAI tunnel ecosystem uses `CONTROL_PLANE_API_KEY` for Secure MCP Tunnel infrastructure. That credential/name is **unrelated** to the project's planned local deterministic **execution Control Plane**.

Never infer that possession of a tunnel/control-plane key grants local action authority.

## Security objective

Control consequence, scope, lifetime and progression without making legitimate workflows impossible.

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

Procedure trust lifecycle:

```text
new/demo
 -> project CANDIDATE
 -> replay/regression/variant evidence
 -> trusted reusable
 -> stale/quarantine/disable/rollback
```

Capability authorization and procedure trust remain separate.

## Deterministic local execution Control Plane

The target Control Plane is a security boundary, not a second general planner.

It may own:

- structured TaskState;
- selected procedure/ProgramGraph version and current node;
- current evidence references/digests;
- allowed outgoing transitions;
- capability scope and consequence policy;
- current action authorization;
- checkpoints/rollback metadata;
- verifier/postconditions;
- retry/recovery ceilings;
- time/action/resource budgets;
- escalation reason.

A known selected procedure may continue locally through repeated:

```text
observe current state
 -> exactly one permitted transition
 -> authorize current action
 -> act
 -> observe result
 -> verify explicit postcondition
 -> checkpoint / advance
```

The Control Plane must stop with zero further mutation and escalate when:

- current state is stale/ambiguous/UNKNOWN;
- no known transition matches;
- incompatible multiple transitions match;
- authorization scope is absent;
- postcondition FAIL/UNKNOWN cannot be resolved by an explicitly defined bounded recovery branch;
- retry/resource budget is exhausted;
- continuing requires a new strategy.

It must never invent a new user goal or infer broad authority from a procedure/model/planner request.

## General planner boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. It interprets user goals, chooses strategy/procedure and handles novel-state adaptation.

A future local planner may only enter through optional Track P research. Its output is still non-authorizing proposal data. It remains above the same deterministic Control Plane and cannot bypass capability policy/verifier gates.

Initial future planner research must be shadow/proposal-only before any bounded planning authority is considered.

## Chat-facing tool semantics

Current accepted public tool names:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

Generic adaptive `tool_invoke` is not the ordinary-Chat product surface. `semantic-projection` must remain deterministic and truthful; it cannot become the procedure Control Plane, hidden planner, generic desktop dispatcher or arbitrary server/tool selector.

A public desktop/procedure surface requires its own ADR/schema/review/ordinary-Chat acceptance.

## Browser semantic -> vision authorization — ACCEPTED

Stage 25.2 remains structure-first. Model output is untrusted evidence. Only reviewed visual fallback classes reach deterministic authorization/freshness before one coordinate action or ABSTAIN.

Browser screenshot -> coordinate action remains a narrow non-atomic TOCTOU residual boundary.

## Windows capability security — ACCEPTED THROUGH STAGE 26.2D FOR BOUNDED CONTRACTS

The old statement that product acceptance of the Windows agent is still pending Stage 26.1C is obsolete.

Accepted foundations now include:

- bounded authenticated typed executor;
- legacy generic `/execute_windows` disabled/unreachable;
- exact PID/HWND window-scoped UIA;
- DesktopState evidence;
- native exact-window F16 Grounder proposal-only;
- deterministic structure-first UIA -> vision routing;
- fresh process/window/frame/target evidence;
- native foreground + WindowFromPoint/root-HWND/PID guard;
- delivery receipts separate from completion.

Stage 26.2D exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

This is controlled fixture evidence, not universal Windows authorization.

## Stage 26.2E real-app security gate — ACTIVE

The isolated VS Code qualification uses one specifically prefixed TEMP root and no user profile/project.

Before its one guarded Unicode delivery it requires:

- exact disposable containment;
- unique Code.exe PID/HWND/DesktopState;
- enabled/visible focused editor evidence;
- deliberate verifier mismatch -> FAIL -> ABSTAIN with zero action;
- **fresh pre-action DesktopState with same exact window and focused-editor fingerprint**;
- native foreground/hit-test guard;
- authenticated loopback agent with legacy exec absent.

After action it requires exact saved artifact hash/size, same current window identity, expected-only workspace, natural CLI/window exit and rollback. Forced process cleanup is allowed only after a failure and cannot convert the run to PASS.

## Procedural-memory security

### No private chain-of-thought persistence

Store only execution-relevant structured/user-visible state: goal summaries, procedure/version IDs, observations, actions/receipts, postconditions, verification and provenance.

Never persist hidden model reasoning.

### Raw demonstration retention

Raw desktop capture is sensitive by default. Long-term arbitrary demo storage requires explicit:

- location/ownership;
- retention/expiry;
- screenshot/text redaction;
- secret filtering;
- deletion/disable semantics;
- encryption-at-rest policy;
- backup/export/sync policy.

### Compiled procedure evidence

A compiled procedure may retain structural/native evidence and bounded pixel/template/OCR/geometry evidence, but blind historical absolute-coordinate replay is never authority or primary identity.

### Skill poisoning/trust resistance

- one successful demonstration creates at most CANDIDATE;
- candidate retrieval is non-authorizing;
- promotion requires measured replay/regression/variant evidence;
- malformed/incompatible/stale procedures fail closed;
- version/provenance history is preserved;
- imported/upstream procedures receive no implicit local authorization.

## Completion integrity

A model, ChatGPT, procedure or future planner saying “done” is not enough.

Use deterministic/native/system-of-record postcondition evidence where practical:

```text
PASS -> checkpoint / advance
FAIL -> bounded recovery or stop
UNKNOWN -> observe / ABSTAIN / escalation
```

## F16 / specialist grounding security

Local LFM2.5-VL-450M F16 remains bounded perception only:

```text
current PNG + bounded target evidence
 -> proposed match OR ABSTAIN
```

It never plans, grants authority or declares completion.

## Secrets

- tunnel runtime keys stay local and out of repository/procedure/task-state content;
- child backends receive credentials only when explicitly needed;
- never copy secrets into procedure metadata, screenshots, logs or docs;
- rotate suspected exposed secrets first.

## Workspace/files security

- workspace paths remain scoped/rooted;
- containment includes Windows junction/link escape checks;
- procedure history cannot broaden current file scope.

## Browser network boundary

Current policy is not a complete DNS/rebinding/redirect/private-network sandbox. Do not describe it as one.

## Bootstrap/lifecycle integrity

Manager/tray owns lifecycle/configuration/diagnostics only. It must not become the general planner or the procedure Control Plane.

The procedure Control Plane must not own tunnel credentials merely because both systems use the phrase “control plane”.

## Chat permission / OpenAI safety behavior

App permission mode is an additional control, not the only boundary. Distinguish pre-MCP product safety blocks from local backend failures.

Prefer scoped reversible operations; reserve confirmation for genuinely consequential/hard-to-reverse effects where practical.

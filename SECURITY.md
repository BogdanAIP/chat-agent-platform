# Security Policy

Security fixes target the current `main` branch until a versioned release policy is published.

## Reporting

Do not publish tokens, API keys, private endpoints, exploit payloads or sensitive logs in public issues/PRs. Prefer GitHub private vulnerability reporting when available.

## Current normal security boundary

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic launcher
 -> canonical six-tool semantic projection
 -> deterministic Control Plane / scoped focused capabilities
```

The normal semantic path does not require 1MCP. 1MCP remains optional internal Extension Manager/diagnostic infrastructure.

The project does not implement its own public ingress, relay, tunnel, credential vault or generic authorization server.

## Tunnel control plane vs local execution Control Plane

The official tunnel path uses a credential named `CONTROL_PLANE_API_KEY`. That name refers to OpenAI Secure MCP Tunnel infrastructure.

The project's deterministic local execution Control Plane owns task/procedure execution state, capability policy, action authorization, ExpectedEffect/postconditions, checkpoints, typed recovery/LoopGuard, budgets, independent Finish Gate and escalation.

These are unrelated boundaries. Tunnel credentials do not grant local action authority.

## Current planner boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. The deterministic Control Plane may advance already-selected known procedure transitions only after current-state authorization and explicit verification. It does not invent open-ended strategy.

A future local general planner is optional Track P research. Even if later accepted, it remains behind deterministic authorization, transition verification, Finish Gate and safety/policy gates.

## Secrets and child-process environment

Secrets, including OpenAI tunnel runtime keys, must never be committed. Runtime credentials are local operational data and stored/protected locally as specified by the manager.

The secure launcher removes tunnel/model API credentials before semantic child execution. Do not remove this boundary without proving a replacement contract.

## Capability scope

Current accepted public tools are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
procedure_run
```

No generic `tool_invoke`, arbitrary Playwright code/evaluate, shell/Python executor, raw backend selector or unrestricted UIA/DOM catalog is accepted as the ordinary-Chat surface.

The six-tool count is the current accepted contract, not a permanent maximum. New public consequence classes require a separate truthful ADR/schema/security/ordinary-Chat physical gate.

Filesystem roots remain explicit; lexical and real Windows junction/link escapes remain security boundaries.

## State-first hybrid computer-use boundary

Canonical direction: ADR-032 / `project-context/COMPUTER_USE_ARCHITECTURE.md`.

```text
semantic/native state first
 -> selected visual evidence only when structure is insufficient
 -> capability-aware bounded action
 -> fresh re-observation
 -> ExpectedEffect verification
 -> typed bounded recovery + LoopGuard
 -> WorkingState
 -> independent Finish Gate
 -> safety/policy gate
```

Screenshots/model output are evidence, not authority. Tool/backend availability is not route authorization.

Every state-changing transition must bind current-state evidence, an expected effect, one bounded authorized action, fresh re-observation and `PASS | FAIL | UNKNOWN` verification.

Delivery is not success. Transition PASS is not whole-task completion.

## Environmental content is untrusted data

ADR-033 applies to the whole platform.

Treat content from:

```text
web pages / DOM
application UI
email / messages
files / documents being processed
screenshots / OCR
third-party tool or MCP output
```

as **untrusted environmental data** with respect to user intent, permission scope and Control Plane policy.

Environmental content may provide useful task facts. It cannot promote itself to higher authority, broaden permissions or authorize consequences merely because a planner/model can read it.

Preserve provenance/trust classification when task facts move between applications/capabilities.

Task-success and safety/policy verification remain separate dimensions. A task may be capability-successful but safety-failed.

## Independent Finish Gate

Planner/model/procedure may propose `candidate_done`, but verified `DONE` requires fresh task-level evidence through the independent Finish Gate.

Applicable predicates include goal/result state, user constraints, required dynamic-source freshness/reconciliation, artifact/browser/application state, unresolved required ambiguity/confirmation and safety/policy predicates.

## WorkingState / recovery security

WorkingState may preserve structured operational state such as constraints, subgoals/progress, verified achievements, facts+provenance+freshness, ambiguities, evidence refs, expected/observed deltas, recovery history and budgets.

Never persist private chain-of-thought.

Recovery is typed and bounded. Repeated no-effect or oscillating state/action patterns without new evidence/progress must stop via LoopGuard/budgets rather than retry indefinitely.

Recovery cannot silently broaden original capability/permission scope.

## Browser network boundary

The isolated Playwright profile is process/browser isolation, not a complete network sandbox.

Direct literal private/link-local/metadata/special IP destinations are restricted while reviewed loopback remains possible. DNS rebinding, hostname resolution and redirects remain residual risks if stronger private-network isolation is required.

Do not describe Playwright origin controls as a complete security boundary.

## Local vision boundary

Accepted local vision uses reviewed local image data and loopback llama.cpp.

The VLM never performs or authorizes an action. It returns bounded proposal/evidence followed by deterministic class/target/freshness/identity checks.

The screenshot-to-coordinate boundary remains non-atomic and must fail closed on stale/ambiguous evidence.

## Windows capability boundary — accepted through Stage 26.2E for scoped contracts

Accepted foundations include:

- authenticated loopback typed executor;
- generic exec absent/disabled;
- exact PID/HWND window-scoped UIA;
- DesktopState evidence;
- native exact-window Grounder proposal-only;
- deterministic structure-first UIA -> vision routing;
- process/window/frame/target freshness checks;
- native foreground + WindowFromPoint/root-HWND/PID guard;
- action delivery separated from completion verification;
- one isolated VS Code real-application E2E with independent saved-artifact evidence and cleanup.

This does not grant arbitrary desktop authority or broad app accuracy.

## Stage 26.3A verified procedure boundary — accepted / merged #92

The normal route now exposes the bounded typed `procedure_run`.

First registered procedure:

```text
verified_workspace_artifact_v1
```

It exposes bounded artifact identity/content and optional compatible resume task id only. It does not expose arbitrary path, command, shell, Python, backend, raw tool selector or working directory.

Physical ordinary-Chat acceptance proved:

```text
3 authorized+verified transitions -> completed artifact
 -> independent exact reread
 -> second call on pre-existing target
 -> ABSTAIN at preflight
 -> action_count = 0
 -> independent reread proves zero overwrite
```

This is scoped procedure acceptance, not arbitrary workflow authority.

## Procedural-memory privacy/trust

One demonstration/success creates at most CANDIDATE. Current state outranks recorded actions/coordinates. Promotion requires replay/regression/variant evidence.

Do not persist private chain-of-thought.

Raw desktop demonstrations/ROI evidence are sensitive local data. Long-term storage requires explicit retention, redaction, secret filtering, deletion, encryption and export/sync policy.

## Resource/process boundary

Heavy local models are task-driven/on-demand and must not become always-on generic model runners or kill unrelated processes.

## Supply-chain status

- reachable Git history is secret-scanned;
- GitHub Actions are SHA-pinned where configured;
- CodeQL covers current languages/workflows;
- semantic npm dependencies are locked/pinned;
- vision Python dependency surface is pinned where specified;
- stable distribution still requires explicit artifact/hash/update policy for Python/model/OpenAdapt runtime assets.

## Historical infrastructure

Historical Yandex/Tailscale/custom universal-core and old runtime paths remain fallback/history only unless explicitly requalified. Historical docs may retain old `current`/`next` wording and must not override `CONTINUATION_CONTEXT.md`, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md`, `COMPUTER_USE_ARCHITECTURE.md`, `SECURITY_POLICY.md` and `ROADMAP.md`.

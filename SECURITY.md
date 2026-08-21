# Security Policy

Security fixes target the current `main` branch until a versioned release policy is published.

## Reporting

Do not publish tokens, API keys, private endpoints, exploit payloads or sensitive logs in public issues/PRs. Prefer GitHub private vulnerability reporting when available.

## Current normal security boundary

```text
ordinary ChatGPT
 -> OpenAI Secure MCP Tunnel
 -> official tunnel-client
 -> direct stdio semantic-projection launcher
 -> semantic-projection
 -> scoped Filesystem / isolated Playwright / focused local adapters
```

The normal semantic path does not require a local 1MCP hop. 1MCP remains internal diagnostic/adaptive infrastructure.

The project does not implement its own public ingress, relay, tunnel, credential vault or generic authorization server.

## Important terminology: tunnel control plane vs local execution Control Plane

The official tunnel path uses a credential named `CONTROL_PLANE_API_KEY`. That name refers to **OpenAI Secure MCP Tunnel infrastructure**.

The project also plans a **deterministic local execution Control Plane** for Stage 26.3: task/procedure state, capability policy, action authorization, checkpoints, verification and bounded recovery.

These are unrelated boundaries. A tunnel control-plane key does not grant local action authority, and the local execution Control Plane must not inherit tunnel credentials without explicit need.

## Current planner boundary

Ordinary ChatGPT is the only **current general planner/intelligence**. The local deterministic Control Plane is permitted to advance already-selected known procedure transitions only after current-state authorization and postcondition verification. It must not invent open-ended strategy.

A future local general planner is optional Track P research. Even if later accepted, planner output remains proposal data and cannot bypass deterministic local authorization/verifier gates.

## Secrets and child-process environment

Secrets, including the OpenAI tunnel runtime key, must never be committed. The runtime key should have only tunnel permissions required by operation and is stored locally through Windows DPAPI `CurrentUser` by the manager.

Exact tunnel-client review established that its stdio MCP child can inherit parent environment. The accepted secure launcher therefore removes tunnel/model API credentials before importing semantic-projection core.

Do not remove this boundary without proving a replacement contract.

## Capability scope

Normal semantic projection exposes only reviewed semantic operations and must not leak generic/raw backend capabilities.

Current public tools remain:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

No generic `tool_invoke`, arbitrary Playwright code/evaluate, shell/Python executor or raw backend selection is accepted as the ordinary-Chat surface.

Filesystem roots remain explicit; lexical and real Windows junction/link escapes remain security boundaries.

## Browser network boundary

The isolated Playwright profile is process/browser isolation, not a complete network sandbox.

Direct literal private/link-local/metadata/special IP destinations are restricted while reviewed loopback remains possible. DNS rebinding, hostname resolution and redirects remain residual risks if stronger private-network isolation is required.

Do not describe Playwright origin controls as a complete security boundary.

## Local vision boundary

Accepted local vision uses reviewed local image data and loopback llama.cpp.

The local VLM never performs or authorizes an action. It returns bounded proposal/evidence that is followed by deterministic class/target/freshness/identity checks.

The final screenshot-to-coordinate action boundary remains non-atomic and therefore must fail closed on stale/ambiguous evidence.

## Windows capability boundary

Windows foundations are accepted through Stage 26.2D for bounded contracts:

- authenticated loopback typed executor;
- legacy generic exec absent/disabled;
- exact PID/HWND window-scoped UIA;
- DesktopState evidence;
- native exact-window Grounder proposal-only;
- deterministic structure-first UIA -> vision routing;
- process/window/frame/target freshness checks;
- native foreground + WindowFromPoint/root-HWND/PID guard;
- action delivery separated from completion verification.

Stage 26.2D exact physically accepted head:

`1c74713edcd6321d5583a39234929169e68b5ac1`

This does not grant arbitrary desktop authority.

## Stage 26.2E real-app boundary

The active isolated VS Code qualification may perform one harmless guarded Unicode text mutation only after:

- exact TEMP containment;
- unique Code.exe PID/HWND/DesktopState;
- focused editor evidence;
- deliberate verifier mismatch -> ABSTAIN with zero mutation;
- fresh pre-action same-window/same-focused-editor fingerprint;
- native foreground/hit-test guard.

Completion requires exact saved-file SHA/size, expected-only workspace, same current window, natural window/CLI exit and cleanup/rollback. Forced process termination cannot convert a failed run to PASS.

## Deterministic procedure Control Plane security

Stage 26.3 target:

```text
ChatGPT selects goal/procedure
 -> local deterministic TaskState / ProgramGraph state
 -> current observation
 -> exactly one permitted transition
 -> capability policy + authorization
 -> bounded action
 -> postcondition verification
 -> checkpoint / advance
 -> repeat while known
 -> ABSTAIN/escalate on novel/ambiguous/stale/incompatible state
```

Neither ChatGPT, a stored procedure, a VLM, a specialist reasoner nor a future local planner grants authority by itself.

## Procedural-memory privacy

Do not persist private chain-of-thought.

Persist only structured/user-visible goal summaries, observations/state, actions/receipts, postconditions, verification and provenance needed for operation/reuse/debugging.

Raw desktop demonstrations are sensitive local data. Long-term storage requires explicit retention, redaction, secret filtering, deletion, encryption and export/sync policy.

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

Historical Yandex/Tailscale/custom universal-core and LM Studio/llmster paths are fallback/history only unless explicitly requalified. Historical docs may retain old `current`/`next` wording and must not override current `CONTINUATION_CONTEXT.md`, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `CONTROL_PLANE.md` and `ROADMAP.md`.

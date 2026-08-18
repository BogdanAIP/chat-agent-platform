# Security Policy — Bridge

## Trust boundaries

Normal public path:

```text
ordinary ChatGPT
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio secure semantic launcher
  -> semantic-projection
  -> selected focused backend(s)/adapters
```

1MCP remains internal/diagnostic where useful; it is not the normal public semantic hop.

The tunnel provides authenticated reachability. It is not a substitute for backend-level scope, truthful tool semantics, capability authorization, procedural-memory trust or product-level safety review.

## Security objective

Control consequence, scope and lifetime without making legitimate workflows impossible.

Capability lifecycle:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

- **AVAILABLE:** backend/capability is locally approved/known;
- **ACTIVE:** required process/runtime is running for the task;
- **AUTHORIZED:** the requested action is within accepted local scope plus applicable product/user policy.

Procedural-memory trust is separate. The project boundary remains candidate-first even if an upstream library uses different internal names:

```text
new / learned procedure
  -> project CANDIDATE
  -> verification / regression / variant evidence
  -> trusted reusable status
  -> stale / quarantine / disable / rollback as needed
```

An upstream `active` status is **not** automatically equivalent to product trust or action authorization.

## Chat-facing tool semantics

Prefer concrete typed actions with truthful schemas and side-effect semantics.

Current accepted public tool names are exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

The generic adaptive `tool_invoke` boundary is not the accepted ordinary-Chat product surface. `semantic-projection` must remain deterministic and non-agentic; it cannot become a hidden workflow engine, generic desktop dispatcher or arbitrary server/tool selector.

After a future Windows desktop surface exists, any public-contract expansion requires a separate architecture decision/schema review/ordinary-Chat acceptance. Do not overload harmless-looking existing tools with unrelated desktop/workflow consequence classes merely to preserve the number five.

## Browser semantic→vision authorization — ACCEPTED

Stage 25.2 browser interaction is semantic-first:

```text
fresh accessibility evidence
  -> exact enabled button -> semantic action
  -> disabled/non-button/unresolved ambiguity -> ABSTAIN, no VLM
  -> reviewed zero-exact-candidate miss only
       -> same-session capture
       -> bounded local F16 grounding
       -> deterministic authorization
       -> freshness proof
       -> one coordinate action OR ABSTAIN
```

Security rules:

- `targetText` is the authorization anchor;
- planner-supplied `kind`, alternate `target` or free-form instruction cannot redirect visual authorization;
- generic semantic click errors do not trigger vision;
- uncertain/stale/unpromoted visual evidence causes zero page mutation;
- local model output is untrusted evidence and never self-authorizes an action;
- screenshot→click remains a narrow non-atomic TOCTOU residual boundary.

## Procedural-memory security — Stage 26

A remembered workflow can carry sensitive operational context and can bias future actions. Treat it as a distinct security/privacy boundary.

Stage 26.1A qualified OpenAdapt Flow/Capture as upstream candidates on exact target-tested pins, but qualification does **not** grant production authority. No OpenAdapt dependency is product-integrated merely because install/tutorial verification passed.

### No private chain-of-thought persistence

Do not record or persist private model reasoning. Procedural traces may contain only data needed for execution/verification such as:

- user-visible/structured intent summaries;
- bounded tool/capability actions;
- structured observations/state fingerprints;
- outcome classifications;
- explicit completion/verification evidence;
- reviewed metadata needed for versioning/applicability.

### Raw demonstration retention

Raw desktop capture may contain everything visible or typed. It is sensitive local data by default.

Before arbitrary demonstrations are stored long term, define and test:

- explicit storage location and ownership;
- retention/expiry behavior;
- screenshot/text redaction rules;
- secret/credential filtering;
- path/content minimization;
- deletion and disable semantics;
- encryption-at-rest policy;
- backup/export/sync policy if later supported.

Raw capture must remain inside the explicitly selected local qualification/product directory unless a later reviewed export path is added. Raw screenshots should not automatically become permanent reusable-skill content.

### Compiled-procedure evidence rule

A compiled procedure may retain structural/native evidence and bounded pixel/template/OCR/geometry evidence, but it must not use blind historical absolute-coordinate replay as authority or primary identity.

Preferred authorization/evidence order:

```text
live structural/native/semantic evidence
  -> deterministic re-resolution
  -> bounded OCR/template/geometry/visual fallback when allowed
  -> identity/risk/freshness checks
  -> scoped action
  -> postcondition/effect verification
  -> HALT/ABSTAIN on unresolved state
```

Historical pixel evidence is evidence, not authority.

### Skill trust and poisoning resistance

- one successful run/demonstration creates at most a project candidate;
- upstream `SkillLibrary.create_skill()` immediate-active bootstrap must be wrapped by stricter product policy;
- candidate retrieval is non-authorizing;
- promotion/trust requires measured re-application/verification policy;
- malformed, incompatible or stale procedures fail closed;
- version changes preserve provenance and prior evidence rather than silently overwriting trust history;
- a remembered milestone cannot override contradictory current observed state;
- imported/upstream procedures receive no implicit local authorization.

### Completion integrity

A model/Chat completion report is not enough to advance workflow state. Use deterministic/native verification or stronger system-of-record effect evidence where available. UNKNOWN should cause further observation/HALT/ABSTAIN/user input rather than optimistic advancement.

## OpenAdapt Windows-agent security — explicit qualification boundary

The pinned OpenAdapt server has materially safer default behavior than the legacy WAA contract alone suggests:

- bounded typed `/input` and `/input/guarded` routes;
- `/uia/find`, `/uia/act`, `/uia/locator-at`, `/uia/text-at-point` structural routes;
- frame/context/focus stale checks on guarded input;
- action-delivery receipts separated from outcome verification;
- legacy arbitrary-Python `/execute_windows` route **disabled by default**.

However, product acceptance is still pending because the server runs with interactive-session authority.

Before adoption, Stage 26.1C must compare:

```text
A. OpenAdapt typed WindowsBackend + hardened local interactive-session agent
B. OpenAdapt IR/runtime + narrower native/project-owned actuator
```

The selected product configuration must prove:

1. callable authority is bounded to accepted operation classes;
2. process/session ownership is known;
3. loopback/authentication boundary is explicit;
4. stale frame/focus/context is refused before mutation;
5. ambiguous UIA targets refuse rather than pick a candidate;
6. before/after and delivery/effect evidence are preserved;
7. blast radius is understood if the local caller is compromised;
8. legacy `/execute_windows` cannot be enabled or reached through normal product configuration;
9. no generic Python/command execution surface is exposed to ordinary ChatGPT.

A qualification fixture passing does not imply arbitrary Windows application support.

## F16 / local grounding security

The accepted local LFM2.5-VL-450M F16 remains bounded perception, not a second planner.

For future OpenAdapt integration, use the narrow `Grounder` seam only:

```text
current PNG + intent + optional OCR label
  -> proposed match OR None
```

Requirements:

- local-only by default; no screenshot egress;
- focused/on-demand lifecycle and deterministic unload;
- model proposal never authorizes an action;
- identity/risk/freshness/effect checks remain authoritative;
- no new public Chat vision tool is introduced merely for the adapter.

## Windows desktop surface security — future explicit product gate

Stage 26.3 must not inherit browser-click or OpenAdapt-fixture authorization by analogy.

Before promotion, separately review:

1. native/deterministic UI observation scope;
2. screen capture scope/privacy;
3. bounded vision fallback;
4. keyboard/mouse action classes;
5. focus/window identity and stale-screen handling;
6. irreversible/external consequences and confirmation policy;
7. before/after verification;
8. process/window ownership where applicable;
9. demonstration recording boundaries;
10. recovery/HALT/ABSTAIN behavior.

Concrete local programs/capabilities are chosen from real tasks at that time; no fixed future application list is security policy.

## Secrets

- `CONTROL_PLANE_API_KEY` stays local and is never repository content.
- Long-lived runtime principal uses only permissions required by tunnel runtime unless a separate admin operation explicitly requires more.
- Manager stores runtime key via DPAPI `CurrentUser`; plaintext exists only as needed for child startup.
- Tunnel IDs and runtime secrets remain local operational configuration.
- Never commit secrets or copy them into workflow/skill metadata, logs, screenshots or documentation.
- If exposure is suspected, rotate first.
- Child backends must not inherit tunnel credentials unless explicitly required.

## Workspace/files security

- workspace paths remain rooted/scoped;
- containment accounts for Windows links/junctions, not only lexical traversal;
- writes remain within accepted roots/capability scope;
- procedural memory must not broaden a previously scoped path simply because an older trajectory referenced it.

## Browser network boundary

Current policy blocks direct literal private/link-local/metadata/non-public destinations while preserving reviewed loopback use. This is **not** a complete DNS/rebinding/redirect sandbox. Do not describe it as one. A stronger boundary remains a future decision if consequences require it.

## Bootstrap/lifecycle integrity

Accepted bootstrap/manager must preserve:

- official reviewed tunnel-client artifact path and integrity checks;
- one authoritative installed/source manager owner;
- fail-closed ambiguous/foreign runtime state;
- clean startup rollback and deterministic stop/recovery;
- secure installed semantic dependency closure;
- no tunnel-key inheritance into semantic core/downstream children without need.

Manager/tray owns lifecycle/configuration/diagnostics only. Procedural memory may have storage/state components, but the manager must not become an independent planner or authorization brain.

## Chat permission and OpenAI safety behavior

App permission mode is an additional user/product control, not the only security boundary. OpenAI safety can block a composite workflow even when local typed calls are healthy. Distinguish pre-MCP product blocking from backend failure.

Prefer scopes, reversible workspaces, backups/git/rollback and bounded tools. Reserve confirmation for genuinely consequential/hard-to-reverse effects where practical; do not force approval for every low-risk action.

## External fallback paths

Historical public/Yandex/Tailscale routes are not active security architecture. Do not extend them without a new measured requirement and review.

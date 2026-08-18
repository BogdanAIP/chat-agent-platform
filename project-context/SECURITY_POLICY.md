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

Procedural-memory trust is separate:

```text
CANDIDATE -> VERIFIED -> PROMOTED
     |          |          |
     +-------> STALE / DISABLED
```

A promoted skill is trusted procedural guidance; it is **not** blanket action authorization.

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

## Procedural-memory security — Stage 26 design

A remembered workflow can carry sensitive operational context and can bias future actions. Treat it as a distinct security/privacy boundary.

### No private chain-of-thought persistence

Do not record or persist private model reasoning. Procedural traces may contain only data needed for execution/verification such as:

- user-visible/structured intent summaries;
- bounded tool/capability actions;
- structured observations/state fingerprints;
- outcome classifications;
- explicit completion/verification evidence;
- reviewed metadata needed for versioning/applicability.

### Raw demonstration retention

Before arbitrary demonstrations are stored long term, define:

- explicit storage location and ownership;
- retention/expiry behavior;
- screenshot/text redaction rules;
- secret/credential filtering;
- path/content minimization;
- deletion and disable semantics;
- backup/export policy if later supported.

Raw screenshots should not automatically become permanent compiled-skill content.

### Skill trust and poisoning resistance

- one successful run creates at most a candidate;
- candidate retrieval is non-authorizing;
- promotion requires measured re-application/verification policy;
- malformed, incompatible or stale skills fail closed;
- version changes preserve provenance and prior evidence rather than silently overwriting trust history;
- a remembered milestone cannot override contradictory current observed state;
- imported/upstream procedures receive no implicit local authorization.

### Completion integrity

A model/Chat completion report is not enough to advance workflow state. Use deterministic/native verification where available. UNKNOWN should cause further observation/ABSTAIN/user input rather than optimistic advancement.

## Windows desktop surface security — future explicit gate

The future Stage 26.3 desktop surface must not inherit browser-click authorization by analogy.

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
10. recovery/ABSTAIN behavior.

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

## Local specialist inference security

Accepted local vision remains a bounded capability, not a second planner.

- local-only/focused serving by default;
- no arbitrary model-management/install/search/admin surface to ordinary Chat;
- use accepted local artifact/profile identities;
- resource-admit before heavy start and unload predictably;
- treat inference output as untrusted evidence;
- never let a local model grant itself capabilities or change authorization policy.

Earlier unaccepted runtime/model candidates are historical research, not current security configuration.

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

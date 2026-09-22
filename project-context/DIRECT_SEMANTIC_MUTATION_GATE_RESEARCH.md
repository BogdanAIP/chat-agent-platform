# Direct Semantic Mutation Gate — Stage Research

Status: **STAGE RESEARCH — NARROW**

Research date: 2026-09-22.

Base: `#168 / 4e940f5aa40d580183790b0a4e2ebe280b50787c`

## Stage goal

Close the remaining direct-mutation authority gap in the accepted six-tool
ordinary-Chat route without changing the public tool inventory.

The affected tools are:

```text
workspace_write
web_open
web_interact
```

The target contract is:

```text
trusted semantic-profile activation
 -> fresh capability-native pre-state
 -> one exact concrete CapabilityGrant / AuthorizationRequest
 -> Core authorization
 -> one bounded delivery
 -> fresh capability-native final-state verification
 -> PASS | FAIL | UNKNOWN
 -> reconciliation of ambiguous delivery before any equivalent redelivery
```

This stage does not add a new planner, policy engine, capability registry, public
tool, arbitrary dispatcher or durable scheduler.

## Current project baseline

The Core-v1 stack already provides:

- provider-neutral `CapabilityGrant`, `AuthorizationRequest`,
  `AuthorizationDecision`;
- `authorize_request()`;
- WorkingState / LoopGuard authorization enforcement for stateful consumers;
- Verification Kernel `ObservationRef / ExpectedEffect / PASS|FAIL|UNKNOWN`;
- independent Finish Gate for whole-task completion;
- a real concrete-grant consumer in `verified_workspace_artifact_v1`.

The ordinary semantic profile currently provides a fixed six-tool surface. The
user/operator starts that profile with one explicit `FilesRoot`.
`start-semantic-profile.ps1` rejects a whole drive and several broad/system
roots. The launcher canonicalizes that root and proves it is disjoint from
private manager/reviewer state.

Browser execution is an isolated Playwright profile with fixed reviewed network
policy. Direct non-public/metadata destinations are rejected while public
HTTP(S) and loopback remain admitted.

### Current direct-mutator behavior

`workspace_write`:

```text
validate rooted relative path
 -> filesystem MCP write_file
 -> return backend result
```

It has no project-owned fresh post-write byte verification.

`web_open`:

```text
validate URL/network policy
 -> fresh browser observation
 -> browser_navigate
 -> fresh observation
 -> project Verification Kernel
```

`web_interact`:

```text
normalize bounded expected effect
 -> fresh browser observation
 -> prove expected effect is not already satisfied/unknown
 -> one click/type (semantic or reviewed visual fallback)
 -> fresh observation
 -> project Verification Kernel
```

Browser verification is already strong when delivery returns normally.

None of these three paths currently consumes the new Core capability-grant
contract.

## Confirmed problem evidence

### P1 — direct semantic mutation bypasses Core grant evaluation

The public `workspace_write`, `web_open` and `web_interact` handlers call
filesystem/Playwright mechanics directly. Tool availability and schema bounds are
real controls, but there is no `CapabilityGrant -> AuthorizationRequest`
decision before the physical action.

That is inconsistent with the Core-v1 boundary now being frozen:

```text
AVAILABLE != ACTIVE != AUTHORIZED
provider/tool availability != action authority
```

### P2 — workspace_write trusts delivery acknowledgement as success

The current handler returns the filesystem MCP `write_file` result without an
independent project observation of the final bytes.

This violates the accepted project invariant:

```text
delivery != effect success
```

and is materially weaker than the accepted workspace-artifact procedure.

### P3 — browser delivery acknowledgement loss can leave the effect ambiguous

Both Browser paths assign the downstream result only after the awaited provider
call returns. If the browser physically mutates but the backend call rejects or
transport acknowledgement is lost before the result reaches the projection, the
catch path can return an error without first reconciling fresh browser state.

The physical effect may therefore have happened while delivery acknowledgement is
unknown.

This is the classic ambiguous-side-effect failure: Stripe documents that a remote
operation can succeed while the connection breaks before the caller receives the
answer, leaving retry safety unknown. AWS likewise recommends stable
idempotency/correlation for mutating operations and warns against retrying
non-idempotent effects blindly.

Sources:

- https://stripe.com/blog/idempotency
- https://docs.aws.amazon.com/wellarchitected/2025-02-25/framework/rel_prevent_interaction_failure_idempotent.html
- https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html

CAP does not need to copy their storage/token implementation here; the relevant
lesson is that transport failure is not proof of non-application.

## Authorization-domain evidence

Cedar models every authorization question as explicit
`principal + action + resource + context`. Its current guidance also
distinguishes agent identity from the user/on-behalf-of context.

- https://docs.cedarpolicy.com/auth/authorization.html
- https://docs.cedarpolicy.com/bestpractices/bp-using-the-context.html
- https://docs.cedarpolicy.com/bestpractices/bp-authorization-patterns.html

OPA separates the Policy Decision Point from the Policy Enforcement Point and
recommends fail-closed/local enforcement where appropriate.

- https://www.openpolicyagent.org/docs
- https://www.openpolicyagent.org/docs/deploy

MCP authorization protects access to MCP servers/tools through transport/OAuth
authorization. Current MCP Apps guidance supports per-server/per-tool OAuth
protection, and current SDK guidance treats OAuth as transport authorization.

- https://apps.extensions.modelcontextprotocol.io/api/documents/authorization.html
- https://ruby.sdk.modelcontextprotocol.io/client/authorization/

These mechanisms solve different layers. An MCP token or the ability to invoke a
tool is **not** evidence that one exact local CAP consequence is authorized.

### Solution conclusion from external evidence

No external policy engine is required. CAP already owns the exact
principal/action/resource-style grant decision. What is missing is:

1. a trustworthy active-scope source for the ordinary semantic runtime;
2. capability-specific attenuation from that scope to one exact request;
3. fail-closed fresh verification/reconciliation after delivery.

## Architecture lineage

| Role | Existing owner | Decision |
|---|---|---|
| user goal/general planning | ordinary ChatGPT | **KEEP** |
| capability activation/profile | project semantic profile + launcher | **REFINE** — make activation identity explicit |
| exact effect authorization | CAP Core | **REUSE_MORE** — use existing CapabilityGrant contract |
| Files scope interpretation | project semantic Files adapter | **KEEP/REFINE** |
| Browser URL/control/network interpretation | project Browser semantic adapter | **KEEP/REFINE** |
| Browser physical execution | Playwright MCP | **KEEP** |
| Files physical execution | filesystem MCP | **KEEP** |
| Browser final verification | project Browser Verification Kernel bridge | **REUSE_MORE** |
| Files final observation | project file_artifact_observation | **REUSE_MORE** |
| MCP/OAuth authorization | transport/backend boundary | **KEEP separate** |
| CapabilityRegistry/EventBus | ADR-037 future | **DEFER** — not required for this gate |
| OPA/Cedar runtime | none | **REJECT for this stage** |
| universal generic provider/invoke API | none | **REJECT** |

No accepted baseline role is replaced.

## New/narrow architecture primitives

### 1. SemanticActivationContext

A non-public, process-lifetime project state created by the trusted semantic
launcher **after** canonical startup scope validation.

Minimum contents:

```text
activation_ref       random bounded identity created by launcher
activation_version   semantic-activation-v1
workspace_root       canonical startup FilesRoot
browser_policy_ref   pinned isolated-browser policy version
```

Properties:

- overwritten/generated by the launcher, never accepted from a Chat tool call;
- not a public MCP argument;
- not environmental page/file content;
- not persisted across profile restart;
- provider subprocesses do not receive the activation context;
- profile restart creates a new `activation_ref`, making prior decisions stale.

The context is not a new general grant database. It is the truthful identity of
the already-existing semantic-profile activation/lifetime.

### 2. Capability-specific attenuation

The active profile scope is broader than one concrete effect. The adapter already
owns resource semantics, so it performs only its existing reviewed validation,
then derives one exact Core grant for the normalized request.

Files:

```text
active canonical workspace root
 + validated rooted relative target
 + exact UTF-8 content SHA-256/size
 -> concrete workspace.write grant
```

Browser navigation:

```text
active isolated-browser policy
 + fresh before observation
 + accepted canonical HTTP(S)/loopback URL
 -> concrete browser.navigate grant
```

Browser interaction:

```text
active isolated-browser policy
 + fresh before observation/fingerprint
 + exact click/type target
 + bounded action parameters
 + declared ExpectedEffect
 -> concrete browser.click/type grant
```

The Chat/model call supplies the requested action. It does **not** supply or
construct the activation identity.

### 3. Fresh post-effect reconciliation

Every direct mutation must re-observe even when the provider delivery call errors
after initiation.

- Files use the existing race-aware `file_artifact_observation` mechanism to
  prove exact final path/size/SHA or return UNKNOWN/FAIL.
- Browser uses the existing fresh snapshot + Verification Kernel bridge.
- No automatic blind retry is added.
- A later equivalent call must first observe current state; if the expected
  effect is already satisfied, it performs no second physical action.

## Approaches compared

### A. Treat each public tool call as its own grant — REJECT

The planner/model would effectively mint authority by asking for the action.
This collapses request and permission and contradicts
`tool availability != authorization`.

### B. Add OPA/Cedar/CapabilityRegistry now — REJECT/DEFER

A general policy runtime/registry could represent these decisions but introduces
policy storage, lifecycle, distribution/discovery and another failure domain.
There are only three current direct semantic mutators and the Core already has the
required exact-match decision primitive.

### C. Static broad allow for the whole semantic process — REJECT

A single `semantic-profile-can-mutate` boolean would not bind exact target,
content, current browser observation or expected effect. It would preserve broad
ambient authority rather than use the new Core contract.

### D. Ephemeral launcher activation + capability-specific attenuation + Core exact grant — SELECT

This reuses existing activation/profile scope and existing Core authorization.
It adds only a per-process activation identity and exact request derivation.

### E. Force every direct semantic action into durable WorkingState — DEFER

Durable WorkingState is necessary when CAP owns retries/recovery/history across
calls. The current direct semantic handlers perform one action per call and do not
automatically retry. Browser next-call safety is enforced through fresh expected-
effect preflight; workspace write is idempotent and will gain fresh exact-byte
verification.

A durable per-chat task identity is not currently available on this route. Adding
one only to satisfy a storage shape would create a new session/task subsystem.

If a future direct semantic flow gains automatic retries, multi-step recovery or
cross-call continuation, re-enter research and promote it to WorkingState.

## Failure / crash matrix

| Boundary | Possible state | Required behavior |
|---|---|---|
| before profile activation | no active semantic scope | mutating tools unavailable/fail closed |
| inherited environment contains fake activation fields | caller/local env tries to preseed authority | launcher overwrites/removes; only launcher-created activation accepted |
| after activation, before tool call | active scope, no concrete effect | no physical action |
| request path escapes workspace | active Files profile but foreign resource | reject before grant/effect |
| browser URL violates network policy | active Browser profile but foreign destination | reject before grant/effect |
| environmental page/file text requests broader authority | untrusted evidence | cannot alter activation/grant |
| exact request authorized, page/file changes before delivery | stale pre-state possible | provider/action may fail; post-state must verify; no success from grant alone |
| provider rejects before effect | no effect | fresh observation may prove not applied; no blind retry inside handler |
| effect happens, ACK lost | physical effect + delivery unknown | always fresh re-observe; PASS if exact effect proven, otherwise FAIL/UNKNOWN |
| post-observation unavailable/ambiguous | physical state unknown | return UNKNOWN/error; no automatic repeat |
| profile process restarts | old activation_ref dead | new activation_ref; old authorization result unusable |
| provider process receives environmental/tool data | provider may be compromised | provider never receives launcher activation context; provider success cannot mint grant |
| second identical web call after prior ambiguous effect | state may already satisfy expected | fresh preflight detects already-satisfied and performs zero second effect |
| second identical workspace write | file may already equal requested bytes | fresh pre-state may return verified no-op; otherwise exact idempotent write + fresh verify |
| parameters change while reusing an operation identity | semantic mismatch | exact resource/request fingerprint changes; old decision cannot authorize |
| browser backend reports success but final state disagrees | bad/partial effect | Verification Kernel FAIL/UNKNOWN, never PASS |
| filesystem backend reports success but bytes disagree | bad/partial effect | file observation FAIL/UNKNOWN, never success |

No release-critical matrix cell requires blind retry.

## Failure shields before code

The first implementation must prove:

1. public tool schemas remain exactly six and expose no activation/grant fields;
2. inherited activation environment cannot choose the launcher's activation ref;
3. provider child environments exclude activation state;
4. activation ref changes across launcher lifetimes;
5. exact request/grant fingerprints change with resource/action/content/before-state;
6. wrong activation/resource/action is blocked before provider delivery;
7. `workspace_write` independently proves final exact bytes;
8. injected filesystem delivery-ACK loss reconciles final bytes before response;
9. injected browser delivery-ACK loss still performs fresh snapshot verification;
10. browser expected-already-satisfied preflight delivers zero second action;
11. provider success without final verification cannot become semantic success;
12. current six-tool inventory and procedure_run behavior are unchanged.

## Implementation slices

### Slice 1 — activation + Files direct mutation

- launcher-owned `SemanticActivationContext`;
- private capability-specific authorizer bridge using the existing Core
  `CapabilityGrant / AuthorizationRequest`;
- provider environment scrub;
- `workspace_write` exact path/content grant;
- race-aware before/fresh-after file observation;
- verified no-op when exact requested bytes already exist;
- reconcile provider ACK loss from fresh file state.

### Slice 2 — Browser direct mutation

- exact activation-bound `web_open` and `web_interact` requests;
- bind browser request to fresh before observation;
- keep existing URL/network/expected-effect policy;
- always fresh re-observe after an initiated delivery, including provider error;
- no blind retry;
- expose delivery acknowledgement separately from final verification.

Keeping these slices separate makes Files and Browser failure models independently
reviewable while sharing only the already-accepted Core authorization primitive.

## Explicit non-goals

Do not add:

- a seventh public tool;
- dynamic CapabilityRegistry/EventBus runtime;
- OPA/Cedar service;
- user-authored arbitrary policy expressions;
- a generic grant store;
- durable ordinary-Chat session identity;
- automatic retries;
- browser persistence/recovery;
- raw provider tool exposure;
- provider-owned authorization;
- Rust Native Host implementation in this stage.

The roadmap's Rust Native Host v1 remains the next systems-host stage after Core
v1 completion/freeze. This work should make its future input boundary cleaner:
the native host will receive already-authorized operations rather than becoming an
authority source.

## Acceptance ladder

L1:

- activation derivation/scrub/adversarial tests;
- exact authorization mismatch tests;
- workspace observation/verification tests;
- browser ACK-loss reconciliation tests.

L2:

- six-tool semantic acceptance;
- installed-layout Semantic Projection acceptance;
- Direct Tunnel acceptance;
- existing Browser verification/vision fallback regressions;
- Stage 26.3A/Windows regressions;
- full CI/security.

L3:

This changes the ordinary semantic consequence boundary but not the real-user
headed browser path. Before final merge of the Browser slice, re-evaluate whether
the existing hosted isolated-Playwright physical acceptance is sufficient or
whether one target-Windows ordinary-Chat semantic call is required by the current
acceptance owner. Do not claim broader physical acceptance from unit tests alone.

Independent exact-head semantic review remains mandatory before merge.

## Decision

**NARROW**

Proceed with the two slices above.

Must-have now:

- explicit ephemeral semantic activation identity;
- capability-specific attenuation from trusted startup scope;
- existing Core exact authorization;
- independent `workspace_write` final-byte verification;
- fresh browser reconciliation after initiated delivery regardless of ACK result;
- no blind retry.

Deferred/rejected:

- general policy engine;
- CapabilityRegistry/EventBus;
- durable per-chat task/grant store;
- provider framework;
- automatic retry/idempotency ledger.

The selected design introduces no new Core authority type. It reuses the Core-v1
authorization/verification contracts and refines the existing semantic adapter
boundary.

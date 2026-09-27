# BrowserSkill Provider — Core v1 re-entry

Status: **STAGE RESEARCH — PROCEED**

This brief re-enters the BrowserSkill provider decision on the CAP Core v1 freeze head from PR #175.
It supersedes the implementation authority of the older PR #161 research, which was based on pre-Core-v1
provider/reconciliation boundaries and BrowserSkill 0.3.0.

It does **not** replace the accepted isolated Playwright provider. It authorizes implementation of a
capability-preserving BrowserSkill provider below the existing CAP Browser authority boundary.

## Stage goal

Integrate the already-built Tencent BrowserSkill runtime as a full internal Browser provider without
reimplementing its browser mechanics and without silently dropping upstream capabilities.

The provider contract must preserve the complete pinned upstream capability inventory even when CAP policy
does not yet authorize a particular consequence class.

The target shape is:

```text
ordinary ChatGPT
  -> existing CAP six-tool semantic surface
  -> CAP Browser semantic/authority layer
  -> one browser-session-scoped provider binding
       +-- accepted isolated Playwright provider
       `-- BrowserSkill provider
             -> bsk CLI / daemon / extension
             -> Chromium user profile / Agent Window
```

CAP continues to own:

- capability authorization;
- logical operation / attempt identity;
- WorkingState;
- ExpectedEffect;
- PASS | FAIL | UNKNOWN verification;
- reconciliation and no-blind-retry rules;
- LoopGuard / budgets;
- task Finish Gate.

BrowserSkill owns:

- browser connection/session mechanics;
- Agent Window lifecycle;
- tab ownership/borrow/return;
- DOM/AX/VOM refs and browser interaction;
- screenshots/canvas geometry;
- upload/download browser transaction mechanics;
- request-help UI;
- recording/debugging mechanics;
- provider-local queue/cancellation/session cleanup;
- provider receipts/effect metadata.

Provider availability or provider success never becomes CAP authorization, project PASS, or task DONE.

## Current project baseline

The implementation base for this re-entry is the CAP Core v1 aggregate freeze head:

```text
ca6923924952a2f457dc12e3604c97034a8fae23
```

At this head:

- Core is provider-neutral and explicitly forbids dependencies on browser/provider implementations;
- `CapabilityGrant` / `AuthorizationRequest` are the project-owned authority contract;
- `WorkingState` already models `VERIFIED_APPLIED`, `NOT_APPLIED`,
  `APPLIED_BUT_ACK_FAILED`, and `OUTCOME_UNKNOWN`;
- unresolved mutating outcomes block further physical mutation;
- reconciliation can resolve an ambiguous attempt only as `CONFIRMED_APPLIED`,
  `CONFIRMED_NOT_APPLIED`, or `STILL_UNKNOWN`;
- `LoopGuard` prevents replay of an already-applied logical operation and repeated identical physical effects;
- the semantic Browser path already contains ACK-loss reconciliation tests;
- Playwright remains the accepted isolated/headless provider.

Therefore BrowserSkill does **not** need its own CAP recovery framework. Its provider adapter must map
provider evidence into the existing Core semantics.

## Exact upstream source provenance

Fresh source-code research was performed on 2026-09-27.

Repository:

```text
Tencent/BrowserSkill
```

Pinned release tags:

```text
ext-v0.3.1
cli-v0.3.1
```

Both annotated tags resolve to:

```text
da6bf4eed2dd7256567e152df8c903c87f6598c3
```

Relevant inspected paths include:

```text
crates/bsk-protocol/src/method.rs
crates/bsk-protocol/src/tools/*
crates/bsk-cli/src/daemon/ipc.rs
crates/bsk-cli/src/daemon/probe.rs
crates/bsk-cli/src/daemon/ws.rs
crates/bsk-cli/src/daemon/remote/authorization.rs
packages/dsh-plugin-browserskill/src/browser-tools.ts
packages/dsh-plugin-browserskill/src/tools.ts
packages/dsh-plugin-browserskill/src/session-starts.ts
packages/dsh-plugin-browserskill/src/sessions.ts
packages/dsh-plugin-browserskill/src/debug-tool.ts
apps/extension/src/transport/daemon-endpoint.ts
docs/architecture.md
CHANGELOG.md
```

### Source-code evidence

Classification: **OPEN_IMPLEMENTED / REUSE_COMPONENT** for browser mechanics and provider lifecycle.

BrowserSkill 0.3.1 exposes typed browser/session RPC methods through `bsk-protocol`. Its `Method`
enum is exhaustive and its upstream `MethodEffect` classification has no catch-all branch: adding a new
protocol method requires an explicit upstream effect classification at compile time.

This is useful evidence but does not replace CAP's own consequence classification.

The DSH adapter exposes six grouped model-facing browser domains:

```text
browser_session
browser_page
browser_inspect
browser_interact
browser_tabs
browser_assist
```

The grouped actions include:

```text
session:
  start stop list

page:
  navigate back forward reload wait

inspect:
  observe snapshot html screenshot console network debug

interact:
  click hover wheel scroll-to focus blur fill select press

tabs:
  list create select close borrow return

assist:
  resize emulate request-help
```

The underlying protocol additionally contains capabilities that are not all represented by CAP's current
public Browser semantics:

```text
browser.list
upload / download / transfer lifecycle
full-page screenshot + screenshot read/release
evaluate
record start/stop/await
debug/network control
audit.request
cancel
system/handshake/status
session tracked-start/request lifecycle
```

BrowserSkill 0.3.1 also introduced or strengthened:

- recoverable session starts with request identity;
- daemon IPC verification and process identity checks used for daemon management;
- explicit browser profile selection;
- task-scoped debugging and network-control evidence;
- background controlled tabs;
- session-start recovery;
- page-content-as-data guidance;
- authenticated remote gateways.

### Session ownership/recovery evidence

`packages/dsh-plugin-browserskill/src/session-starts.ts` implements request-identified session-start
lifecycle with prepare/register/claim/cancel/reconcile states. The adapter journal preserves pending cleanup,
and stop retry can target the original request identity even when a short session id is reused or was never
returned.

`sessions.ts` rejects unknown/foreign session ids rather than adopting them.

CAP should **reuse** these mechanics instead of creating another BrowserSkill session database or
provider-local exactly-once framework.

### Ambiguous-effect evidence

BrowserSkill's architecture documents browser-side transfer results with effect states such as
`none`, `committed`, and `unknown`. Its own guidance states that transport timeout cannot prove that
Chrome did not apply an effect.

This aligns with CAP Core:

```text
provider delivery ambiguous
  -> CAP OUTCOME_UNKNOWN / APPLIED_BUT_ACK_FAILED
  -> fresh authoritative observation
  -> reconciliation
  -> no blind replay
```

Exploratory ordinary-Chat BrowserSkill runs on 2026-09-27 independently reproduced the same class:

- owned session loss made the old workflow unusable;
- a fresh acquire restored provider execution context;
- a persistent external effect remained observable after complete BrowserSkill-session loss;
- a deliberately discarded action acknowledgement reconciled as already applied;
- no duplicate write was issued.

These runs are development evidence, not formal release acceptance.

## Capability-preservation invariant

The previous "first slice" framing is removed as an implementation strategy.

The BrowserSkill adapter must have a **complete pinned capability manifest**. Every upstream provider method
or grouped action at the selected BrowserSkill version must have exactly one CAP classification.

Allowed classifications are:

```text
PROVIDER_INTERNAL
READ_ONLY_EVIDENCE
TRANSIENT_INPUT
BROWSER_MUTATION_EXISTING_CAP_CONTRACT
CROSS_CAPABILITY_GRANT_REQUIRED
NEW_CONSEQUENCE_CONTRACT_REQUIRED
HUMAN_ASSIST
```

No capability may be silently omitted.

For each manifest entry record at minimum:

```text
upstream_method
upstream_version
effect_class
CAP semantic family
authorization requirement
ExpectedEffect / verification requirement
reconciliation rule
provider-session requirement
file/network/privacy consequence flags
runtime enablement status
blocked_reason when not authorized
```

### Fail-on-unclassified rule

A new or changed BrowserSkill capability must never disappear because the CAP adapter has not noticed it.

Required guard:

```text
pinned BrowserSkill inventory
        vs
CAP BrowserSkill capability manifest
        ↓
exact set comparison
        ↓
unknown / removed / reclassified capability
        => test/startup failure
```

The provider must also fail closed on a BrowserSkill runtime/protocol version outside the reviewed compatible
set.

This is the primary protection against the failure mode:

```text
BrowserSkill gained capability X
CAP forgot capability X
integration silently stayed incomplete
```

## Capability policy at this stage

"Full provider integration" means **full inventory and adapter awareness**, not "give ordinary ChatGPT every
upstream privilege through an existing misleading CAP tool".

### Existing CAP Browser consequence family

These can be implemented through the existing Browser semantic/authority path, subject to exact grants and
verification:

```text
session lifecycle needed by provider ownership
browser/profile discovery needed for exact target binding
page navigate/back/forward/reload/wait
observe/snapshot/html
screenshot and screenshot lifecycle
console/network read evidence
click/hover/wheel/scroll/focus/blur/fill/select/press
tab list/create/select/close
window resize / emulation
request-help lifecycle
cancel/cleanup needed to terminate owned work
```

Borrow/return of an existing user tab is included in the provider inventory and implementation, but it is
a stronger authenticated-user-browser effect and must be authorized by an exact Browser scope rather than
treated as ordinary isolated-tab discovery.

### Cross-capability consequence

Upload/download/transfer are implemented provider capabilities but also cross the Browser <-> Files boundary.

They must not be omitted from the adapter. They require a file-disclosure/import grant and exact file
identity/size/path evidence before being enabled by CAP.

Status:

```text
adapter inventory: REQUIRED
provider transport support: REQUIRED
CAP execution authority: requires cross-capability grant
```

### New consequence contracts

The following remain fully represented in the manifest but cannot be smuggled through current
`web_interact` semantics:

```text
tool.evaluate / arbitrary page script
debug rule_add / rule_enable / replay
remote/server BrowserSkill authority
record/audit retention where privacy policy is consequence-relevant
```

They are not "forgotten" and do not require later adapter rediscovery. They remain blocked until CAP has a
truthful reviewed consequence/security contract for that authority class.

This preserves the current architecture rule that a genuinely new consequence class is not hidden behind a
provider seam.

## Provider binding rule

Provider selection is bound at browser execution/session scope, not chosen independently for each action.

Required invariant:

```text
one CAP browser execution scope
  -> one provider identity + provider generation
  -> provider-native observations/refs
  -> provider-native actions
  -> fresh provider-native re-observation
```

Do not permit:

```text
observe via Playwright
  -> click via BrowserSkill
  -> reuse Playwright ref
```

Provider refs such as BrowserSkill `@eN` are valid only for their source observation generation.

## Local peer / transport security re-evaluation

The old PR #161 conclusion treated local peer authentication as a blanket production blocker.

BrowserSkill 0.3.1 changes part of that evidence:

- CLI <-> daemon uses local UDS or Windows named-pipe IPC;
- daemon discovery now verifies file/RPC PID agreement and kernel peer identity before process-management
  signaling;
- remote/server mode has explicit device pairing, credential rotation, expiry and revocation;
- the local extension WebSocket still accepts a syntactically valid `chrome-extension://<32 a-p chars>`
  Origin and the source contains a TODO for an exact extension-id allow-list;
- source comments explicitly acknowledge that a same-machine process completing the WebSocket handshake is
  possible.

Therefore the security conclusion is now scoped rather than blanket:

### Local trusted-host profile

For a local desktop deployment whose threat boundary already trusts the user's same-account local processes,
the remaining local BrowserSkill peer limitation is a **documented residual risk**, not a reason to rebuild
BrowserSkill before integration.

CAP must still:

- bind exact BrowserSkill runtime/protocol provenance;
- operate only provider-owned sessions;
- never infer CAP authority from provider reachability;
- fail closed on foreign session/browser identity;
- keep credentials/page secrets below the adapter evidence boundary.

### Hostile-local-process profile

CAP does **not** claim isolation from an already-hostile same-user local process through BrowserSkill 0.3.1
local mode.

If that becomes a product guarantee, re-enter security research for an exact-extension/native-messaging or
equivalent authenticated local peer mechanism, or evaluate BrowserSkill's authenticated server mode against
the required local/file-transfer semantics.

This stronger threat profile is outside the current local provider goal.

## Architecture lineage comparison

| Role | Prior owner/source | Current evidence | Decision |
| --- | --- | --- | --- |
| General planning | ordinary ChatGPT | BrowserSkill provides browser mechanics, not project planning | KEEP |
| Browser semantic execution | Playwright behind CAP Browser | remains accepted for isolated/headless tasks | KEEP |
| Authenticated user-browser mechanics | BrowserSkill candidate from #161 | 0.3.1 strengthens lifecycle/recovery/profile mechanics | REUSE_MORE |
| Browser observation normalization | project Browser semantic layer | provider-native refs/state must remain below CAP evidence model | KEEP |
| Capability authorization | CAP Core | provider availability/success is not authority | KEEP |
| WorkingState/reconciliation | CAP Core | already models ACK loss/UNKNOWN/no-blind-retry | KEEP |
| Verification / Finish Gate | project Kernel / Finish Gate | BrowserSkill receipts are evidence only | KEEP |
| Provider session lifecycle | BrowserSkill tracked-start + owned-session mechanics | mature current upstream mechanism; custom duplicate would add risk | REUSE_MORE |
| File transfer browser mechanics | BrowserSkill upload/download/transfer | mature mechanics exist; CAP still owns Files disclosure/import authority | REUSE_MORE |
| Raw page-script/debug-network authority | no current CAP public consequence contract | upstream supports it but existing CAP schema cannot represent authority truthfully | DEFER outside current authorized consequence scope |
| Remote BrowserSkill server | BrowserSkill authenticated remote mode | useful but not required for local desktop provider; remote file transfer differs | DEFER outside current local goal |
| Generic provider registry | none | not required for two explicit capability-specific bindings | REJECT |

No role required for the selected local BrowserSkill-provider goal remains lineage-DEFER.

## Architecture primitives and adjacent domains

The implementation relies on:

| Primitive | Domain | Rule |
| --- | --- | --- |
| pinned provider capability manifest | protocol/version compatibility | exact inventory; fail on unknown |
| browser-session-scoped provider binding | driver/session ownership | no cross-provider ref/action mixing |
| provider-owned session identity | resource ownership | never adopt foreign sessions |
| operation/attempt correlation | distributed side-effect semantics | Core identity remains authoritative |
| ambiguous delivery reconciliation | distributed systems / idempotency | observe before retry |
| provider-local serialized action queue | browser ref consistency | reuse upstream; do not duplicate |
| cross-capability file disclosure | information-flow security | separate Files grant |
| local same-user trust boundary | endpoint/security threat modeling | residual risk explicit; no false hostile-local claim |
| runtime/protocol provenance | supply-chain/runtime binding | record and gate compatible versions |

No generic EventBus, CapabilityRegistry, provider framework, second planner, new database, or host-side idempotency
ledger is required.

## Problem evidence

The accepted Playwright Browser path is intentionally isolated/headless and does not cover tasks that require
the user's existing authenticated Chromium state.

BrowserSkill already implements the missing physical mechanics:

- controlled Agent Windows in the user's browser;
- explicit browser/profile selection;
- user-tab borrow/return;
- browser-native refs and screenshots;
- human-help flow;
- file transfer;
- lifecycle recovery/cleanup;
- operation/debug evidence.

Building those mechanics again inside CAP would duplicate a mature external component and expand the project's
browser-security surface.

The older #161 "small first slice" also creates a product-management failure mode: upstream capability
growth can be silently absent from CAP. BrowserSkill 0.3.1 already added material functionality after the
0.3.0 research, demonstrating that this is not hypothetical.

## Solution evidence

The selected design reuses BrowserSkill as a complete provider while keeping project-owned authority above it.

Evidence supporting this fit:

1. BrowserSkill already separates model-facing grouped tools from internal typed operations.
2. Its protocol has explicit method/effect classification and typed schemas.
3. It has owned-session and tracked-start recovery instead of requiring CAP to invent a session manager.
4. Its own transfer semantics preserve unknown effects after timeout, matching CAP reconciliation invariants.
5. CAP Core #175 already isolates provider-specific code below provider-neutral authorization/state/verification.
6. CAP already has Browser ACK-loss tests, so BrowserSkill can plug into an existing semantic rather than create a
   new recovery layer.

## Best current approaches / alternatives

### A. Keep Playwright only

Strengths:

- already accepted;
- isolated and predictable;
- smallest authority surface.

Failure for this goal:

- does not provide the existing logged-in browser/profile/session outcome.

Decision: **KEEP as default isolated provider, insufficient alone.**

### B. Full BrowserSkill provider under CAP

Strengths:

- reuses Agent Window/session/tab/ref/file/help/debug mechanics;
- current upstream has stronger recovery than the previously researched release;
- directly covers the authenticated-user-browser gap;
- avoids rebuilding a browser-control stack.

Risks:

- broader authority over the real browser profile;
- local same-user peer trust is weaker than remote device-auth mode;
- some upstream consequences exceed current CAP Browser public semantics.

Decision: **SELECT / REUSE_COMPONENT with complete capability manifest and CAP authority gates.**

### C. Direct Playwright/CDP attachment to the user's existing Chromium

Strengths:

- fewer external components;
- reuses current CAP Playwright familiarity.

Weaknesses:

- lower-fidelity CDP attachment than Playwright's native protocol path;
- no BrowserSkill Agent Window lifecycle;
- no upstream borrow/return ownership UX;
- no BrowserSkill tracked session-start recovery;
- no BrowserSkill file/help/audit/debug product mechanics.

Decision: **retain as fallback/reference; not selected.**

### D. Raw BrowserSkill tools directly exposed beside CAP

Strengths:

- least adapter work;
- immediate full feature reach.

Failure:

- bypasses CAP authorization/ExpectedEffect/reconciliation/Finish Gate;
- lets provider tool semantics become public authority;
- makes new BrowserSkill methods silently become new CAP consequences.

Decision: **REJECT.**

### E. BrowserSkill authenticated remote/server mode as the local integration path

Strengths:

- explicit pairing/credential rotation/revocation.

Weaknesses:

- solves a stronger/different transport threat;
- adds remote/TLS/server lifecycle;
- remote upload/download are unsupported;
- unnecessary for the selected same-user local-host profile.

Decision: **DEFER for remote/hostile-local threat profiles.**

## Failure / crash matrix

| Boundary | Possible state | Required CAP/provider behavior |
| --- | --- | --- |
| before provider session start | no session | no provider effect |
| tracked start prepared, no physical session | prepared request | reconcile/cancel exact request; no second blind start |
| session created, start ACK lost | owned session may exist | query tracked request/session state; never start another blindly |
| foreign session visible | not CAP-owned | refuse adoption/action |
| observation produced | refs belong to one provider generation | bind ref to exact observation/session/tab |
| page changes before action | ref may be stale | action may fail; fresh observe required |
| mutation dispatched, ACK received | effect still not proven | fresh observation + ExpectedEffect |
| mutation dispatched, ACK lost | effect may exist | Core UNKNOWN/ACK_FAILED -> reconcile; no blind retry |
| session disappears after possible effect | provider context lost, external page effect may persist | fresh provider session/authoritative external observation where possible; reconcile or ABSTAIN |
| provider reconnect succeeds | connection restored only | never infer prior effect absence |
| action returns partial/completed-steps | some effects already occurred | preserve completed evidence; do not replay whole chain |
| upload dispatch ambiguous | file may already be attached | cross-capability reconciliation; no re-upload without proof |
| download ambiguous | browser/server effect may have occurred | reconcile destination/provider transfer state before repeat |
| user tab borrowed | user-visible tab ownership changed | exact ownership record; return only owned borrowed tab |
| process/controller exits with owned session | browser resources may remain | upstream exact-id cleanup/reconciliation; never stop foreign sessions |
| BrowserSkill version differs | capability contract may have changed | fail closed before effect |
| new upstream method appears | CAP classification missing | inventory test/startup failure |
| provider says success but postcondition disagrees | bad/partial effect | CAP FAIL/UNKNOWN |
| same-user hostile local process exists | local BrowserSkill control can be attacked outside CAP threat claim | no false isolation claim; stronger threat requires security re-entry |

No selected-scope matrix cell requires blind replay.

## Failure shields required in implementation

1. **Complete-inventory shield** — exact manifest covers every pinned upstream method/grouped action.
2. **Version shield** — unsupported BrowserSkill CLI/protocol version fails closed.
3. **Provider-scope shield** — one browser execution scope is bound to one provider/generation.
4. **Foreign-session shield** — only exact adapter-created/claimed BrowserSkill sessions are operable.
5. **Observation-ref shield** — refs cannot cross observation/session/provider generations.
6. **Authorization shield** — BrowserSkill availability never grants action authority.
7. **Unknown-effect shield** — transport/session failure after possible delivery becomes reconciliation, not retry.
8. **Verification shield** — provider success never directly maps to CAP PASS.
9. **Cross-capability file shield** — upload/download require exact Files authority.
10. **New-consequence shield** — evaluate/debug writes/remote authority cannot hide behind current web semantics.
11. **Environmental-content shield** — page/tool text remains task data, not authority.
12. **Cleanup shield** — cleanup/return affects only owned provider resources.

## Architecture decision

**PROCEED**

Implement a full capability-preserving BrowserSkill provider on top of CAP Core #175.

"Full" means:

- the whole reviewed BrowserSkill 0.3.1 inventory is represented from the beginning;
- no capability is silently deleted because CAP does not yet authorize it;
- all provider mechanics remain BrowserSkill-owned where upstream already implements them;
- every capability has an explicit CAP classification and runtime authorization status;
- unknown/new provider capabilities fail closed;
- Playwright remains an independent accepted isolated provider;
- BrowserSkill is selected per browser execution/session scope, not per individual action;
- Core authorization/WorkingState/verification/reconciliation/Finish Gate remain unchanged.

Explicitly **do not**:

- build a generic provider registry/framework;
- build another BrowserSkill session manager when tracked-start/owned-session mechanics already exist upstream;
- build a separate BrowserSkill recovery state machine;
- expose raw BrowserSkill as a public parallel tool catalog;
- map arbitrary JavaScript/debug-network writes into ordinary `web_interact`;
- claim hostile-same-user local-process isolation that BrowserSkill local mode does not provide;
- replace Playwright merely because BrowserSkill is available.

## Verification plan

### L1 — deterministic contract tests

- exact capability-manifest set equality against the pinned BrowserSkill inventory fixture;
- unknown capability/version fails closed;
- every capability has exactly one consequence classification;
- foreign session ids rejected;
- provider refs rejected across observation/session/provider generations;
- file transfer cannot run without exact Files grant;
- new-consequence methods remain explicitly blocked rather than absent;
- provider success without matching postcondition cannot become PASS.

### L2 — provider integration

On BrowserSkill 0.3.1:

- browser discovery and exact profile binding;
- tracked session start/list/stop;
- navigate/observe/snapshot/html/screenshot;
- interact actions;
- tabs create/select/close/borrow/return;
- resize/emulate/request-help;
- file-transfer transport exercised under an explicit test grant;
- debug/read/record/audit inventory confirmed;
- evaluate/debug-write/remote modes prove explicit CAP block where current consequence contracts do not admit them.

### L2 adversarial/fault injection

- session-start ACK loss;
- mutation ACK loss;
- partial action sequence;
- session loss after possible effect;
- reacquire + fresh reconciliation;
- duplicate replay attempt;
- stale ref;
- foreign session;
- provider-version drift;
- injected unclassified method;
- cleanup after controller/provider interruption.

### L3 — target Windows ordinary-Chat physical evidence

Use exact reviewed CAP head + exact BrowserSkill runtime identity:

```text
ordinary ChatGPT
 -> Secure MCP Tunnel
 -> CAP semantic Browser
 -> BrowserSkill provider
 -> real Chromium Agent Window
```

Require representative existing-profile tasks plus the ambiguity/recovery cases above.

The exploratory TodoMVC ACK-loss/reacquire test is useful precursor evidence but does not substitute for exact-head
L3 acceptance.

### Independent review

Runtime/security/recovery changes require the normal fresh exact-BASE/HEAD semantic code review before merge.

## Complexity budget

New project-owned pieces should be limited to:

1. one complete BrowserSkill capability manifest;
2. one provider adapter/binding implementation;
3. focused provider conformance/fault tests;
4. minimal provider selection/configuration at browser execution scope.

These pieces replace the need for:

- custom logged-in Chrome/session mechanics;
- custom tab borrow/return mechanics;
- custom BrowserSkill session recovery;
- one-off feature-by-feature BrowserSkill PRs.

If implementation starts adding a generic registry/event bus, second recovery framework, session database, or
BrowserSkill feature reimplementation, stop and re-enter research.

## Implementation handoff

The first implementation PR after this research must start from the same frozen Core #175 identity or re-run
bootstrap if the base changes.

Implementation order is **not** a reduced feature ladder. It is dependency order for one full provider:

```text
pin/version + complete capability manifest
  -> provider transport/session binding
  -> map all reviewed capabilities to explicit CAP classifications
  -> enable existing CAP Browser consequences
  -> enforce explicit blocks/grants for the remaining classified consequences
  -> conformance/fault tests
  -> physical qualification
```

The stage is incomplete if a BrowserSkill 0.3.1 capability has no manifest entry, even when that capability is
intentionally blocked by CAP policy.

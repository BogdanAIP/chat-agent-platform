# BrowserSkill as a CAP Browser Provider — Stage Research Brief

Status: **RESEARCH ONLY — NARROW**
Date: **2026-09-19**

This brief follows `.agents/skills/stage-research/SKILL.md` v1.2 and
`.agents/skills/source-code-research/SKILL.md` v1.0 from CAP main
`24ed938c587c9d3e2288c92bc156ccc476c955f3`.

It does not authorize production BrowserSkill routing, does not change the six-tool
public surface, and does not displace the current product sequence in `ROADMAP.md`.
The automatic-reviewer migration remains the immediate roadmap work.

## Stage goal

Determine whether Tencent BrowserSkill can become a **full-capability Browser provider
family under CAP authority** so ordinary ChatGPT can eventually use the useful
BrowserSkill capability set — including logged-in Chromium sessions, tabs, borrowing,
inspection, interaction, human assistance and file transfer — without letting
BrowserSkill replace CAP authorization, WorkingState, ExpectedEffect verification,
reconciliation, or Finish Gate semantics.

The first executable slice may be narrow, but the architecture decision is **not** to
shrink BrowserSkill to that slice. Experimental sequencing and long-horizon product
capability are separate concerns.

Desired long-horizon shape:

```text
ordinary ChatGPT
        |
        v
CAP canonical semantic surface
        |
        v
CAP Control Plane / Browser capability
        |
        +--> accepted isolated Playwright provider
        |
        `--> candidate BrowserSkill authenticated-browser provider
                  |
                  v
             real Chromium profile
```

The provider is an executor/evidence source below CAP. It is not a second planner.

## Capability-preservation invariant

This integration must not repeat the pattern where an experiment omits a capability and
the omission later becomes an accidental permanent product boundary.

Rules:

1. The exact upstream BrowserSkill feature inventory is a tracked architecture input.
2. Every feature family must remain explicitly classified as one of:
   `FIRST_SLICE`, `TRACKED_NEXT`, `BLOCKED_WITH_REASON`, or
   `REJECTED_BY_REVIEWED_DECISION`.
3. `Not in the first experiment` never means `not part of the product target`.
4. A capability may move to `REJECTED_BY_REVIEWED_DECISION` only through an explicit
   architecture/security decision with evidence. Silence, omission and schema
   convenience do not count.
5. Every BrowserSkill-adapter implementation PR must update this matrix when support
   changes, so missing capabilities remain visible until resolved.
6. The current six-tool CAP surface is the current accepted contract, not an eternal
   ceiling. If a BrowserSkill consequence class cannot be represented truthfully through
   the existing semantic tools, CAP must review a truthful public-surface extension
   rather than hide or discard the capability.
7. Provider choice must not be exposed as an arbitrary raw backend dispatcher, but CAP
   may later expose explicit user/planner semantics for authenticated browser/profile/tab
   selection when that consequence class is reviewed and accepted.

### BrowserSkill v0.3.0 capability inventory

| BrowserSkill capability | Long-horizon CAP target | First executable slice |
| --- | --- | --- |
| session start / stop / list | preserve | `FIRST_SLICE` |
| navigate | preserve | `FIRST_SLICE` |
| back / forward / reload / wait | preserve | `TRACKED_NEXT` |
| observe | preserve | `FIRST_SLICE` |
| snapshot / HTML | preserve | `TRACKED_NEXT` |
| screenshot | preserve | `TRACKED_NEXT` |
| console / network inspection | preserve as bounded read-only evidence | `TRACKED_NEXT` |
| click / fill | preserve | `FIRST_SLICE` |
| hover / wheel / scroll-to / focus / blur / select / press | preserve | `TRACKED_NEXT` |
| user/agent/all tab list | preserve | `TRACKED_NEXT` |
| tab create / select / close | preserve | `TRACKED_NEXT` |
| **borrow existing user tab / return** | **core authenticated-browser target; preserve** | `BLOCKED_WITH_REASON` only until local-auth + lifecycle gates are solved |
| resize / emulate | preserve | `TRACKED_NEXT` |
| request-help / human handoff | preserve | `TRACKED_NEXT` |
| upload / drop-upload | preserve as separate file-disclosure consequence | `BLOCKED_WITH_REASON` pending file authority/effect design |
| download | preserve as separate file-ingest consequence | `BLOCKED_WITH_REASON` pending destination/effect design |
| multiple connected browsers / instance-id or label selection | preserve | `BLOCKED_WITH_REASON` pending identity/routing acceptance |
| remote/server BrowserSkill mode | preserve in inventory; adopt only after separate network/auth research | `BLOCKED_WITH_REASON` |
| evaluate / raw page script | preserve in inventory; requires explicit high-authority decision | `BLOCKED_WITH_REASON` |
| record / trace capture | preserve in inventory; requires privacy/retention/provenance decision | `BLOCKED_WITH_REASON` |
| BrowserSkill audit/effect metadata | reuse where useful as evidence/provenance | `TRACKED_NEXT` |

No BrowserSkill capability in this table is rejected by this brief. The only rejected
architecture pattern is **raw BrowserSkill directly exposed as an unrestricted parallel
authority that bypasses CAP**.

## Current project baseline

At CAP main `24ed938c587c9d3e2288c92bc156ccc476c955f3`:

- ordinary ChatGPT is the only current general planner;
- the accepted public surface remains exactly
  `workspace_read`, `workspace_write`, `web_open`, `web_observe`,
  `web_interact`, `procedure_run`;
- the accepted Browser provider is isolated/headless Playwright/Chrome;
- `browser_observation.py` normalizes browser evidence without owning a browser;
- `browser_transition.py` binds explicit before/after observations to
  `ExpectedEffect` and returns `PASS | FAIL | UNKNOWN`;
- semantic projection intentionally exposes no browser/backend selector;
- ADR-036 already reserves a future Authenticated Browser Companion for a
  user-approved logged-in profile while keeping credentials inside the browser boundary.

Relevant CAP owners:

- `project-context/ARCHITECTURE.md`
- `project-context/ROADMAP.md`
- `project-context/SECURITY_POLICY.md`
- `project-context/BROWSER_HARNESS_ARCHITECTURE.md`
- `project-context/ARCHITECTURE_REUSE_BASELINE.md`
- `runtime/control_plane/browser_observation.py`
- `runtime/control_plane/browser_transition.py`
- `runtime/semantic-projection/bin/semantic-control-plane-projection.mjs`

## Exact upstream source provenance

BrowserSkill was inspected at the exact source commit shared by all three v0.3.0 tags:

```text
Tencent/BrowserSkill
commit: 75e2c64abaf4b7cc75682d94b0c1fd5db0cbd5e5
cli-v0.3.0        -> 75e2c64...
ext-v0.3.0        -> 75e2c64...
dsh-plugin-v0.3.0 -> 75e2c64...
research date: 2026-09-19
```

Material paths inspected:

- `docs/architecture.md`
- `crates/bsk-cli/src/daemon/ws.rs`
- `crates/bsk-cli/src/daemon/browsers.rs`
- `packages/dsh-plugin-browserskill/src/index.ts`
- `packages/dsh-plugin-browserskill/src/browser-tools.ts`
- `packages/dsh-plugin-browserskill/src/sessions.ts`
- `skill/SKILL.md`
- `apps/extension/PRIVACY.md`

Upstream exact-ref links:

- https://github.com/Tencent/BrowserSkill/blob/75e2c64abaf4b7cc75682d94b0c1fd5db0cbd5e5/docs/architecture.md
- https://github.com/Tencent/BrowserSkill/blob/75e2c64abaf4b7cc75682d94b0c1fd5db0cbd5e5/crates/bsk-cli/src/daemon/ws.rs
- https://github.com/Tencent/BrowserSkill/blob/75e2c64abaf4b7cc75682d94b0c1fd5db0cbd5e5/crates/bsk-cli/src/daemon/browsers.rs
- https://github.com/Tencent/BrowserSkill/blob/75e2c64abaf4b7cc75682d94b0c1fd5db0cbd5e5/packages/dsh-plugin-browserskill/src/browser-tools.ts
- https://github.com/Tencent/BrowserSkill/blob/75e2c64abaf4b7cc75682d94b0c1fd5db0cbd5e5/packages/dsh-plugin-browserskill/src/sessions.ts

## Source-code evidence

### Runtime path — OPEN_IMPLEMENTED / REUSE_COMPONENT candidate

BrowserSkill's local execution path is:

```text
bsk CLI
 -> Windows named pipe / local IPC
 -> bsk daemon
 -> loopback WebSocket
 -> MV3 extension
 -> chrome.debugger / WebExtension APIs
 -> Agent Window / explicitly borrowed tab
```

The daemon tracks connected browser instances and sessions. It serializes calls per
session. A BrowserSkill session has a dedicated Agent Window, ref store, and borrow
table.

The DSH plugin demonstrates an important ownership rule worth preserving: only sessions
created by that plugin enter its `SessionRegistry`; explicit foreign session ids are
rejected and unload cleanup stops only owned sessions. This is a useful provider-local
mechanic, but CAP must own the higher-level operation/effect identity.

Lesson: **REUSE_COMPONENT**, not raw public tool exposure.

### Browser selection — OPEN_IMPLEMENTED / ADAPT_MECHANIC

`BrowserRegistry::select` proves current v0.3.0 selection semantics:

- with exactly one connected browser and no selector, select it;
- with more than one and no selector, fail as ambiguous;
- an explicit selector first matches exact `instance_id`;
- otherwise it matches one exact, case-sensitive non-empty label;
- an unknown selector fails.

The upstream tests cover one/multiple browser, instance-id, unique label, unknown and
ambiguous label cases.

CAP implication: the first adapter slice may fail closed when multiple browsers are
connected, but **multi-browser selection remains a tracked target capability**. The first
slice must not hard-code a permanent one-browser architecture. A later reviewed semantic
contract can expose explicit browser/profile selection without becoming an arbitrary raw
backend dispatcher.

### Page/action semantics — OPEN_IMPLEMENTED / REUSE_COMPONENT

The six DSH-facing BrowserSkill tools are grouped as:

```text
browser_session
browser_page
browser_inspect
browser_interact
browser_tabs
browser_assist
```

BrowserSkill refs such as `@e1` are explicitly observation-scoped and can become stale
after navigation or meaningful DOM changes. The skill instructs callers to re-observe
before subsequent interactions and to inspect state before retrying unknown effects.

CAP implication: BrowserSkill refs may be used **inside one CAP observation/action
transaction**, but must not become durable CAP identity. CAP retains its own
observation-stream and ExpectedEffect contract.

### Chrome authority — OPEN_IMPLEMENTED / high-consequence backend

BrowserSkill uses Chrome's `debugger` extension permission. Chrome's official API
documents that this transport can instrument network activity, debug JavaScript and
mutate DOM/CSS through CDP. The permission is therefore materially stronger than the
current isolated Playwright backend when attached to a user's authenticated profile.

Primary reference:
https://developer.chrome.com/docs/extensions/reference/api/debugger

### Local daemon peer-authentication boundary — OPEN_IMPLEMENTED and insufficient for production CAP use

At exact v0.3.0, `origin_allowed()` in `crates/bsk-cli/src/daemon/ws.rs` accepts any
origin with the syntactic shape `chrome-extension://<32 a-p characters>` unless
`allow_any` is enabled. The source itself contains a TODO for a real extension-id
allow-list and notes that a side-loaded extension currently passes the gate.

BrowserSkill's own privacy document also states that local mode trusts processes able to
reach the configured loopback boundary.

Open upstream security report #273 independently reports this v0.3.0 behavior:
https://github.com/Tencent/BrowserSkill/issues/273

A related open report requests per-install peer authentication:
https://github.com/Tencent/BrowserSkill/issues/118

CAP implication: loopback binding is valuable network isolation, but it is **not an
authenticated local peer boundary** in this exact release. Production use against an
authenticated user browser is therefore blocked until this boundary is fixed upstream
or an equivalent fail-closed mechanism is independently designed, researched and
accepted.

Chrome Native Messaging is a credible future authentication/transport mechanism because
its host manifest admits exact `allowed_origins` without wildcards and communicates via
stdio:
https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging

This brief does **not** select or implement Native Messaging; that would be a separate
material authority/transport change.

### Environmental-content / prompt-injection boundary — BrowserSkill gap, CAP already owns the required invariant

Open BrowserSkill issue #286 reports that BrowserSkill's agent skill does not mark page
content as untrusted policy input even though the real logged-in profile can perform
consequential actions:
https://github.com/Tencent/BrowserSkill/issues/286

CAP already has the stronger invariant in ADR-033:
environmental DOM/UI/file/message/tool output is task data, not authority.

CAP implication: do not expose raw BrowserSkill model tools as the final architecture.
Normalize BrowserSkill observations below CAP and preserve CAP trust/provenance rules.

### Session cleanup / orphan risk — OPEN upstream lifecycle gap

Open issue #279 reports that sessions require explicit `session stop`; client
disconnect/interruption does not automatically bind cleanup to the caller lifecycle and
orphan Agent Windows can remain:
https://github.com/Tencent/BrowserSkill/issues/279

CAP implication: provider-session ownership and cleanup/reconciliation are required before
production. A caller crash cannot be treated as proof that the session/action did not
exist.

### Multi-profile failure evidence

Open issue #272 reports a v0.3.0 multi-profile Yandex/Chromium case where adding a second
profile can wedge `chrome.debugger` operations until browser restart:
https://github.com/Tencent/BrowserSkill/issues/272

This is environment-specific evidence, not proof of a universal Chrome failure. It
justifies a one-browser **first physical control**, not a permanent one-browser product
boundary. Multi-browser/profile support remains explicitly tracked in the capability
inventory.

## Problem evidence

The existing CAP Browser route is accepted for isolated/headless Playwright, but does not
provide general access to the user's already-authenticated desktop Chromium profile.

That leaves a real product gap for tasks requiring existing login/session state. ADR-036
already anticipates an Authenticated Browser Companion rather than pretending isolated
Playwright satisfies that role.

BrowserSkill demonstrates the missing mechanics in running code: an Agent Window in the
real profile, explicit borrowing of user tabs, ref-based observation/action, human-help
handoff and session-scoped ownership.

The problem is therefore real: CAP lacks a production provider for the authenticated-user
browser role.

## Solution evidence

BrowserSkill is a plausible component for that role because:

1. its execution model is already a thin local CLI/daemon/extension substrate rather than
   a competing general planner;
2. it exposes structured observations and bounded browser operations that can sit below
   CAP semantic operations;
3. its session/ref/unknown-effect guidance aligns with several CAP invariants;
4. its existing user-tab borrow confirmation is useful as an additional user-control
   layer;
5. CAP can keep browser content non-authorizing and retain independent verification.

However, exact v0.3.0 has material local peer-authentication and lifecycle gaps. The
solution evidence therefore supports staged implementation. That staging narrows the
**first executable slice**, not the long-horizon BrowserSkill capability target.

## Architecture lineage comparison

| Role | Prior CAP owner/source | Decision | Reason |
| --- | --- | --- | --- |
| Default Browser execution | project Browser + Playwright | **KEEP** | Accepted isolated/headless scope remains the safe default and must not regress. |
| Authenticated user-browser role | ADR-036 Browser Companion direction, not yet production | **REFINE** | BrowserSkill is a concrete candidate for this future role; do not invent a parallel public tool family. |
| Browser observation normalization | project `browser_observation.py` | **KEEP** | BrowserSkill evidence must be normalized into CAP state; upstream output is not project authority. |
| Transition verification | project Verification Kernel | **KEEP** | BrowserSkill success/receipt is evidence, never unconditional CAP PASS. |
| Task completion | project Finish Gate | **KEEP** | BrowserSkill/session success is not user-task DONE. |
| Capability authorization | project Control Plane | **KEEP** | BrowserSkill availability/connected profile does not grant consequence authority. |
| Provider session/ref mechanics | BrowserSkill | **REUSE_MORE** for experiment | Reuse Agent Window/session/ref/borrow mechanics rather than rebuilding them. |
| Local peer authentication | BrowserSkill v0.3.0 local WS | **DEFER** production role | Exact release lacks a sufficient authenticated peer boundary for logged-in-profile production authority. |

The role-level peer-authentication DEFER is outside the selected **experimental** scope.
It blocks production promotion but does not block a local research experiment on the
owner's machine.

## Architecture primitives and adjacent domains

The narrow experiment materially relies on:

- provider session ownership;
- browser-instance identity;
- observation-scoped ephemeral refs;
- one-action delivery followed by fresh re-observation;
- ambiguous-effect reconciliation before retry;
- provider lifecycle cleanup;
- source/version/protocol provenance;
- local peer authentication as a production prerequisite.

Adjacent domains:

- browser extension privilege and CDP authority;
- local IPC/loopback authentication;
- TOCTOU between observation and browser action;
- crash/restart reconciliation;
- identity/ABA safety across reconnects;
- prompt-injection / environmental-content trust.

No new database, event bus, generic provider registry or new public tool is justified by
this experiment.

## Alternatives comparison

### A. Keep only isolated Playwright

**Owner:** current CAP Browser provider.

**Strengths:** already accepted; isolated from the user's normal profile; strongest
existing CAP test/evidence path; minimal new authority.

**Limitations:** does not satisfy the authenticated existing-session outcome.

**Decision:** KEEP as default, but insufficient alone for the new role.

### B. BrowserSkill as a CAP provider with staged capability admission

**Owner split:** BrowserSkill owns browser mechanics/session transport; CAP owns
authorization, identity above provider, ExpectedEffect, verification, recovery and
completion.

**Strengths:** real logged-in browser, Agent Window isolation within the profile,
explicit user-tab borrow, structured refs/observations, human-help mechanism, active
upstream implementation.

**Known failures/risks:** v0.3.0 local WS peer authentication is insufficient for
production; orphan/session cleanup risk; multi-profile CDP issue report; stronger
authenticated consequences; provider refs are ephemeral.

**Decision:** selected for a **research-only first adapter slice**, while the full
BrowserSkill capability inventory remains tracked and must not silently disappear.

### C. Direct Playwright `connectOverCDP` to the user's existing Chromium

Playwright officially supports attaching to an existing Chromium browser over CDP, but
documents that this connection has significantly lower fidelity than the Playwright
protocol and warns that browsers launched without Playwright's curated arguments can
break functionality:
https://playwright.dev/docs/api/class-browsertype#browser-type-connect-over-cdp

**Strengths:** fewer external components; preserves more existing CAP Playwright code.

**Limitations:** requires a suitably exposed/debuggable browser; lower-fidelity route;
does not supply BrowserSkill's Agent Window ownership, user-tab borrow confirmation,
session/ref lifecycle or human-help semantics.

**Decision:** retain as a credible fallback/reference, not selected for the first
experiment.

### D. Raw BrowserSkill directly exposed to ChatGPT

**Strengths:** already easy to use and maximizes BrowserSkill feature coverage.

**Limitations:** lets model-visible BrowserSkill authority bypass CAP's public semantic
contract, Control Plane, ExpectedEffect binding and Finish Gate; duplicates a separate
planner-facing browser surface.

**Decision:** REJECT as final CAP architecture. It may remain a temporary diagnostic tool
outside CAP while the experiment is developed.

## Failure / crash matrix

| Boundary | Possible physical state | CAP rule for narrow experiment |
| --- | --- | --- |
| Before BrowserSkill session start | no provider session | start at most once for the logical attempt |
| Start succeeds, response captured | Agent Window exists | record exact returned session/browser identity before further action |
| Start may have happened but response is lost | orphan/unknown session possible | do not blindly start again; inspect provider state or ABSTAIN |
| Before browser mutation | fresh CAP observation exists | bind ExpectedEffect and exact provider session/ref |
| Mutation returns success | effect may still differ from user goal | fresh observe; only CAP verifier can produce PASS |
| Mutation times out / transport fails | effect may be applied | classify UNKNOWN; fresh observe/reconcile; no blind retry |
| Browser/extension disconnect during action | provider session may be gone, physical effect may remain | reconnect is not proof of non-effect; reconcile from current page/system state or ABSTAIN |
| CAP/provider process exits with owned session | Agent Window may remain | best-effort exact-id cleanup only; never stop/adopt foreign sessions |
| CAP restart with old BrowserSkill sessions | provider may list stale/foreign sessions | initial experiment does not adopt them; fail closed |
| Two callers target same session | interleaving could stale refs | CAP serializes one logical transition; BrowserSkill per-session queue is additional defense |
| Browser reconnect reuses instance id | old generation may be stale | require fresh status/session identity; never infer continuity from browser label alone |
| Multiple connected browsers | ambiguous target | initial experiment refuses operation; no model guess |
| Version/protocol mismatch | semantics may differ | require tested CLI/daemon/extension protocol identity; fail closed |
| Borrowed user tab not returned after interruption | user surface remains moved/controlled | production borrow is out of scope; research test must explicitly return/stop and report failures |
| Local unauthenticated peer reaches v0.3.0 daemon | logged-in browser authority may be exposed locally | blocks production promotion of authenticated BrowserSkill provider |

## Minimum sufficient experiment architecture

No production code is authorized by this research PR. If a later implementation PR
enters the experiment, the smallest acceptable shape is:

```text
CAP web_* semantic operation
        |
        v
internal Browser provider adapter
        |
        +-- provider policy chooses Playwright OR BrowserSkill
        |   (not a model-supplied arbitrary backend string)
        |
        v
BrowserSkill CLI --json
        |
        v
CAP-normalized BrowserObservation
        |
        v
CAP Verification Kernel
```

### First executable slice — sequencing only, not the product boundary

The first physical proof is deliberately small so failures can be attributed, but every
omitted BrowserSkill feature remains in the capability-preservation matrix above.

For that first proof:

- Windows local mode is the tested environment;
- one connected BrowserSkill browser is used as the control case;
- BrowserSkill 0.3.0 / protocol 1.3 is pinned for the current probe;
- `BSK_AUTO_START=0`; host lifecycle owns daemon start/stop;
- the test starts with an adapter-created BrowserSkill session;
- the first path proves navigate -> observe -> one bounded interaction -> observe ->
  CAP verification -> stop;
- Playwright remains available so the experiment does not regress the accepted path.

The first proof does **not** establish a permanent ban on multi-browser selection,
borrowing, files, assistance, screenshots, remote mode, evaluate or recording. Those
capabilities are intentionally tracked for subsequent admission/research.

Likewise, the current six public CAP tools are not frozen as the only possible future
surface. If tabs, file transfer, human assistance or another BrowserSkill consequence
cannot be represented truthfully through current semantics, the correct response is a
reviewed surface expansion — not dropping the capability or hiding it in a generic
dispatcher.

Borrowing an existing user tab is specifically a **core target capability**, not an
optional extra. It follows the initial Agent Window proof as soon as the local-peer
authentication and lifecycle/reconciliation gates needed for authenticated user-tab
authority are satisfied.

## Mapping BrowserSkill evidence to current CAP Browser state

The adapter should normalize one fresh BrowserSkill observation into the existing CAP
browser-observation shape:

```text
BrowserSkill:
  session_id
  browser_instance_id
  tab_id
  current URL/title
  observe/snapshot text
  current refs/controls

        -> adapter ->

CAP:
  subject = provider + exact browser/session/tab identity
  url/title/document identity
  snapshot_text
  normalized controls
  complete/ambiguous/settled
  ObservationRef stream + sequence + fingerprint
```

A BrowserSkill `@eN` ref is valid only inside its source observation generation. It must
be rebound from a fresh observation after navigation or meaningful page change.

## Failure shields required before code can be called production-capable

1. **Foreign-session shield:** only exact adapter-created sessions are actionable.
2. **Multiple-browser shield:** ambiguity fails closed; no browser-name guessing.
3. **Stale-ref shield:** refs carry/resolve against fresh observation identity.
4. **Unknown-effect shield:** timeout/transport error cannot authorize blind mutation retry.
5. **Verification shield:** provider success never directly maps to CAP PASS.
6. **Environmental-content shield:** DOM/page/tool text remains ADR-033 untrusted data.
7. **Lifecycle shield:** stop/cleanup can affect only owned provider sessions.
8. **Version/provenance shield:** current accepted/tested provider version and protocol are
   proven before consequence-bearing use.
9. **Local-peer-auth shield:** required before production logged-in-profile authority; not
   satisfied by BrowserSkill v0.3.0 local mode today.

## Acceptance ladder for a future implementation PR

### L1 — deterministic adapter tests

- parse exact BrowserSkill status/session/observe results;
- reject zero/multiple browser ambiguity as specified;
- reject foreign session ids;
- prove stale refs cannot cross observation generations;
- normalize observations into current CAP verifier input;
- simulate timeout/unknown-effect and prove no automatic second mutation;
- prove provider success without matching postcondition is CAP FAIL/UNKNOWN, not PASS.

### L2 — local integration

- fake/process-backed `bsk` runner;
- one owned session start -> navigate -> observe -> bounded interaction -> observe -> stop;
- forced child failure, disconnect and malformed JSON;
- cleanup never touches pre-existing foreign sessions;
- no raw BrowserSkill tool/backend selector becomes public.

### L3 — target Windows physical experiment

On exact reviewed code and exact provider identity:

```text
ordinary ChatGPT
 -> existing CAP six-tool surface
 -> BrowserSkill internal provider
 -> one BrowserSkill Agent Window
 -> navigate a benign test page
 -> fresh semantic observation
 -> one bounded interaction with explicit expected effect
 -> fresh re-observation
 -> CAP verification PASS
 -> owned session stop
 -> independent final evidence
```

Negative gates for the **first slice**:

- an ambiguous browser target must not be guessed;
- extension disconnect -> no blind retry;
- action timeout after possible effect -> reconcile/UNKNOWN;
- raw BrowserSkill authority must not bypass CAP;
- page text attempting to widen authority remains environmental data.

The next acceptance slice must explicitly exercise existing-user-tab borrow/return,
including denial, timeout, crash/interruption and return/cleanup behavior. It may not be
silently omitted from the integration roadmap.

Production authenticated-user-tab promotion additionally requires a resolved and accepted
local peer-authentication boundary and physical borrow/return/crash tests.

## Falsification conditions

Reconsider or stop the BrowserSkill provider direction if any of these occur:

- CAP cannot obtain enough structured/fresh evidence to reuse the existing Verification
  Kernel without trusting BrowserSkill's own success verdict;
- adapter session/ref identity cannot be bound tightly enough to prevent stale/foreign
  operation;
- logged-in browser authority cannot be protected by a credible local peer-authentication
  boundary;
- BrowserSkill lifecycle ambiguity forces blind duplicate actions;
- a model-visible raw backend selector/tool catalog becomes necessary for useful operation;
- direct CDP/Playwright attachment proves materially simpler and at least as safe/reliable
  under the same physical acceptance.

## Architecture decision

**NARROW — IMPLEMENTATION SEQUENCE ONLY**

Proceed with a **research/experimental internal BrowserSkill provider adapter**, while
preserving the full BrowserSkill capability inventory as the long-horizon integration
target. `NARROW` here means the first implementation slice is bounded; it does **not**
authorize capability deletion or redefine BrowserSkill as a permanently reduced provider.

Must keep now:

- ordinary ChatGPT as sole general planner;
- CAP Control Plane authorization;
- CAP observation/ExpectedEffect/Verification Kernel;
- CAP Finish Gate;
- Playwright as the accepted default provider;
- BrowserSkill as internal executor/evidence source only;
- strict provider-session ownership and ambiguity handling;
- fail-closed unknown-effect semantics;
- ADR-033 environmental-content trust boundary.

Tracked beyond the first slice — **not rejected**:

- borrowed pre-existing user tabs and return/cleanup;
- authenticated-site mutation;
- multiple connected browsers and explicit instance/profile selection;
- tab lifecycle operations;
- screenshots, console and network evidence;
- human assistance;
- uploads/downloads;
- BrowserSkill remote/server mode;
- raw page-script evaluation;
- record/trace capture;
- any truthful CAP public-surface expansion required to represent those consequence
  classes.

Still separately research-gated:

- automatic provider fallback after an ambiguous mutation;
- Native Messaging or another local peer-authentication mechanism;
- generic provider-registry infrastructure unless a real second-provider abstraction
  justifies it.

Production promotion of logged-in-profile authority remains blocked while the v0.3.0
local peer-authentication gap is unresolved, but that security block must not be
misrepresented as product rejection of the affected BrowserSkill capabilities.

## Next implementation slice if explicitly started later

A later implementation invocation must rerun repository bootstrap against the then-live
main and open PR state. If this decision is still valid, start with the bounded Agent-Window proof and its tests,
then continue against the capability-preservation matrix. Every later implementation PR
must state which BrowserSkill rows it advances and which remain tracked/blocked. A row
may disappear only through an explicit reviewed rejection or completion, never by
omission.
